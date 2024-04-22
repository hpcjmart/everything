#!/bin/bash

echo "Starting Spark master node..."
spark-class org.apache.spark.deploy.master.Master --ip "$SPARK_MASTER_HOST"
