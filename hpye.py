"""
  hpye -- a python client for The Hype Machine
"""

import cookielib, re, sys
import urllib2
from bs4 import BeautifulSoup

# globals
cookie_jar = cookielib.CookieJar()
query_results = []

class Song:
    def __init__(self, id, artist, title, key):
        self.id = str(id.encode('utf-8'))
        self.artist = str(artist.encode('utf-8'))
        self.title = str(title.encode('utf-8'))
        self.key = str(key.encode('utf-8'))

    def __str__(self):
        return "[%s] %s - %s (KEY: %s)" % (self.id, self.artist,
            self.title, self.key)

"""
    Updates the given CookieJar with a fresh cookie from
    the given hypem response.
"""
def hype_cookie(jar, response):
    jar.clear_session_cookies()
    jar.extract_cookies(urllib2.urlopen(req), req)

def grab_song(song, jar):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
    json_url = 'http://hypem.com/serve/source/' + song.id + '/' + song.key
    print json_url
    json_url_req = urllib2.Request(json_url)
#   json_url_req.add_header('Host', 'hypem.com')
#   json_url_req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')
#   json_url_req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
#   json_url_req.add_header('Accept-Language', 'en-us,en;q=0.5')
#   json_url_req.add_header('Connection', 'keep-alive')
#   json_url_req.add_header('Accept-Encoding', 'gzip, deflate')
#   json_url_req.add_header('X-Requested-With', 'XMLHttpRequest')
#   json_url_req.add_header('Referer', 'http://hypem.com/')
    jar.add_cookie_header(json_url_req)
    print json_url_req.header_items()
    print BeautifulSoup(opener.open(json_url_req))

def queryloop():
    global query_results
    global cookie_jar

    result_count = 0
    while True:
        query = raw_input('\n> ')
        if query == 'q':
            quit()

        # Obtain and parse the results list
        while True:
            try:
                req = urllib2.Request("http://hypem.com/search/"+ query +
                    '/1/?ax=1')
                qresponse = urllib2.urlopen(req)
                cookie_jar.clear_session_cookies()
                cookie_jar.extract_cookies(qresponse, req)
                qresponse_soup = BeautifulSoup(qresponse)
                break
            except urllib2.HTTPError, e:
                if e.code == 500:
                    print "500 encountered; retrying"
                    continue

        div_results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))
        print len(div_results)

        for div in div_results:
            artist_link = div.find('a', { 'class' : 'artist' })
            js = div.find('script').contents[0]

            song = Song(div['id'][14:], artist_link.contents[0].strip(),
                artist_link.find_next_sibling('a').contents[0].strip(),
                re.search(r"key: '(\w+)'", js).group(1))

            if result_count == 1:
                grab_song(song, cookie_jar)

            print song

            result_count += 1

        result_count = 0

print ('\nWelcome to hpye')

# Grab a cookie from hypem
#hype_cookie(cookie_jar)
#s = Song("1kwh6", "a", "b", "d045b43e0413fb690345234d74514f7a")
#grab_song(s, cookie_jar)

queryloop()
