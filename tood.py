#!/usr/bin/env python2

import curses
import os
import sys

from git import Git


def store(git, filepath, done, queue, msg):
    data = ""

    if len(done) > 0:
        data += "- [X] "
        data += "\n- [X] ".join(done)
        data += "\n"
        pass

    if len(queue) > 0:
        data += "- [ ] "
        data += "\n- [ ] ".join(queue)
        data += "\n"
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
    for t in queue[:rows]:
        stdscr.addstr("- [ ] %s\n" % t)
        pass

    stdscr.addstr(rows - 1, 0, "& ")

    while True:
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
