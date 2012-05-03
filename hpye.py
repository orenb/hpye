"""
  hpye -- a python client for The Hype Machine
"""

import cookielib, re, sys
import urllib2
from bs4 import BeautifulSoup

# globals
cookie_jar = cookielib.CookieJar()
song_results = []

class Song:
    def __init__(self, id, artist, title, key):
        self.id = str(id.encode('utf-8'))
        self.artist = str(artist.encode('utf-8'))
        self.title = str(title.encode('utf-8'))
        self.key = str(key.encode('utf-8'))

    def __str__(self):
        return "[%s] %s - %s (KEY: %s)" % (self.id, self.artist,
            self.title, self.key)

def grab_song(song, jar):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
    json_url = 'http://hypem.com/serve/source/' + song.id + '/' + song.key
    print json_url
    json_url_req = urllib2.Request(json_url)
    jar.add_cookie_header(json_url_req)
    print json_url_req.header_items()
    print BeautifulSoup(opener.open(json_url_req))

"""
    For the given query string, gets the proper search results
    from hypem and returns these results as a BeautifulSoup object.
"""
def grab_query_results_soup(query):
    global cookie_jar

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
    return qresponse_soup

"""
    For the given query response soup, clears song_results and
    populates it with the results, as Song objects, of the query.
"""
def populate_song_results(qresponse_soup):
    global song_results

    del song_results[:]

    result_count = 0

    div_results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))
    print len(div_results)

    for div in div_results:
        artist_link = div.find('a', { 'class' : 'artist' })
        js = div.find('script').contents[0]

        song = Song(div['id'][14:], artist_link.contents[0].strip(),
            artist_link.find_next_sibling('a').contents[0].strip(),
            re.search(r"key: '(\w+)'", js).group(1))

        song_results.append(song)

        if result_count == 1:
            grab_song(song, cookie_jar)

        result_count += 1

    result_count = 0

def queryloop():
    global query_results

    while True:
        query = raw_input('\n> ')
        if query == 'q':
            quit()

        # Obtain and parse the results list
        qresponse_soup = grab_query_results_soup(query)
        populate_song_results(qresponse_soup)
        for r in song_results:
            print r

print ('\nWelcome to hpye')

queryloop()
