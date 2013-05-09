# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import tweepy
import webapp2
import datetime
import calendar
import ConfigParser

from google.appengine.ext import db
from google.appengine.api import xmpp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template

class Util(object):
    config_path = os.path.join(os.path.dirname(__file__),
                               'config',
                               'pravoslaven.conf')
    config = ConfigParser.ConfigParser()
    config.read(config_path)
                               
    auth = tweepy.OAuthHandler(config.get('twitter', 'consumer_key'), 
                               config.get('twitter', 'consumer_secret'))
    auth.set_access_token(config.get('twitter', 'access_token'),
                          config.get('twitter', 'access_token_secret'))
    twitter = tweepy.API(auth)
    
    @classmethod
    def today(cls):
        today = datetime.date.today()
        return today
    
    @classmethod
    def tomorrow(cls):
        delta = datetime.timedelta(days=1)
        tomorrow = cls.today() + delta 
        return tomorrow
    
    @classmethod
    def get_day_number(cls, day=datetime.date.today()):
        not_leap = not calendar.isleap(day.year)
        leap_day = datetime.date(day.year, 3, 14)
        offset = 1 if not_leap and day > leap_day else 0
        print offset
        return day.timetuple().tm_yday + offset


class Easter(db.Model):
    year = db.IntegerProperty(required=True)
    date = db.DateProperty(required=True)
     
    @classmethod
    def get_date(cls, year):
        year = str(year)
        easter = memcache.get(year)
        if easter is None:
            easter = cls.get_by_key_name(year)
            memcache.set(year, easter)
        return easter
    
    def day_number(self):
        day_number = Util.get_day_number(self.date)
        return day_number


class Feast(db.Model):
    day_number = db.IntegerProperty(required=True)
    name = db.StringProperty(required=True)
    hagiography = db.TextProperty(required=False)
    url = db.LinkProperty(required=False)
    weight = db.RatingProperty(default=0)
     
    @classmethod
    def get_feasts(cls, date):
        delta = 1000 - Easter.get_date(date.year).day_number()
        day_number = Util.get_day_number(date)
        variable_day_number = delta + day_number
        feasts = cls.all()
        feasts.filter("day_number IN", [day_number, variable_day_number])
        feasts.order("-weight")
        return feasts


class MainHandler(webapp2.RequestHandler):
    def get(self):
        pass


class TwitterHandler(webapp2.RequestHandler):
    CROSSES = ['', '', '✝', '✞', '✞']
    
    def get(self):
        feasts = Feast.get_feasts(Util.tomorrow())
        template_path = os.path.join(os.path.dirname(__file__), 
                                     "templates",
                                     Util.config.get("templates", "twitter"))
        for feast in feasts:
            twitt = template.render(template_path, 
                                    {'feast': feast, 
                                     'cross': self.CROSSES[feast.weight]})
             Util.twitter.update_status(twitt)
             xmpp.send_message(Util.config.get("user", "email"), twitt)
        feasts = ", ".join(map(lambda f: f.name, feasts))
        self.response.write(feasts)


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/twitter', TwitterHandler),
                               ('/json', None)], debug=True)
