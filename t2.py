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

helptext = """TOOD write helptext
gotta do this gotta do it
press any key to continue
"""

def curses_main(stdscr):
    def stub():
        curses.flash()
        return 0, 0

    cmds = [{"text": "Create new", "command": stub}]
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

                lower, upper = cs.store.toggle(cs.get_highlight_abs())
                for r in range(lower, upper + 1):
                    cs.display_nth(r)
                    pass
                continue
            continue
        elif c in [ord('?'), ord('h')]:
            cs.display_help()
            continue
        elif c == ord('c'):
            # make a new one
            continue        
        if c == ord('q'):
            break

        # bad key
        curses.flash()
        continue
    return        
    
if __name__ == "__main__":
    exit(curses.wrapper(curses_main))
