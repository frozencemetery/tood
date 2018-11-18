#!/usr/bin/python3

import curses
import json
import os
import subprocess
import sys

from cstate import CState
from storage import *

# if they ever decide to fix this...
try:
    curses.BUTTON5_PRESSED
    pass
except AttributeError:
    curses.BUTTON5_PRESSED = 0x200000
    pass

helptext = "hi this is the help text\n" \
           "the ui is mostly finger/mouse driven\n" \
           "scrolling should just work\n" \
           "press once on a thing to select it\n" \
           "press again to toggle it\n" \
           "commands are at the top\n" \
           "press twice on them to do the thing\n" \
           "queue boundaries are in blue\n" \
           "hope this helps\n" \
           "do anything to return"
def cmd_help(stdscr):
    stdscr.erase()
    stdscr.move(0, 0)

    stdscr.addstr(helptext)
    stdscr.getch()
    return 0, -1

def cmd_stub(*args):
    curses.flash()
    return 0, 0

def curses_main(stdscr):
    cmds = [
        {"text": "(top of list)", "command": cmd_stub},
        {"text": "Help (press twice)", "command": cmd_help},
        {"text": "Create new ", "command": cmd_stub},
    ]
    store = Storage(cmds)

    cs = CState(stdscr, store, helptext)
    cs.display_store()
    while True:
        # UI
        c = stdscr.getch()
        if c == curses.KEY_RESIZE:
            cs.resize()
            continue
        elif c in [curses.KEY_DOWN, 14]: # 14 is C-n
            cs.scroll_down()
            continue
        elif c in [curses.KEY_UP, 16]: # 16 is C-p
            cs.scroll_up()
            continue
        elif c == curses.KEY_MOUSE:
            # sometimes curses will fail this call!  If you send it input it
            # doesn't understand (e.g., button 6/7) when it's not in "all",
            # python dumps a traceback.  Love that they made this exception
            # easy to catch.
            try:
                _, col, row, _, bstate = curses.getmouse()
                pass
            except Exception:
                continue

            if bstate & curses.BUTTON4_PRESSED:
                cs.scroll_up()
                pass
            if bstate & curses.BUTTON5_PRESSED:
                cs.scroll_down()
                pass
            if bstate & curses.BUTTON1_PRESSED:
                same = cs.set_highlight_local(row)
                if not same:
                    continue

                lower, upper = cs.store.toggle(stdscr, cs.get_highlight_abs())
                upper = len(cs.store) if upper == -1 else upper
                for r in range(lower, upper + 1):
                    cs.display_nth(r)
                    pass
                continue
            continue

        # bad key
        curses.flash()
        continue
    return        
    
if __name__ == "__main__":
    exit(curses.wrapper(curses_main))
