import json, re, socket

import locale
import time
import curses, curses.wrapper, curses.textpad

# globals
ss = None
song_results = []
# curses windows + textbox
input_prompt_window = None
input_window = None
results_window = None
status_line_window = None
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

def queryloop():
    global song_results
    global results_window, status_line_window, textbox
    first_query = True

    while True:
        #query = raw_input('\n> ')
        clear_prompt()
        textbox.edit()
        query = textbox.gather().strip()

        if query == 'q':
            quit_client()
        elif query == '':
            continue
        elif not first_query and re.match(r"[01]?[0-9]", query) and int(query) < len(song_results):
            first_query = False
            ss.sendall('play ' + song_results[int(query)][0])
            reply = ss.recv(PACKET_MAX_LENGTH)
            status_line_window.clear()
            if reply == 'ERROR_REMOVED':
                status_line_window.addstr(0, 0, 'Song was removed :( Try another.')
            elif reply == 'OK':
                status_line_window.addstr(0, 0, 'Now playing.')
            status_line_window.refresh()
        elif not first_query and query == 'p':
            first_query = False
            ss.sendall('pauseresume')
            reply = ss.recv(PACKET_MAX_LENGTH)
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
    global input_prompt_window, input_window, results_window, textbox
    global status_line_window
    print ('\nWelcome to hpye CLI.')

    # Now-playing bar
    scr_height, scr_width = stdscr.getmaxyx()
    now_playing_win = curses.newwin(3, scr_width, 0, 0)
    now_playing_win.hline(0, 0, '=', scr_width)
    now_playing_win.addstr(1, 0, 'NOW PLAYING:', curses.A_STANDOUT)
    now_playing_win.hline(2, 0, '=', scr_width)

    # Input window + textbox
    input_prompt_window = curses.newwin(1, scr_width, scr_height - 1, 0)
    input_prompt_window.addstr(0, 0, '>')
    input_window = curses.newwin(1, scr_width, scr_height - 1, 2)
    textbox = curses.textpad.Textbox(input_window)

    # Results and error windows
    results_window = curses.newwin(40, scr_width, 8, 0)
    status_line_window = curses.newwin(2, scr_width, 54, 0)

    now_playing_win.refresh()
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
