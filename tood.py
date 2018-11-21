#!/usr/bin/python3

import curses
import json
import os
import subprocess
import sys

from cstate import CState
from storage import Storage

# if they ever decide to fix this...
try:
    curses.BUTTON5_PRESSED
    pass
except AttributeError:
    curses.BUTTON5_PRESSED = 0x200000
    pass

def cmd_stub(*args):
    curses.flash()
    return 0, 0

helptext = "hi this is the help text\n" \
           "the ui is mostly finger/mouse driven\n" \
           "scrolling should just work\n" \
           "press once on a thing to select it\n" \
           "press on a selected checkbox to toggle it\n" \
           "press on the selected text to edit it\n" \
           "commands are at the top\n" \
           "press twice on them to do the thing\n" \
           "queue boundaries are in blue\n" \
           "drag items to move their priority\n" \
           "hope this helps\n" \
           "do anything to return"
def cmd_help(stdscr, *args):
    stdscr.erase()
    stdscr.move(0, 0)

    stdscr.addstr(helptext)
    stdscr.getch() # doesn't matter, just call one
    return 0, -1

def cmd_quit(*args):
    exit(0)

def cmd_new(stdscr, cs):
    row, _ = stdscr.getyx()
    stdscr.move(row + 1, 0)
    stdscr.insertln()
    stdscr.addstr("[ ] ")

    new_text = cs.getline(stdscr)
    if new_text != "":
        cs.store.prepend(new_text)
        cs.set_highlight_local(row + 1)
        return row, row + 1
    stdscr.move(row + 1, 0)
    stdscr.deleteln()
    line = stdscr.getmaxyx()[0]
    return line - 1, line - 1

def click_here(click_col, cs, stdscr):
    idx = cs.get_highlight_abs()

    if click_col > 3 and idx >= len(cs.store.cmds):
        # edit mode!
        row, _ = stdscr.getyx() # TODO pass this in
        text = cs.store[idx]["text"]
        stdscr.move(row, 4 + len(text))
        newtext = cs.getline(stdscr, text, edge=idx == len(cs.store) - 1)
        if newtext != "" and newtext != text:
            cs.store[idx] = newtext
            pass
        return

    lower, upper = cs.store.toggle(stdscr, cs, idx)
    upper = len(cs.store) if upper == -1 else upper
    for r in range(lower, upper + 1):
        cs.display_nth(r)
        pass
    return

def curses_main(stdscr):
    cmds = [
        {"text": "(top of list)", "command": cmd_stub},
        {"text": "Help (press twice)", "command": cmd_help},
        {"text": "Quit", "command": cmd_quit},
        {"text": "Create new ", "command": cmd_new},
    ]
    store = Storage(cmds)

    cs = CState(stdscr, store, helptext)
    cs.display_store()
    second = False
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
                continue
            if bstate & curses.BUTTON5_PRESSED:
                cs.scroll_down()
                continue

            if bstate & curses.BUTTON1_PRESSED:
                second = cs.set_highlight_local(row)
                srow = row
                continue
            if bstate & curses.BUTTON1_RELEASED:
                if srow == row and not second:
                    continue
                if srow == row:
                    second = False
                    click_here(col, cs, stdscr)
                    continue

                srow += cs._offset
                row += cs._offset
                if srow < len(cs.store.cmds) or \
                   srow >= len(cs.store.cmds) + len(cs.store.queue):
                    # you can't move that!  Or that!
                    continue
                if row >= len(cs.store.cmds) + len(cs.store.queue):
                    # you can't put that there!
                    row = len(cs.store.cmds) + len(cs.store.queue) - 1
                    pass
                if row < len(cs.store.cmds):
                    # or there!
                    row = len(cs.store.cmds)
                    pass
                if srow == row:
                    continue

                cs.set_highlight_local(row - cs._offset)

                second = False
                store.move(srow, row)
                for r in range(srow, row + 1):
                    cs.display_nth(r)
                    pass
                for r in range(row, srow + 1):
                    cs.display_nth(r)
                    pass
                srow = None
                continue
            if bstate & curses.BUTTON1_CLICKED:
                second = False
                same = cs.set_highlight_local(row)
                if not same:
                    continue

                click_here(col, cs, stdscr)
                continue
            continue

        # bad key
        curses.flash()
        continue
    return        
    
if __name__ == "__main__":
    exit(curses.wrapper(curses_main))
