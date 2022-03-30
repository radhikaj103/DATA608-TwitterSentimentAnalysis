from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
# from pyspark.sql import functions as F
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as sia



kafka_topic_name = "twitter"
kafka_bootstrap_servers = 'http://kafka:29092'
kafk_output_topic_name = "sentiment"

# Vader
sentiment = sia()
def sps(text):
	"Get Vader sentiment polarity compound score"
	return sentiment.polarity_scores(text)['compound']
def spsSpark(sparkDF, textColumn="tweet_body"):
	"Apply Vader sps to Spark"
	sps_udf = udf(sps, StringType())
	return sparkDF.withColumn('score', sps_udf(textColumn))

if __name__ == "__main__":
	print("PySpark Structured Streaming with Kafka Applications Started ...")

	spark = SparkSession \
		.builder \
		.appName("twitterStreaming") \
		.master("spark://spark-master:7077") \
		.getOrCreate()

	spark.sparkContext.setLogLevel("ERROR")

	# Construct a streaming DataFrame that reads from test-topic
	df = spark \
		.readStream \
		.format("kafka") \
		.option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
		.option("subscribe", kafka_topic_name) \
		.option("startingOffsets", "latest") \
		.load()
		
	twitterStringdf = df.selectExpr("CAST(value AS STRING)")
	schema = (StructType() \
		.add("tweet_id", StringType()) \
		.add("created_at", TimestampType()) \
		.add("user_name", StringType()) \
		.add("user_id", StringType()) \
		.add("retweet", BooleanType()) \
		.add("tweet_body", StringType()) \
		.add("tags", StringType()))


	twitter_df = twitterStringdf.select(from_json(col("value"), schema).alias("data"))

	print("------------------------")
	twitter_df.printSchema()
	print("------------------------")
    
	# Vader
	twitter_df=twitter_df.select("data.*")
	twitter_df=spsSpark(twitter_df)
	
	# Write to Kafka Sink
	kafka_df = twitter_df.withColumn("value", to_json(struct(twitter_df.columns)))
	query = kafka_df.writeStream \
		.format("kafka") \
		.option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
		.option("topic", kafk_output_topic_name) \
		.trigger(processingTime="5 seconds") \
		.outputMode("update") \
		.option("checkpointLocation", "/tmp/kafka-sink-checkpoint") \
		.start()

#	query = twitter_df.writeStream \
#		.trigger(processingTime='5 seconds') \
#		.format("console") \
#		.option("truncate", "false") \
#		.start()
		# .outputMode("append") \
		# .start() 

	
		
	query.awaitTermination()

	# query = twitter_df.writeStream \
	# 	.format("csv") \
	# 	.option("csv.block.size", 1024) \
	# 	.trigger(processingTime="5 seconds") \
	# 	.option("checkpointLocation", "checkPoi/") \
	# 	.option("path", "cry/") \
	# 	.outputMode("append") \
	# 	.start() \
	# 	.awaitTermination()



	print("------------------------")
	print("PySpark Structured Streaming with Kafka Application Completed.")