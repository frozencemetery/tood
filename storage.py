import json
import os
import subprocess

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


# Commands have a normal "text" field and a "command" field, which is a
# function that does ~something~ and returns the updated range.
class Storage:
    cmds = []
    queue = []
    done = []

    def store(self, filepath=None, msg="Update"):
        if not filepath:
            filepath = self.filepath
            pass

        whole = {"queue": self.queue, "done": self.done}
        with open(filepath, "w") as f:
            json.dump(whole, f, indent=4, separators=(",", ": "))
            pass
        cmd("git", "add", filepath)
        cmd("git", "commit", "-m", msg)
        return

    def toggle(self, stdscr, cs, n):
        old_pos = n
        if n < len(self.cmds):
            return self.cmds[n]["command"](stdscr, cs)

        n -= len(self.cmds)
        if n < len(self.queue):
            t = self.queue.pop(n)
            self.done.insert(0, t)
            new_pos = len(self.queue) + len(self.cmds)
            self.store(msg="Completed item\n\n%s\n" % t["text"])
            pass
        else:
            n -= len(self.queue)
            t = self.done.pop(n)
            self.queue.append(t)
            new_pos = len(self.queue) + len(self.cmds)
            self.store(msg="Un-completed item\n\n%s\n" % t["text"])
            pass
        return min(old_pos, new_pos) - 1, max(old_pos, new_pos) + 1

    def move(self, move_from, move_to):
        g_from, g_to = move_from, move_to

        storelen = len(self)
        if move_from >= storelen:
            return move_from, move_to
        move_to = min(move_to, storelen - 1)

        cmdlen = len(self.cmds)
        if move_from < cmdlen:
            return move_from, move_to
        move_to = max(move_to, cmdlen)
        move_from -= cmdlen
        move_to -= cmdlen

        queuelen = len(self.queue)
        if move_from < queuelen:
            tqueue = self.queue
            move_to = min(move_to, queuelen - 1)
            pass
        else:
            tqueue = self.done
            move_to = max(move_to, queuelen)
            move_from -= queuelen
            move_to -= queuelen
            pass

        if move_from == move_to:
            return move_from, move_to

        t = tqueue.pop(move_from)
        tqueue.insert(move_to, t)
        self.store(msg=f"Adjusted order of item\n\n{t['text']}\n")
        return min(g_from, g_to), max(g_from, g_to)

    def prepend(self, desc):
        self.queue.insert(0, {"text": desc})
        self.store(msg="Created new\n\n%s\n" % desc)
        return len(self.queue) - 1 + len(self.cmds)

    def __init__(self, cmds=None):
        if cmds is not None:
            self.cmds = cmds
            pass

        self.storagedir = os.path.join(os.environ["HOME"], ".toodata")
        self.filename = "tood.json"
        self.filepath = os.path.join(self.storagedir, self.filename)

        if not os.path.exists(self.storagedir):
            os.mkdir(self.storagedir)
            pass
        os.chdir(self.storagedir)

        try:
            cmd("git", "status")
            pass
        except subprocess.CalledProcessError:
            cmd("git", "init", ".")
            pass

        if not os.path.exists(self.filename):
            self.queue = [{"text": "Make some TOOD"}]
            self.done = [{"text": "Create list"}]
            self.store(msg="Create list")
            return

        with open(self.filepath, "r") as f:
            d = json.load(f)
            pass

        try:
            self.queue = d["queue"]
            pass
        except AttributeError:
            pass

        try:
            self.done = d["done"]
            pass
        except AttributeError:
            pass
        return

    def __len__(self):
        return len(self.cmds) + len(self.queue) + len(self.done)

    def __getitem__(self, key):
        if type(key) != int:
            raise TypeError
        cmdlen = len(self.cmds)
        if key < cmdlen:
            return self.cmds[key]
        key -= cmdlen
        qlen = len(self.queue)
        if key < qlen:
            return self.queue[key]
        return self.done[key - qlen]

    def __setitem__(self, key, value):
        if type(key) != int or type(value) != str:
            raise TypeError
        if value == "": # abort on empty string
            return
        cmdlen = len(self.cmds)
        key -= cmdlen # TODO
        assert(key >= 0)
        qlen = len(self.queue)
        if key < qlen:
            self.queue[key]["text"] = value
            pass
        else:
            key -= qlen
            self.done[key]["text"] = value
            pass
        self.store(msg="Edited: " + value)
        return
