"""
  hpye -- a python client
"""

import cookielib, json, os, re, shutil, sys
import pyglet
import urllib2
from bs4 import BeautifulSoup

# constants
TMP_PATH = '/tmp/hpye'
Q_NORMAL = 0
Q_LATEST = 1
Q_POPULAR = 2

# globals
cookie_jar = cookielib.CookieJar()
player = pyglet.media.Player()
song_results = []
downloaded_file_paths = set([])

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
def grab_query_results_soup(query, special_q=Q_NORMAL):
    global cookie_jar

    # Obtain and parse the results list
    while True:
        try:
            if special_q == Q_LATEST:
                url = "http://hypem.com/latest/"
            elif special_q == Q_POPULAR:
                url = "http://hypem.com/popular/"
            else:
                url = "http://hypem.com/search/" + query
            url += "/1/?ax=1"
            req = urllib2.Request(url)
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
    Downloads the song in the temp folder.
    Returns the complete path to the downloaded file.
"""
def download_file(song, path=TMP_PATH):
    # Make the /tmp/hpye folder if doesn't exist already.
    if not os.path.exists(path):
        os.makedirs(path)

    print 'Loading . . . '
    f = urllib2.urlopen(grab_song_url(song))
    path = path + '/' + str(song) + '.mp3'
    local_file = open(path, 'w')
    local_file.write(f.read())
    local_file.close()
    print "PLAYING. Press Ctrl+C to pause or switch tracks."
    downloaded_file_paths.add(path)
    return path

"""
    Plays this song.
"""
def play_song(song):
    try:
        sound = pyglet.media.load(download_file(song))
        player.queue(sound)
        if player.playing:
            player.next()
        player.play()
        pyglet.app.run()
    except KeyboardInterrupt:
        pass

"""
    Delete temp files and quit.
"""
def quit_hpye():
    if os.path.exists(TMP_PATH):
        shutil.rmtree(TMP_PATH, True)
    quit()

def queryloop():
    global song_results

    first_query = True

    while True:
        if first_query:
            qresponse_soup = grab_query_results_soup(None, Q_LATEST)
            populate_song_results(qresponse_soup)

            print '\n-- Results for %s:' % 'latest'
            for index, r in enumerate(song_results):
                print '[' + str(index) + '] ' + str(r)
            print '\n[q] Quit hpye'
            first_query = False
            continue
        query = raw_input('\n> ')
        if query == 'q':
            quit_hpye()
        elif not first_query and re.match(r"[01]?[0-9]", query) and int(query) < len(song_results):
            first_query = False
            song = song_results[int(query)]
            song_url = grab_song_url(song)
            if song_url == None:
                print 'Song was removed :( Try another.'
            else:
                play_song(song)
        else:
            first_query = False
            # Obtain and parse the results list
            qresponse_soup = grab_query_results_soup(query)
            populate_song_results(qresponse_soup)

            print '\n-- Results for %s:' % query
            for index, r in enumerate(song_results):
                print '[' + str(index) + '] ' + str(r)
            print '\n[q] Quit hpye'

print ('\nWelcome to hpye.')

queryloop()
