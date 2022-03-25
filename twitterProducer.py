from kafka import KafkaProducer
import configparser
from json import dumps, loads
import tweepy
import re
import pickle

# read config
config = configparser.ConfigParser()
config.read('config.ini')

api_key=config['twitter']['api_key']
api_key_secret=config['twitter']['api_key_secret']
access_token=config['twitter']['access_token']
access_token_secret=config['twitter']['access_token_secret']

# authenticate
auth = tweepy.OAuthHandler(api_key,api_key_secret)
auth.set_access_token(access_token,access_token_secret)
api=tweepy.API(auth)

# matched tags
def matchTag(s):
    '''
    Searches filtered hashtags given the entire raw status
    '''
    return [tag for tag in keywords if re.search(tag.lower(),str(s).lower())]

def clean(s):
    s=re.sub(r'(@|https|#)\S+','',s) # links, @mentions, #tags
    s=re.sub(r'\n',' ',s) # new lines
    s=re.sub(r' +',' ',s) # extra spaces
    s=s.rstrip() # trailing spaces
    return s
    

class Listener(tweepy.Stream):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, **kwargs):
        super().__init__(consumer_key, consumer_secret, access_token, access_token_secret, **kwargs)
        self.limit = 5

    def on_status(self, status):
        
        # data
        data={'tweet_id':status.id_str,
              'created_at':str(status.created_at),
              'user_name':status.user.screen_name,
              'user_id':status.user.id_str,
              'retweet':False,
              "tweet_body":0,
              'tags':matchTag(status)}

        # pull message
        if re.match(r'RT*',status.text):
            data['retweet']=True
            if not status.retweeted_status.truncated: data['tweet_body']=status.retweeted_status.text        
            else: data['tweet_body']=status.retweeted_status.extended_tweet['full_text']
        else:
            if not status.truncated: data['tweet_body']=status.text
            else: data['tweet_body']=status.extended_tweet['full_text']

        data['tweet_body']=clean(data['tweet_body'])

        # send to producer
        text = dumps(data, indent=2)
        producer.send(topic_name, value=text.encode('utf-8'))

        # termination
        self.limit-=1
        if self.limit<1: self.disconnect()

# trending
# https://www.geeksforgeeks.org/python-api-trends_place-in-tweepy/
woeid=23424775 # 1=worldwide, 23424775=Canada
# worldwide might include non English tags. Listener will run indefinitely because tweets are not in English & it's looking for English tweets due to filter(languages=['en'])
# tweets will not populate & limit will not be reached.

trends=api.get_place_trends(id=woeid)

# stream by keywords
# keywords = ["dog"]
keywords=  [trend['name'] for trend in trends[0]['trends']][:5]
# print(keywords)
with open("trends.pkl", "wb") as out_file:
    pickle.dump(keywords, out_file)

# to Kafka:
topic_name = "twitter"
producer = KafkaProducer(bootstrap_servers='localhost:9092') 

# the filter calls the tweets
stream_tweet = Listener(api_key,api_key_secret,access_token,access_token_secret)
stream_tweet.filter(track=keywords,languages=['en'])
