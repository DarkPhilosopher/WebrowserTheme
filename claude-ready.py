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
import shlex
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
    half = (not ubuntu) and have("proot-distro") and _ubuntu_half_done()
    out.append({
        "name": "Ubuntu",
        "how": OK if ubuntu else (NO if have("proot-distro") else NA),
        "says": ("installed" if ubuntu else
                 ("here but will not open -- needs resetting" if half
                  else "a few minutes to download")),
        # A half-finished one must be RESET, not installed. Installing
        # over it is refused: "container 'ubuntu' already exists".
        "fix": (None if not have("proot-distro") else
                (["proot-distro", "reset", "ubuntu"] if half
                 else ["proot-distro", "install", "ubuntu"])),
        "doing": ("reset Ubuntu -- the one here is half finished" if half
                  else "install Ubuntu (a few minutes)"),
        "fixtell": (None if not have("proot-distro") else
                    ("An install that stopped part way leaves a container\n"
                     "that exists but cannot be opened. proot-distro refuses\n"
                     "to install over it, so it has to be reset instead."
                     if half else None)),
    })

    node = _node_version() if ubuntu else None
    enough = _node_major(node) >= NEED_NODE
    out.append({
        "name": "Node, in Ubuntu",
        "how": OK if (node and enough) else (NO if ubuntu else NA),
        "says": ((node if enough else
                  "%s -- too old, Claude Code needs v%d" % (node, NEED_NODE))
                 if node else
                 ("not installed" if ubuntu else "needs Ubuntu first")),
        "fix": _NODE_STEPS if ubuntu else None,
        "doing": ("replace Node -- the one here is too old" if node
                  else "install Node inside Ubuntu"),
    })

    claude = _claude_version() if (node and enough) else None
    out.append({
        "name": "Claude Code",
        "how": OK if claude else (NO if node else NA),
        "says": (("%s -- installed. `--deep` asks whether your account"
                  " may actually use it" % claude) if claude else
                 ("not installed" if (node and enough)
                  else "needs Node v%d first" % NEED_NODE)),
        "fix": _CLAUDE_STEPS if (node and enough) else None,
        "doing": "install Claude Code inside Ubuntu",
    })

    out.append({
        "name": "the `claude` word",
        "how": OK if _alias_set() else NO,
        "says": ("the word is here -- it works once the steps above do"
                 if _alias_set() else "not set up yet"),
        "fix": "alias",
        "doing": "make `claude` work straight from Termux",
        "fixtell": "Writes a small `claude` program into Termux's bin, so you\n"
                   "never type the proot line. `claude --continue` works too.",
    })

    return out


# setup_22.x by name, not setup_lts.x. LTS moves, and the day it
# moves to something Claude does not accept, this would break with no
# clue why.
_NODE_STEPS = [
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "apt-get update -y && apt-get install -y curl ca-certificates"],
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -"],
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "apt-get install -y nodejs"],
]

_CLAUDE_STEPS = [
    ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
     "npm install -g @anthropic-ai/claude-code"],
]

# The `claude` word is a SCRIPT, not an alias.
#
# An alias only exists inside an interactive bash. It is missing from
# scripts, from Termux:Widget shortcuts, from `sh -c`, and from the
# very first shell after an install -- all places you would reasonably
# type `claude`. A file in bin is the word itself, everywhere.
#
# /sdcard is bound so Claude can see the phone's own files, and your
# Termux home appears inside as /root/phone.
SHORTCUT = """#!{sh}
# claude -- start Claude Code, which lives inside the proot Ubuntu.
# Written by claude-ready.py. Safe to delete; run that again to restore.
#
# No --bind for /sdcard: proot-distro already binds it, and binding it
# twice warns on every start.
#
# It goes through sh because proot-distro wraps the command in the
# container login shell, and a container whose /usr/bin/bash is
# missing kills every start with execve: No such file or directory.
#
# Arguments are passed positionally, never pasted into a string, so
# spaces and apostrophes survive without any quoting to get wrong.
# TERM has to be carried IN. A login into proot starts with a bare
# environment, and Claude Code draws a full-screen interface -- with
# no terminal type it enters the alternate screen and paints nothing,
# which looks exactly like the program hanging on a black screen.
#
# sh -c, not sh -lc. A login shell also sources the container's
# profile, which can clear the screen before Claude ever draws.
exec proot-distro login \\
  --bind "$HOME:/root/phone" \\
  ubuntu -- sh -c 'export TERM="$1"; if [ -n "$2" ]; then export ANTHROPIC_API_KEY="$2"; fi; shift 2; cd /root/phone 2>/dev/null; exec claude "$@"' \\
  claude "${TERM:-xterm-256color}" "${ANTHROPIC_API_KEY:-}" "$@"
"""

# Nothing writes an alias any more. If an older version of this
# program left one in .bashrc it still works, but it SHADOWS the
# script in interactive bash -- two mechanisms for one word, which is
# the fault this project exists to avoid. So we find it and say so,
# rather than quietly adding a second.
OLD_ALIAS_MARK = "alias claude="


def _version(cmd):
    worked, said = run(cmd)
    return said.split("\n")[0] if worked and said else "not installed"


def _ubuntu_rootfs():
    """Where the Ubuntu folder would be, if there is one."""
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    for root in (os.path.join(prefix, "var", "lib", "proot-distro",
                              "installed-rootfs", "ubuntu"),
                 "/data/data/com.termux/files/usr/var/lib/proot-distro/"
                 "installed-rootfs/ubuntu"):
        if os.path.isdir(root):
            return root
    return None


def _ubuntu_half_done():
    """Is there an Ubuntu that exists but cannot be opened?

    Three states, not two. An install that stopped part way leaves the
    folder behind, so `proot-distro install` refuses with "container
    'ubuntu' already exists" -- while nothing can actually log in. It
    is neither installed nor absent, and treating it as absent walks
    you straight into that refusal.
    """
    return _ubuntu_rootfs() is not None and not _ubuntu_installed()


def _ubuntu_installed():
    """Is there an Ubuntu we can actually log in to?

    This used to read `proot-distro list` and look for the words
    `ubuntu` and `installed`. That is always true, because the list
    prints every distro there is and an uninstalled one says
    **not installed** -- which contains `installed`. So it answered
    yes on a phone with no Ubuntu at all, and every step after it
    failed with `container 'ubuntu' is not installed`.

    Nothing here parses that text any more. It asks the thing itself:
    log in and run `true`. That is the same door every later step goes
    through, so it cannot say yes to a door that will not open.
    """
    if not have("proot-distro"):
        return False

    # Cheap look first, so we do not pay for starting proot when there
    # is plainly nothing there. A rootfs with no /etc is a half-done
    # install, which counts as not installed.
    # The only test that counts: can anything actually log in? The
    # folder existing is not enough -- that is the half-finished case.
    worked, _said = run(["proot-distro", "login", "ubuntu", "--", "true"],
                        timeout=120)
    return worked


# Claude Code's package says engines node >= 22. Read off the npm
# registry, not remembered. Ubuntu's OWN nodejs is 18, which installs
# cleanly and then Claude refuses to start -- so "is node there" is
# not the question. "Is node new enough" is.
NEED_NODE = 22


def _node_version():
    worked, said = in_ubuntu("node --version")
    got = said.strip().split("\n")[0] if worked and said else ""
    return got if got.startswith("v") else None


def _node_major(version):
    try:
        return int(str(version).lstrip("v").split(".")[0])
    except (ValueError, AttributeError):
        return 0


def _node_new_enough():
    return _node_major(_node_version()) >= NEED_NODE


def _claude_version():
    worked, said = in_ubuntu("claude --version")
    if worked and said.strip():
        return said.strip().split("\n")[0]
    return None


def _shortcut_path():
    """Where the `claude` word goes -- Termux's own bin."""
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    return os.path.join(prefix, "bin", "claude")


def _claude_answers():
    """Can Claude actually do anything? Returns (yes, what it said).

    `claude --version` proves a file runs. It does NOT prove the
    account behind it is allowed to use it -- on the A33 everything
    reported ok while every real request came back

        Your organization has disabled Claude subscription access
        for Claude Code

    which is invisible to any check that never asks it to work. This
    is the third time today that "it exists" and "it works" turned
    out to be different questions.

    Not run by default: it costs a request. `--deep` asks for it.
    """
    worked, said = in_ubuntu("claude -p hi 2>&1")
    text = (said or "").strip()
    bad = ("disabled" in text or "api key" in text.lower()
           or "log in" in text.lower() or "unauthor" in text.lower())
    return (worked and bool(text) and not bad), text


def _alias_set():
    """Is `claude` a word you can type, from anywhere?

    Asks the one question that matters -- is there a `claude` on the
    PATH that is ours -- rather than reading .bashrc, which only ever
    described one kind of shell.
    """
    path = _shortcut_path()
    if os.path.isfile(path) and os.access(path, os.X_OK):
        return True
    # Something else may already provide it, if Claude were ever
    # installed in Termux proper. That counts.
    found = shutil.which("claude")
    return bool(found) and found != path


def set_alias():
    """Write the `claude` script, and note the alias as well."""
    path = _shortcut_path()
    sh = shutil.which("sh") or "/bin/sh"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(SHORTCUT.format(sh=sh))
        os.chmod(path, 0o755)
    except OSError as e:
        return False, str(e)

    told = "wrote %s\n  `claude` and `claude --continue` now work anywhere" % path

    gone = _remove_old_alias()
    if gone:
        told += ("\n\n  Took an old  alias claude=...  out of ~/.bashrc."
                 "\n  In bash an alias beats a program on the PATH, so that"
                 "\n  line was shadowing the one just written and `claude`"
                 "\n  kept failing the old way."
                 "\n  The previous file is kept as ~/.bashrc.before-wakeup"
                 "\n\n  This shell still has it loaded. Clear it with:"
                 "\n      unalias claude"
                 "\n  or close Termux and open it again.")
    return True, told


def _remove_old_alias():
    """Take out the alias an older version of this wrote.

    Warning about it was not enough. He is on a phone, and "edit
    ~/.bashrc by hand" is not a fix -- it stayed there, kept winning
    over the script, and every start failed the same old way.

    Only lines that are plainly ours go: an `alias claude=` that
    mentions proot-distro. The file is copied first.
    """
    brc = os.path.join(HOME, ".bashrc")
    try:
        with open(brc) as fh:
            lines = fh.readlines()
    except OSError:
        return False
    keep = [l for l in lines
            if not (l.lstrip().startswith("alias claude=")
                    and "proot-distro" in l)]
    if len(keep) == len(lines):
        return False
    try:
        shutil.copy2(brc, brc + ".before-wakeup")
        with open(brc, "w") as fh:
            fh.writelines(keep)
    except OSError:
        return False
    return True


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
        # Quote it the way a shell needs, so the line shown is a line
        # you can paste. Joining on spaces turned
        #   sh -lc "apt update && apt install -y curl"
        # into something that ran apt install OUTSIDE the container.
        print("\n$ %s" % " ".join(shlex.quote(word) for word in step))
        worked, _ = run(step, quiet=False)
        if not worked:
            print("\nthat step did not work. Nothing after it was tried.")
            return False
    print("\ndone.")
    return True


# ==========================================================================
#  PROVING THE OLD LIE STAYS DEAD
# ==========================================================================

# What `proot-distro list` really prints for a distro you have NOT
# installed. The word "installed" is in there, inside "not installed",
# which is how the old check came to answer yes on a phone with no
# Ubuntu on it.
LIST_WITH_NOTHING_INSTALLED = """
Supported distributions:

  * Ubuntu (24.04)

    Alias: ubuntu
    Status: not installed

  * Alpine Linux (edge)

    Alias: alpine
    Status: not installed
"""


def selftest():
    """Check the things that went wrong before cannot go wrong again."""
    bad = []

    def want(what, got, expected):
        if got != expected:
            bad.append("%s: said %r, should be %r" % (what, got, expected))

    # 1. The lie itself. This is the exact test the old code did.
    said = LIST_WITH_NOTHING_INSTALLED
    old_way = "ubuntu" in said and "installed" in said.lower()
    want("the old text match on a phone with no Ubuntu", old_way, True)
    print("  the old check answered YES to that text -- which is the bug.")

    # 2. Nothing in the program reads that text any more. Look at the
    #    source above this test, so the test cannot pass by describing
    #    itself.
    import re
    body = open(os.path.abspath(__file__)).read().split(
        "#  PROVING THE OLD LIE STAYS DEAD")[0]
    want("nothing runs `proot-distro list` any more",
         bool(re.search(r'["\']list["\']', body)), False)

    # 3. With no proot-distro, there is no Ubuntu. No text involved.
    if not have("proot-distro"):
        want("no proot-distro means no Ubuntu", _ubuntu_installed(), False)
    else:
        print("  (proot-distro is here, so that one was not tried)")

    # 4. Backticks inside an unquoted heredoc get RUN, not printed.
    #    This has bitten three times now: once printing `wakeup: not
    #    found` in the middle of a successful install, once eating a
    #    comment down to "synopsis is .". Anything written into a
    #    file by a heredoc gets checked for them.
    getter = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "get-claude.sh")
    if os.path.exists(getter):
        text = open(getter).read()
        inside = ""
        if "<<WRAPEOF" in text and "\nWRAPEOF" in text:
            inside = text[text.index("<<WRAPEOF"):text.index("\nWRAPEOF")]
        want("no backtick inside the heredoc that writes the claude word",
             "`" in inside, False)

        # Nor in any `say` line. The heredoc was only where it bit
        # FIRST. It then bit again inside a say, printing the output
        # of running `claude` in the middle of a sentence about it.
        loud = [n for n, l in enumerate(text.split("\n"), 1)
                if l.lstrip().startswith("say ") and '"' in l and "`" in l]
        want("no backtick in a double-quoted say line (lines %s)" % loud,
             bool(loud), False)
    else:
        print("  (get-claude.sh is not here, so that one was not tried)")

    # 5. An Ubuntu that exists but will not open must be RESET, never
    #    installed over. proot-distro refuses the install with
    #    "container 'ubuntu' already exists", which on his phone left
    #    the installer stuck in a loop with no way forward.
    if not have("proot-distro"):
        want("no proot-distro means no half-finished Ubuntu either",
             _ubuntu_half_done(), False)
    if os.path.exists(getter):
        text = open(getter).read()
        want("get-claude.sh knows how to reset a half-finished Ubuntu",
             "reset" in text, True)

    # 6. The echoed command must be pasteable -- quoting kept.
    step = ["proot-distro", "login", "ubuntu", "--", "sh", "-lc",
            "apt update && apt install -y curl"]
    shown = " ".join(shlex.quote(w) for w in step)
    want("the shown command keeps its quotes",
         shlex.split(shown) == step, True)

    print()
    if bad:
        for line in bad:
            print("  WRONG  %s" % line)
        print("\n%d wrong." % len(bad))
        return 1
    print("  all well -- the Ubuntu check no longer reads any text,")
    print("  and the commands it shows you can be pasted.")
    return 0


def deep():
    """Ask Claude to actually answer, and print whatever comes back."""
    if not have("proot-distro"):
        print("\nThere is no proot-distro here, so there is no Ubuntu to")
        print("ask. This one is for the phone.\n")
        return 1
    print("\nAsking Claude to answer something, which is the only way")
    print("to find out whether the account may use it at all.\n")
    ok, said = _claude_answers()
    if ok:
        print("  it answered:")
        for line in said.split("\n")[:6]:
            print("    %s" % line)
        print("\nClaude works on this phone.")
        return 0
    print("  it did NOT answer. What it said:\n")
    for line in (said or "(nothing at all)").split("\n")[:10]:
        print("    %s" % line)
    if "disabled" in said or "API key" in said:
        print("""
This is not a fault in anything here. Everything is installed and
runs; the account is refused at the other end.

Two ways on, and both are yours:

  * ask whoever runs your organization to enable Claude Code
  * use an API key from console.anthropic.com, then in Termux:

        export ANTHROPIC_API_KEY=your-key-here
        claude

    Put that export line in ~/.bashrc to keep it. The `claude`
    word carries the key into Ubuntu for you -- the container
    starts with a bare environment, so without that it would
    never arrive.""")
    return 1


def main(argv):
    if "--deep" in argv:
        return deep()
    if "--selftest" in argv:
        print("\nchecking the faults that bit before:\n")
        return selftest()

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
