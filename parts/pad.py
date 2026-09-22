#!/usr/bin/env python3
"""pad -- the screen as eight squares you press, and a strip that talks.

    python3 -m parts pad

The window is divided into a grid two squares across and five down:

    +---------------------+
    |        strip        |   the top two squares, joined: what the
    |                     |   program says, and what you have built
    +----------+----------+
    |    1     |    2     |
    +----------+----------+
    |    3     |    4     |   eight squares, pressed by touch
    +----------+----------+
    |    5     |    6     |
    +----------+----------+
    |    7     |    8     |   the eighth always goes back
    +----------+----------+

Eight, because that is the same rule the numbered menu follows: never
more than eight choices, and the last one always goes back. When a list
is longer, the seventh becomes `more`.

The squares size themselves to whatever window Termux gives them, so it
fits a tall phone screen without being told anything about it.

MADE OF BLOCKS
--------------
The pad is not special. It is blocks like everything else, and a program
can lay out its own:

    pad
    button 1 "go left"
    button 2 "go right"
    button 8 back
    press
    say pressed

Standard library only.
"""

import os
import sys

from .core import Part
from .screen import read_tap

HOLD = "#pad"

TOPLEFT = "+"
ACROSS  = "-"
DOWN    = "|"


# ==========================================================================
#  THE LAYOUT
# ==========================================================================

class Layout:
    """Where every square sits, in characters."""

    def __init__(self, cols=2, rows=4, strip=1):
        try:
            self.w, self.h = os.get_terminal_size()
        except OSError:
            self.w, self.h = 40, 24
        self.cols, self.rows, self.strip = cols, rows, strip
        # the strip is `strip` rows of squares tall; the buttons take the rest
        cells_down     = rows + strip
        self.cell_h    = max(3, self.h // cells_down)
        self.cell_w    = max(6, self.w // cols)
        self.strip_h   = self.cell_h * strip
        self.button_h  = self.cell_h

    def strip_box(self):
        return 0, 0, self.cell_w * self.cols, self.strip_h

    def box(self, n):
        """Square n, counting from one, as (x, y, w, h) in characters."""
        i = n - 1
        if not 0 <= i < self.cols * self.rows:
            return None
        cx, cy = i % self.cols, i // self.cols
        return (cx * self.cell_w,
                self.strip_h + cy * self.button_h,
                self.cell_w, self.button_h)

    def which(self, col, row):
        """Which square holds this character cell? None for the strip."""
        if row < self.strip_h:
            return None
        cx = col // self.cell_w
        cy = (row - self.strip_h) // self.button_h
        if not (0 <= cx < self.cols and 0 <= cy < self.rows):
            return None
        return cy * self.cols + cx + 1


def layout_of(ctx, make=True):
    lay = ctx.vars.get(HOLD)
    if lay is None and make:
        lay = Layout()
        ctx.vars[HOLD] = lay
    return lay


# ==========================================================================
#  DRAWING
# ==========================================================================

def at(x, y):
    return "\033[%d;%dH" % (y + 1, x + 1)


def frame(x, y, w, h, label="", tag="", filled=False):
    """One square, drawn where it belongs, with its words in the middle."""
    if w < 4 or h < 2:
        return
    out = [at(x, y) + TOPLEFT + ACROSS * (w - 2) + TOPLEFT]
    body = "#" if filled else " "
    for row in range(1, h - 1):
        out.append(at(x, y + row) + DOWN + body * (w - 2) + DOWN)
    out.append(at(x, y + h - 1) + TOPLEFT + ACROSS * (w - 2) + TOPLEFT)

    if tag:
        out.append(at(x + 2, y) + tag[:w - 4])
    if label:
        words = _wrap(label, w - 4)
        start = y + max(1, (h - len(words)) // 2)
        for i, line in enumerate(words):
            if start + i >= y + h - 1:
                break
            out.append(at(x + (w - len(line)) // 2, start + i) + line)
    sys.stdout.write("".join(out))


def _wrap(text, room):
    if room < 1:
        return []
    words, line, out = str(text).split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > room:
            if line:
                out.append(line)
            line = word[:room]
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out[:4]


def wipe():
    sys.stdout.write("\033[2J\033[H")


def flush():
    sys.stdout.flush()


# ==========================================================================
#  THE BLOCKS
# ==========================================================================

class Pad(Part):
    """Lay the window out in squares and clear it.

    `pad` alone gives two across and four down, with a strip one square
    tall joined across the top -- eight buttons, which is the most a
    menu here ever shows.
    """
    def __init__(self, cols=2, rows=4, strip=1):
        self.cols, self.rows, self.strip = int(cols), int(rows), int(strip)

    def step(self, ctx):
        ctx.vars[HOLD] = Layout(self.cols, self.rows, self.strip)
        wipe()
        flush()
        return ctx.value


class Button(Part):
    """Draw one square, with words in it.

    `button 3 "find files"` -- and `button 3 "" on=true` fills it in, so a
    square can show something being on as well as being pressable.
    """
    def __init__(self, n, label="", on=False, tag=None):
        self.n, self.label, self.on = int(n), label, on
        self.tag = str(n) if tag is None else tag

    def step(self, ctx):
        lay = layout_of(ctx)
        box = lay.box(self.n)
        if box:
            frame(*box, label=self.label, tag=self.tag, filled=self.on)
            flush()
        return ctx.value


class Banner(Part):
    """Write into the strip across the top. A list becomes one line each."""
    def __init__(self, text=None, line=0):
        self.text, self.line = text, line

    def step(self, ctx):
        lay = layout_of(ctx)
        x, y, w, h = lay.strip_box()
        what = ctx.value if self.text is None else self.text
        rows = what if isinstance(what, (list, tuple)) else [what]
        for i, row in enumerate(rows):
            if self.line + i >= h:
                break
            text = str(row)[:w - 1]
            sys.stdout.write(at(x, y + self.line + i) + " " * (w - 1))
            sys.stdout.write(at(x, y + self.line + i) + text)
        flush()
        return ctx.value


class Press(Part):
    """Wait for a square to be pressed. Answers its number, or None.

    A typed digit counts too, so it still works where touch does not.
    """
    def __init__(self, seconds=None):
        self.seconds = seconds

    def step(self, ctx):
        return press(layout_of(ctx), self.seconds)


def press(lay, seconds=None):
    """One press: by touch, or by a typed digit. None if neither came."""
    spot = read_tap(seconds)
    if spot is None:
        return _typed_digit(lay)
    col, row = spot
    return lay.which(col, row)


def _typed_digit(lay):
    """Fall back to the keyboard when the terminal reports no touches."""
    if not sys.stdin.isatty():
        return None
    try:
        said = input()
    except (EOFError, KeyboardInterrupt):
        return None
    said = said.strip()
    if said.isdigit():
        n = int(said)
        if 1 <= n <= lay.cols * lay.rows:
            return n
    return None


CATALOGUE = {
    "pad": [Pad, Button, Banner, Press],
}


# ==========================================================================
#  THE MENU, PRESSED RATHER THAN TYPED
#
#  The same rule as the numbered menu: never more than eight choices, the
#  eighth always goes back, and a longer list puts `more` on the seventh.
#  Here each choice is a square you press.
# ==========================================================================

def _tail(program, lines=1):
    """The last lines of the program, for the strip to show."""
    if not program:
        return ["(nothing built yet)"]
    return ["%d. %s" % (len(program) - len(program[-lines:]) + i + 1, l)
            for i, l in enumerate(program[-lines:])]


def choose(lay, title, items, program=None, back="back"):
    """Draw the choices as squares and wait for one to be pressed."""
    most = lay.cols * lay.rows            # eight
    page = 0
    while True:
        room  = most - 1                  # the last square is always back
        many  = len(items) > room
        per   = room - 1 if many else room
        pages = max(1, (len(items) + per - 1) // per)
        page %= pages
        window = items[page * per:(page + 1) * per]

        wipe()
        head = title if pages == 1 else "%s  (%d/%d)" % (title, page + 1, pages)
        x, y, w, h = lay.strip_box()
        sys.stdout.write(at(x + 1, y) + head[:w - 2])
        for i, line in enumerate(_tail(program, min(2, max(1, h - 1)))):
            if y + 1 + i < y + h:
                sys.stdout.write(at(x + 1, y + 1 + i) + line[:w - 2])

        n = 0
        for label, _v in window:
            n += 1
            Button(n, label).step(_Bag(lay))
        more_at = None
        if many:
            n += 1
            more_at = n
            Button(n, "more").step(_Bag(lay))
        Button(most, back).step(_Bag(lay))
        flush()

        got = press(lay)
        if got is None:
            return None
        if got == most:
            return None
        if more_at and got == more_at:
            page += 1
            continue
        if 1 <= got <= len(window):
            return window[got - 1][1]


class _Bag:
    """The least a block needs to be stepped: somewhere to keep the layout."""
    def __init__(self, lay):
        self.vars = {HOLD: lay}
        self.value = None
        self.world = self.body = None
        self.dt = 0.0


def _pick_block(lay, program, title, without=()):
    from .menu import catalogue
    book = catalogue()
    drop = {w.lower() for w in without}
    while True:
        mod = choose(lay, title, [(m, m) for m in book], program)
        if mod is None:
            return None
        while True:
            kinds = {}
            for k, v in book[mod].items():
                left = [(n, c) for n, c in v if n.lower() not in drop]
                if left:
                    kinds[k] = left
            if not kinds:
                break
            kind = choose(lay, "%s -- what sort?" % mod,
                          [("%s %d" % (k, len(v)), k) for k, v in kinds.items()],
                          program)
            if kind is None:
                break
            got = choose(lay, "%s / %s" % (mod, kind),
                         [(n, (n, c)) for n, c in kinds[kind]], program)
            if got is not None:
                return got


def _settings(lay, name, cls, program):
    """Drop out of the squares to type, because a setting needs typing."""
    from .menu import type_settings
    line = type_settings(name, cls, program)
    return line


def _add(lay, program):
    from .script import HOLDERS, FANWAYS
    got = _pick_block(lay, program, "add a block")
    if got is None:
        return None
    name, cls = got
    low = name.lower()

    if low == "fan":
        how = choose(lay, "fan -- combine them how?",
                     [(w, w) for w in FANWAYS], program)
        return None if how is None else "fan %s" % how

    if low in HOLDERS:
        inner = _pick_block(lay, program,
                            "%s holds which block?" % low, without=HOLDERS)
        if inner is None:
            return None
        iname, icls = inner
        return "%s %s" % (low, _settings(lay, iname, icls, program))

    return _settings(lay, name, cls, program)


def _edit(lay, program):
    while True:
        if not program:
            return
        which = choose(lay, "change which line?",
                       [("%d %s" % (i, l[:14]), i)
                        for i, l in enumerate(program, 1)], program)
        if which is None:
            return
        i = which - 1
        what = choose(lay, "line %d" % which,
                      [("up", "up"), ("down", "down"), ("delete", "delete")],
                      program)
        if what == "up" and i > 0:
            program[i - 1], program[i] = program[i], program[i - 1]
        elif what == "down" and i < len(program) - 1:
            program[i + 1], program[i] = program[i], program[i + 1]
        elif what == "delete":
            program.pop(i)


def _run(lay, program):
    from .core import run as go
    from .script import ScriptError, parse
    wipe()
    sys.stdout.write(at(0, 0))
    flush()
    if not program:
        print("nothing to run")
    else:
        try:
            answer = go(parse("\n".join(program)))
            if isinstance(answer, (list, tuple)):
                print("\n%d item%s" % (len(answer),
                                       "" if len(answer) == 1 else "s"))
            elif answer is not None:
                print("\n%s" % answer)
        except ScriptError as e:
            print("\n%s" % e)
        except Exception as e:
            print("\nit stopped: %s" % e)
    try:
        input("\npress enter ")
    except (EOFError, KeyboardInterrupt):
        pass


def _file(lay, program, saving):
    wipe()
    sys.stdout.write(at(0, 0))
    flush()
    try:
        said = input("file name (blank to stop): ").strip()
    except (EOFError, KeyboardInterrupt):
        return program
    if not said:
        return program
    if not said.endswith(".parts"):
        said += ".parts"
    path = os.path.abspath(os.path.expanduser(said))
    try:
        if saving:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as fh:
                fh.write("\n".join(program) + "\n")
            print("wrote %s" % path)
        else:
            with open(path) as fh:
                program = [l.rstrip() for l in fh if l.strip()]
            print("read %d lines" % len(program))
    except OSError as e:
        print("%s" % e)
    try:
        input("\npress enter ")
    except (EOFError, KeyboardInterrupt):
        pass
    return program


def main(argv=()):
    program = []
    if argv and os.path.exists(os.path.expanduser(argv[0])):
        with open(os.path.expanduser(argv[0])) as fh:
            program = [l.rstrip() for l in fh if l.strip()]

    lay = Layout()
    if not sys.stdin.isatty():
        print("the pad needs a terminal -- run it in Termux itself")
        return 1

    sys.stdout.write("\033[?25l")                  # hide the cursor
    try:
        while True:
            what = choose(lay, "parts -- press a square", [
                ("add a block", "add"),
                ("change lines", "edit"),
                ("run it", "run"),
                ("save", "save"),
                ("open", "open"),
                ("see it all", "list"),
                ("quit", "quit"),
            ], program, back="quit")

            if what in (None, "quit"):
                break
            if what == "add":
                line = _add(lay, program)
                if line:
                    program.append(line)
            elif what == "edit":
                _edit(lay, program)
            elif what == "run":
                _run(lay, program)
            elif what in ("save", "open"):
                program = _file(lay, program, what == "save")
            elif what == "list":
                wipe()
                sys.stdout.write(at(0, 0))
                print("\n".join(program) or "(nothing built yet)")
                try:
                    input("\npress enter ")
                except (EOFError, KeyboardInterrupt):
                    pass
    finally:
        sys.stdout.write("\033[?25h\033[2J\033[H")
        flush()

    if program:
        print("your program:\n")
        print("\n".join(program))
        print("\n(save it next time to keep it)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
