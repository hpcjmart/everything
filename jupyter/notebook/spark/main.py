from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.streaming import *

from uuid import uuid1

# create a Spark session
spark = SparkSession \
    .builder \
    .master("spark://192.168.65.1:7077") \
    .appName("StreamProcessor") \
    .config("spark.cassandra.connection.host", '192.168.65.1') \
    .config("spark.cassandra.connection.port", '9042') \
    .config("spark.cassandra.auth.username", 'cassandra') \
    .config("spark.cassandra.auth.password", 'cassandra') \
    .getOrCreate()

# suppress all the INFO logs except for errors
spark.sparkContext.setLogLevel("ERROR")

# define the Avro schema that corresponds to the encoded data
tradesSchema = open('./trades.avsc', 'r').read()

@udf(returnType=StringType())
def makeUUID():
    return str(uuid1())

# define the stream to read from the Kafka topic market
inputDF = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "192.168.65.1:29092") \
    .option("subscribe", "market") \
    .option("minPartitions", "1") \
    .option("maxOffsetsPerTrigger", "1000") \
    .option("useDeprecatedOffsetFetching", "false") \
    .load()



# explode the data column and select the columns we need
expandedDF = inputDF \
    .withColumn("avroData", from_avro(col("value"), tradesSchema)) \
    .select(col("avroData.*")) \
    .select(explode(col("data")), col("type")) \
    .select(col("col.*"), col("type"))

# create the final dataframe with the columns we need plus the ingest timestamp
finalDF = expandedDF \
    .withColumn("uuid", makeUUID()) \
    .withColumnRenamed("c", "trade_conditions") \
    .withColumnRenamed("p", "price") \
    .withColumnRenamed("s", "symbol") \
    .withColumnRenamed("t", "trade_timestamp") \
    .withColumnRenamed("v", "volume") \
    .withColumn("trade_timestamp", (col("trade_timestamp") / 1000).cast("timestamp")) \
    .withColumn("ingest_timestamp", current_timestamp().alias("ingest_timestamp"))

# write the final dataframe to Cassandra
# spark handles the streaming and batching for us
query = finalDF \
    .writeStream \
    .trigger(processingTime="5 seconds") \
    .foreachBatch(lambda batchDF, batchId: \
        batchDF.write \
            .format("org.apache.spark.sql.cassandra") \
            .option("table", "trades") \
            .option("keyspace", "market") \
            .mode("append") \
            .save()) \
    .outputMode("update") \
    .start()

# create a summary dataframe with the average price * volume
summaryDF = finalDF \
    .withColumn("price_volume_multiply", col("price") * col("volume")) \
    .withWatermark("trade_timestamp", "15 seconds") \
    .groupBy("symbol") \
    .agg(avg("price_volume_multiply").alias("price_volume_multiply"))

# add UUID and ingest timestamp to the summary dataframe and rename agg column
finalsummaryDF = summaryDF \
    .withColumn("uuid", makeUUID()) \
    .withColumn("ingest_timestamp", current_timestamp().alias("ingest_timestamp")) \
    .withColumnRenamed("avg(price_volume_multiply)", "price_volume_multiply")

# write the summary dataframe to Cassandra in 5 second batches
query2 = finalsummaryDF \
    .writeStream \
    .trigger(processingTime="5 seconds") \
    .foreachBatch(lambda batchDF, batchId: \
        batchDF.write \
            .format("org.apache.spark.sql.cassandra") \
            .option("table", "running_averages_15_sec") \
            .option("keyspace", "market") \
            .mode("append") \
            .save()) \
    .outputMode("update") \
    .start()

# wait for the stream to terminate - i.e. wait forever
spark.streams.awaitAnyTermination()
