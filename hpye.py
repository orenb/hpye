"""
  hpye -- a python client for The Hype Machine
"""

import re, sys
import urllib2
from bs4 import BeautifulSoup

# globals
query_results = {}

def queryloop():
    while True:
        query = raw_input('> ')
        if query == 'q':
            quit()
        qresponse_soup = BeautifulSoup(urllib2.urlopen('http://hypem.com/search/' +
            query + '/1/?ax=1'))
        results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))
        print len(results)

        print [div['id'] for div in results]
        query_results.clear()

queryloop()