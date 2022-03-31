# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 12:35:04 2022

Function: Writes Kafka Stream to InfluxDB
"""

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from kafka import KafkaConsumer
import json


db_name = 'twitter_data'
db_token = "token123"
db_url = "http://localhost:8086"
db_org = "data608_project"


class InfluxDb:
    def __init__(self, database, token, url, org):
        self.client = InfluxDBClient(token=token, url=url)
        self.database = database
        self.org = org
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)


    def write_rows(self, record):
        # Print imported tweet to Console
        # If tweet in stream does not have tag, do not push to InfluxDB
        
        print(record)
        if 'tags' in record:
            point = Point("sentiment") \
                .tag("tag", record['tags']) \
                .field("tweet_id", record['tweet_id']) \
                .field("user_id", record['user_id']) \
                .field("score", float(record['score'])) \
                .field("retweet", int(record['retweet'])) \
                .time(record["created_at"], WritePrecision.MS)
            
            self.write_api.write(self.database, self.org, point)



def main():
    print('Writing To InfluxDB')
    
    consumer = KafkaConsumer(
        "sentiment",
        bootstrap_servers=['localhost:9092'],
        enable_auto_commit=True,
        group_id=None,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')))

    db = InfluxDb(db_name, db_token, db_url, db_org)
    for message in consumer:
        message = message.value
        db.write_rows(message)
        
main()