#!/usr/bin/env python3
"""claude-ready -- is this phone ready to run Claude in Termux, and if not, why.

    python3 claude-ready.py            look, then offer to fix what is missing
    python3 claude-ready.py --check    look and say, fix nothing

It checks everything Claude Code needs on an Android phone, in order,
and tells you which step you are actually stuck on. Where something is
missing it offers to install it -- pick a number, nothing to type.

It will also tell you plainly when a phone CANNOT run Claude Code at
all, rather than walking you through an install that was never going to
work. That happens on 32-bit phones, and no amount of proot fixes it.

Nothing but Python's own library. Works on a bare Termux.
"""

import os
import platform
import shutil
import subprocess
import sys

SLOTS = 8                      # options on screen, counting the last one
HOME  = os.path.expanduser("~")


def width():
    """However wide the Termux window is, within reason."""
    try:
        return max(38, min(72, os.get_terminal_size().columns))
    except OSError:
        return 46

OK, NO, NA = "ok", "--", "n/a"


# ==========================================================================
#  RUNNING THINGS
# ==========================================================================

def run(cmd, quiet=True, timeout=1800):
    """Run a command. Returns (worked, what it said)."""
    try:
        out = subprocess.run(cmd, shell=isinstance(cmd, str),
                             capture_output=quiet, text=True, timeout=timeout)
        said = ((out.stdout or "") + (out.stderr or "")).strip() if quiet else ""
        return out.returncode == 0, said
    except subprocess.TimeoutExpired:
        return False, "it took too long and was stopped"
    except Exception as e:
        return False, str(e)


def in_ubuntu(cmd):
    """Run a command inside the proot Ubuntu, if there is one."""
    return run(["proot-distro", "login", "ubuntu", "--", "sh", "-lc", cmd],
               timeout=120)


def have(prog):
    return shutil.which(prog) is not None


# ==========================================================================
#  THE CHECKS
#
#  Each one answers: what is it called, how is it, what does it say, and
#  how would you fix it. A fix of None means there is nothing to do --
#  either it is fine, or it is impossible.
# ==========================================================================

def arch():
    m = platform.machine().lower()
    if m in ("aarch64", "arm64"):
        return "64-bit", True
    if m.startswith("arm") or m in ("armv7l", "armv8l", "i686", "x86"):
        return m + " (32-bit)", False
    return m, True              # x86_64 and anything else: assume it can


def look():
    """Everything, in the order you would hit it. Returns a list of checks."""
    out = []
    kind, can_run = arch()

    out.append({
        "name": "Termux",
        "how": OK if os.path.isdir("/data/data/com.termux") else NO,
        "says": "the app itself",
        "fix": None,
        "fixtell": "Install Termux from F-Droid, not the Play Store.",
    })

    out.append({
        "name": "Python",
        "how": OK,
        "says": platform.python_version(),
        "fix": None,
    })

    out.append({
        "name": "this phone",
        "how": OK if can_run else NO,
        "says": kind + (" -- Claude Code can run" if can_run
                        else " -- Claude Code CANNOT run here"),
        "fix": None,
        "fixtell": None if can_run else (
            "No 32-bit build of Claude Code exists -- the package ships\n"
            "binaries for 64-bit only, so proot and Ubuntu do not help.\n"
            "Everything else below still works, and so do the Spark\n"
            "blocks. Use claude.ai in the browser on this phone."),
    })

    out.append({
        "name": "storage access",
        "how": OK if os.path.isdir(os.path.join(HOME, "storage")) else NO,
        "says": "lets Termux see Downloads, DCIM and Documents",
        "fix": ["termux-setup-storage"],
        "doing": "grant storage access",
        "fixtell": "A permission box will appear -- tap Allow.",
    })

    out.append({
        "name": "git",
        "how": OK if have("git") else NO,
        "says": _version("git --version") if have("git") else "not installed",
        "fix": ["pkg", "install", "git", "-y"],
    })

    out.append({
        "name": "curl",
        "how": OK if have("curl") else NO,
        "says": "needed to fetch the Node installer",
        "fix": ["pkg", "install", "curl", "-y"],
    })

    if not can_run:
        # Nothing below this line can lead anywhere on a 32-bit phone,
        # so do not pretend otherwise by listing it.
        return out

    out.append({
        "name": "proot-distro",
        "how": OK if have("proot-distro") else NO,
        "says": "runs a small Ubuntu inside Termux",
        "fix": ["pkg", "install", "proot-distro", "-y"],
        "fixtell": "Claude Code needs glibc, which Android does not have.\n"
                   "A proot Ubuntu provides it.",
    })

    ubuntu = have("proot-distro") and _ubuntu_installed()
    out.append({
        "name": "Ubuntu",
        "how": OK if ubuntu else (NO if have("proot-distro") else NA),
        "says": "installed" if ubuntu else "a few minutes to download",
        "fix": ["proot-distro", "install", "ubuntu"] if have("proot-distro") else None,
        "doing": "install Ubuntu (a few minutes)",
        "fixtell": None if have("proot-distro") else "needs proot-distro first",
    })

    node = _node_version() if ubuntu else None
    out.append({
        "name": "Node, in Ubuntu",
        "how": OK if node else (NO if ubuntu else NA),
        "says": node or ("not installed" if ubuntu else "needs Ubuntu first"),
        "fix": _NODE_STEPS if ubuntu else None,
        "doing": "install Node inside Ubuntu",
    })

    claude = _claude_version() if node else None
    out.append({
        "name": "Claude Code",
        "how": OK if claude else (NO if node else NA),
        "says": claude or ("not installed" if node else "needs Node first"),
        "fix": _CLAUDE_STEPS if node else None,
        "doing": "install Claude Code inside Ubuntu",
    })

    out.append({
        "name": "the `claude` word",
        "how": OK if _alias_set() else NO,
        "says": "so `claude` works straight from Termux"
                if _alias_set() else "not set up yet",
        "fix": "alias",
        "doing": "make `claude` work straight from Termux",
        "fixtell": "Adds one line to ~/.bashrc so you need not log in by hand.",
    })

    return out


_NODE_STEPS = [
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "apt update && apt install -y curl"],
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -"],
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "apt install -y nodejs"],
]

_CLAUDE_STEPS = [
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "npm install -g @anthropic-ai/claude-code"],
]

ALIAS = ("alias claude='proot-distro login ubuntu "
         "--bind /storage/emulated/0:/sdcard -- claude'")


def _version(cmd):
    worked, said = run(cmd)
    return said.split("\n")[0] if worked and said else "not installed"


def _ubuntu_installed():
    for root in ("/data/data/com.termux/files/usr/var/lib/proot-distro/"
                 "installed-rootfs/ubuntu",
                 os.path.join(HOME, "../usr/var/lib/proot-distro/"
                              "installed-rootfs/ubuntu")):
        if os.path.isdir(root):
            return True
    worked, said = run(["proot-distro", "list"])
    return worked and "ubuntu" in said and "installed" in said.lower()


def _node_version():
    worked, said = in_ubuntu("node --version")
    return said.strip() if worked and said.strip().startswith("v") else None


def _claude_version():
    worked, said = in_ubuntu("claude --version")
    if worked and said.strip():
        return said.strip().split("\n")[0]
    return None


def _alias_set():
    try:
        with open(os.path.join(HOME, ".bashrc")) as fh:
            return "alias claude=" in fh.read()
    except OSError:
        return False


def set_alias():
    path = os.path.join(HOME, ".bashrc")
    try:
        with open(path, "a") as fh:
            fh.write("\n" + ALIAS + "\n")
        return True, "added to %s -- reopen Termux, or run: source ~/.bashrc" % path
    except OSError as e:
        return False, str(e)


# ==========================================================================
#  SAYING IT
# ==========================================================================

def show(checks):
    w = width()
    room = w - 25                       # what is left for the detail
    print("\n" + "=" * w)
    print(" Claude in Termux -- what you have")
    print("=" * w)
    for c in checks:
        says = c["says"]
        if len(says) <= room:
            print("  %-4s %-17s %s" % (c["how"], c["name"], says))
        else:
            # too long for the line -- put it underneath rather than cut it
            print("  %-4s %s" % (c["how"], c["name"]))
            for line in _fold(says, w - 8):
                print("        %s" % line)
    print("=" * w)

    stuck = [c for c in checks if c["how"] == NO]
    if not stuck:
        print(" Everything is here. Type:  claude")
        return []

    first = stuck[0]
    print(" First thing missing: %s" % first["name"])
    if first.get("fixtell"):
        for line in first["fixtell"].split("\n"):
            print("   %s" % line)
    return stuck


def _fold(text, room):
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


def fixable(stuck):
    return [c for c in stuck if c.get("fix")]


def menu(todo):
    """At most eight: six to fix, one to do them all, and quit last."""
    room = SLOTS - 2
    window = todo[:room]
    print()
    for i, c in enumerate(window, 1):
        print("  %d) %s" % (i, c.get("doing") or ("install " + c["name"])))
    print("  %d) do all of it, in order" % (SLOTS - 1))
    print("  %d) quit" % SLOTS)
    try:
        said = input("\n 1-%d: " % SLOTS).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not said.isdigit():
        return None
    n = int(said)
    if n == SLOTS:
        return None
    if n == SLOTS - 1:
        return todo
    if 1 <= n <= len(window):
        return [window[n - 1]]
    return None


def do(check):
    print("\n--- %s ---" % check["name"])
    if check.get("fixtell"):
        print(check["fixtell"])
    fix = check["fix"]

    if fix == "alias":
        worked, said = set_alias()
        print(("done. " if worked else "could not: ") + said)
        return worked

    steps = fix if isinstance(fix[0], list) else [fix]
    for step in steps:
        print("\n$ %s" % " ".join(step))
        worked, _ = run(step, quiet=False)
        if not worked:
            print("\nthat step did not work. Nothing after it was tried.")
            return False
    print("\ndone.")
    return True


def main(argv):
    checks = look()

    if "--check" in argv:
        show(checks)
        return 0 if not [c for c in checks if c["how"] == NO] else 1

    while True:
        checks = look()
        stuck = show(checks)
        if not stuck:
            return 0
        todo = fixable(stuck)
        if not todo:
            print("\n Nothing here can be fixed by installing something.")
            return 1
        picked = menu(todo)
        if picked is None:
            print()
            return 0
        for c in picked:
            if not do(c):
                break
        try:
            input("\npress enter to look again ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
