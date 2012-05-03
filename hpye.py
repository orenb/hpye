"""
  hpye -- a python client
"""

import cookielib, json, re, sys
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
        self.url = None

    def __str__(self):
        return "%s - %s" % (self.artist, self.title)

    def add_url(self, url):
        self.url = url

"""
    Grabs the url for song, assigns song.url to the url if song.url hasn't
    already been assigned, and returns the url.
    Or, returns None if the song can't be played (404). This usually occurs
    if the song has been removed by hypem.
"""
def grab_song_url(song):
    global cookie_jar

    if song.url != None:
        return song.url
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    json_url = 'http://hypem.com/serve/source/' + song.id + '/' + song.key

    try:
        json_url_req = urllib2.Request(json_url)
        cookie_jar.add_cookie_header(json_url_req)
        json_text = str(BeautifulSoup(opener.open(json_url_req)))
        song.url = json.loads(json_text)['url']
        return song.url
    except urllib2.HTTPError, e:
        if e.code == 404:
            return None
        else:
            print "HTTP error %d encountered" % e.code

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

    div_results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))

    for div in div_results:
        artist_link = div.find('a', { 'class' : 'artist' })
        if artist_link != None:
            js = div.find('script').contents[0]

            song = Song(div['id'][14:], artist_link.contents[0].strip(),
                artist_link.find_next_sibling('a').contents[0].strip(),
                re.search(r"key: '(\w+)'", js).group(1))

            song_results.append(song)

"""
    Downloads the song in the given path.
"""
def download_file(song, path='.'):
    f = urllib2.urlopen(grab_song_url(song))
    local_file = open(path + '/' + str(song) + '.mp3', 'w')
    local_file.write(f.read())
    local_file.close()
    print "Done."

def queryloop():
    global song_results

    first_query = True

    while True:
        query = raw_input('\n> ')
        if query == 'q':
            quit()
        elif not first_query and re.match(r"[01]?[0-9]", query) and int(query) < len(song_results):
            song = song_results[int(query)]
            song_url = grab_song_url(song)
            if song_url == None:
                print 'Song was removed :( Try another.'
            else:
                download_file(song)
        else:
            # Obtain and parse the results list
            qresponse_soup = grab_query_results_soup(query)
            populate_song_results(qresponse_soup)

            print
            for index, r in enumerate(song_results):
                print '[' + str(index) + '] ' + str(r)
            first_query = False

print ('\nWelcome to hpye.')

queryloop()
