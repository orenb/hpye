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
        query = raw_input('\n> ')
        if query == 'q':
            quit()

        # Obtain and parse the results list
        while True:
            try:
                qresponse_soup = BeautifulSoup(urllib2.urlopen('http://hypem.com/search/' +
                    query + '/1/?ax=1'))
                break
            except urllib2.HTTPError, e:
                if e.code == 500:
                    print "500 encountered; retrying"
                    continue

        div_results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))
        print len(div_results)

        for div in div_results:
            print '[' + div['id'][14:] + ']',
            artist_link = div.find('a', { 'class' : 'artist' })
            print artist_link.contents[0].strip() + " -",
            print artist_link.find_next_sibling('a').contents[0].strip()

        query_results.clear()

print ('\nWelcome to hpye')
queryloop()
