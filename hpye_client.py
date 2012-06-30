# coding: utf-8

import json, re, socket
import locale
import curses, curses.wrapper, curses.textpad
from song import Song

# globals
ss = None
song_results = []
scr_height, scr_width = 0, 0
current_song = None
# curses windows + searchbox
search_prompt_window = None
search_window = None
results_window = None
status_line_window = None
now_playing_window = None
searchbox = None

# constants
HOST = 'localhost'
PORT = 4793
PACKET_MAX_LENGTH = 16384

"""
    Clears the search_prompt_window and search_window, and if
    enabled is True, also re-draws the searchbox then refreshes
    the window.
    This is done so that the query box only shows up when searching,
    and so that consecutive queries don't end up with concatenated
    query strings.
"""
def toggle_search_prompt(enabled=False):
    global search_prompt_window, search_window, searchbox
    search_prompt_window.clear()
    search_window.clear()

    if enabled is True:
        search_prompt_window = curses.newwin(2, scr_width, scr_height - 2, 0)
        search_prompt_window.addstr(0, 0, 'SEARCH QUERY:')
        search_prompt_window.addstr(1, 0, '>')
        search_window = curses.newwin(1, scr_width, scr_height - 1, 2)
        searchbox = curses.textpad.Textbox(search_window)
        search_window.refresh()

    search_prompt_window.refresh()

def update_now_playing(paused=False):
    global current_song
    global now_playing_window

    now_playing_window.clear()
    now_playing_window.hline(0, 0, '=', scr_width)
    now_playing_window.addstr(1, 0, 'hpye CLI ❤ ', curses.color_pair(1))
    now_playing_window.addstr(1, 11, ' NOW PLAYING:', curses.color_pair(2))

    if current_song is not None:
        now_playing_window.addstr(1, 25, str(current_song))
        if paused:
            now_playing_window.addstr(1, 27 + len(str(current_song)), '(paused)')

    now_playing_window.hline(2, 0, '=', scr_width)
    now_playing_window.refresh()

def queryloop(stdscr):
    global song_results, current_song
    global results_window, status_line_window, searchbox
    first_query = True

    while True:
        toggle_search_prompt(False)
        c = search_window.getch()
        if c in range(0, 256):

            # QUIT CLIENT
            if chr(c) == 'q':
                ss.sendall('quit')
                reply = ss.recv(PACKET_MAX_LENGTH)
                if reply == 'OK':
                    quit_client()

            # SEARCH
            elif chr(c) == '/':
                toggle_search_prompt(True)
                searchbox.edit()
                query = searchbox.gather().strip()

                if query == '':
                    continue
                else:
                    first_query = False
                    ss.sendall('search ' + query)
                    reply = ss.recv(PACKET_MAX_LENGTH)
                    del song_results
                    song_results = json.loads(reply)

                    status_line_window.clear()
                    results_window.clear()
                    results_window.addstr(0, 0, '-- Results for ' + query)
                    for index, r in enumerate(song_results):
                        if index < 10:
                            index_displayed = str(index)
                        else:
                            index_displayed = chr(ord('a') + (index - 10))
                        results_window.addnstr(index + 1, 0, '[' + index_displayed + '] ' +
                            r[1].encode('utf-8') + ' - ' + r[2].encode('utf-8'),
                            128)
                    results_window.addstr(len(song_results) + 2, 0, '[q] Quit hpye')
                    status_line_window.refresh()
                    results_window.refresh()

            elif chr(c) == 'p' and not first_query:
                first_query = False
                ss.sendall('pauseresume')
                reply = ss.recv(PACKET_MAX_LENGTH)
                if reply == 'OK_PAUSED':
                    update_now_playing(paused=True)
                elif reply == 'OK_RESUMED':
                    update_now_playing(paused=False)

            elif c in range(ord('0'), ord('9') + 1) or \
                c in range(ord('a'), ord('j') + 1):

                if c in range(ord('0'), ord('9') + 1):
                    song_index = int(chr(c))
                else:
                    song_index = 10 + (c - ord('a'))

                first_query = False
                ss.sendall('play ' + song_results[song_index][0])
                reply = ss.recv(PACKET_MAX_LENGTH)
                status_line_window.clear()
                if reply == 'ERROR_REMOVED':
                    status_line_window.addstr(0, 0,
                        'Song was removed :( Try another.')
                elif reply == 'OK':
                    status_line_window.addstr(0, 0, 'Now playing.')
                    current_song = Song(song_results[song_index][0],
                        song_results[song_index][1],
                        song_results[song_index][2])
                    update_now_playing()
                status_line_window.refresh()

def quit_client():
    curses.endwin()
    quit()

def main(stdscr):
    global ss
    global scr_height, scr_width
    global search_prompt_window, search_window, results_window, now_playing_window
    global searchbox, status_line_window

    scr_height, scr_width = stdscr.getmaxyx()
    # Now-playing bar
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    now_playing_window = curses.newwin(3, scr_width, 0, 0)
    update_now_playing()

    # Input window + searchbox
    search_prompt_window = curses.newwin(2, scr_width, scr_height - 2, 0)
    search_prompt_window.addstr(0, 0, 'SEARCH QUERY:')
    search_prompt_window.addstr(1, 0, '>')
    search_window = curses.newwin(1, scr_width, scr_height - 1, 2)
    searchbox = curses.textpad.Textbox(search_window)

    # Results and error windows
    results_window = curses.newwin(40, scr_width, 8, 0)
    status_line_window = curses.newwin(2, scr_width, 54, 0)

    curses.use_default_colors()
    search_prompt_window.refresh()
    search_window.refresh()

    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((HOST, PORT))
    queryloop(stdscr)
    ss.close()
    print 'done'

locale.setlocale(locale.LC_ALL,"")
curses.wrapper(main)
