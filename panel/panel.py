#!/usr/bin/env python3
"""panel -- the plain control panel. Works anywhere a prompt does.

    python3 panel.py

This is the one that always works. It uses nothing but `print` and
`input`: no colours, no cursor moving, no mouse, no curses, no termios.
That is the point -- Windows `cmd.exe`, PowerShell, Termux, a serial
console, a pipe. Where the pad and the coloured menus will not run,
this will.

It reads `catalogue.json` next to it, so it knows every block even when
the Python package cannot be imported at all. If `parts` IS importable
it can also run what you build; if not, it still builds and saves the
program for you to run somewhere that can.

Eight choices at most, the last one always back. Same rule everywhere.
"""

import json
import os
import subprocess
import sys

HERE  = os.path.dirname(os.path.abspath(__file__))
SLOTS = 8
WIDE  = 64


# ==========================================================================
#  WHAT WE CAN REACH FROM HERE
# ==========================================================================

def load_book():
    """The catalogue: from the JSON beside us, or from Python, or nothing."""
    path = os.path.join(HERE, "catalogue.json")
    try:
        with open(path) as fh:
            return json.load(fh), "catalogue.json"
    except (OSError, ValueError):
        pass
    try:
        sys.path.insert(0, os.path.dirname(HERE))
        from parts.book import book
        return book(), "the parts package"
    except Exception:
        return None, None


def have_parts():
    """Can we actually run a program here, or only write one?"""
    try:
        sys.path.insert(0, os.path.dirname(HERE))
        import parts                                   # noqa: F401
        return True
    except Exception:
        return False


def where_we_are():
    if os.name == "nt":
        return "Windows"
    if os.path.isdir("/data/data/com.termux"):
        return "Termux"
    return sys.platform


# ==========================================================================
#  THE SCREEN -- print and input, nothing else
# ==========================================================================

def clear():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        print("\n" * 40)


def rule(ch="="):
    print(ch * WIDE)


def head(title, program=None, note=None):
    clear()
    rule()
    print(" " + title)
    rule()
    if program is not None:
        if program:
            for i, line in enumerate(program, 1):
                print("  %2d  %s" % (i, line))
        else:
            print("  (nothing built yet)")
        rule("-")
    if note:
        for line in fold(note, WIDE - 2):
            print(" " + line)
        rule("-")


def fold(text, room):
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


def ask(prompt):
    try:
        return input(" %s: " % prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def pause():
    try:
        input("\n press enter ")
    except (EOFError, KeyboardInterrupt):
        print()


def choose(title, items, program=None, back="back", note=None):
    """Eight at most, the last always back. More than fits becomes `more`."""
    page = 0
    while True:
        room  = SLOTS - 1
        many  = len(items) > room
        per   = room - 1 if many else room
        pages = max(1, (len(items) + per - 1) // per)
        page %= pages
        window = items[page * per:(page + 1) * per]

        head(title if pages == 1 else "%s  (%d of %d)" % (title, page + 1, pages),
             program, note)
        n = 0
        for label, _v in window:
            n += 1
            print("  %d) %s" % (n, label))
        more_at = None
        if many:
            n += 1
            more_at = n
            print("  %d) more..." % n)
        print("  %d) %s" % (SLOTS, back))

        said = ask("1-%d" % SLOTS)
        if not said or not said.isdigit():
            return None
        pick = int(said)
        if pick == SLOTS:
            return None
        if more_at and pick == more_at:
            page += 1
            continue
        if 1 <= pick <= len(window):
            return window[pick - 1][1]


# ==========================================================================
#  BUILDING A PROGRAM
# ==========================================================================

def pick_block(book, program, title, without=()):
    """module -> kind -> block. Returns the block's record, or None."""
    drop = {w.lower() for w in without}
    while True:
        mods = sorted(book["modules"])
        mod = choose(title, [(m, m) for m in mods], program)
        if mod is None:
            return None
        while True:
            kinds = {}
            for kind, names in book["modules"][mod].items():
                left = [n for n in names if n not in drop]
                if left:
                    kinds[kind] = left
            if not kinds:
                break
            kind = choose("%s -- what sort?" % mod,
                          [("%s (%d)" % (k, len(v)), k)
                           for k, v in sorted(kinds.items())], program)
            if kind is None:
                break
            got = choose("%s / %s" % (mod, kind),
                         [(book["blocks"][n]["name"], n)
                          for n in kinds[kind]], program,
                         note="pick one to use it")
            if got is not None:
                return book["blocks"][got]


def type_settings(block, program):
    """Ask for the settings, as one line, exactly as in a .parts file."""
    low = block["name"].lower()
    if not block["settings"]:
        return low
    head("%s -- settings" % block["name"], program, block["says"])
    for s in block["settings"]:
        print("   %-12s %s" % (s["name"],
                               "(needed)" if s["needed"]
                               else "(%s)" % s["default"]))
    print()
    print(" Type them in order, spaces between, or name=value.")
    print(" Quote anything with a space in it. Blank takes the usual values.")
    said = ask("settings")
    return ("%s %s" % (low, said)).strip() if said else low


def add_line(book, program):
    block = pick_block(book, program, "add a block")
    if block is None:
        return None
    low = block["name"].lower()

    if low == "fan":
        how = choose("fan -- combine the branches how?",
                     [(w, w) for w in book["fanways"]], program,
                     note="Add it as `fan all`, then indent its `- ` "
                          "branches underneath in a text editor.")
        return None if how is None else "fan %s" % how

    if block["holds"]:
        inner = pick_block(book, program, "%s holds which block?" % low,
                           without=book["holders"])
        if inner is None:
            return None
        return "%s %s" % (low, type_settings(inner, program))

    return type_settings(block, program)


def edit(program):
    while True:
        if not program:
            return
        which = choose("change which line?",
                       [("%d  %s" % (i, l), i)
                        for i, l in enumerate(program, 1)], program)
        if which is None:
            return
        i = which - 1
        what = choose("line %d" % which,
                      [("move it up", "up"), ("move it down", "down"),
                       ("retype it", "retype"), ("delete it", "delete")],
                      program)
        if what == "up" and i > 0:
            program[i - 1], program[i] = program[i], program[i - 1]
        elif what == "down" and i < len(program) - 1:
            program[i + 1], program[i] = program[i], program[i + 1]
        elif what == "delete":
            program.pop(i)
        elif what == "retype":
            head("line %d" % which, program, program[i])
            said = ask("new line (blank to keep)")
            if said:
                program[i] = said


# ==========================================================================
#  DOING THINGS WITH IT
# ==========================================================================

def save(program):
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
        print("\n wrote %s" % path)
        print("\n Open it in any text editor to move the lines around.")
    except OSError as e:
        print("\n could not save: %s" % e)
    pause()


def open_file(program):
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
        print("\n read %d lines" % len(lines))
        pause()
        return lines
    except OSError as e:
        print("\n could not open: %s" % e)
        pause()
        return program


def run_it(program, runnable):
    head("run", program)
    if not program:
        print(" nothing to run")
        pause()
        return
    if not runnable:
        print(" This machine cannot run it -- the parts package is not")
        print(" importable from here. Save it and run it somewhere that")
        print(" has Python with parts installed:")
        print()
        print("     python3 -m parts run yourfile.parts")
        pause()
        return
    print()
    try:
        from parts.core import run
        from parts.script import ScriptError, parse
        answer = run(parse("\n".join(program)))
        if isinstance(answer, (list, tuple)):
            print("\n %d item%s" % (len(answer), "" if len(answer) == 1 else "s"))
        elif answer is not None:
            print("\n %s" % answer)
    except ScriptError as e:
        print("\n%s" % e)
    except Exception as e:
        print("\n it stopped: %s: %s" % (type(e).__name__, e))
    pause()


def open_browser(program):
    """Hand the program to the browser panel, which draws things."""
    page = os.path.join(HERE, "panel.html")
    head("the browser panel", program)
    if not os.path.exists(page):
        print(" panel.html is not next to this file.")
        pause()
        return
    try:
        with open(os.path.join(HERE, "handover.json"), "w") as fh:
            json.dump({"program": program}, fh, indent=1)
    except OSError:
        pass
    print(" Opening %s" % page)
    print()
    print(" If it does not open by itself, open that file in Chrome.")
    opened = False
    try:
        import webbrowser
        opened = webbrowser.open("file://" + page)
    except Exception:
        pass
    if not opened and os.path.isdir("/data/data/com.termux"):
        # Termux: hand it to Android to open
        try:
            subprocess.run(["termux-open", page], timeout=20)
            opened = True
        except Exception:
            pass
    if not opened:
        print(" Could not open it for you. Open it by hand.")
    pause()


def show_block(book, program):
    block = pick_block(book, program, "explain which block?")
    if not block:
        return
    head(block["name"], None, block["says"])
    if block["more"]:
        for line in block["more"].split("\n"):
            print(" " + line)
        print()
    if block["settings"]:
        print(" settings:")
        for s in block["settings"]:
            print("   %-12s %s" % (s["name"], "(needed)" if s["needed"]
                                   else "(%s)" % s["default"]))
    else:
        print(" takes no settings")
    pause()


# ==========================================================================
#  THE TOP
# ==========================================================================

def main(argv):
    book, source = load_book()
    if book is None:
        print("Cannot find the blocks.")
        print("Expected catalogue.json next to this file, or the parts")
        print("package importable from the folder above it.")
        return 1

    runnable = have_parts()
    program  = []
    if argv and os.path.exists(os.path.expanduser(argv[0])):
        with open(os.path.expanduser(argv[0])) as fh:
            program = [l.rstrip() for l in fh if l.strip()]

    note = "%s, %d blocks, read from %s. %s" % (
        where_we_are(), book["count"], source,
        "Can run programs." if runnable
        else "Cannot run programs here -- build and save, run elsewhere.")

    while True:
        what = choose("Wakeup -- control panel", [
            ("add a block", "add"),
            ("change the lines", "edit"),
            ("run it", "run"),
            ("save to a file", "save"),
            ("open a file", "open"),
            ("explain a block", "explain"),
            ("open the browser panel", "browser"),
        ], program, back="quit", note=note)

        if what is None:
            clear()
            if program:
                print("your program:\n")
                print("\n".join(program))
                print("\n(save it next time to keep it)")
            return 0
        if what == "add":
            line = add_line(book, program)
            if line:
                program.append(line)
        elif what == "edit":
            edit(program)
        elif what == "run":
            run_it(program, runnable)
        elif what == "save":
            save(program)
        elif what == "open":
            program = open_file(program)
        elif what == "explain":
            show_block(book, program)
        elif what == "browser":
            open_browser(program)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
