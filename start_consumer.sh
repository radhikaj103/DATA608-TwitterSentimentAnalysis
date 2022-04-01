#!/bin/bash

spark/bin/spark-submit \
	--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0 \
	./scripts/sparkConsumer3.py