#!/bin/bash

echo "Starting Spark slave node..."
spark-class org.apache.spark.deploy.worker.Worker "spark://master:7077"
