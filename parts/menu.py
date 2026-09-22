#!/usr/bin/env python3
"""menu -- see and connect the blocks from a phone, with numbers only.

    python3 -m parts menu

Eight options on the screen, never more. The last one always goes back.
Nothing to type but a number, except when a block wants a setting.

What you build here is the same plain text as a .parts file, so you can
save it, open it in any text editor, move the lines around by hand, and
open it here again. The menu and the text are two views of one thing.
"""

import inspect
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import parts as _parts
    from parts import connect as _connect
    from parts.core import run
    from parts.script import HOLDERS, FANWAYS, ScriptError, parse, show
else:
    _parts = sys.modules[__package__]
    from . import connect as _connect
    from .core import run
    from .script import HOLDERS, FANWAYS, ScriptError, parse, show

SLOTS = 8                  # options on screen, counting `back`
CLEAR = "\033[2J\033[H"
WIDE  = 46


# ==========================================================================
#  SCREEN
# ==========================================================================

def rule(ch="="):
    print(ch * WIDE)


def head(title, program=None, note=None):
    print(CLEAR, end="")
    rule()
    print(" " + title[:WIDE - 2])
    rule()
    if program is not None:
        if program:
            print(" your program:")
            for i, line in enumerate(program, 1):
                print("  %2d  %s" % (i, line[:WIDE - 6]))
        else:
            print(" your program is empty")
        rule("-")
    if note:
        print(" " + note[:WIDE - 2])
        rule("-")


def ask(prompt="choose"):
    try:
        return input(" %s: " % prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def pause(note="press enter"):
    try:
        input("\n " + note + " ")
    except (EOFError, KeyboardInterrupt):
        print()


def choose(title, items, program=None, back="back", note=None):
    """Show at most SLOTS options, the last of which always goes back.

    `items` is a list of (label, value). Returns the value, or None for
    back. When the list is too long for one screen, the second-to-last
    slot becomes `more`, so the count on screen never changes.
    """
    page = 0
    while True:
        room = SLOTS - 1                          # one slot is always back
        many = len(items) > room
        per  = room - 1 if many else room         # one more slot for `more`
        pages = max(1, (len(items) + per - 1) // per)
        page %= pages
        window = items[page * per:(page + 1) * per]

        where = "" if pages == 1 else "  (%d of %d)" % (page + 1, pages)
        head(title + where, program, note)

        n = 0
        for label, _value in window:
            n += 1
            print("  %d) %s" % (n, label[:WIDE - 6]))
        more_at = None
        if many:
            n += 1
            more_at = n
            print("  %d) more..." % n)
        print("  %d) %s" % (SLOTS, back))

        said = ask("1-%d" % SLOTS)
        if not said:
            return None
        if not said.isdigit():
            continue
        pick = int(said)
        if pick == SLOTS:
            return None
        if more_at and pick == more_at:
            page += 1
            continue
        if 1 <= pick <= len(window):
            return window[pick - 1][1]


# ==========================================================================
#  WHAT THE BLOCKS ARE
# ==========================================================================

def catalogue():
    """{module: {kind: [(name, class), ...]}}, plus connect's own."""
    out = {}
    for mod, groups in _parts.CATALOGUE.items():
        out[mod] = {k: [(c.__name__, c) for c in g] for k, g in groups.items()}
    out["connect"] = {"compare": [(n, getattr(_connect, n))
                                  for n in ("Words", "Urls", "Shared", "Among")
                                  if hasattr(_connect, n)]}
    return out


def one_line(cls):
    """The first line of a block's own description."""
    doc = (cls.__doc__ or "").strip()
    return doc.split("\n")[0] if doc else "no description"


def settings_of(cls):
    """What the block takes, written the way you would type it."""
    try:
        sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return []
    out = []
    for name, p in list(sig.parameters.items())[1:]:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is inspect.Parameter.empty:
            out.append((name, None, True))
        else:
            out.append((name, p.default, False))
    return out


def explain(name, cls):
    head("%s" % name)
    print(" " + one_line(cls))
    doc = (cls.__doc__ or "").strip().split("\n")[1:]
    for line in doc:
        line = line.strip()
        if line:
            print(" " + line[:WIDE - 2])
    settings = settings_of(cls)
    rule("-")
    if settings:
        print(" settings:")
        for sname, default, needed in settings:
            if needed:
                print("   %-12s (needed)" % sname)
            else:
                print("   %-12s (%s)" % (sname, default))
    else:
        print(" takes no settings")
    pause()


# ==========================================================================
#  BUILDING A LINE
# ==========================================================================

def pick_block(program, title="pick a block", without=()):
    """Walk module -> kind -> block. Returns (name, class) or None.

    `without` drops block names from the lists -- used to keep a holder
    from being offered a holder, which the one-line form cannot express.
    """
    book = catalogue()
    drop = {w.lower() for w in without}
    while True:
        mod = choose(title, [(m, m) for m in book], program)
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
            kind = choose("%s -- what sort?" % mod,
                          [("%s (%d)" % (k, len(v)), k) for k, v in kinds.items()],
                          program)
            if kind is None:
                break
            got = choose("%s / %s" % (mod, kind),
                         [(n, (n, c)) for n, c in kinds[kind]], program,
                         note="pick one to use it")
            if got is not None:
                return got


def type_settings(name, cls, program):
    """Ask for the block's settings, as one line, the same as in a file."""
    low = name.lower()
    settings = settings_of(cls)
    if not settings:
        return low
    head("%s -- settings" % name, program, one_line(cls))
    print(" leave blank to take the usual values")
    print()
    for sname, default, needed in settings:
        print("   %-12s %s" % (sname, "(needed)" if needed else "(%s)" % default))
    print()
    print(" type them in order, spaces between,")
    print(" or name=value. quote anything with a space.")
    said = ask("settings")
    return ("%s %s" % (low, said)).strip() if said else low


def build_line(program):
    """One whole line, including the block a holder holds."""
    got = pick_block(program, "add a block")
    if got is None:
        return None
    name, cls = got
    low = name.lower()

    if low == "fan":
        head("fan", program, "fan needs branches, which the menu cannot draw")
        print(" Add it here as `fan all`, then open the saved")
        print(" file in a text editor and indent the branches")
        print(" underneath it with `- ` in front of each.")
        print()
        how = choose("how should fan combine them?",
                     [(w, w) for w in FANWAYS], program)
        return None if how is None else "fan %s" % how

    if low in HOLDERS:
        # A holder's one setting IS the block it holds, so it is picked,
        # never typed. Holders are kept off that list: `keep drop ...` has
        # nowhere to put the block the inner holder would need, and only
        # the indented form in a text file can say it.
        inner = pick_block(program, "%s -- which block does it hold?" % low,
                           without=HOLDERS)
        if inner is None:
            return None
        iname, icls = inner
        return "%s %s" % (low, type_settings(iname, icls, program))

    return type_settings(name, cls, program)


# ==========================================================================
#  THE PROGRAM
# ==========================================================================

def edit(program):
    while True:
        if not program:
            head("your program", program)
            pause("nothing to edit -- press enter")
            return
        which = choose("edit which line?",
                       [("%2d  %s" % (i, l), i) for i, l in enumerate(program, 1)],
                       program)
        if which is None:
            return
        i = which - 1
        while True:
            what = choose("line %d: %s" % (which, program[i][:24]),
                          [("move it up", "up"),
                           ("move it down", "down"),
                           ("change its settings", "edit"),
                           ("delete it", "delete")],
                          program)
            if what is None:
                break
            if what == "up" and i > 0:
                program[i - 1], program[i] = program[i], program[i - 1]
                i -= 1; which -= 1
            elif what == "down" and i < len(program) - 1:
                program[i + 1], program[i] = program[i], program[i + 1]
                i += 1; which += 1
            elif what == "delete":
                program.pop(i)
                break
            elif what == "edit":
                head("line %d" % which, program, program[i])
                said = ask("new line (blank to keep)")
                if said:
                    program[i] = said
                break


def do_run(program):
    if not program:
        head("run", program)
        pause("nothing to run -- press enter")
        return
    text = "\n".join(program)
    print(CLEAR, end="")
    rule()
    print(" running")
    rule()
    try:
        answer = run(parse(text))
    except ScriptError as e:
        print("\n%s" % e)
        pause()
        return
    except Exception as e:
        print("\n it stopped: %s" % e)
        pause()
        return
    if isinstance(answer, (list, tuple)):
        print("\n %d item%s" % (len(answer), "" if len(answer) == 1 else "s"))
    elif answer is not None:
        print("\n %s" % answer)
    pause()


def do_show(program):
    if not program:
        head("shape", program)
        pause("nothing to show -- press enter")
        return
    print(CLEAR, end="")
    rule()
    print(" the shape it builds")
    rule()
    try:
        show("\n".join(program))
    except ScriptError as e:
        print("\n%s" % e)
    pause()


def do_save(program):
    head("save", program)
    said = ask("file name (blank to stop)")
    if not said:
        return
    if not said.endswith(".parts"):
        said += ".parts"
    path = os.path.abspath(os.path.expanduser(said))
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as fh:
            fh.write("\n".join(program) + "\n")
        head("saved", program)
        print(" wrote %s" % path)
        print()
        print(" open it in any text editor to move the")
        print(" lines around, then load it again here.")
    except OSError as e:
        head("could not save", program)
        print(" %s" % e)
    pause()


def do_open(program):
    head("open", program)
    said = ask("file name (blank to stop)")
    if not said:
        return program
    path = os.path.abspath(os.path.expanduser(said))
    if not os.path.exists(path) and not path.endswith(".parts"):
        path += ".parts"
    try:
        with open(path) as fh:
            lines = [l.rstrip() for l in fh if l.strip()]
    except OSError as e:
        head("could not open", program)
        print(" %s" % e)
        pause()
        return program
    head("opened", lines)
    print(" %d line%s from %s" % (len(lines), "" if len(lines) == 1 else "s",
                                  os.path.basename(path)))
    pause()
    return lines


def do_explain(program):
    got = pick_block(program, "explain which block?")
    if got:
        explain(*got)


# ==========================================================================
#  THE TOP
# ==========================================================================

def main(argv=()):
    program = []
    if argv and os.path.exists(os.path.expanduser(argv[0])):
        with open(os.path.expanduser(argv[0])) as fh:
            program = [l.rstrip() for l in fh if l.strip()]

    while True:
        what = choose("parts -- build with blocks", [
            ("add a block", "add"),
            ("edit the lines", "edit"),
            ("run it", "run"),
            ("see its shape", "shape"),
            ("save to a file", "save"),
            ("open a file", "open"),
            ("explain a block", "explain"),
        ], program, back="quit")

        if what is None:
            print(CLEAR, end="")
            if program:
                print("your program was:\n")
                print("\n".join(program))
                print("\n(save it next time to keep it)")
            return 0
        if what == "add":
            line = build_line(program)
            if line:
                program.append(line)
        elif what == "edit":
            edit(program)
        elif what == "run":
            do_run(program)
        elif what == "shape":
            do_show(program)
        elif what == "save":
            do_save(program)
        elif what == "open":
            program = do_open(program)
        elif what == "explain":
            do_explain(program)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
