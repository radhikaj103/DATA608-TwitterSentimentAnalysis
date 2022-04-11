# DATA608-Team5
This is a project allowing the user to visualize sentiment scores from the current top 5 trending topics on Twitter. It uses a series of softwares, containers, and natural language processing tools. The microservices architecture, meaning each component of application is its own service running in its own container that communicates through APIs, is visualized. The advantages of having each service in its own container are the ability for independent modification, ease of scaling, and can add or remove remote services when required without affecting other services. Following the instructions below will let you set up the entire application.


![microservicearch](https://user-images.githubusercontent.com/100740803/162824013-b9999bd6-e238-4c12-b5e2-cb8f6f5e44a5.png)


Step 1: Account Set-Ups
- Go to the Twitter API Documentation (https://developer.twitter.com/en/docs/twitter-api), and click Sign up to create your own Developer account. Once the account is created, four secret keys are generated that are necessary to pull from the API. Store these in a config.ini file as 'api_key', 'api_key_secret', 'access_token', and 'access_token_secret'.
- Kafka?
- Docker?

Step 2: File Downloads
There are 8 files in the GitHub repository that create a pipeline from the Twitter API to an InfluxDB dashboard. Key information about the main files is explained below:
- *docker-compose.yml*: Starts all containers at once, creates a common network
	- Services: all five containers in application.
		- **Zookeeper**: Official image from Confluent Inc.
		- **Kafka**: Image from Confluent inc.
		- **Spark-master**
		- **Spark-worker-1**
		- **influxDB**: timeseries DB for storing data and visualization
		- init-kafka: Initializing by creating two topics: twitter (ingests data from Twitter API into Kafka server) and sentiment (ingests processed data from Spark with sentiment scores into Kafka)
- *twitterProducer.py*: Twitter producer script that pulls tweets from top 5 trending topics in Canada and sends them to Kafaka.
	- JSON data is converted to raw text.
	- Two things to send to Kafka: a Kafka topic (to know what topic to pull from the Kafka consumer) and tell Kafka where server is (defined in Kafka Docker container)
- *sparkConsumer3.py*: Spark consumer script. Pulls data from Kafka, manipulates with Spark, then sends back to Kafka
	- Includes Kafka location and topic
	- Deserialization of Kafka binary data as string to read JSON formatting.
	- Can now perform manipulations on dataframe (cleaning and sentiment polarities using VADER Sentiment Analysis: https://github.com/cjhutto/vaderSentiment)
	- Send back to Kafka
- *toInfluxDB.py*: InfluxDB consumer script. Takes each element of stream, splits components to get data needed, writes to InfluxDB using custom writer.

Step 3: Running Docker Compose
-	Go to directory where all files are located. Start containers with command “docker-compose up -d”. Docker Copmose is a container orchestration tool that can run a number of containers on a single host machine. The docker-compose.yml contains the run commands.
-	Once containers are started, the application is started by running producer and consumer scripts.
-	Next, open terminal application with multiple clients (for producer, Kafka server, and import from Kafka sink to InfluxDB). Tweets should be streaming in, viewable in the terminal window.

Step 4: InfluxDB Dashboard
- Open http://localhost:8086/ in a browser window. Log-in with credentials defined in docker-compose file.
- Navigate GUI to Boards to view the Sentiment Analysis Dashboard. It has multiple auto-refreshing plots, with adjustable refreshing periods. The Dashboard includes:
  - Trend sentiment 30-second aggregates.
  - Engagement count: number of tweets per 30 seconds.
  - Histograms: distribution of sentiment scores for a few topics.
  - Table containing total nubmer of tweets for each trend over window.
