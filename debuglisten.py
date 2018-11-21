#!/usr/bin/env python3

import curses
import os
import sys

from datetime import datetime

# Python curses (and curses generally) are *terrible*.
#
# Python only binds mouse buttons 1-4, despite the C API defining five
# buttons.  Buttons 4 and 5 are vertical scrolling, by the way.  So you only
# have readable symbols for up.
#
# But curses is at fault here too.  C doesn't bind buttons 6 and 7 at all -
# that's horizontal scrolling, by the way.  No way to get that information.
#
# Honestly, having them be mouse events at all is a bit dodgy.  Maybe it made
# sense before they were the same bus, but what on earth does a triple scroll
# up mean?  When control is held down?  I think at least a third of these are
# impossible to generate on normal setups.
#
# Back on track, mousemask() doesn't seem to work.  I definitely get events
# that should be filtered.  Not sure whose fault it is.  I seem to be able to
# filter out event *types* - like, I can do presses only - but not buttons (so
# I'll still get 4 and 5 events when I've only asked for 1-3).  Sending 6 and
# 7 events causes a *traceback* from Python consistently (because curses
# returns ERR), which Python of course bungles.  And the exception isn't
# exposed in a part of the class that I can easily find, which is extra fun
# because now I have to catch something way too broad.
#
# Oh, and there's no pretty-printer in either Python or C, so enjoy the next
# few lines.

mods = {curses.BUTTON_SHIFT: "s",
        curses.BUTTON_CTRL: "c",
        curses.BUTTON_ALT: "a",
}
mousedict = {curses.BUTTON1_PRESSED: "1p ",
             curses.BUTTON1_RELEASED: "1r ",
             curses.BUTTON1_CLICKED: "1c ",
             curses.BUTTON1_DOUBLE_CLICKED: "1d ",
             curses.BUTTON1_TRIPLE_CLICKED: "1t ",
             curses.BUTTON2_PRESSED: "2p ",
             curses.BUTTON2_RELEASED: "2r ",
             curses.BUTTON2_CLICKED: "2c ",
             curses.BUTTON2_DOUBLE_CLICKED: "2d ",
             curses.BUTTON2_TRIPLE_CLICKED: "2t ",
             curses.BUTTON3_PRESSED: "3p ",
             curses.BUTTON3_RELEASED: "3r ",
             curses.BUTTON3_CLICKED: "3c ",
             curses.BUTTON3_DOUBLE_CLICKED: "3d ",
             curses.BUTTON3_TRIPLE_CLICKED: "3t ",
             curses.BUTTON4_PRESSED: "4p ",
             curses.BUTTON4_RELEASED: "4r ",
             curses.BUTTON4_CLICKED: "4c ",
             curses.BUTTON4_DOUBLE_CLICKED: "4d ",
             curses.BUTTON4_TRIPLE_CLICKED: "4t ",
             0x200000: "5p ",
             0x100000: "5r ",
             0x400000: "5c ",
             0x800000: "5d ",
             0x1000000: "5t ",
}
def ser_mouse(bstate):
    m = ""
    for k in mods.keys():
        if bstate & k:
            m += mods[k]
            pass
        pass

    s = ""
    for k in mousedict.keys():
        if bstate & k:
            s += mousedict[k]
            pass
        pass

    return m + s if s else "error (%d) " % bstate

def main(stdscr):
    stdscr.scrollok(True)
    stdscr.addstr("SHELL is: %s\n" % os.getenv("SHELL"))
    stdscr.addstr("TERM is: %s\n" % os.getenv("TERM"))

    while True:
        stdscr.addstr("OKAY so I need to know what behavior to use here\n")
        stdscr.addstr("curses lies A LOT about this, so pick your poison:\n")
        stdscr.addstr("1: No mouse events\n")
        stdscr.addstr("2: Buttons 1-3\n")
        stdscr.addstr("3: All mouse events\n")
        stdscr.addstr("4: Presses only\n")
        stdscr.addstr("5: Button 1 presses only\n")
        stdscr.addstr("6: Button 1 clicks and releases\n")
        stdscr.addstr("q: quit\n")
        c = stdscr.get_wch()
        stdscr.addstr("%s\n" % c)
        if c == "q":
            exit(0)
        elif c == "1":
            break
        elif c == "2":
            curses.mousemask(curses.BUTTON1_PRESSED |
                             curses.BUTTON1_RELEASED |
                             curses.BUTTON1_CLICKED |
                             curses.BUTTON1_DOUBLE_CLICKED |
                             curses.BUTTON1_TRIPLE_CLICKED |
                             curses.BUTTON2_PRESSED |
                             curses.BUTTON2_RELEASED |
                             curses.BUTTON2_CLICKED |
                             curses.BUTTON2_DOUBLE_CLICKED |
                             curses.BUTTON2_TRIPLE_CLICKED |
                             curses.BUTTON3_PRESSED |
                             curses.BUTTON3_RELEASED |
                             curses.BUTTON3_CLICKED |
                             curses.BUTTON3_DOUBLE_CLICKED |
                             curses.BUTTON3_TRIPLE_CLICKED)
            break
        elif c == "3":
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            break
        elif c == "4":
            curses.mousemask(curses.BUTTON1_PRESSED |
                             curses.BUTTON2_PRESSED |
                             curses.BUTTON3_PRESSED |
                             curses.BUTTON4_PRESSED |
                             0x200000)
            break
        elif c == "5":
            curses.mousemask(curses.BUTTON1_PRESSED)
            break
        elif c == "6":
            curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED)
            break
                
        stdscr.addstr("Come on, try again\n")
        continue
    
    while True:
        stdscr.addstr("Listening (q to quit)...\n")

        c = stdscr.get_wch()
        if c == 'q':
            break

        if c == curses.KEY_MOUSE:
            # sometimes curses will fail this call!  If you send it input it
            # doesn't understand (e.g., button 6/7) when it's not in "all",
            # python dumps a traceback.  Love that they made this exception
            # easy to catch.
            try:
                (devid, col, row, _, bstate) = curses.getmouse()
                pass
            except Exception as e:
                stdscr.addstr("%s  python-curses error: %s\n" %
                              (str(datetime.now()), str(e)))
                continue

            stdscr.addstr("%s  MOUSE#%s %s@ row %d, col %d\n" %
                          (str(datetime.now()), str(devid), ser_mouse(bstate),
                           row, col))
            continue

        row, _ = stdscr.getyx()
        stdscr.move(row, 0)
        stdscr.deleteln()

        desc = c if type(c) == str else curses.keyname(c).decode("utf8")
        stdscr.addstr(f"{datetime.now()}  {c}: {desc}\n")
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
