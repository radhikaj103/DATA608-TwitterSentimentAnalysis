from kafka import KafkaProducer
import configparser
from json import dumps, loads
import tweepy
import re

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
    Searches hastags given the entire raw status
    '''
    for tag in keywords:
        if re.search(tag.lower(),str(s).lower()): return tag
    # return [tag for tag in keywords if re.search(tag.lower(),str(s).lower())]

def clean(s):
    s=re.sub(r'(RT @|@|https|#)\S+','',s) # links
    s=re.sub(r'\n',' ',s) # new lines
    s=re.sub(r' +',' ',s) # extra spaces
    s=s.rstrip() # trailing spaces
    return s
    

class Listener(tweepy.Stream):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, **kwargs):
        super().__init__(consumer_key, consumer_secret, access_token, access_token_secret, **kwargs)
        self.limit = 20

    def on_status(self, status):
        
        # data
        data={'tweet_id':status.id_str,
              'created_at':str(status.created_at),
              'user_name':status.user.screen_name,
              'user_id':status.user.id_str,
              'retweet':False,
              "tweet_body":0,
              'tags':matchTag(status)}

        if re.match(r'RT*',status.text):
            data['retweet']=True
        # pull message
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
woeid=23424775 # 1=worldwide, 23424775=Canada

trends=api.get_place_trends(id=woeid)

# stream by keywords
keywords=  [trend['name'] for trend in trends[0]['trends']][:5]
# print(keywords)

# to Kafka:
topic_name = "twitter"
producer = KafkaProducer(bootstrap_servers='localhost:9092') 

# the filter calls the tweets
stream_tweet = Listener(api_key,api_key_secret,access_token,access_token_secret)
stream_tweet.filter(track=keywords,languages=['en'])
