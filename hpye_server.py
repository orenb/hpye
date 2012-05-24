import cookielib, json, os, re, shutil, socket, sys, urllib2
import pyglet
from bs4 import BeautifulSoup

# constants
TMP_PATH = '/tmp/hpye'
Q_NORMAL = 0
Q_LATEST = 1
Q_POPULAR = 2
PACKET_MAX_LENGTH = 16384

# globals
client_socket = 42
cookie_jar = cookielib.CookieJar()
player = pyglet.media.Player()
song_results = []
downloaded_file_paths = set([])

HOST = 'localhost'
PORT = 4793

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
    Returns as a STRINGIFIED json the song results list according to API
    in response to the most recent query (as determined by the contents
    of global song_results).
"""
def stringified_query_results():
    global song_results
    return str([[s.id, s.artist, s.title] for s in song_results])

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

"""
    Handle searches.
    msg is an incoming message as a string.
    Returns the reply message as a string.
"""
def handle_search(msg):
    m = re.match(r"search (\w+)", msg)
    if m is None:
        return "ERROR"
    query = m.group(1)

    # Obtain and parse the results list
    qresponse_soup = grab_query_results_soup(query)
    populate_song_results(qresponse_soup)

    return stringified_query_results()

"""
    Perpetually read messages from the client (until client quits)
    and forward to proper handlers upon each message.
"""
def msgloop(client_socket):
    global song_results

    msg_handlers = {'search' : handle_search}

    while True:
        msg = client_socket.recv(PACKET_MAX_LENGTH)
        if not msg: break

        print 'msg received:', msg
        the_split = msg.split()
        print the_split
        if len(the_split) < 1:
            continue    # Not a valid message; just wait for the next

        return_msg = msg_handlers[the_split[0]](msg)
        client_socket.sendall(return_msg)


def main():
    global client_socket

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1) # At most one connection

    while True:
        (client_socket, address) = server_socket.accept()
        print 'Accepted', address
        msgloop(client_socket)
        # TODO: Clear out state from exited client in
        # anticipation of next client.

main()
