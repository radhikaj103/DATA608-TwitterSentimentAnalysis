from kafka import KafkaConsumer
import json
from time import sleep
from kafka import TopicPartition

topic_name = "sentiment"



# Create Consumer
consumer = KafkaConsumer(
    topic_name,
     bootstrap_servers=['localhost:9092'],
     
     auto_offset_reset='latest',  # earliest
     group_id = None,
     enable_auto_commit=True,
     auto_commit_interval_ms =  5000,
     #fetch_max_bytes = 128,
     max_poll_records = 2,

     value_deserializer=lambda x: x.decode('utf-8'))
     

tps = [TopicPartition(topic_name, partition_id) for partition_id in consumer.partitions_for_topic(topic_name)]

while True:
	messages = consumer.poll()
	if messages:
		for tp in tps:
			print("-------------------------")
			
			try: 
				if messages[tp]:
					for message in messages[tp]:
						print("> " + message.value)  # This prints out the tweet text
			except:
				print("Could not find data in partition: " + str(tp))




  

  
