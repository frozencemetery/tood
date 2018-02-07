#!/usr/bin/env python2

import curses
import os
import sys

from datetime import datetime

def main(stdscr):
    stdscr.scrollok(True)
    while True:
        stdscr.addstr("Listening (q to quit)...")

        c = stdscr.getch()
        if c == ord('q'):
            break

        row, _ = stdscr.getyx()
        stdscr.move(row, 0)
        stdscr.deleteln()

        stdscr.addstr("%s  %s\n" % (str(datetime.now()), curses.keyname(c)))
        pass
    return

if __name__ == "__main__":
    # some distros make python be python3, which is... brave
    if sys.version_info.major != 2:
        print("I'm python2-only; trying to switch interpreters...")
        # argv[0] needs to be the interpreter; python hides this, making
        # argv[0] the program being interpreted
        exit(os.execlp("python2", "python2", sys.argv[0]))

    curses.wrapper(main)
    pass
