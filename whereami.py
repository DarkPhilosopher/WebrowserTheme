#!/usr/bin/env python3
"""whereami -- say which of Gabriel's machines this is, from the files on it.

    python3 whereami.py              name this machine
    python3 whereami.py --facts      show the raw signs, matched or not
    python3 whereami.py --all        show every machine on the register

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
        "name": "Dell laptop (Windows)",
        "note": "Windows user `sauve`. Has an S: drive as well as C:. "
                "Claude Desktop was downloaded to its Downloads folder.",
        "sure": False,
        "signs": [
            ("fact", "system", "Windows"),
            ("fact", "user", "sauve"),
        ],
    },
    {
        "name": "Windows machine of user xzg4b",
        "note": "Seen once, in a path. May be the Dell under another "
                "profile, or a different machine entirely -- unresolved.",
        "sure": False,
        "signs": [
            ("fact", "system", "Windows"),
            ("fact", "user", "xzg4b"),
        ],
    },
    {
        "name": "Lenovo tower",
        "note": "A desktop, not a laptop. Would not boot past the recovery "
                "command prompt. F12 for the boot menu, F1 for BIOS.",
        "sure": False,
        "signs": [
            ("fact", "system", "Windows"),
            ("fact", "chassis", "tower"),
        ],
    },
    {
        "name": "phone, 64-bit (Termux)",
        "note": "An aarch64 Android phone. Claude Code can run here, "
                "through proot-distro ubuntu -- not in Termux directly.",
        "sure": False,
        "signs": [
            ("file", "/data/data/com.termux"),
            ("fact", "machine", "aarch64"),
        ],
    },
    {
        "name": "phone, 32-bit (Termux)",
        "note": "armv7l. Claude Code CANNOT run here at all -- the package "
                "ships no 32-bit build, so proot and Ubuntu do not help. "
                "Python, git and the parts language all work fine.",
        "sure": True,
        "signs": [
            ("file", "/data/data/com.termux"),
            ("fact", "machine", "armv7l"),
        ],
    },
]


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
        if kind == "fact":
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
    """The best match, or None. Returns (entry, hits, total)."""
    now = now or facts()
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
