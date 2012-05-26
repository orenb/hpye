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
# curses windows + textbox
input_prompt_window = None
input_window = None
results_window = None
status_line_window = None
now_playing_window = None
textbox = None

# constants
HOST = 'localhost'
PORT = 4793
PACKET_MAX_LENGTH = 16384

"""
    Clears the input_window and re-draws the textbox, then refreshes
    the window.
    This is done so that consecutive queries don't end up with concatenated
    query strings.
"""
def clear_prompt():
    input_window.clear()
    textbox = curses.textpad.Textbox(input_window)

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

def queryloop():
    global song_results, current_song
    global results_window, status_line_window, textbox
    first_query = True

    while True:
        #query = raw_input('\n> ')
        clear_prompt()
        textbox.edit()
        query = textbox.gather().strip()

        if query == 'q':
            ss.sendall('quit')
            reply = ss.recv(PACKET_MAX_LENGTH)
            if reply == 'OK':
                quit_client()
        elif query == '':
            continue
        elif not first_query and re.match(r"[01]?[0-9]", query) and \
                int(query) < len(song_results):
            first_query = False
            ss.sendall('play ' + song_results[int(query)][0])
            reply = ss.recv(PACKET_MAX_LENGTH)
            status_line_window.clear()
            if reply == 'ERROR_REMOVED':
                status_line_window.addstr(0, 0,
                    'Song was removed :( Try another.')
            elif reply == 'OK':
                status_line_window.addstr(0, 0, 'Now playing.')
                current_song = Song(song_results[int(query)][0],
                    song_results[int(query)][1],
                    song_results[int(query)][2])
                update_now_playing()
            status_line_window.refresh()
        elif not first_query and query == 'p':
            first_query = False
            ss.sendall('pauseresume')
            reply = ss.recv(PACKET_MAX_LENGTH)
            if reply == 'OK_PAUSED':
                update_now_playing(paused=True)
            elif reply == 'OK_RESUMED':
                update_now_playing(paused=False)
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
                results_window.addnstr(index + 1, 0, '[' + str(index) + '] ' +
                    r[1].encode('utf-8') + ' - ' + r[2].encode('utf-8'),
                    128)
            results_window.addstr(len(song_results) + 2, 0, '[q] Quit hpye')
            status_line_window.refresh()
            results_window.refresh()

def quit_client():
    curses.endwin()
    quit()

def main(stdscr):
    global ss
    global scr_height, scr_width
    global input_prompt_window, input_window, results_window, now_playing_window
    global textbox, status_line_window

    scr_height, scr_width = stdscr.getmaxyx()
    # Now-playing bar
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    now_playing_window = curses.newwin(3, scr_width, 0, 0)
    update_now_playing()

    # Input window + textbox
    input_prompt_window = curses.newwin(1, scr_width, scr_height - 1, 0)
    input_prompt_window.addstr(0, 0, '>')
    input_window = curses.newwin(1, scr_width, scr_height - 1, 2)
    textbox = curses.textpad.Textbox(input_window)

    # Results and error windows
    results_window = curses.newwin(40, scr_width, 8, 0)
    status_line_window = curses.newwin(2, scr_width, 54, 0)

    input_prompt_window.refresh()
    input_window.refresh()
    curses.use_default_colors()

    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((HOST, PORT))
    queryloop()
    ss.close()
    print 'done'

locale.setlocale(locale.LC_ALL,"")
curses.wrapper(main)
