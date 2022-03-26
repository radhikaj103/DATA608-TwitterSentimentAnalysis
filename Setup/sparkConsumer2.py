#from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
#from pyspark.ml.feature import Normalizer, StandardScaler
from pyspark.sql import functions as F
from textblob import TextBlob
import random
import time



kafka_topic_name = "twitter"
kafka_bootstrap_servers = 'http://kafka:29092'

def preprocessing(df):
    words = df.select(explode(split(df.Text, " ")).alias("word"))
    words = words.na.replace('', None)
    words = words.na.drop()
    words = words.withColumn('word', F.regexp_replace('word', r'http\S+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '@\w+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '#', ''))
    words = words.withColumn('word', F.regexp_replace('word', 'RT', ''))
    words = words.withColumn('word', F.regexp_replace('word', ':', ''))
    return words

# text classification
def polarity_detection(text):
    return TextBlob(text).sentiment.polarity
def subjectivity_detection(text):
    return TextBlob(text).sentiment.subjectivity
def text_classification(words):
    # polarity detection
    polarity_detection_udf = udf(polarity_detection, StringType())
    words = words.withColumn("polarity", polarity_detection_udf("word"))
    # subjectivity detection
    subjectivity_detection_udf = udf(subjectivity_detection, StringType())
    words = words.withColumn("subjectivity", subjectivity_detection_udf("word"))
    return words

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
	df.printSchema()
		
	twitterStringdf = df.selectExpr("CAST(value AS STRING)", "timestamp")
	schema = (StructType() \
		.add("DateTime", StringType()) \
		.add("Text", StringType()))

	#schema = "text STRING"
	twitter_df = twitterStringdf.select(from_json(col("value"), schema).alias("data"), "timestamp")

	print("------------------------")
	twitter_df.printSchema()

	twitter_df2 = twitter_df.select("data.*", "timestamp")
	twitter_data = twitter_df.select("data.Text")
	print("------------------------")
	#twitter_df2.printSchema()
	
	# Preprocessing for Sentiment Analysis
	words = preprocessing(twitter_data)
	
    # text classification to define polarity and subjectivity
	words = text_classification(words)

	words = words.repartition(4)
    
	query = words.writeStream \
		.trigger(processingTime='5 seconds') \
		.format("console") \
		.option("truncate", "false") \
		.outputMode("append") \
		.start() 
		
	query.awaitTermination()

	print("------------------------")
	print("PySpark Structured Streaming with Kafka Application Completed.")
