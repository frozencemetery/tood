#!/usr/bin/env python2

import curses
import json
import os
import subprocess
import sys

# Order matches my phone keyboard, but characters are removed that can't be
# easily typed on a normal American keyboard.  Don't like the order?  Don't
# have more than 26 items.  Or make it configurable.  That works too.
#
# normal (0) + shifted (1) + symbols (1) + special (2)
letters = "1234567890qwertyuiopasdfghjklzxcvbnm,." + \
          "!@#$%^&*()QWERTYUIOPASDFGHJKLZXCVBNM" + \
          "_-+/\"':;?" + "~`|={}\\[]<>"

# In a real language, this would be an enum type - maybe even a sum type!
CURSES_STATES = {
    "DEFAULT": 0,
    "HELPING": 1,
    "WAIT_TOGGLE": 2,
    "WAIT_MOVE_FROM": 3,
    "WAIT_MOVE_TO": 4,
    "WAIT_CREATE": 5,
    "WAIT_EDIT_LETTER": 6,
    "WAIT_EDIT_TEXT": 7,
}

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

def display_nth(stdscr, state, cols, n, at):
    letter = letters[n] if n < len(letters) else ' '

    qlen = len(state["queue"])
    if n < qlen:
        text = state["queue"][n]["text"]
        done = ' '
        pass
    elif n < qlen + len(state["done"]):
        text = state["done"][n - qlen]["text"]
        src = state["done"]
        done = 'X'
        pass
    else:
        return

    stdscr.move(at, 0)
    stdscr.clrtoeol()
    return stdscr.addnstr("%s: [%s] %s" % (letter, done, text), cols)

def display_state(stdscr, state, rows, cols, offset):
    stdscr.erase()
    stdscr.move(0, 0)

    for i in range(rows - 1): # for the prompt
        display_nth(stdscr, state, cols, i + offset, i)
        pass

    return update_prompt(stdscr, rows, cols, "& ")

def display_help(stdscr, rows):
    # TODO scrolling the help text re-introduces the main list
    helps = [
        "(?h)elp",
        "(q)uit",
        "(c)reate",
        "(t)oggle #",
        "(m)ove # #",
        "(l) refresh",
        "drag to scroll, or uparrow/downarrow, or C-p/C-n",
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
    return

def lookup_item(c):
    # TODO error handling?
    return letters.index(chr(c))

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

    curses_state = CURSES_STATES["DEFAULT"]

    offset = 0
    stdscr.scrollok(True)
    rows, cols = stdscr.getmaxyx()
    stdscr.setscrreg(0, rows - 2) # don't scroll the prompt
    display_state(stdscr, state, rows, cols, offset)
    while True:
        c = stdscr.getch()

        # First check the "global" operations
        if c == curses.KEY_RESIZE:
            old_rows, old_cols = rows, cols
            rows, cols = stdscr.getmaxyx()
            stdscr.setscrreg(0, rows - 2) # don't scroll the prompt

            for old_rows in range(old_rows, rows):
                # start at (old_rows + 1), and account for prompt
                display_nth(stdscr, state, cols, old_rows - 1 + offset,
                            old_rows - 1)
                pass
            update_prompt(stdscr, rows, cols, "& ")
            continue
        elif c in [curses.KEY_DOWN, 14]: # 14 is C-n
            offset += 1
            max_offset = len(state["queue"]) + len(state["done"]) - 1
            if offset > max_offset:
                offset = max_offset
                curses.flash()
                continue

            stdscr.scroll(1)

            # as always, account for the prompt
            display_nth(stdscr, state, cols, rows + offset - 2, rows - 2)
            continue
        elif c in [curses.KEY_UP, 16]: # 16 is C-p
            offset -= 1
            if offset < 0:
                offset = 0
                curses.flash()
                continue

            stdscr.scroll(-1)
            display_nth(stdscr, state, cols, offset, 0)
            continue

        # Next, we check states
        if curses_state == CURSES_STATES["HELPING"]:
            curses_state = CURSES_STATES["DEFAULT"]
            display_state(stdscr, state, rows, cols, offset)
            continue
        elif curses_state == CURSES_STATES["WAIT_TOGGLE"]:
            n = lookup_item(c)
            old_pos = n
            if n < len(state["queue"]):
                t = state["queue"].pop(n)
                state["done"].insert(0, t)
                new_pos = len(state["queue"])
                store(filename, state, "Completed item\n\n%s\n" % t["text"])
                pass
            else:
                n -= len(state["queue"])
                t = state["done"].pop(n)
                state["queue"].append(t)
                new_pos = len(state["queue"]) - 1
                store(filename, state,
                      "Un-completed item\n\n%s\n" % t["text"])
                pass

            for i in range(max(offset, min(old_pos, new_pos)),
                           min(rows - 1 + offset, max(old_pos, new_pos))):
                display_nth(stdscr, state, cols, i, i - offset)
                pass
            update_prompt(stdscr, rows, cols, "& ")
            curses_state = CURSES_STATES["DEFAULT"]
            continue
        elif curses_state == CURSES_STATES["WAIT_MOVE_FROM"]:
            move_from = lookup_item(c)
            stdscr.addnstr("%s " % letters[move_from], cols)
            curses_state = CURSES_STATES["WAIT_MOVE_TO"]
            continue
        elif curses_state == CURSES_STATES["WAIT_MOVE_TO"]:
            move_to = lookup_item(c)
            t = state["queue"].pop(move_from)
            state["queue"].insert(move_to, t)
            store(filename, state,
                  "Adjusted order of item\n\n%s\n" % t["text"])

            curses_state = CURSES_STATES["DEFAULT"]

            for i in range(max(offset, min(move_from, move_to)),
                           min(offset + rows - 1, max(move_from, move_to))):
                display_nth(stdscr, state, cols, i, i - offset)
                pass
            update_prompt(stdscr, rows, cols, "& ")
            continue
        elif curses_state == CURSES_STATES["WAIT_CREATE"]:
            if c in [curses.KEY_BACKSPACE, 0x7f]:
                if desc != "":
                    # TODO this could redraw slightly less
                    desc = desc[:-1]
                    update_prompt(stdscr, rows, cols, "& c %s" % desc)
                    pass
                continue
            elif c != ord('\n'):
                desc += chr(c)
                stdscr.addch(c)
                continue

            if desc != "": # allow empty string to abort
                state["queue"].append({"text": desc})
                store(filename, state, "Created new\n\n%s\n" % desc)

                i = len(state["queue"]) - 1
                # redraw everything below because lettering has changed
                for i in range(i, rows + offset):
                    display_nth(stdscr, state, cols, i, i - offset)
                    pass
                pass

            update_prompt(stdscr, rows, cols, "& ")
            curses_state = CURSES_STATES["DEFAULT"]
            continue
        elif curses_state == CURSES_STATES["WAIT_EDIT_LETTER"]:
            edit_idx = lookup_item(c)
            if edit_idx < len(state["queue"]):
                edit_item = state["queue"].pop(edit_idx)
                pass
            else:
                edit_item = state["done"].pop(edit_idx - len(state["queue"]))
                pass
            edit_text = edit_item["text"]
            update_prompt(stdscr, rows, cols, "& e " + edit_text)
            curses_state = CURSES_STATES["WAIT_EDIT_TEXT"]
            continue
        elif curses_state == CURSES_STATES["WAIT_EDIT_TEXT"]:
            if c in [curses.KEY_BACKSPACE, 0x7f]:
                if edit_text != "":
                    # TODO this could redraw slightly less
                    edit_text = edit_text[:-1]
                    update_prompt(stdscr, rows, cols, "& e " + edit_text)
                    pass
                continue
            elif c != ord('\n'):
                edit_text += chr(c)
                stdscr.addch(c)
                continue

            if edit_text != "": # empty reverts
                edit_item["text"] = edit_text
                pass

            if edit_idx <= len(state["queue"]):
                state["queue"].insert(edit_idx, edit_item)
                pass
            else:
                state["done"].insert(edit_idx - len(state["queue"]),
                                     edit_item)
                pass
            if edit_text != "":
                store(filename, state, "Edited: " + edit_item["text"])
                pass
            display_nth(stdscr, state, cols, edit_idx, edit_idx - offset)
            update_prompt(stdscr, rows, cols, "& ")
            curses_state = CURSES_STATES["DEFAULT"]
            continue

        # Finally, keys in the default state
        assert(curses_state == CURSES_STATES["DEFAULT"])
        if c == ord('q'):
            break
        elif c == ord('l'):
            stdscr.clear()
            display_state(stdscr, state, rows, cols, offset)
            continue
        elif c == ord('c'):
            update_prompt(stdscr, rows, cols, "& c ")
            curses_state = CURSES_STATES["WAIT_CREATE"]
            desc = ""
            continue
        elif c == ord('t'):
            update_prompt(stdscr, rows, cols, "& t ")
            curses_state = CURSES_STATES["WAIT_TOGGLE"]
            continue
        elif c == ord('m'):
            update_prompt(stdscr, rows, cols, "& m ")
            curses_state = CURSES_STATES["WAIT_MOVE_FROM"]
            continue
        elif c == ord('e'):
            update_prompt(stdscr, rows, cols, "& e ")
            curses_state = CURSES_STATES["WAIT_EDIT_LETTER"]
            continue
        elif c in [ord('?'), ord('h')]:
            display_help(stdscr, rows)
            curses_state = CURSES_STATES["HELPING"]
            continue

        # bad key
        curses.flash()
        continue
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
