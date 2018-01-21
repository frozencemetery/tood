#!/usr/bin/env python2

import curses
import json
import os
import sys

from git import Git

letters = "1234567890qwertyuiopasdfghjklzxcvbnm"

def store(git, filepath, state, msg="Update"):
    # TODO visual feedback on store

    json.dump(state, open(filepath, "w"))

    git.add(filepath)
    git.commit("-m", msg)
    pass

def load(filepath):
    return json.load(open(filepath, "r"))

def display_state(stdscr, state, rows):
    # TODO handle stupid wide lines frig
    stdscr.erase()
    stdscr.move(0, 0)
    i = 0
    for t in state["queue"]:
        if i > rows - 1: # for the prompt
            return

        letter = letters[i] if i < len(letters) else ' '
        stdscr.addstr("%s: [ ] %s\n" % (letter, t["text"]))
        i += 1
        pass
    for t in state["done"]:
        if i > rows - 1: # for the prompt
            return

        letter = letters[i] if i < len(letters) else ' '
        stdscr.addstr("%s: [X] %s\n" % (letter, t["text"]))
        i += 1
        pass
    stdscr.addstr(rows - 1, 0, "& ")
    return

def get_index(stdscr):
    n = letters.index(chr(stdscr.getch()))
    return n

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
    rows, cols = stdscr.getmaxyx()

    while True:
        display_state(stdscr, state, rows)
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            pass
        elif c == ord('l'):
            stdscr.clear()
            pass
        elif c == ord('c'):
            stdscr.addstr("c ")
            curses.echo()
            desc = stdscr.getstr()
            curses.noecho()
            state["queue"].append({"text": desc})
            store(git, filepath, state, "Created new\n\n%s\n" % desc)
            pass
        elif c == ord('t'):
            stdscr.addstr("t ")
            n = get_index(stdscr)
            if n < len(state["queue"]):
                t = state["queue"].pop(n)
                state["done"].insert(0, t)
                store(git, filepath, state,
                      "Completed item\n\n%s\n" % t["text"])
                pass
            else:
                n -= len(state["queue"])
                t = state["done"].pop(n)
                state["queue"].append(t)
                store(git, filepath, state,
                      "Un-completed item\n\n%s\n" % t["text"])
                pass
            pass
        elif c == ord('m'):
            stdscr.addstr("m ")

            cur_ind = get_index(stdscr)
            stdscr.addstr("%s " % letters[cur_ind])

            tgt_ind = get_index(stdscr)

            t = state["queue"].pop(cur_ind)

            state["queue"].insert(tgt_ind, t)

            store(git, filepath, state,
                  "Adjusted order of item\n\n%s\n" % t["text"])
            pass
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
