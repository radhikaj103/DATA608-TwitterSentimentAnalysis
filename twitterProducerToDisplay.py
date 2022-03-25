"""API ACCESS KEYS"""


import tweepy
from tweepy import Stream
from kafka import KafkaProducer
from json import dumps, loads
import sys
import re
import configparser
import pickle


# read config
config_keys = configparser.ConfigParser()
config_keys.read('config.ini')

consumer_key = config_keys['twitter']['api_key']
consumer_secret = config_keys['twitter']['api_key_secret']
access_token = config_keys['twitter']['access_token']
access_token_secret = config_keys['twitter']['access_token_secret']

keywords = []

producer = KafkaProducer(bootstrap_servers='localhost:9092') #Same port as your Kafka server

def clean(s):
    s=re.sub(r'(@|https|#)\S+','',s) # @mentions, links, #tags
    s=re.sub(r'\n','',s) # new lines
    return s

def match(s):
  '''
  All matching tags for a given string are returned with a list.
  '''
  tags=[]
  for tag in keywords:
      if re.search(tag.lower(),str(s).lower()): 
            tags.append(tag)
  return tags

def get_trends():
    '''
    Retreives trending topics from Twitter API, places topics 
    into pickle file for use by Consumer. Returns for use to create 
    individual topics.
    '''
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    woeid = 23424775 # 1=worldwide, 23424775=Canada
    trends = api.get_place_trends(id=woeid)
    keywords = [trend['name'] for trend in trends[0]['trends']][:5]
        
    with open("trends.pkl", "wb") as out_file:
        pickle.dump(keywords, out_file)

    return(trends)


class TwitterStreamer():
    def stream_tweets(self):
        global keywords
        keywords = get_trends()
        while True:

            listener = ListenerTS(consumer_key, consumer_secret, access_token, access_token_secret) 
            #auth = self.twitterAuth.authenticateTwitterApp()
            #stream = Stream(auth, listener)
            
            listener.filter(track=keywords, stall_warnings=True, languages= ["en"])          
            
            
class ListenerTS(Stream):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        super(ListenerTS, self).__init__(consumer_key, consumer_secret, access_token, access_token_secret)
        self.counter = 0
        print("Counter set to 0")
        
    def on_data(self, raw_data):
        print(keywords)
        if self.counter == 10:
            sys.exit(0)
        if raw_data:
            data = loads(raw_data)
            dt = data['created_at']
            qte_cnt = data['quote_count']
            rpy_cnt = data['reply_count']
            rtw_cnt = data['retweet_count']
            fav_cnt = data['favorite_count']
            #print(type(dt))
            #print('----------')
            # Debug info
   
            if data['retweeted'] or data['text'].startswith("RT @"):
                if not data['retweeted_status']['truncated']: 
                    text = data['retweeted_status']['text']
                else:
                    text = data['retweeted_status']['extended_tweet']['full_text']
            else:
                if not data['truncated']:
                    text = data['text']
                else:
                    text = data['extended_tweet']['full_text']
                    
            # Attach Keyword/Trend to Tweet
            tag_matches = match(text)
            text = clean(text)
                                    
            
            text = dumps({'DateTime':dt, 'Text': text, 
                          'Quote_Count': qte_cnt, 'Reply_Count': rpy_cnt,
                          'Retweet_Count': rtw_cnt, 'Favorite_Count': fav_cnt                          
                          }, indent=2)
            
            
            if len(tag_matches) > 1:
                for tag in tag_matches:
                    producer.send(tag, value= text.encode('utf-8'))
                else:
                    producer.send(tag_matches[0], value= text.encode('utf-8'))
                    
                    
            print(text)
            self.counter += 1
            print("Counter = " + str(self.counter))
            return True
        return False
	  		

if __name__ == "__main__":

    TS = TwitterStreamer()
    TS.stream_tweets()
    