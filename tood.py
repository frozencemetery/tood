#!/usr/bin/env python2

import curses
import json
import os
import subprocess
import sys

letters = "1234567890qwertyuiopasdfghjklzxcvbnm,."

def cmd(*args):
    DEVNULL = open(os.devnull, "w")
    return subprocess.check_call(args, stdout=DEVNULL,
                                 stderr=subprocess.STDOUT)

def store(filepath, state, msg="Update"):
    # TODO visual feedback on store

    json.dump(state, open(filepath, "w"))

    cmd("git", "add", filepath)
    cmd("git", "commit", "-m", msg)
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
    os.chdir(storagedir)

    try:
        cmd("git", "status")
        pass
    except subprocess.CalledProcessError:
        cmd("git", "init", ".")
        pass

    if not os.path.exists(filename):
        state = {"queue": [{"text": "Make some TOOD"}],
                 "done": [{"text": "Create list"}]}
        store(filename, state, "Create list")
        pass

    state = load(filename)
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
            store(filename, state, "Created new\n\n%s\n" % desc)
            pass
        elif c == ord('t'):
            stdscr.addstr("t ")
            n = get_index(stdscr)
            if n < len(state["queue"]):
                t = state["queue"].pop(n)
                state["done"].insert(0, t)
                store(filename, state, "Completed item\n\n%s\n" % t["text"])
                pass
            else:
                n -= len(state["queue"])
                t = state["done"].pop(n)
                state["queue"].append(t)
                store(filename, state,
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

            store(filename, state,
                  "Adjusted order of item\n\n%s\n" % t["text"])
            pass
        elif c in [ord('?'), ord('h')]:
            stdscr.addstr(rows - 1, 0,
                          "[q]uit [c]reate [t]oggle [m]ove redraw[l] <ret>")
            stdscr.getch()
            pass
        pass
    return

if __name__ == "__main__":
    curses.wrapper(main)
    pass
