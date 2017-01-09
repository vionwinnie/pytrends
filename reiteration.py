# -*- coding: utf-8 -*-
"""
Created on Sun Jan 08 21:06:22 2017

@author: a560304
"""
from __future__ import absolute_import, print_function, unicode_literals
import sys
import requests
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

class TrendReq(object):
    """
    Google Trends API
    """
    def __init__(self, username, password, custom_useragent=None):
        """
        Initialize hard-coded URLs, HTTP headers, and login parameters
        needed to connect to Google Trends, then connect.
        """
        self.username = username
        self.password = password
        # google rate limit
        self.google_rl = 'You have reached your quota limit. Please try again later.'
        self.url_login = "https://accounts.google.com/ServiceLogin"
        self.url_auth = "https://accounts.google.com/ServiceLoginAuth"


        # custom user agent so users know what "new account signin for Google" is
        if custom_useragent is None:
            self.custom_useragent = {'User-Agent': 'PyTrends'}
        else:
            self.custom_useragent = {'User-Agent': custom_useragent}
        self._connect()
        self.results = None

    def _connect(self):
        """
        Connect to Google.
        Go to login page GALX hidden input value and send it back to google + login and password.
        http://stackoverflow.com/questions/6754709/logging-in-to-google-using-python
        """
        self.ses = requests.session()
        login_html = self.ses.get(self.url_login, headers=self.custom_useragent, proxies = self.proxy)
        soup_login = BeautifulSoup(login_html.content, "lxml").find('form').find_all('input')
        dico = {}
        for u in soup_login:
            if u.has_attr('value'):
                try:
                    dico[u['name']] = u['value']
                except KeyError:
                    pass
        # override the inputs with out login and pwd:
        dico['Email'] = self.username
        dico['Passwd'] = self.password
        self.ses.post(self.url_auth, data=dico, proxies= None)
        
    def trend(self, payload, return_type=None):
        payload['cid'] = 'TIMESERIES_GRAPH_0'
        payload['export'] = 3
        req_url = "http://www.google.com/trends/fetchComponent"
        req = self.ses.get(req_url, params=payload, proxies = None)
        try:
            if self.google_rl in req.text:
                raise RateLimitError
            # strip off js function call 'google.visualization.Query.setResponse();
            text = req.text[62:-2]
            # replace series of commas ',,,,'
            text = re.sub(',+', ',', text)
            # replace js new Date(YYYY, M, 1) calls with ISO 8601 date as string
            pattern = re.compile(r'new Date\(\d{4},\d{1,2},\d{1,2}\)')
            for match in re.finditer(pattern, text):
                # slice off 'new Date(' and ')' and split by comma
                csv_date = match.group(0)[9:-1].split(',')
                year = csv_date[0]
                # js date function is 0 based... why...
                month = str(int(csv_date[1]) + 1).zfill(2)
                day = csv_date[2].zfill(2)
                # covert into "YYYY-MM-DD" including quotes
                str_dt = '"' + year + '-' + month + '-' + day + '"'
                text = text.replace(match.group(0), str_dt)
            self.results = json.loads(text)
        except ValueError:
            raise ResponseError(req.content)
        if return_type == 'json' or return_type is None:
            return self.results
        if return_type == 'dataframe':
            self._trend_dataframe()
            return self.results
        
if __name__ == '__main__':
    google_username = 'xx'
    google_password = 'xx'
    pytrends = TrendReq(google_username, google_password, custom_useragent=None)
    #print 'successfully logged in'
    trend_payload = {'q': '%2Fm%2F03b7w3,%2Fm%2F0g4ccb,%2Fm%2F04s4g6,%2Fm%2F03ccxvf,%2Fm%2F04bnxg,%2Fm%2F0105kq0y', 
                     'cat': '18',
                     'hl': 'en-US',
                     'date': '1/2011 73m',
                     'geo': 'US'
                     }
    trend = pytrends.trend(trend_payload)
    print(trend)
