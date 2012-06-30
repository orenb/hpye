import cookielib, json, os, re, shutil, socket, sys, urllib2
import pygame.mixer
from bs4 import BeautifulSoup
from song import Song

# constants
TMP_PATH = '/tmp/hpye'
Q_NORMAL = 0
Q_LATEST = 1
Q_POPULAR = 2
PACKET_MAX_LENGTH = 16384

# globals
cookie_jar = cookielib.CookieJar()
downloaded_file_paths = set([])
# playback
is_paused = True

HOST = 'localhost'
PORT = 4793

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
    For the given hypem songid, returns a new Song object corresponding
    to the song.
    If error, return None.
"""
def new_song_obj(songid):
    global cookie_jar

    while True:
        try:
            url = "http://hypem.com/track/" + songid + "/?ax=1"
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

    div = qresponse_soup.find(id=re.compile("section-track-[a-zA-Z0-9]+"))
    return grab_song_from_soup_div(div)

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
    Returns as a STRINGIFIED json the given song results list according to API,
    generally in response to the most recent query.
"""
def stringified_query_results(song_results):
    r = json.dumps([[s.id, s.artist, s.title] for s in song_results])
    return r

"""
    Given a BeautifulSoup object representing a "section-track" div, returns
    a new Song object corresponding to the song inside that div.
    If no Song could be retrieved from this div (i.e., because the song was
    removed from hypem but still had an entry on the site), return None.
"""
def grab_song_from_soup_div(div):
    artist_link = div.find('a', { 'class' : 'artist' })
    title_link = div.find('a', { 'class' : 'track' })

    if title_link is None:
        return None

    js = div.find('script').contents[0]

    title_spans = title_link.find_all('span')
    song_title = unicode(title_spans[0].contents[0]).strip()
    if len(title_spans) > 1:
        subtitle = str(title_spans[1].find('span', {'class' : 'remix-link'}).contents[0]).strip()
        if not re.search(r'remixes$', subtitle):
            song_title += ' (' + subtitle + ')'

    song = Song(div['id'][14:],
        '(No artist)' if artist_link is None else str(artist_link.contents[0]).strip(),
        song_title,
        re.search(r"key: '(\w+)'", js).group(1))

    return song

"""
    For the given query response soup, returns a list of Songs
    that are the results of the query.
"""
def populated_song_results(qresponse_soup):
    div_results = qresponse_soup.find_all(id=re.compile("section-track-[a-zA-Z0-9]+"))
    song_results = []

    for div in div_results:
        song = grab_song_from_soup_div(div)
        if song is not None:
            song_results.append(song)

    return song_results

"""
    Downloads the song in the temp folder.
    Returns the complete path to the downloaded file, or
    returns None if the file can't be found (404) i.e. because
    hypem has removed the file.
"""
def download_file(song, path=TMP_PATH):
    # Make the /tmp/hpye folder if doesn't exist already.
    if not os.path.exists(path):
        os.makedirs(path)

    print '\nLOADING:', song
    song_url = grab_song_url(song)
    if song_url is None:
        return None

    f = urllib2.urlopen(song_url)
    path = path + '/' + str(song) + '.mp3'
    local_file = open(path, 'w')
    local_file.write(f.read())
    local_file.close()
    print "PLAYING. Press Ctrl+C to pause or switch tracks.\n"
    downloaded_file_paths.add(path)
    return path

"""
    Plays this song.
    Return "OK" to indicate no problems; else return "ERROR" for unexpected
    error or "ERROR_REMOVED" if download_file(song) returned None.
"""
def play_song(song):
    try:
        if song is None:
            return "ERROR"

        file_path = download_file(song)
        if file_path is None:
            return "ERROR_REMOVED"

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        return "OK"
    except KeyboardInterrupt:
        return "OK"
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
    m = re.match(r"search (.+)", msg)
    if m is None:
        return "ERROR"
    query = m.group(1)

    # Obtain and parse the results list
    qresponse_soup = grab_query_results_soup(query)
    song_results = populated_song_results(qresponse_soup)

    return stringified_query_results(song_results)

"""
    Handle song play requests.
    Forgoes the play queue and just plays the song with the id
    given in this msg.
"""
def handle_play(msg):
    global is_paused

    m = re.match(r"play (\w+)", msg)
    if m is None:
        return "ERROR"
    songid = m.group(1)
    song_obj = new_song_obj(songid)
    if song_obj is None:
        return "ERROR_REMOVED"
    is_paused = False
    return play_song(song_obj)

"""
    Handle pause/resume.
"""
def handle_pauseresume(msg):
    global is_paused

    if not is_paused:
        pygame.mixer.music.pause()
        is_paused = True
        return "OK_PAUSED"
    else:
        pygame.mixer.music.unpause()
        is_paused = False
        return "OK_RESUMED"

"""
    Handle a client quit.
"""
def handle_quit(msg):
    global is_paused

    is_paused = True
    pygame.mixer.music.stop()
    return "OK"

"""
    Perpetually read messages from the client (until client quits)
    and forward to proper handlers upon each message.
"""
def msgloop(client_socket):
    msg_handlers = {'search' : handle_search, 'play' : handle_play,
        'pauseresume' : handle_pauseresume, 'quit' : handle_quit}

    while True:
        try:
            msg = client_socket.recv(PACKET_MAX_LENGTH).strip()
            if not msg: break

            print 'msg received:', '[' + msg + ']'
            the_split = msg.split()
            if len(the_split) < 1:
                continue    # Not a valid message; just wait for the next

            return_msg = msg_handlers[the_split[0]](msg)
            client_socket.sendall(return_msg)
        except KeyboardInterrupt:
            quit_hpye()

def main():
    pygame.mixer.init(frequency=44100)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1) # At most one connection

    while True:
        (client_socket, address) = server_socket.accept()
        print 'Accepted client connection:', address
        msgloop(client_socket)
        # TODO: Clear out state from exited client in
        # anticipation of next client.

main()
