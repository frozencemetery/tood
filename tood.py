#!/usr/bin/env python2

import curses
import os
import sys

from git import Git

def store(git, filepath, done, queue, msg="Update"):
    # TODO visual feedback on store
    data = ""

    for d in done:
        data += "- [X] %s\n" % d
        pass

    for q in queue:
        data += "- [ ] %s\n" % q
        pass

    open(filepath, "w").write(data)

    git.add(filepath)
    git.commit("-m", msg)
    pass

def load(filepath):
    # TODO this can't deal with line wrapping
    data = open(filepath, "r").read().split("\n")
    queue = []
    done = []
    for line in data:
        if len(line) <= 0:
            continue
        elif line.startswith("- [X] "):
            done.append(line[len("- [X] "):])
            continue
        elif line.startswith("- [ ] "):
            queue.append(line[len("- [ ] "):])
            continue
        print("Parse error on line: %s\n" % line)
        pass
    return (queue, done)

def display_queue(stdscr, queue, rows):
    stdscr.erase()
    stdscr.move(0, 0)
    i = 1
    for t in queue[:rows]:
        stdscr.addstr("%s: [ ] %s\n" % (str(i), t))
        if i == 0:
            i = ' '
            pass
        elif i == 9:
            i = 0
            pass
        elif i != ' ':
            i += 1
            pass
        pass
    return

def prompt(stdscr, rows):
    stdscr.addstr(rows - 1, 0, "& ")
    return

def main(stdscr):
    storagedir = "/home/frozencemetery/.toodata"
    filename = "tood.org"

    if not os.path.exists(storagedir):
        os.mkdir(storagedir)
        pass

    git = Git(storagedir)
    try:
        git.status()
        pass
    except:
        git.init()
        pass

    filepath = os.path.join(storagedir, filename)
    if not os.path.exists(filepath):
        open(filepath, "w").write("- [ ] add some TOOD\n")
        git.add(filepath)
        git.commit("-m", "Create new TOOD")
        pass

    queue, done = load(filepath)

    # TODO handle stupid wide lines frig
    rows, cols = stdscr.getmaxyx()
    display_queue(stdscr, queue, rows)
    prompt(stdscr, rows)

    while True:
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == ord('w'):
            store(git, filepath, done, queue)
            pass
        elif c == ord('c'):
            stdscr.addstr("c ")
            curses.echo()
            desc = stdscr.getstr()
            curses.noecho()
            queue.append(desc)
            display_queue(stdscr, queue, rows)
            prompt(stdscr, rows)
            pass
        elif c == ord('t'):
            # TODO display as done without removing until next write?
            stdscr.addstr("t ")
            n = stdscr.getch() - ord('0')
            if n == 0:
                n = 10
                pass
            t = queue.pop(n - 1)
            done.append(t)
            display_queue(stdscr, queue, rows)
            prompt(stdscr, rows)
            pass
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
