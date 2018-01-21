#!/usr/bin/env python2

import curses
import json
import os
import sys

from git import Git

def store(git, filepath, state, msg="Update"):
    # TODO visual feedback on store

    json.dump(state, open(filepath, "w"))

    git.add(filepath)
    git.commit("-m", msg)
    pass

def load(filepath):
    return json.load(open(filepath, "r"))

def inc_ind(i):
    if i == 9:
        return 0
    elif i != ' ':
        return i + 1
    return i        

def display_state(stdscr, state, rows):
    stdscr.erase()
    stdscr.move(0, 0)
    i = 1
    # TODO handle more than can fit on the screen
    for t in state["queue"]:
        stdscr.addstr("%s: [ ] %s\n" % (str(i), t["text"]))
        i = inc_ind(i)
        pass
    for t in state["done"]:
        stdscr.addstr("%s: [X] %s\n" % (str(i), t["text"]))
        i = inc_ind(i)
        pass
    return

def prompt(stdscr, rows):
    stdscr.addstr(rows - 1, 0, "& ")
    return

def get_index(stdscr):
    n = stdscr.getch() - ord('0')
    if n == 0:
        n = 10
        pass
    return n - 1

def main(stdscr):
    storagedir = "/home/frozencemetery/.toodata"
    filename = "tood.json"

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
        state = {"queue": [{"text": "Make some TOOD"}],
                 "done": [{"text": "Create list"}]}
        store(git, filepath, state, "Create list")
        pass

    state = load(filepath)

    # TODO handle stupid wide lines frig
    rows, cols = stdscr.getmaxyx()
    display_state(stdscr, state, rows)
    prompt(stdscr, rows)

    while True:
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == ord('w'):
            store(git, filepath, state)
            pass
        elif c == ord('c'):
            stdscr.addstr("c ")
            curses.echo()
            desc = stdscr.getstr()
            curses.noecho()
            state["queue"].append({"text": desc})
            display_state(stdscr, state, rows)
            prompt(stdscr, rows)
            pass
        elif c == ord('t'):
            # TODO display as done without removing until next write?
            # TODO toggling of done things
            stdscr.addstr("t ")
            n = get_index(stdscr)
            t = state["queue"].pop(n)
            state["done"].insert(0, t)
            display_state(stdscr, state, rows)
            prompt(stdscr, rows)
            pass
        elif c == ord('m'):
            stdscr.addstr("m ")

            cur_ind = get_index(stdscr)
            stdscr.addstr("%s " % str(cur_ind + 1)[-1])

            tgt_ind = get_index(stdscr)

            t = state["queue"].pop(cur_ind)

            state["queue"].insert(tgt_ind, t)

            display_state(stdscr, state, rows)
            prompt(stdscr, rows)
            pass
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
