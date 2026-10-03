#!/usr/bin/env python3
"""tool -- the blocks a program needs to be a tool, not just a sum.

Same one contract: `step(ctx) -> value`.

Up to now a program could look at things and draw things. These are the
pieces that let one ASK you something, RUN something, and SHOW you a
list of what it found -- which is everything `claude-ready.py` does, and
the reason that was written in Python instead of in blocks.

    have git                  is git here?
    row  "git"                remember that answer as a row
    have curl
    row  "curl"
    table                     show every row gathered
    pick "install git" "quit" eight choices at most, the last goes back

THE INSIDES ARE BLOCKS TOO
--------------------------
Every block below is a name, a sentence, and one line of doing. The
shapes they share -- "answers yes or no", "takes a line from the
person", "remembers a row" -- are written once as small bases at the
top, and each block is the smallest difference from one of those.

Standard library only.
"""

import os
import shutil
import subprocess
import sys

from .core import Part, _as_list

# What every block in this module needs, unless it says otherwise.
FITS = {"needs": ["shell"], "changes": "nothing", "waits": False}

SLOTS = 8                      # choices on screen, the last always back
ROWS  = "#rows"                # where a run's table is kept
LAST  = "#lastrun"             # how the last `run` went


# ==========================================================================
#  THE SMALL SHAPES, WRITTEN ONCE
# ==========================================================================

class Test(Part):
    """A block that answers yes or no. Override `yes`."""
    def step(self, ctx):
        return bool(self.yes(ctx))

    def yes(self, ctx):
        return False


class Doing(Part):
    """A block that does something and says what came of it. Override `did`."""
    def step(self, ctx):
        return self.did(ctx)

    def did(self, ctx):
        return ctx.value


class Asking(Part):
    """A block that asks the person something. Override `question`.

    Where nobody is there to answer -- a pipe, a test -- it hands back
    `None` at once rather than waiting forever.
    """
    def step(self, ctx):
        if not sys.stdin.isatty():
            return None
        try:
            return self.question(ctx)
        except (EOFError, KeyboardInterrupt):
            print()
            return None


# ==========================================================================
#  LOOKING
# ==========================================================================

class Have(Test):
    """Is this program installed and runnable? `have git`"""
    fits = {"needs": []}
    def __init__(self, program): self.program = program
    def yes(self, ctx): return shutil.which(str(self.program)) is not None


class Inside(Test):
    """Is this folder there? `inside /data/data/com.termux`"""
    fits = {"needs": ["files"]}
    def __init__(self, path): self.path = path
    def yes(self, ctx): return os.path.isdir(os.path.expanduser(str(self.path)))


class Kind(Doing):
    """What sort of machine is this -- aarch64, armv7l, x86_64, AMD64."""
    fits = {"needs": []}
    def did(self, ctx):
        import platform
        return platform.machine()


class Worked(Test):
    """Did the last `run` work? Nothing run yet counts as no."""
    def yes(self, ctx): return bool(ctx.vars.get(LAST, {}).get("worked"))


# ==========================================================================
#  DOING
# ==========================================================================

class Run(Doing):
    """Run a command and hand on what it said.

        run pkg install git -y

    The command is printed before it runs, so nothing happens unseen.
    `run quiet=true` keeps the output to itself; otherwise you watch it
    as it goes. Whether it worked is remembered for `worked`.
    """
    fits = {"needs": ["shell"], "changes": "anything", "waits": True}
    def __init__(self, *words, **how):
        self.words = [str(w) for w in words]
        self.quiet = bool(how.get("quiet", False))
        self.secs  = how.get("seconds", 1800)

    def did(self, ctx):
        if not self.words:
            return ""
        print("\n$ " + " ".join(self.words))
        try:
            out = subprocess.run(self.words, capture_output=self.quiet,
                                 text=True, timeout=self.secs)
            said = ((out.stdout or "") + (out.stderr or "")).strip() \
                if self.quiet else ""
            ctx.vars[LAST] = {"worked": out.returncode == 0, "said": said}
            return said
        except Exception as e:
            ctx.vars[LAST] = {"worked": False, "said": str(e)}
            print("  it did not run: %s" % e)
            return ""


class Open(Doing):
    """Open a file or an address with whatever usually opens it.

    `open panel/panel.html` puts the browser panel on the screen. On a
    phone it hands the job to Android.
    """
    fits = {"needs": ["shell"], "changes": "anything"}
    def __init__(self, what=None): self.what = what

    def did(self, ctx):
        what = str(self.what if self.what is not None else ctx.value)
        path = os.path.abspath(os.path.expanduser(what))
        target = path if os.path.exists(path) else what
        try:
            import webbrowser
            if webbrowser.open(
                    ("file://" + target) if os.path.exists(target) else target):
                return target
        except Exception:
            pass
        for opener in (["termux-open", target], ["xdg-open", target]):
            try:
                if subprocess.run(opener, timeout=20).returncode == 0:
                    return target
            except Exception:
                continue
        print("  could not open it -- open %s by hand" % target)
        return target


class Stop(Part):
    """Give up here, quietly, when what came in is true."""
    fits = {"needs": []}
    class Enough(Exception):
        """Thrown to end a run early. The runner catches it."""

    def __init__(self, saying=""): self.saying = saying

    def step(self, ctx):
        if ctx.value:
            raise Stop.Enough(str(self.saying))
        return ctx.value


# ==========================================================================
#  ASKING
# ==========================================================================

class Ask(Asking):
    """Ask the person something and hand on what they typed."""
    fits = {"needs": ["person", "terminal"], "waits": True}
    def __init__(self, about="", default=""):
        self.about, self.default = about, default

    def question(self, ctx):
        said = input(" %s: " % (self.about or "")).strip()
        return said or self.default


class Sure(Asking):
    """Ask a yes-or-no question. Anything but yes counts as no."""
    fits = {"needs": ["person", "terminal"], "waits": True}
    def __init__(self, about="go on?"): self.about = about

    def question(self, ctx):
        said = input(" %s (y/n): " % self.about).strip().lower()
        return said.startswith("y")


class Pick(Asking):
    """Eight choices at most, the last always back, pick one by number.

        pick "install git" "install curl" "do both"

    Hands on the words you picked, or None for back. The same rule the
    menus and the pad keep, as a block you can put in a program.
    """
    fits = {"needs": ["person", "terminal"], "waits": True}
    def __init__(self, *choices, **how):
        self.choices = [str(c) for c in choices]
        self.back = str(how.get("back", "back"))

    def question(self, ctx):
        choices = self.choices or [str(c) for c in _as_list(ctx.value)]
        window  = choices[:SLOTS - 1]
        print()
        for i, choice in enumerate(window, 1):
            print("  %d) %s" % (i, choice))
        print("  %d) %s" % (SLOTS, self.back))
        said = input(" 1-%d: " % SLOTS).strip()
        if not said.isdigit():
            return None
        n = int(said)
        return window[n - 1] if 1 <= n <= len(window) else None


# ==========================================================================
#  SHOWING WHAT YOU FOUND
# ==========================================================================

class Row(Doing):
    """Remember what came in as a row of a table, under this name.

        have git
        row "git"

    True becomes `ok`, false becomes `--`. The answer carries on, so a
    row never gets in the way of what follows.
    """
    fits = {"needs": [], "changes": "vars"}
    def __init__(self, name, note=""):
        self.name, self.note = str(name), str(note)

    def did(self, ctx):
        ctx.vars.setdefault(ROWS, []).append(
            {"name": self.name, "ok": bool(ctx.value), "note": self.note,
             "said": "" if isinstance(ctx.value, bool) else str(ctx.value)})
        return ctx.value


class Table(Doing):
    """Show every row gathered so far, and hand on the ones that failed."""
    fits = {"needs": ["terminal"], "changes": "screen"}
    def __init__(self, title=""): self.title = str(title)

    def did(self, ctx):
        rows = ctx.vars.get(ROWS, [])
        wide = _room()
        if self.title:
            print("\n" + "=" * wide)
            print(" " + self.title)
        print("=" * wide)
        for r in rows:
            says = r["note"] or r["said"]
            room = wide - 25
            if len(says) <= room:
                print("  %-4s %-16s %s" % (_mark(r), r["name"][:16], says))
            else:
                # too long for the line: put it underneath, not cut off
                print("  %-4s %s" % (_mark(r), r["name"]))
                for line in _fold(says, wide - 8):
                    print("        %s" % line)
        print("=" * wide)
        return [r["name"] for r in rows if not r["ok"]]


class Missing(Doing):
    """The names of the rows that said no. Nothing missing is an empty list."""
    def did(self, ctx):
        return [r["name"] for r in ctx.vars.get(ROWS, []) if not r["ok"]]


class Forget(Doing):
    """Throw the rows away and start the table again."""
    fits = {"needs": [], "changes": "vars"}
    def did(self, ctx):
        ctx.vars[ROWS] = []
        return ctx.value


def _mark(row):
    return "ok" if row["ok"] else "--"


def _fold(text, room):
    """Break a line to fit a narrow phone screen, on spaces."""
    words, line, out = str(text).split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > room:
            if line:
                out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out


def _room():
    try:
        return max(38, min(72, os.get_terminal_size().columns))
    except OSError:
        return 46


CATALOGUE = {
    "look":  [Have, Inside, Kind, Worked],
    "do":    [Run, Open, Stop],
    "ask":   [Ask, Sure, Pick],
    "table": [Row, Table, Missing, Forget],
}
