import curses
from curses import ascii

# if they ever decide to fix this...
try:
    curses.BUTTON5_PRESSED
    pass
except AttributeError:
    curses.BUTTON5_PRESSED = 0x200000
    pass

COLOR_PAIRS = {
    "HIGHLIGHT": lambda: curses.color_pair(1),
    "EDGE": lambda: curses.color_pair(2),
    "EDGE_HIGHLIGHT": lambda: curses.color_pair(3),
}

class CState:
    def __init__(self, stdscr, store, helptext):
        self.stdscr = stdscr
        self.store = store
        self.helptext = helptext

        self._highlight = 0
        self._offset = 0

        self.stdscr.scrollok(True)
        self.rows, self.cols = stdscr.getmaxyx()
        self.stdscr.setscrreg(0, self.rows - 1)
        curses.curs_set(0) # invisible cursor

        # 1 is left click, 4 is scroll up, 5 is scroll down
        curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED |
                         curses.BUTTON1_CLICKED | curses.BUTTON4_PRESSED |
                         curses.BUTTON5_PRESSED) # button5 defined above
        curses.mouseinterval(0) # waiting here makes everything really laggy

        curses.use_default_colors()
        curses.init_pair(1, 0, 0xb)
        curses.init_pair(2, 0xc, -1)
        curses.init_pair(3, 0xc, 0xb)
        pass

    def display_nth(self, n):
        at = n - self._offset
        if at >= self.rows or at < 0:
            return
        elif n >= len(self.store):
            return

        text = self.store[n]["text"]

        cmdlen = len(self.store.cmds)        
        qlen = len(self.store.queue)
        done = " ->" if n < cmdlen else "[ ]" if n - cmdlen < qlen else "[X]"

        self.stdscr.move(at, 0);
        self.stdscr.clrtoeol()

        if n == self._highlight and (n == 0 or n == len(self.store) - 1):
            return self.stdscr.addnstr(f"{done} {text}", self.cols,
                                       COLOR_PAIRS["EDGE_HIGHLIGHT"]())
        elif n == self._highlight:
            return self.stdscr.addnstr(f"{done} {text}", self.cols,
                                       COLOR_PAIRS["HIGHLIGHT"]())
        elif n == 0 or n == len(self.store) - 1:
            return self.stdscr.addnstr(f"{done} {text}", self.cols,
                                       COLOR_PAIRS["EDGE"]())
        return self.stdscr.addnstr(f"{done} {text}", self.cols)

    def display_store(self):
        self.stdscr.erase()
        self.stdscr.move(0, 0)

        for i in range(self.rows):
            self.display_nth(i + self._offset)
            pass
        return

    def resize(self):
        old_rows, old_cols = self.rows, self.cols
        self.rows, self.cols = self.stdscr.getmaxyx()
        self.stdscr.setscrreg(0, self.rows - 1)

        for old_row in range(old_rows, self.rows):
            self.display_nth(old_row + self._offset)
            pass
        else:
            # have to make a draw call here; otherwise, it doesn't actually
            # process the resize and you get a blank screen
            self.stdscr.refresh()
            pass
        pass

    def scroll_down(self):
        self._offset += 1
        max_offset = len(self.store) - 1
        if self._offset > max_offset:
            self._offset = max_offset
            return

        self.stdscr.scroll(1)

        if self._highlight < self._offset:
            self._highlight = self._offset
            self.display_nth(self._highlight)
            pass
        
        self.display_nth(self.rows + self._offset - 1)
        return

    def scroll_up(self):
        self._offset -= 1
        if self._offset < 0:
            self._offset = 0
            return

        self.stdscr.scroll(-1)

        bot = min(self.rows + self._offset, len(self.store)) - 1
        if self._highlight > bot:
            self._highlight = bot
            self.display_nth(self._highlight)
            pass

        self.display_nth(self._offset)
        return

    def _set_highlight_abs(self, new):
        if new == self._highlight:
            return True

        oldh = self._highlight
        self._highlight = new

        bot = min(self.rows + self._offset, len(self.store)) - 1
        if self._highlight < 0:
            self._highlight = 0
            pass
        elif self._highlight >= bot:
            self._highlight = bot
            pass            

        self.display_nth(oldh)
        self.display_nth(self._highlight)
        return False

    def set_highlight_local(self, i):
        return self._set_highlight_abs(i + self._offset)

    def get_highlight_abs(self):
        return self._highlight

    def getline(self, stdscr, text="", edge=False):
        # surprise!  State machine.  (For text entry.)
        curses.curs_set(1) # visible cursor
        color = "EDGE_HIGHLIGHT" if edge else "HIGHLIGHT"
        while True:
            c = stdscr.getch()
            if c in [curses.KEY_ENTER, ascii.LF]:
                break
            elif c == curses.KEY_RESIZE:
                self.resize()
                continue
            elif c == curses.KEY_MOUSE:
                # not worth disabling mouse support here, but also ignore it
                continue
            elif c in [curses.KEY_BACKSPACE, ascii.DEL]:
                if text == "":
                    continue
                text = text[:-1]
                row, col = stdscr.getyx()
                stdscr.move(row, col - 1)
                stdscr.delch()
                continue
            elif c < ord(' '):
                continue

            cc = chr(c)
            # addch seems to ignore the attrs passed...
            stdscr.addstr(cc, COLOR_PAIRS[color]())
            text += cc
            continue

        curses.curs_set(0) # invisible cursor
        return text

    pass # end of class CState
