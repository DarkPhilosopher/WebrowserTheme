#!/usr/bin/env python3
"""whereami -- say which of Gabriel's machines this is, from the files on it.

    python3 whereami.py                     name this machine
    python3 whereami.py --facts             show the signs, matched or not
    python3 whereami.py --all               show the whole register
    python3 whereami.py --name "Revvl 7"    tell this machine what it is

There is more than one Android phone, and two of them can look alike in
every sign a program can read. The only cure is to name each one, once:

    python3 whereami.py --name "Revvl 7"

That writes ~/.whereami, and a written name beats every guess. Renaming
a machine that already has a name needs --force, on purpose.

Claude has no memory between sessions and cannot see your screen. It has
been told, more than once in one conversation, that it was on a machine
it was not on. This file is how a session finds out instead of assuming:
it reads the signs this machine actually carries and matches them
against the register below.

The register is the list in this file. It is meant to be edited by hand
-- add a machine, correct one, delete one. Nothing parses it but Python.

A match is never the end of it. Claude must say which machine it thinks
this is and WAIT for you to agree before doing anything that depends on
the answer. See CLAUDE.md, which says so as a rule.
"""

import os
import platform
import socket
import sys

# ==========================================================================
#  THE REGISTER
#
#  Each machine is a name, a note, and the signs that give it away.
#  A sign is either  ("fact", name, value)   -- must equal this
#                or  ("file", path)          -- this path must exist
#                or  ("nofile", path)        -- this path must NOT exist
#
#  `sure` says whether Gabriel has confirmed the entry. An unconfirmed
#  entry is a guess written down, and Claude must say so when it matches.
# ==========================================================================

REGISTER = [
    {
        "name": "cloud container",
        "note": "Claude Code on the web. Fresh every session, nothing of "
                "yours on it, no reach to any of your own machines.",
        "sure": True,
        "signs": [
            ("fact", "system", "Linux"),
            ("fact", "host", "vm"),
            ("file", "/home/user"),
            ("nofile", "/data/data/com.termux"),
        ],
    },
    {
        "name": "Dell i7 laptop",
        "note": "Modified, bought on Facebook Marketplace. Windows. Two "
                "profiles on the one machine, `sauve` and `xzg4b`. Has an "
                "S: drive as well as C:.",
        "sure": True,
        "signs": [
            ("fact", "system", "Windows"),
            ("anyfact", "user", ("sauve", "xzg4b")),
        ],
    },
    {
        "name": "A33",
        "note": "Samsung Galaxy A33, Android, 64-bit. The phone Gabriel is "
                "usually on. Claude Code runs here, inside proot-distro "
                "ubuntu. Name it with --name A33 so it says so itself.",
        "sure": True,
        "signs": [
            ("file", "/data/data/com.termux"),
            ("fact", "machine", "aarch64"),
        ],
    },
    {
        "name": "A17",
        "note": "Android phone. Gabriel's other one. Not yet run on, so "
                "its architecture is unconfirmed -- run whereami.py there. "
                "Name it with --name A17; the signs alone cannot tell it "
                "from the A33.",
        "sure": False,
        "signs": [
            ("file", "/data/data/com.termux"),
            ("fact", "machine", "aarch64"),
        ],
    },
    {
        "name": "an unnamed Android phone",
        "note": "A phone carrying Termux that has not been named. It is "
                "the A33 or the A17 -- the signs cannot say which. Run "
                "`whereami.py --name` on it and this stops happening.",
        "sure": True,
        "signs": [
            ("file", "/data/data/com.termux"),
        ],
    },
    {
        "name": "a 32-bit phone (Termux)",
        "note": "armv7l. Claude Code CANNOT run here -- the package ships "
                "no 32-bit build, so proot and Ubuntu do not help. "
                "Gabriel's own 32-bit phone was a Hotpepper ACP and he has "
                "DISPOSED OF IT, so this should no longer match anything "
                "of his. Kept because the warning stays true for any "
                "32-bit phone.",
        "sure": True,
        "signs": [
            ("file", "/data/data/com.termux"),
            ("fact", "machine", "armv7l"),
        ],
    },
    {
        "name": "Lenovo tower -- NOT GABRIEL'S",
        "note": "A friend's machine. Would not boot past the recovery "
                "prompt; F12 for the boot menu, F1 for BIOS. REMINDER: "
                "Gabriel asked for this to be taken off the register. It "
                "is listed only so the reminder is not lost. Ask him "
                "before removing it.",
        "sure": True,
        "signs": [
            ("fact", "system", "Windows"),
            ("fact", "chassis", "tower"),
        ],
    },
]


# ==========================================================================
#  THE NAME FILE
#
#  Gabriel has three or more Android phones. Two of them can be the same
#  architecture, carry Termux, and look identical to every sign above --
#  so the signs alone cannot tell them apart, and never will.
#
#  The only thing that can is a name written on the machine itself:
#
#      python3 whereami.py --name "Revvl 7"
#
#  That writes ~/.whereami, and from then on this machine says what it
#  is rather than being guessed at. A name beats every other sign.
# ==========================================================================

NAMEFILE = os.path.join(os.path.expanduser("~"), ".whereami")


def written_name():
    """The name this machine was given, if it was given one."""
    try:
        with open(NAMEFILE) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def write_name(name, force=False):
    """Name this machine. Refuses to rename one without being told twice."""
    already = written_name()
    if already and already != name and not force:
        return False, already
    with open(NAMEFILE, "w") as fh:
        fh.write(name.strip() + "\n")
    return True, already


# ==========================================================================
#  THE SIGNS THIS MACHINE CARRIES
# ==========================================================================

def facts():
    """Everything worth knowing about where we are, gathered cheaply."""
    home = os.path.expanduser("~")
    return {
        "system":  platform.system(),
        "machine": platform.machine(),
        "host":    socket.gethostname(),
        "user":    _user(),
        "home":    home,
        "release": platform.release(),
        "python":  platform.python_version(),
        "termux":  os.path.isdir("/data/data/com.termux"),
        "android": bool(os.environ.get("ANDROID_ROOT")) or
                   os.path.isdir("/system/app"),
        "sdcard":  os.path.isdir("/sdcard") or
                   os.path.isdir(os.path.join(home, "storage", "shared")),
        "chassis": "",          # nothing portable reads this; filled by hand
    }


def _user():
    for key in ("USER", "USERNAME", "LOGNAME"):
        if os.environ.get(key):
            return os.environ[key]
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return ""


def matches(entry, now):
    """How well one register entry fits, and what did not fit.

    Returns (hits, misses). A miss means it is not this machine.
    """
    hits, misses = 0, []
    for sign in entry["signs"]:
        kind = sign[0]
        if kind == "anyfact":
            _, name, wants = sign
            got = str(now.get(name, "")).lower()
            if got in [str(w).lower() for w in wants]:
                hits += 1
            elif got == "":
                pass
            else:
                misses.append("%s is %r, none of %r" % (name, now.get(name), wants))
        elif kind == "fact":
            _, name, want = sign
            if str(now.get(name, "")).lower() == str(want).lower():
                hits += 1
            elif now.get(name, "") == "":
                pass                       # nothing to go on; not a miss
            else:
                misses.append("%s is %r, not %r" % (name, now.get(name), want))
        elif kind == "file":
            if os.path.exists(sign[1]):
                hits += 1
            else:
                misses.append("%s is not there" % sign[1])
        elif kind == "nofile":
            if not os.path.exists(sign[1]):
                hits += 1
            else:
                misses.append("%s is there, and should not be" % sign[1])
    return hits, misses


def identify(now=None):
    """The best match, or None. Returns (entry, hits, total).

    A name written on the machine wins outright -- it is the only sign
    that can tell two identical phones apart.
    """
    now = now or facts()
    named = written_name()
    if named:
        for entry in REGISTER:
            if entry["name"].lower() == named.lower():
                return (entry, len(entry["signs"]), len(entry["signs"]))
        return ({"name": named, "sure": True,
                 "note": "named on the machine itself, in ~/.whereami. "
                         "Not on the register -- add it if it should be.",
                 "signs": []}, 1, 1)
    best = None
    for entry in REGISTER:
        hits, misses = matches(entry, now)
        if misses:
            continue
        if best is None or hits > best[1]:
            best = (entry, hits, len(entry["signs"]))
    return best


# ==========================================================================
#  SAYING SO
# ==========================================================================

def show_facts(now):
    print("the signs this machine carries:")
    for key in ("system", "machine", "release", "host", "user", "home",
                "python", "termux", "android", "sdcard"):
        print("  %-9s %s" % (key, now[key]))


def main(argv):
    now = facts()

    if "--name" in argv:
        i = argv.index("--name")
        if i + 1 >= len(argv):
            print("say what to call it:  whereami.py --name \"Revvl 7\"")
            return 2
        want  = argv[i + 1]
        force = "--force" in argv
        done, already = write_name(want, force)
        if not done:
            print("This machine is already named %r." % already)
            print()
            print("Renaming it to %r would make every earlier note about" % want)
            print("%r point at nothing. If that is what you want:" % already)
            print()
            print('    python3 whereami.py --name "%s" --force' % want)
            return 1
        if already:
            print("Renamed from %r to %r." % (already, want))
        else:
            print("This machine is now %r." % want)
        print("  written to %s" % NAMEFILE)
        if not any(e["name"].lower() == want.lower() for e in REGISTER):
            print()
            print("That name is not on the register in whereami.py.")
            print("Add it there so other machines know what it is.")
        return 0

    if "--all" in argv:
        print("the register (edit whereami.py to change it):\n")
        for e in REGISTER:
            print("  %-26s %s" % (e["name"], "confirmed" if e["sure"]
                                  else "NOT confirmed"))
            print("      %s" % e["note"])
        return 0

    if "--facts" in argv:
        show_facts(now)
        print()

    got = identify(now)
    if got is None:
        print("This machine is not on the register.")
        print()
        show_facts(now)
        print()
        print("Add it to REGISTER in whereami.py, or ask Gabriel which it is.")
        print("Do not guess, and do not carry on as if it were a known one.")
        return 2

    entry, hits, total = got
    named = written_name()
    if named:
        print("This machine says it is: %s" % named)
        print("  (from %s -- a written name, not a guess)" % NAMEFILE)
        print("  %s" % entry["note"])
        print()
        print("Ask Gabriel to confirm before doing anything that depends on it.")
        return 0

    print("This looks like: %s" % entry["name"])
    print("  %s" % entry["note"])
    print("  matched %d of %d signs" % (hits, total))
    if not entry["sure"]:
        print()
        print("  NOT CONFIRMED. This entry was written from what was said in")
        print("  conversation, not from being run here. Ask before relying on it.")
    print()
    print("Ask Gabriel to confirm before doing anything that depends on it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
