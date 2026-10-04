#!/usr/bin/env python3
"""saves -- your own programs: tagged, found wherever they are, moved only if you say so.

    python3 -m sparkblocks saves            everything of yours, newest first
    python3 -m sparkblocks saves --tidy     offer to gather them in one place
    python3 -m sparkblocks saves --adopt D  take the loose ones out of folder D

THE COMMON STANDARD
-------------------
Every program saved by the menu, the pad or the panel begins with one
line that says what it is:

    # wakeup program · hello · saved 2026-10-04 11:40 MDT · on A33

It is an ordinary `#` comment, so every reader here ignores it and the
program runs exactly the same. But it means a file can be **found by
what it is** rather than by remembering where you put it -- which is
the only thing that works on a phone, where files end up in Downloads
whatever anybody intended.

WHERE IT LOOKS
--------------
Everywhere likely, **most likely first**, and shallowly -- a phone
cannot afford to walk the whole card:

    Downloads            where things actually end up
    ~/.wakeup/programs   the tidy place, if you have used it
    the Termux home
    the project folder   where saving used to land them
    Documents, shared storage, and where you are standing

Everything found is listed **newest first**.

MOVING THEM IS YOUR CHOICE
--------------------------
Nothing is ever moved on its own. `--tidy` shows what it found and
asks. Say no and everything stays exactly where it is -- the tag means
it will still be found next time.
"""

import os
import shutil
import sys
import time

KINDS = (".spark", ".parts")
TAG = "# wakeup program"
DEPTH = 2                      # how far down to look. A phone is slow.
LOOK_AT_MOST = 400             # files per place, so a huge Downloads cannot hang it


# ==========================================================================
#  THE TAG -- the common standard
# ==========================================================================

WHERE_HE_IS = "America/Denver"


def when_of(stamp=None):
    """A time written the way HE reads it, not the way the machine does.

    A cloud container's clock is UTC. Saying a UTC hour on a tag means
    a file saved at tea time looks like it was saved in the evening,
    and the chronology stops matching his memory of it.
    """
    import datetime
    try:
        from zoneinfo import ZoneInfo
        t = (datetime.datetime.fromtimestamp(stamp, ZoneInfo(WHERE_HE_IS))
             if stamp else datetime.datetime.now(ZoneInfo(WHERE_HE_IS)))
        return t.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return (time.strftime("%Y-%m-%d %H:%M", time.localtime(stamp))
                if stamp else time.strftime("%Y-%m-%d %H:%M"))


def when_now():
    return when_of()


def this_machine():
    """The name written on this machine, if it has one. Never a guess."""
    try:
        with open(os.path.join(os.path.expanduser("~"), ".whereami")) as fh:
            for line in fh:
                if line.strip():
                    return line.strip()
    except OSError:
        pass
    return "an unnamed machine"


def tag_line(name):
    return "%s · %s · saved %s · on %s" % (TAG, name, when_now(),
                                           this_machine())


def tagged(text, name):
    """Put the tag on, unless it is already there."""
    body = text if text.endswith("\n") else text + "\n"
    first = body.split("\n", 1)[0]
    if first.startswith(TAG):
        rest = body.split("\n", 1)[1] if "\n" in body else ""
        return tag_line(name) + "\n" + rest
    return tag_line(name) + "\n" + body


def has_tag(path):
    try:
        with open(path, errors="ignore") as fh:
            return fh.readline().startswith(TAG)
    except OSError:
        return False


def read_tag(path):
    """(name, saved, on) off the tag line, or None."""
    try:
        with open(path, errors="ignore") as fh:
            first = fh.readline().strip()
    except OSError:
        return None
    if not first.startswith(TAG):
        return None
    bits = [b.strip() for b in first.split("·")]
    name = bits[1] if len(bits) > 1 else os.path.basename(path)
    saved = bits[2][6:] if len(bits) > 2 and bits[2].startswith("saved") else ""
    on = bits[3][3:] if len(bits) > 3 and bits[3].startswith("on ") else ""
    return name, saved, on


# ==========================================================================
#  WHERE THEY MIGHT BE -- most likely first
# ==========================================================================

def home():
    return os.path.join(os.path.expanduser("~"), ".wakeup")


def folder():
    """The tidy place. Made when first needed, not before."""
    where = os.path.join(home(), "programs")
    try:
        os.makedirs(where, exist_ok=True)
    except OSError:
        return os.getcwd()
    return where


def places():
    """[(folder, why it is likely)], most likely first, only ones that exist."""
    me = os.path.expanduser("~")
    shared = os.path.join(me, "storage", "shared")
    maybe = [
        (os.path.join(shared, "Download"), "Downloads -- where things land"),
        (os.path.join(me, "Downloads"),    "Downloads"),
        (os.path.join(home(), "programs"), "your own folder"),
        (me,                               "the Termux home"),
        (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           "the project folder"),
        (os.path.join(shared, "Documents"), "Documents"),
        (os.path.join(me, "Documents"),    "Documents"),
        (shared,                           "shared storage"),
        (os.getcwd(),                      "where you are standing"),
    ]
    seen, out = set(), []
    for path, why in maybe:
        full = os.path.abspath(path)
        if full in seen or not os.path.isdir(full):
            continue
        seen.add(full)
        out.append((full, why))
    return out


def _under(root, depth):
    """Files under a folder, no deeper than `depth`, and not too many."""
    out = []
    root = root.rstrip(os.sep)
    base = root.count(os.sep)
    skip = {".git", "__pycache__", "node_modules", ".cache", "Android"}
    for here, dirs, names in os.walk(root, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        if here.count(os.sep) - base >= depth:
            dirs[:] = []
        for n in names:
            if n.endswith(KINDS):
                out.append(os.path.join(here, n))
                if len(out) >= LOOK_AT_MOST:
                    return out
    return out


PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_THEIRS = None


def theirs():
    """Files the PROJECT owns. Not yours, and never to be moved.

    The examples that ship here are programs too, and without this
    they would be offered up for tidying -- which would move them out
    of the folder `check` reads and break the thing it checks.

    Asked of git, so it stays right as the project changes. With no
    git, the examples folder is skipped by name, which is the only
    case that has ever mattered.
    """
    global _THEIRS
    if _THEIRS is not None:
        return _THEIRS
    out = set()
    try:
        import subprocess
        got = subprocess.run(["git", "ls-files"], cwd=PROJECT,
                             capture_output=True, text=True, timeout=30)
        if got.returncode == 0:
            for name in got.stdout.split("\n"):
                if name.strip():
                    out.add(os.path.realpath(os.path.join(PROJECT, name)))
    except Exception:
        pass
    if not out:
        examples = os.path.join(PROJECT, "sparkblocks", "examples")
        try:
            for n in os.listdir(examples):
                out.add(os.path.realpath(os.path.join(examples, n)))
        except OSError:
            pass
    _THEIRS = out
    return out


def found():
    """Every program of YOURS anywhere likely. Newest first.

    [(path, when, why that place, tag or None)]

    The project's own files are left out. They are not yours, and
    offering to move them would break the thing that checks them.
    """
    out, seen, mine_not = [], set(), theirs()
    for root, why in places():
        for path in _under(root, DEPTH):
            real = os.path.realpath(path)
            if real in seen or real in mine_not:
                continue
            seen.add(real)
            try:
                when = os.path.getmtime(path)
            except OSError:
                when = 0
            out.append((path, when, why, read_tag(path)))
    out.sort(key=lambda row: row[1], reverse=True)
    return out


# ==========================================================================
#  SAVING AND OPENING
# ==========================================================================

def is_bare(name):
    said = str(name).strip()
    return not (os.sep in said or "/" in said or said.startswith("~")
                or said.startswith("."))


def where(name, for_saving=True):
    """The full path a typed name means.

    A bare name means the tidy folder. Anything with a slash, a dot or
    a ~ is taken exactly as written -- you are allowed to put a file
    wherever you like, and the tag will still find it.
    """
    said = str(name).strip()
    if not said.endswith(KINDS):
        said += ".spark"
    if not is_bare(said):
        return os.path.abspath(os.path.expanduser(said))

    mine = os.path.join(folder(), said)
    if for_saving:
        return mine
    if os.path.exists(mine):
        return mine
    here = os.path.abspath(said)
    if os.path.exists(here):
        return here
    # Last resort: anything with that name, anywhere likely, newest first.
    for path, _when, _why, _tag in found():
        if os.path.basename(path) == said:
            return path
    return mine


def write(path, lines, name=None):
    """Write a program with its tag on. One place does this, so the
    tag cannot be on some saves and not others."""
    body = "\n".join(lines) + "\n" if isinstance(lines, (list, tuple)) \
        else str(lines)
    name = name or os.path.splitext(os.path.basename(path))[0]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        fh.write(tagged(body, name))
    return path


# ==========================================================================
#  MOVING THEM -- only ever when asked
# ==========================================================================

def free_name(into, name):
    stem, ext = os.path.splitext(name)
    out, n = os.path.join(into, name), 2
    while os.path.exists(out):
        out = os.path.join(into, "%s-%d%s" % (stem, n, ext))
        n += 1
    return out


def relocate(paths, into=None):
    """Move these into the tidy folder. Never writes over anything."""
    into = into or folder()
    moved = []
    for path in paths:
        if os.path.dirname(os.path.abspath(path)) == os.path.abspath(into):
            continue
        new = free_name(into, os.path.basename(path))
        try:
            shutil.move(path, new)
            moved.append((path, new))
        except (OSError, shutil.Error):
            pass
    return moved


def adopt(from_dir):
    """Take loose programs out of one folder. Used before an update."""
    try:
        names = sorted(os.listdir(from_dir))
    except OSError:
        return []
    mine_not = theirs()
    loose = [os.path.join(from_dir, n) for n in names
             if n.endswith(KINDS)
             and os.path.isfile(os.path.join(from_dir, n))
             and os.path.realpath(os.path.join(from_dir, n)) not in mine_not]
    return relocate(loose)


# ==========================================================================
#  SAYING IT
# ==========================================================================

def show(rows):
    print("\nwhere it looked, most likely first:")
    for path, why in places():
        print("  %-40s %s" % (_short(path), why))
    print()
    if not rows:
        print("nothing of yours found yet.")
        print()
        print("Build one with `menu` or `pad` and save it. It gets a tag,")
        print("and after that it can be found wherever it ends up.")
        return
    print("%d found, newest first:\n" % len(rows))
    for path, when, why, tag in rows:
        stamp = when_of(when) if when else "?"
        mark = "" if tag else "   (no tag -- saved before this, or by hand)"
        print("  %-22s %-26s %s%s"
              % (stamp, os.path.basename(path), why, mark))
        print("  %-22s %s" % ("", _short(os.path.dirname(path))))


def _short(path):
    me = os.path.expanduser("~")
    return "~" + path[len(me):] if path.startswith(me) else path


def main(argv=()):
    argv = list(argv)

    if "--adopt" in argv:
        i = argv.index("--adopt")
        moved = adopt(argv[i + 1] if i + 1 < len(argv) else os.getcwd())
        if moved:
            print("\nMoved %d of your program%s out of the project folder, so"
                  % (len(moved), "" if len(moved) == 1 else "s"))
            print("updating cannot touch them:\n")
            for old, _new in moved:
                print("  %s" % os.path.basename(old))
            print("\nThey are in %s" % _short(folder()))
        return 0

    rows = found()
    show(rows)

    if "--tidy" not in argv:
        if rows and any(os.path.dirname(os.path.abspath(p)) !=
                        os.path.abspath(folder()) for p, _w, _y, _t in rows):
            print("\nThey are in more than one place. To gather them:")
            print("    python3 -m sparkblocks saves --tidy")
        return 0

    stray = [p for p, _w, _y, _t in rows
             if os.path.dirname(os.path.abspath(p)) != os.path.abspath(folder())]
    if not stray:
        print("\nAll of them are already in %s" % _short(folder()))
        return 0

    print("\nMove these %d into %s?" % (len(stray), _short(folder())))
    for p in stray:
        print("  %s" % _short(p))
    print("\nNothing is moved unless you say yes. Saying no is fine --")
    print("the tag means they will still be found next time.")
    try:
        said = input("\nmove them? (y/n) ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    if not said.startswith("y"):
        print("\nleft where they are.")
        return 0
    moved = relocate(stray)
    print("\nmoved %d." % len(moved))
    for _old, new in moved:
        print("  %s" % _short(new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
