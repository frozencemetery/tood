#!/usr/bin/env python2

import curses
import json
import os
import subprocess
import sys

letters = "1234567890qwertyuiopasdfghjklzxcvbnm,."

def cmd(*args):
    # try/except is faster than hasattr() only in the success case
    try:
        cmd.devnull
        pass
    except AttributeError:
        cmd.devnull = open(os.devnull, "w")
        pass

    return subprocess.check_call(args, stdout=cmd.devnull,
                                 stderr=subprocess.STDOUT)

def store(filepath, state, msg="Update"):
    json.dump(state, open(filepath, "w"),
              indent=4, separators=(',', ': '))

    cmd("git", "add", filepath)
    cmd("git", "commit", "-m", msg)
    pass

def load(filepath):
    return json.load(open(filepath, "r"))

def update_prompt(stdscr, rows, cols, p):
    stdscr.move(rows - 1, 0)
    stdscr.clrtoeol()

    # can't paint bottom right
    return stdscr.addnstr(p, cols - 1)

def display_state(stdscr, state, rows, cols):
    stdscr.erase()
    stdscr.move(0, 0)
    i = 0
    for t in state["queue"]:
        if i > rows - 2: # for the prompt
            break

        letter = letters[i] if i < len(letters) else ' '
        stdscr.addnstr("%s: [ ] %s\n" % (letter, t["text"]), cols)
        i += 1
        pass
    for t in state["done"]:
        if i > rows - 2: # for the prompt
            break

        letter = letters[i] if i < len(letters) else ' '
        stdscr.addnstr("%s: [X] %s\n" % (letter, t["text"]), cols)
        i += 1
        pass

    return update_prompt(stdscr, rows, cols, "& ")

def display_help(stdscr, rows):
    helps = [
        "(?h)elp",
        "(q)uit",
        "(c)reate",
        "(t)oggle #",
        "(m)ove # #",
        "(l) refresh",
        "press any key to continue\n",
    ]
    if len(helps) < rows:
        disp = "\n".join(helps)
        pass
    else:
        disp = "  ".join(helps)
        pass

    stdscr.erase()
    stdscr.move(0, 0)
    stdscr.addstr(disp)

    c = stdscr.getch()
    if c == curses.KEY_RESIZE:
        # hack: forward back to main loop so we don't discard a refresh event
        curses.ungetch(c)
        pass
    return

def get_index(stdscr):
    return letters.index(chr(stdscr.getch()))

def main(stdscr):
    storagedir = os.path.join(os.environ["HOME"], ".toodata")
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
    display_state(stdscr, state, rows, cols)

    while True:
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == curses.KEY_RESIZE:
            # TODO don't redraw the entire screen here
            rows, cols = stdscr.getmaxyx()
            stdscr.erase()
            display_state(stdscr, state, rows, cols)
            pass
        elif c == ord('l'):
            stdscr.clear()
            display_state(stdscr, state, rows, cols)
            pass
        elif c == ord('c'):
            update_prompt(stdscr, rows, cols, "& c ")

            curses.echo()
            desc = stdscr.getstr()
            curses.noecho()

            state["queue"].append({"text": desc})
            store(filename, state, "Created new\n\n%s\n" % desc)

            # TODO don't redraw the entire screen here
            stdscr.erase()
            display_state(stdscr, state, rows, cols)
            pass
        elif c == ord('t'):
            update_prompt(stdscr, rows, cols, "& t ")

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

            # TODO don't redraw the entire screen here
            stdscr.erase()
            display_state(stdscr, state, rows, cols)
            pass
        elif c == ord('m'):
            update_prompt(stdscr, rows, cols, "& m ")

            cur_ind = get_index(stdscr)
            stdscr.addnstr("%s " % letters[cur_ind], cols)

            tgt_ind = get_index(stdscr)

            t = state["queue"].pop(cur_ind)

            state["queue"].insert(tgt_ind, t)

            store(filename, state,
                  "Adjusted order of item\n\n%s\n" % t["text"])

            # TODO don't redraw the entire screen here
            stdscr.erase()
            display_state(stdscr, state, rows, cols)
            pass
        elif c in [ord('?'), ord('h')]:
            display_help(stdscr, rows)
            pass
        else:
            update_prompt(stdscr, rows, cols, "Whuff-whuff! & ")
            pass
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
