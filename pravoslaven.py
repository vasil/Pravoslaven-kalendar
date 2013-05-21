# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import json
import tweepy
import webapp2
import logging
import datetime
import calendar
import ConfigParser

from google.appengine.ext import db
from google.appengine.api import xmpp
from google.appengine.api import memcache
from google.appengine.api import urlfetch
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
    google_shortener_url = "%s%s" % (config.get('google', 'shortener_base'),
                                      config.get('google', 'api_key'))
    
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
        return day.timetuple().tm_yday + offset

    @classmethod
    def shorten_url(cls, url):
        try:
            values = json.dumps({'longUrl' : url})
            headers = {'Content-Type' : 'application/json'}
            result = urlfetch.fetch(Util.google_shortener_url, 
                                    payload=values, 
                                    method='POST', 
                                    headers=headers)
            output = json.loads(result.content)
            return output["id"]
        except Exception, e:
            logging.error(e)
            return None


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
    CROSSES = ['⁕', '⁕', '✟', '✞', '✞']
    
    def get(self):
        feasts = Feast.get_feasts(Util.tomorrow())
        template_path = os.path.join(os.path.dirname(__file__), 
                                     "templates",
                                     Util.config.get("templates", "twitter"))
        
        xmmp_msg = "\n" + Util.tomorrow().isoformat() + ":\n"
        for feast in feasts:
            twitt = template.render(template_path, 
                                    {'feast': feast,
                                     'url': Util.shorten_url(feast.url), 
                                     'cross': self.CROSSES[feast.weight]})
            Util.twitter.update_status(twitt)
            xmmp_msg = xmmp_msg + twitt 
            if feast.weight == 4:
                break
        xmpp.send_message(Util.config.get("user", "email"), xmmp_msg)
        logging.info(", ".join(map(lambda f: f.name, feasts)))
        self.response.write(xmmp_msg)


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/twitter', TwitterHandler),
                               ('/json', None)], debug=True)
