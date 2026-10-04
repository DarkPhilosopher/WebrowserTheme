#!/usr/bin/env python3
"""wizard -- says what it needs before it takes anything.

    python3 wizard.py

A plain terminal screen, on any machine with Python, that tells you
**first**:

    what the smallest working version needs
    what each extra part needs, and what it costs
    what this machine already has

and only then offers to install anything, **one part at a time**.

WHY THIS WAY ROUND
------------------
An installer that tells you the requirements while it is installing
has already decided for you. Declining should be a decision, not an
interruption. So nothing here writes to disk until a number is
pressed, and the first screen is the whole specification.

There is no graphical wizard and there will not be one. The terminal
is the thing that always works -- on a phone, over ssh, on a laptop
that will not boot into anything else. Big-picture modes are reached
from in here, never instead of it.

MINIMUM
-------
Python 3.6 or newer, a terminal, and about 2 MB. No pip, no network,
no 64-bit, no build tools. Everything past that is optional and says
so.
"""

import os
import platform
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"
SLOTS = 8


# ==========================================================================
#  LOOKING AT THIS MACHINE -- reads only, changes nothing
# ==========================================================================

def have(prog):
    return shutil.which(prog) is not None


def on_android():
    return "com.termux" in os.environ.get("PREFIX", "") or \
           os.path.isdir("/data/data/com.termux")


def bits():
    m = platform.machine().lower()
    if m in ("aarch64", "arm64", "x86_64", "amd64"):
        return 64
    if m in ("armv7l", "armv7", "armv8l", "i686", "i386"):
        return 32
    return 0


def this_machine():
    return {
        "python":  "%d.%d.%d" % sys.version_info[:3],
        "ok_py":   sys.version_info >= (3, 6),
        "system":  "Termux on Android" if on_android() else platform.system(),
        "bits":    bits(),
        "git":     have("git"),
        "browser": True,
        "proot":   have("proot-distro"),
        "claude":  have("claude"),
        "space":   free_here(),
    }


def free_here():
    try:
        return shutil.disk_usage(HERE).free
    except Exception:
        return None


def size(n):
    if n is None:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f %s" % (n, unit)
        n /= 1024.0


# ==========================================================================
#  THE PARTS, AND WHAT EACH ONE COSTS
#
#  One row per part. `ready` looks, `fit` says whether this machine
#  could take it at all, and `do` installs it. Nothing else in this
#  file knows what the parts are.
# ==========================================================================

def _ready_blocks(m):
    try:
        subprocess.run([PY, "-c", "import sparkblocks"], cwd=os.path.expanduser("~"),
                       capture_output=True, timeout=60, check=True)
        return True
    except Exception:
        return False


PARTS = [
    {
        "key":  "blocks",
        "name": "the block language",
        "what": "133 blocks, the text format, the numbered menu and the pad",
        "needs": "Python 3.6+. Nothing else",
        "costs": "about 400 KB, no download",
        "fit":  lambda m: m["ok_py"],
        "ready": _ready_blocks,
        "do":   lambda: [[PY, os.path.join(HERE, "sparkblocks", "install.py")]],
        "why":  "makes `import sparkblocks` work from any folder",
    },
    {
        "key":  "panels",
        "name": "the control panels",
        "what": "the plain terminal panel, and the browser one",
        "needs": "Python for the terminal panel. Any browser for the other",
        "costs": "nothing to install -- already here",
        "fit":  lambda m: m["ok_py"],
        "ready": lambda m: os.path.exists(os.path.join(HERE, "panel", "panel.py")),
        "do":   lambda: [],
        "why":  "already present; nothing to do",
    },
    {
        "key":  "claude",
        "name": "Claude Code in the terminal",
        "what": "Ubuntu inside Termux, Node, Claude, and the `claude` word",
        "needs": "Termux on a 64-bit Android phone, and a network",
        "costs": "a few hundred MB, and the slowest step here",
        "fit":  lambda m: m["bits"] == 64,
        "ready": lambda m: m["claude"],
        "do":   lambda: [["sh", os.path.join(HERE, "get-claude.sh")]],
        "why":  "32-bit cannot run it at all -- no build exists",
    },
    {
        "key":  "tools",
        "name": "the small tools",
        "what": "whereami, claude-ready, tfind",
        "needs": "Python. tfind wants Termux",
        "costs": "nothing -- already here",
        "fit":  lambda m: m["ok_py"],
        "ready": lambda m: os.path.exists(os.path.join(HERE, "whereami.py")),
        "do":   lambda: [],
        "why":  "already present; nothing to do",
    },
    {
        "key":  "private",
        "name": "the private container",
        "what": "an empty, ignored folder for material that must not be committed",
        "needs": "nothing",
        "costs": "nothing",
        "fit":  lambda m: True,
        "ready": lambda m: os.path.isdir(os.path.join(HERE, "private")),
        "do":   lambda: [[PY, os.path.join(HERE, "make-private.py")]],
        "why":  "see WITHHELD.md. It is not storage -- read that first",
    },
    {
        "key":  "word",
        "name": "the `wakeup` word",
        "what": "so you type `wakeup` instead of a path",
        "needs": "somewhere on your PATH that you can write to",
        "costs": "one small file",
        "fit":  lambda m: True,
        "ready": lambda m: have("wakeup"),
        "do":   lambda: [["sh", os.path.join(HERE, "get.sh")]],
        "why":  "get.sh writes it and nothing else changes",
    },
]


# ==========================================================================
#  THE FIRST SCREEN -- the whole specification, before anything is taken
# ==========================================================================

def clear():
    # Plain. No colour, no cursor tricks. This has to read on a phone
    # keyboard overlay and over a bad ssh link.
    print("\n" * 2)


def spec(m):
    clear()
    print("=" * 60)
    print(" WAKEUP -- what it needs, before it takes anything")
    print("=" * 60)
    print()
    print(" THE SMALLEST WORKING VERSION")
    print("   Python 3.6 or newer, a terminal, about 2 MB.")
    print("   No pip. No network. No 64-bit. No build tools.")
    print("   Everything below this line is optional.")
    print()
    print("-" * 60)
    print(" THIS MACHINE")
    print("   python       %s%s" % (m["python"],
                                    "" if m["ok_py"] else "   TOO OLD"))
    print("   system       %s" % m["system"])
    print("   width        %s" % ("%d-bit" % m["bits"] if m["bits"]
                                  else "could not tell"))
    print("   git          %s" % ("yes" if m["git"] else "no"))
    print("   free space   %s" % size(m["space"]))
    print("-" * 60)
    print()
    print(" THE PARTS")
    print()
    for part in PARTS:
        fits = part["fit"](m)
        state = ("installed" if part["ready"](m) else
                 ("available" if fits else "CANNOT -- this machine"))
        print("   %-30s %s" % (part["name"], state))
        print("     what   %s" % part["what"])
        print("     needs  %s" % part["needs"])
        print("     costs  %s" % part["costs"])
        if not fits:
            print("     why    %s" % part["why"])
        print()
    print("-" * 60)
    print(" Nothing has been written to disk. Press a number, or 8 to")
    print(" leave with this machine exactly as you found it.")
    print("-" * 60)


# ==========================================================================
#  CHOOSING, ONE AT A TIME
# ==========================================================================

def ask(question):
    try:
        return input(question).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def offer(m):
    """Only what this machine could actually take, and has not got."""
    return [p for p in PARTS if p["fit"](m) and not p["ready"](m)]


def install(part):
    print("\n--- %s ---" % part["name"])
    print("    %s" % part["what"])
    print("    costs %s" % part["costs"])
    steps = part["do"]()
    if not steps:
        print("\n  Nothing to install -- it is already here.")
        ask("\n-- press enter --")
        return True
    print()
    for step in steps:
        print("  $ %s" % " ".join(step))
    if not ask("\ngo ahead? (y/n) ").lower().startswith("y"):
        print("  left alone.")
        ask("\n-- press enter --")
        return False
    for step in steps:
        print()
        if subprocess.call(step, cwd=HERE) != 0:
            print("\n  that step did not work. Nothing after it was tried.")
            ask("\n-- press enter --")
            return False
    print("\n  done.")
    ask("\n-- press enter --")
    return True


def main(argv=()):
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    while True:
        m = this_machine()
        spec(m)

        todo = offer(m)
        if not todo:
            print("\n Everything this machine can take is already here.")
            print(" Type:  wakeup\n")
            return 0

        print()
        shown = todo[:SLOTS - 2]
        for n, part in enumerate(shown, 1):
            print("  %d) install %s" % (n, part["name"]))
        all_n = len(shown) + 1
        print("  %d) all of it, in order" % all_n)
        print("  %d) leave everything alone" % SLOTS)

        got = ask("\n  1-%d: " % SLOTS)
        if not got or got == str(SLOTS):
            print("\n Nothing was changed.\n")
            return 0
        if not got.isdigit():
            continue
        got = int(got)
        if got == all_n:
            for part in shown:
                if not install(part):
                    break
        elif 1 <= got <= len(shown):
            install(shown[got - 1])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
