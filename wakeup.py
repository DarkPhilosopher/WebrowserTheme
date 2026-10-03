#!/usr/bin/env python3
"""wakeup -- the front door. Open a terminal, type `wakeup`, pick a number.

    python3 wakeup.py

Everything in this folder can be run on its own. This is the one place
that lists it all, so you never have to remember a command. It follows
the same rule as every other menu here: **eight choices at most, and
the last one always goes back.** When there is more than will fit, the
seventh becomes `more`.

It is deliberately dumb. It starts other programs and gets out of the
way; nothing here does any work of its own, so nothing here can break
the work.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"


# ==========================================================================
#  SAYING THINGS
# ==========================================================================

def line(text=""):
    print(text)


def ask(question):
    """One answer, and ctrl-c or end-of-input counts as going back."""
    try:
        return input(question).strip()
    except (EOFError, KeyboardInterrupt):
        line()
        return ""


def choose(title, choices):
    """Show up to eight, number them, and hand back the one picked.

    `choices` is [(label, what)] and `what` is whatever you want back.
    The last is always the way out, and is added here so no caller can
    forget it.
    """
    page = 0
    many = len(choices) > 7
    while True:
        # Six at a time when there is more than will fit, so that the
        # seventh can be `more` and the eighth can still be `back`.
        shown = choices[page * 6:page * 6 + 6] if many else choices

        line()
        line(title)
        line("-" * len(title))
        for i, (label, _what) in enumerate(shown, 1):
            line("  %d. %s" % (i, label))
        n = len(shown)
        if many:
            n += 1
            line("  %d. more" % n)
        line("  %d. back" % (n + 1))

        got = ask("\npick a number: ")
        if not got:
            return None
        if not got.isdigit():
            line("  a number, please.")
            continue
        got = int(got)
        if got == n + 1:
            return None
        if many and got == n:
            page += 1
            if page * 6 >= len(choices):
                page = 0
            continue
        if 1 <= got <= len(shown):
            return shown[got - 1][1]
        line("  there is no %d." % got)


# ==========================================================================
#  DOING THINGS
# ==========================================================================

def go(*args):
    """Run one of our own programs and wait for it, showing its own output."""
    cmd = [PY] + list(args)
    line()
    # Show the command the way you would type it, so you can run it
    # yourself next time and not need this menu at all.
    line("  $ " + " ".join([os.path.basename(PY)] + cmd[1:]))
    line()
    try:
        subprocess.call(cmd, cwd=HERE)
    except KeyboardInterrupt:
        line("\n  stopped.")
    ask("\n-- press enter --")


def on_android():
    return "com.termux" in os.environ.get("PREFIX", "") or \
           os.path.isdir("/data/data/com.termux")


def programs():
    """Every plain-text program sitting about, nearest first."""
    out = []
    for root in (os.getcwd(), HERE, os.path.join(HERE, "examples")):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if name.endswith((".spark", ".parts")):
                full = os.path.join(root, name)
                if full not in out:
                    out.append(full)
    return out


def run_one():
    found = programs()
    if not found:
        line()
        line("No .spark programs here yet. Make one with the menu or the pad,")
        line("or write one by hand -- one block per line.")
        ask("\n-- press enter --")
        return
    pick = choose("Which program?",
                  [(os.path.basename(p), p) for p in found])
    if pick:
        go("-m", "sparkblocks", "run", pick)


def open_browser_panel():
    page = os.path.join(HERE, "panel", "panel.html")
    line()
    if not os.path.exists(page):
        line("panel/panel.html is not here.")
        ask("\n-- press enter --")
        return

    if on_android():
        # Chrome cannot read Termux's own home folder, so the page has
        # to go somewhere the phone shares. Saying this plainly beats
        # an open that quietly does nothing.
        shared = os.path.expanduser("~/storage/shared/Download")
        if not os.path.isdir(shared):
            line("Shared storage is not set up yet. Run this once, and")
            line("say yes to the permission the phone asks for:")
            line()
            line("    termux-setup-storage")
            ask("\n-- press enter --")
            return
        import shutil
        out = os.path.join(shared, "wakeup-panel.html")
        shutil.copy2(page, out)
        line("Copied the panel to:")
        line("    %s" % out)
        line()
        line("Open your Files app, go to Download, and tap")
        line("wakeup-panel.html. Chrome will ask which app -- pick Chrome.")
        if subprocess.call(["sh", "-c", "command -v termux-open >/dev/null"]) == 0:
            if ask("\ntry opening it from here? (y/n) ").lower().startswith("y"):
                subprocess.call(["termux-open", out])
        ask("\n-- press enter --")
        return

    line("Opening %s" % page)
    try:
        import webbrowser
        webbrowser.open("file://" + page)
    except Exception as e:
        line("Could not: %s" % e)
        line("Double-click the file instead.")
    ask("\n-- press enter --")


def save_to_storage():
    """Put a copy where the phone's own file manager can see it."""
    line()
    if not on_android():
        line("This is for Android only. Everywhere else, the folder is")
        line("already somewhere you can see it:")
        line("    %s" % HERE)
        ask("\n-- press enter --")
        return

    shared = os.path.expanduser("~/storage/shared/Download")
    if not os.path.isdir(shared):
        line("Shared storage is not set up yet. Run this once, and say yes")
        line("to the permission the phone asks for:")
        line()
        line("    termux-setup-storage")
        ask("\n-- press enter --")
        return

    import shutil
    out = os.path.join(shared, "wakeup")
    # The working copy stays in Termux's home. Shared storage cannot
    # keep file permissions, so git misbehaves there -- this copy is
    # for looking at and for sending off the phone, not for working in.
    shutil.copytree(HERE, out, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "*.pyc"))
    line("Copied to:")
    line("    %s" % out)
    line()
    line("That is your Download folder -- the Files app can see it, and")
    line("you can send it to a computer from there. Keep working in the")
    line("Termux copy; shared storage cannot hold file permissions, so")
    line("git goes strange on it.")
    ask("\n-- press enter --")


def update():
    line()
    if not os.path.isdir(os.path.join(HERE, ".git")):
        line("This copy did not come from git, so there is nothing to pull.")
        line("Get a fresh one with:")
        line()
        line("    bash %s/get.sh" % HERE)
        ask("\n-- press enter --")
        return
    line("  $ git pull")
    line()
    subprocess.call(["git", "pull"], cwd=HERE)
    ask("\n-- press enter --")


# ==========================================================================
#  THE MENUS
# ==========================================================================

def more_menu():
    while True:
        pick = choose("More", [
            ("check -- make sure it all still hangs together", "check"),
            ("outside -- blocks from somewhere else", "outside"),
            ("whereami -- which machine is this", "where"),
            ("claude-ready -- can this phone run Claude", "ready"),
            ("connect -- what touches what", "connect"),
            ("save a copy to storage", "save"),
            ("update from github", "update"),
        ])
        if pick is None:
            return
        if pick == "check":
            go("-m", "sparkblocks", "check")
        elif pick == "outside":
            go("-m", "sparkblocks", "outside")
        elif pick == "where":
            go(os.path.join(HERE, "whereami.py"))
        elif pick == "ready":
            go(os.path.join(HERE, "claude-ready.py"))
        elif pick == "connect":
            thing = ask("\nwhat shall I look for? ")
            if thing:
                go("-m", "sparkblocks", "connect", thing)
        elif pick == "save":
            save_to_storage()
        elif pick == "update":
            update()


def main(argv=()):
    argv = list(argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    line()
    line("  wakeup")
    line("  %s" % HERE)

    while True:
        pick = choose("Wakeup", [
            ("blocks -- every block there is", "blocks"),
            ("menu -- build a program with numbers", "menu"),
            ("pad -- build one by pressing squares", "pad"),
            ("panel -- the control panel, in this terminal", "panel"),
            ("panel in Chrome -- buttons and pictures", "browser"),
            ("run a program", "run"),
        ] + [("more", "more")])
        if pick is None:
            line("\n  bye.\n")
            return 0
        if pick == "blocks":
            go("-m", "sparkblocks")
        elif pick == "menu":
            go("-m", "sparkblocks", "menu")
        elif pick == "pad":
            go("-m", "sparkblocks", "pad")
        elif pick == "panel":
            go(os.path.join(HERE, "panel", "panel.py"))
        elif pick == "browser":
            open_browser_panel()
        elif pick == "run":
            run_one()
        elif pick == "more":
            more_menu()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
