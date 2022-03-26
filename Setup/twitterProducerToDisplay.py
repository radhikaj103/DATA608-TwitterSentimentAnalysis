"""API ACCESS KEYS"""

access_token = "Your token here"
access_token_secret = "your access token secret"
consumer_key = "Your consumer key"
consumer_secret = "Your consumer secret"



from tweepy import Stream
from kafka import KafkaProducer
from json import dumps, loads
import sys
producer = KafkaProducer(bootstrap_servers='localhost:9092') #Same port as your Kafka server


topic_name = "twitter"


class TwitterStreamer():

    def stream_tweets(self):
        while True:
            listener = ListenerTS(consumer_key, consumer_secret, access_token, access_token_secret) 
            #auth = self.twitterAuth.authenticateTwitterApp()
            #stream = Stream(auth, listener)
            listener.filter(track=["bitcoin"], stall_warnings=True, languages= ["en"])


class ListenerTS(Stream):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        super(ListenerTS, self).__init__(consumer_key, consumer_secret, access_token, access_token_secret)
        self.counter = 0
        print("Counter set to 0")
        
    def on_data(self, raw_data):
            if self.counter == 5:  # Change this to the number of tweets to limit
                sys.exit(0)
            if raw_data:
                data = loads(raw_data)
                dt = data['created_at']
                #print(type(dt))
                #print('----------')
                # Debug info
                if data['retweeted'] or data['text'].startswith("RT @"):
                    print('-------')
                    try:
                        text = 'RT: ' + data['retweeted_status']['extended_tweet']['full_text']  # Get full text from retweet
                    except Exception as e:
                        text = data['text']
                else:
                    try:
                        text = data['extended_tweet']['full_text']
                    except Exception as e:
                        text = data['text']
                        
                text = dumps({'DateTime':dt, 'Text': text}, indent=2)
                producer.send(topic_name, value= text.encode('utf-8'))
                print( text)
                self.counter += 1
                print("Counter = " + str(self.counter))
                return True
            return False
	  		

if __name__ == "__main__":
    TS = TwitterStreamer()
    TS.stream_tweets()
    