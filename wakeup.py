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
import shutil
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

        # `more` and `back` keep the SAME numbers on every page, even
        # a short last page. They used to shuffle up when a page had
        # fewer items, so on the last page `back` was 3 instead of 8 --
        # which undoes the one thing the eight-choice rule is for.
        if many:
            more_at, back_at = 7, 8
            line("  %d. more" % more_at)
        else:
            more_at, back_at = None, len(shown) + 1
        line("  %d. back" % back_at)

        got = ask("\npick a number: ")
        if not got:
            return None
        if not got.isdigit():
            line("  a number, please.")
            continue
        got = int(got)
        if got == back_at:
            return None
        if more_at and got == more_at:
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


def go_cmd(cmd, wait=True):
    """Run any command, letting it own the screen. For things that are
    not our own Python -- `claude`, `sh get-claude.sh`."""
    line()
    line("  $ " + " ".join(cmd))
    line()
    try:
        code = subprocess.call(cmd, cwd=HERE)
    except FileNotFoundError:
        line("  there is no `%s` on this machine yet." % cmd[0])
        code = 127
    except KeyboardInterrupt:
        line("\n  stopped.")
        code = 130
    if wait:
        ask("\n-- press enter --")
    return code


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
#  CLAUDE IN THE TERMINAL
#
#  One number, and it sorts itself out: look first, offer to fix what
#  is missing, then start. He should never have to know which of the
#  five things in the chain is the one that is not there.
# ==========================================================================

READY = os.path.join(HERE, "claude-ready.py")
GETTER = os.path.join(HERE, "get-claude.sh")


def claude_state():
    """(ready, what it said). Looks, says nothing, changes nothing."""
    try:
        out = subprocess.run([PY, READY, "--check"], cwd=HERE,
                             capture_output=True, text=True, timeout=300)
        return out.returncode == 0, (out.stdout or out.stderr)
    except Exception as e:
        return False, "could not look: %s" % e


def tried_path():
    folder = os.path.join(os.path.expanduser("~"), ".wakeup")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        return None
    return os.path.join(folder, "tried.json")


def tried():
    """What has been attempted, so the hard options can be EARNED.

    Suggesting "remove it all and start again" to somebody who has
    not yet tried the gentle thing is how people lose work they did
    not need to lose.
    """
    path = tried_path()
    if not path or not os.path.exists(path):
        return []
    try:
        import json
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return []


def note_try(what, worked):
    path = tried_path()
    if not path:
        return
    try:
        import json
        rows = tried()
        rows.append({"what": what, "worked": bool(worked),
                     "when": _when()})
        with open(path, "w") as fh:
            json.dump(rows[-20:], fh, indent=1)
    except Exception:
        pass


def _when():
    try:
        sys.path.insert(0, HERE)
        from sparkblocks.saves import when_of
        return when_of()
    except Exception:
        import time
        return time.strftime("%Y-%m-%d %H:%M")


def failed_fixes():
    return [r for r in tried() if r.get("what") == "fix" and not r.get("worked")]


def claude_fix():
    """Install whatever is missing, before and after Claude itself."""
    line()
    if not os.path.exists(GETTER):
        line("get-claude.sh is not here. Pull the latest:")
        line("    cd %s && git pull" % HERE)
        ask("\n-- press enter --")
        return False

    line("This installs whatever is missing, in order, and skips")
    line("anything already done. The Ubuntu step is a few hundred")
    line("megabytes and is the slow one -- leave it running.")
    line()
    if not ask("go ahead? (y/n) ").lower().startswith("y"):
        return False
    worked = go_cmd(["sh", GETTER]) == 0
    note_try("fix", worked)
    if not worked:
        line()
        line("That did not finish. Run it again first -- everything")
        line("already done is skipped, so a second go often gets past")
        line("whatever it was.")
        line()
        line("If it keeps stopping in the same place, `start over` is")
        line("the next thing, and it is choice 5.")
        ask("\n-- press enter --")
    return worked


def claude_start(carry_on=False):
    """Start it, after making sure it can start."""
    cmd = ["claude", "--continue"] if carry_on else ["claude"]

    # Off Android there is no proot and no Termux, and claude-ready
    # would tell a Windows laptop to install Termux from F-Droid --
    # which is the kind of useless advice he will actually try.
    if not on_android():
        if shutil.which("claude"):
            go_cmd(cmd)
            return
        line()
        line("Claude is not on this machine, and this is not a phone,")
        line("so none of the proot business applies. Here it installs")
        line("the ordinary way:")
        line()
        line("    npm install -g @anthropic-ai/claude-code")
        line()
        line("Node.js first, from nodejs.org.")
        ask("\n-- press enter --")
        return

    ready, said = claude_state()
    if not ready:
        line()
        line(said.strip())
        line()
        line("Claude cannot start until the above is sorted.")
        if ask("fix it now? (y/n) ").lower().startswith("y"):
            claude_fix()
            ready, said = claude_state()
            if not ready:
                line("\nStill not ready. What it says now:")
                line(said.strip())
                ask("\n-- press enter --")
                return
        else:
            return

    go_cmd(cmd)


def claude_replace():
    """The last rung: throw the Ubuntu away and fetch a clean one.

    Offered, never taken on its own, and it says plainly when the
    gentler thing has not been tried yet. It costs the whole download
    again, so reaching for it first is just a slower way to arrive at
    the same place.
    """
    line()
    if not on_android():
        line("This is about the Ubuntu inside Termux, and there is no")
        line("Termux here. Nothing to replace.")
        ask("\n-- press enter --")
        return

    gone_wrong = failed_fixes()
    line("START OVER -- the last rung")
    line()
    line("  1. update     reuse what is here, fetch only what is not")
    line("  2. install    add what is missing            <- choice 4")
    line("  3. replace    remove the Ubuntu, fetch a clean one")
    line()
    if not gone_wrong:
        line("You have not had `fix what is missing` fail yet.")
        line()
        line("Try choice 4 first. It skips everything already done, so")
        line("running it twice costs almost nothing -- and replacing")
        line("costs the whole few hundred megabytes again.")
        if not ask("\ngo to start over anyway? (y/n) ").lower().startswith("y"):
            return
    else:
        last = gone_wrong[-1]
        line("`fix` has failed %d time%s here, last at %s."
             % (len(gone_wrong), "" if len(gone_wrong) == 1 else "s",
                last.get("when", "?")))
        line("So this is a fair thing to reach for now.")

    line()
    line("It throws away the Ubuntu and everything inside it.")
    line("It does NOT touch your saved programs, the wakeup folder,")
    line("or anything on the phone outside Termux.")
    line()
    line("It will ask you to type a word before doing anything.")
    if not ask("\ncarry on? (y/n) ").lower().startswith("y"):
        return
    worked = go_cmd(["sh", GETTER, "--replace"]) == 0
    note_try("replace", worked)


def claude_menu():
    while True:
        pick = choose("Claude in the terminal", [
            ("start it", "start"),
            ("carry on the last conversation", "continue"),
            ("check what is missing", "check"),
            ("fix what is missing", "fix"),
            ("start over -- replace the Ubuntu (last resort)", "replace"),
        ])
        if pick is None:
            return
        if pick == "start":
            claude_start()
        elif pick == "continue":
            claude_start(carry_on=True)
        elif pick == "check":
            go(READY, "--check")
        elif pick == "fix":
            claude_fix()
        elif pick == "replace":
            claude_replace()


# ==========================================================================
#  SENDING A FILE TO ANOTHER OF HIS MACHINES
#
#  croc does the work. This only checks it is there, offers to put it
#  there, and types the line for him -- see CROC.md.
# ==========================================================================

def croc_there():
    return shutil.which("croc") is not None


def croc_get():
    line()
    if on_android():
        line("croc is an official Termux package, so this is all it takes.")
        cmd = ["pkg", "i", "-y", "croc"]
    elif os.name == "nt":
        line("Try whichever of winget, scoop or choco you have:")
        line("    winget install schollz.croc")
        line("    scoop install croc")
        line("    choco install croc")
        line()
        line("Or take the .exe from github.com/schollz/croc/releases")
        ask("\n-- press enter --")
        return False
    else:
        line("croc is not here, and I will not guess how your machine")
        line("installs things. See github.com/schollz/croc")
        ask("\n-- press enter --")
        return False

    if not ask("install croc? (y/n) ").lower().startswith("y"):
        return False
    return go_cmd(cmd) == 0


def croc_send():
    line()
    if not croc_there() and not croc_get():
        return
    line("What shall I send? A file or a folder.")
    line("Blank to stop. Your saved programs are in ~/.wakeup/programs")
    what = ask("\n  > ")
    if not what:
        return
    path = os.path.abspath(os.path.expanduser(what))
    if not os.path.exists(path):
        line("\n  There is nothing at %s" % path)
        ask("\n-- press enter --")
        return
    line()
    line("croc will print a code phrase and then wait.")
    line("On the other machine, type:  croc THAT-CODE")
    line()
    line("Stop it with ctrl-c if you change your mind.")
    go_cmd(["croc", "send", path])


def croc_get_file():
    line()
    if not croc_there() and not croc_get():
        return
    line("The code phrase from the machine that is sending.")
    line("Three words with a number, like 1234-fairy-tiger-saddle.")
    code = ask("\n  > ")
    if not code:
        return
    line()
    line("It will arrive in %s" % os.getcwd())
    go_cmd(["croc", code])


# ==========================================================================
#  THE MENUS
# ==========================================================================

def more_menu():
    while True:
        pick = choose("More", [
            ("check -- make sure it all still hangs together", "check"),
            ("send -- a file to github, Drive or another machine", "send"),
            ("receive a file, with its code", "receive"),
            ("saves -- your own programs, wherever they are", "saves"),
            ("outside -- blocks from somewhere else", "outside"),
            ("whereami -- which machine is this", "where"),
            ("claude-ready -- can this phone run Claude", "ready"),
            ("connect -- what touches what", "connect"),
            ("withheld -- what is deliberately not here", "withheld"),
            ("panel in Chrome -- buttons and pictures", "browser"),
            ("wizard -- what this needs, and install it a part at a time", "wizard"),
            ("save a copy to storage", "save"),
            ("update from github", "update"),
        ])
        if pick is None:
            return
        if pick == "check":
            go("-m", "sparkblocks", "check")
        elif pick == "send":
            go(os.path.join(HERE, "send.py"))
        elif pick == "receive":
            croc_get_file()
        elif pick == "saves":
            go("-m", "sparkblocks", "saves")
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
        elif pick == "withheld":
            go(os.path.join(HERE, "check-withheld.py"))
        elif pick == "browser":
            open_browser_panel()
        elif pick == "wizard":
            go(os.path.join(HERE, "wizard.py"))
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
            ("claude -- check, fix, and start it", "claude"),
            ("blocks -- every block there is", "blocks"),
            ("menu -- build a program with numbers", "menu"),
            ("pad -- build one by pressing squares", "pad"),
            ("panel -- the control panel, in this terminal", "panel"),
            ("run a program", "run"),
        ] + [("more", "more")])
        if pick is None:
            line("\n  bye.\n")
            return 0
        if pick == "claude":
            claude_menu()
        elif pick == "blocks":
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
