#!/bin/bash

echo "Stopping Containers"
docker-compose stop

sleep 5

echo "Starting Containers"
docker-compose up -d

sleep 10

echo "Starting Spark Consumer"
docker exec spark-master bash scripts/start_consumer.sh
