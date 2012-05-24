import json, socket

# globals
ss = None
song_results = []

# constants
HOST = 'localhost'
PORT = 4793
PACKET_MAX_LENGTH = 16384

def queryloop():
    global song_results
    first_query = True

    while True:
        query = raw_input('\n> ')

        if query == 'q':
            quit_hpye()
#       elif not first_query and re.match(r"[01]?[0-9]", query) and int(query) < len(song_results):
#           first_query = False
#           song = song_results[int(query)]
#           song_url = grab_song_url(song)
#           if song_url == None:
#               print 'Song was removed :( Try another.'
#           else:
#               play_song(song)
        else:
            first_query = False
            ss.sendall('search ' + query)
            reply = ss.recv(PACKET_MAX_LENGTH)
            del song_results
            song_results = json.loads(reply)

            print '\n-- Results for %s:' % query
            for index, r in enumerate(song_results):
                print '[' + str(index) + '] %s - %s' % (r[1], r[2])
            print '\n[q] Quit hpye'

def quit_hpye():
    quit()

def main():
    global ss
    print ('\nWelcome to hpye CLI.')
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((HOST, PORT))
    queryloop()
    ss.close()
    print 'done'

main()
