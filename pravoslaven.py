#!/usr/bin/env python

import codecs
import tweepy
import webapp2
import logging
import datetime
import calendar

from google.appengine.ext import db
from google.appengine.api import memcache

CONSUMER_KEY = '3MyurHe9q1jU69y1Pzp16g'
CONSUMER_SECRET = 'WfP2LTOj3PEUOlVZkwKcweUa47xuM0jbFcmv7y7Ak'
ACCESS_TOKEN = '96093117-WckTpsAvtdXBPq2gltP4dSUN3u1iZB3OmR3TqJqln'
ACCESS_TOKEN_SECRET = 'msSUzJ4yLCsSTr4kdpYUBxZHbnfd6tJO1m97vDPSuE'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitter = tweepy.API(auth)

class Util(object):
    @classmethod    
    def get_day_number(cls, day=datetime.date.today()):
        not_leap = not calendar.isleap(day.year)
        start_day = datetime.date(day.year, 3, 1)
        end_day = datetime.date(day.year, 3, 14)
        offset = 1 if not_leap and day > start_day and day < end_day else 0
        return day.timetuple().tm_yday + offset


class Easter(db.Model):
    date = db.DateProperty(required=True)
    
    @classmethod
    def new(cls, date):
        year = date.year
        try:
            cls.get_date(year)
        except:
            easter = Easter(key_name=year, date=date)
            return easter
    
    @classmethod
    def get_date(cls, year = datetime.date.today().year):
        easter = memcache.get(year)
        if easter is None:
            easter = Easter.get_by_key_name(year)
            memcache.set(year, easter)
        return easter.date


class Feast(db.Model):
    day_number = db.IntegerProperty(required=True)
    name = db.StringProperty(required=True)
    hagiography = db.StringProperty(required=False)
    url = db.LinkProperty(required=False)
    weight = db.RatingProperty(default=0)
    
    @classmethod
    def new(cls, day_number, name, hagiography, url, weight):
        try:
            feast = Feast(key_name=codecs.decode(name, 'utf-8'), 
                          day_number=day_number,
                          name=name,
                          hagiograpy=hagiography,
                          url=url,
                          weight=weight)
            return feast
        except IndexError:
            logging.error('Error while inserting new feast')
            raise Exception('%s wasn\'t found as Twitter user.' % name)
        
    @classmethod
    def get_feasts(cls, date):
        delta = 1000 - Util.get_day_number(Easter.get_date())
        day_number = Util.get_day_number(date)
        variable_day_number = 999 - delta + day_number

        feasts = cls.all()
        feasts.filter("day_number IN", [day_number, variable_day_number])
        feasts.order("weight")
        return feasts

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Pravoslaven Kalendar')

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/', None),
                               ('/json', None)], debug=True)
