#!/usr/bin/env python3
"""send -- put a file somewhere else, and remember exactly where.

    python3 send.py              pick a file, pick a place
    python3 send.py --sent       where things went before
    python3 send.py FILE         skip straight to picking a place

THE THREE PLACES
----------------
    github          into a repository you already have a copy of
    Google Drive    the share sheet, or rclone if you set it up
    another machine croc, with a code phrase

WHAT IT REMEMBERS
-----------------
Every send is written into `~/.wakeup/sent.json`: what, where exactly,
and when. So the second time you send the same file it offers **the
same place as last time** as choice one, and you are updating a thing
rather than making another copy of it somewhere you will not find.

IT ALWAYS SAYS WHERE, BEFORE
----------------------------
No send happens until the exact destination has been printed and
agreed to -- `owner/repo @ branch : folder/name`, not "github".
A file you cannot find afterwards has not really been sent.

PRIVATE THINGS
--------------
It asks, before the public routes, and refuses them if the answer is
yes or not sure. See `WITHHELD.md` and `check-withheld.py --ask`.
"""

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"
SLOTS = 8

sys.path.insert(0, HERE)
try:
    from sparkblocks import saves
except Exception:                                   # degrade, never fail
    saves = None


# ==========================================================================
#  SAYING THINGS -- the same eight-choice rule as everywhere else
# ==========================================================================

def line(text=""):
    print(text)


def ask(question):
    try:
        return input(question).strip()
    except (EOFError, KeyboardInterrupt):
        line()
        return ""


def choose(title, choices):
    """Up to six, then `more`, then `back` -- which is always 8."""
    page, many = 0, len(choices) > 7
    while True:
        shown = choices[page * 6:page * 6 + 6] if many else choices
        line()
        line(title)
        line("-" * len(title))
        for i, (label, _what) in enumerate(shown, 1):
            line("  %d. %s" % (i, label))
        if many:
            more_at, back_at = 7, 8
            line("  7. more")
        else:
            more_at, back_at = None, len(shown) + 1
        line("  %d. back" % back_at)

        got = ask("\npick a number: ")
        if not got or not got.isdigit():
            if got:
                line("  a number, please.")
                continue
            return None
        got = int(got)
        if got == back_at:
            return None
        if more_at and got == more_at:
            page = 0 if (page + 1) * 6 >= len(choices) else page + 1
            continue
        if 1 <= got <= len(shown):
            return shown[got - 1][1]
        line("  there is no %d." % got)


def on_android():
    return "com.termux" in os.environ.get("PREFIX", "") or \
           os.path.isdir("/data/data/com.termux")


def short(path):
    me = os.path.expanduser("~")
    return "~" + path[len(me):] if path.startswith(me) else path


def run(cmd, where=None):
    line()
    line("  $ " + " ".join(cmd))
    line()
    try:
        return subprocess.call(cmd, cwd=where) == 0
    except FileNotFoundError:
        line("  there is no `%s` on this machine." % cmd[0])
        return False
    except KeyboardInterrupt:
        line("\n  stopped.")
        return False


# ==========================================================================
#  WHAT WENT WHERE -- so a second send updates instead of duplicating
# ==========================================================================

def book_path():
    folder = os.path.join(os.path.expanduser("~"), ".wakeup")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        return None
    return os.path.join(folder, "sent.json")


def book():
    path = book_path()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def remember(what, how, exactly):
    """Append-only, like every other record here."""
    path = book_path()
    if not path:
        return
    when = saves.when_of() if saves else ""
    whole = book()
    rows = whole.setdefault(os.path.basename(what), [])
    rows.append({"from": what, "how": how, "exactly": exactly, "when": when})
    try:
        with open(path, "w") as fh:
            json.dump(whole, fh, indent=1, sort_keys=True)
    except OSError:
        pass


def went_before(what):
    return book().get(os.path.basename(what), [])


# ==========================================================================
#  CHECKING THE DIRECTORIES -- what is here to send
# ==========================================================================

def pick_file(given=None):
    if given:
        path = os.path.abspath(os.path.expanduser(given))
        return path if os.path.exists(path) else None

    rows = saves.found() if saves else []
    choices = [("%s  (%s)" % (os.path.basename(p), why), p)
               for p, _when, why, _tag in rows[:12]]
    choices.append(("something else -- type a path", "?"))
    got = choose("What shall I send?", choices)
    if got is None:
        return None
    if got != "?":
        return got
    said = ask("\n  path: ")
    if not said:
        return None
    path = os.path.abspath(os.path.expanduser(said))
    if not os.path.exists(path):
        line("\n  There is nothing at %s" % path)
        ask("\n-- press enter --")
        return None
    return path


def repos():
    """Folders on this machine that are git repositories."""
    out = []
    roots = [os.path.expanduser("~"), os.path.dirname(HERE)]
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            names = sorted(os.listdir(root))
        except OSError:
            continue
        for n in names:
            folder = os.path.join(root, n)
            if os.path.isdir(os.path.join(folder, ".git")) and folder not in out:
                out.append(folder)
    return out


def remote_of(folder):
    try:
        got = subprocess.run(["git", "remote", "get-url", "origin"],
                             cwd=folder, capture_output=True, text=True,
                             timeout=20)
        return got.stdout.strip() if got.returncode == 0 else ""
    except Exception:
        return ""


def branch_of(folder):
    try:
        got = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                             cwd=folder, capture_output=True, text=True,
                             timeout=20)
        return got.stdout.strip() if got.returncode == 0 else "?"
    except Exception:
        return "?"


# ==========================================================================
#  THE PRIVATE QUESTION, ASKED BEFORE THE PUBLIC ROUTES
# ==========================================================================

def is_it_private():
    """True means do not take a public route. Not sure counts as yes."""
    line()
    line("Is this private -- anything you would not want read by")
    line("someone who found it?")
    said = ask("\n  (yes / no / not sure) ").lower()
    if said.startswith("n") and "not sure" not in said:
        return False
    line()
    line("Then not by a public route.")
    line()
    line("The questions worth asking first, and a row to file:")
    line("    python3 %s --ask" % os.path.join(HERE, "check-withheld.py"))
    line()
    line("Between your own machines, croc over YOUR OWN relay is the")
    line("one route here that nobody else touches. See CROC.md.")
    ask("\n-- press enter --")
    return True


# ==========================================================================
#  THE THREE PLACES
# ==========================================================================

def to_github(what):
    mine = repos()
    if not mine:
        line()
        line("No git repositories on this machine to put it in.")
        line("Clone one first, then this can copy a file into it.")
        ask("\n-- press enter --")
        return

    folder = choose("Which repository?",
                    [("%s  (%s)" % (os.path.basename(f), branch_of(f)), f)
                     for f in mine])
    if folder is None:
        return

    url, branch = remote_of(folder), branch_of(folder)
    line()
    line("  repository  %s" % (url or "no remote -- it would stay local"))
    line("  branch      %s" % branch)
    line()
    line("  A repository can be PUBLIC. If you are not certain this one")
    line("  is private, treat it as public -- a pushed file stays in the")
    line("  history even after it is deleted.")
    if is_it_private():
        return

    into = ask("\n  folder inside it (blank for the top): ")
    target_dir = os.path.join(folder, into) if into else folder
    target = os.path.join(target_dir, os.path.basename(what))

    line()
    line("EXACTLY WHERE IT WILL GO")
    line("  %s" % target)
    line("  then committed and pushed to %s" % branch)
    if url:
        line("  which is %s" % url)
    if os.path.exists(target):
        line()
        line("  There is already a file there. It will be REPLACED,")
        line("  and the old one stays in the repository's history.")
    if not ask("\ngo ahead? (y/n) ").lower().startswith("y"):
        line("  left alone.")
        ask("\n-- press enter --")
        return

    try:
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(what, target)
    except (OSError, shutil.Error) as e:
        line("\n  could not copy it: %s" % e)
        ask("\n-- press enter --")
        return

    rel = os.path.relpath(target, folder)
    if not run(["git", "add", rel], folder):
        ask("\n-- press enter --")
        return
    if not run(["git", "commit", "-m", "add %s" % os.path.basename(what)], folder):
        line("  nothing to commit -- the file may be unchanged.")
    pushed = run(["git", "push"], folder)

    exactly = "%s @ %s : %s" % (url or short(folder), branch, rel)
    if pushed:
        line("\n  sent. It is at:")
        line("    %s" % exactly)
        remember(what, "github", exactly)
    else:
        # It still went somewhere exact -- into a commit on this
        # machine. Recording only the pushes would lose that, and then
        # "where did this go" would answer nowhere when the answer is
        # "here, waiting to be pushed".
        line("\n  committed here, but it did not push. It is at:")
        line("    %s" % target)
        line("  on branch %s, not yet anywhere else." % branch)
        line("  Push it with:  cd %s && git push" % short(folder))
        remember(what, "github (committed, not pushed)",
                 "%s : %s" % (short(folder), rel))
    ask("\n-- press enter --")


def to_drive(what):
    line()
    if is_it_private():
        return

    if shutil.which("rclone"):
        line("rclone is here. If you have already run `rclone config`")
        line("and made a Drive remote, name it below.")
        line("Blank uses the share sheet instead.")
        remote = ask("\n  remote name (like gdrive): ")
        if remote:
            into = ask("  folder in Drive (blank for the top): ")
            exactly = "%s:%s/%s" % (remote, into or "", os.path.basename(what))
            line()
            line("EXACTLY WHERE IT WILL GO")
            line("  %s" % exactly)
            if not ask("\ngo ahead? (y/n) ").lower().startswith("y"):
                return
            if run(["rclone", "copy", what, "%s:%s" % (remote, into or "")]):
                line("\n  sent to %s" % exactly)
                remember(what, "drive-rclone", exactly)
            ask("\n-- press enter --")
            return

    if not on_android():
        line("No rclone remote, and the share sheet is an Android thing.")
        line()
        line("On a computer, either set rclone up once:")
        line("    rclone config")
        line("or open drive.google.com and drag the file in. It is in:")
        line("    %s" % what)
        ask("\n-- press enter --")
        return

    line("This hands the file to Android, and you pick Drive from the")
    line("list that comes up. Nothing to sign into here -- it uses the")
    line("Drive app you are already signed into.")
    line()
    line("EXACTLY WHERE IT WILL GO")
    line("  wherever you choose in the Drive app. It will ask.")
    line("  The file being handed over is:")
    line("    %s" % what)
    if not ask("\ngo ahead? (y/n) ").lower().startswith("y"):
        return
    if run(["termux-open", "--send", "--chooser", what]):
        line("\n  handed to Android. Pick Drive from the list.")
        remember(what, "drive-sharesheet", "chosen in the Drive app")
    else:
        line("\n  termux-open is missing. It comes with termux-tools:")
        line("    pkg i -y termux-tools")
    ask("\n-- press enter --")


def to_machine(what):
    line()
    if not shutil.which("croc"):
        line("croc is not here. On a phone:")
        line("    pkg i -y croc")
        line("Elsewhere, see CROC.md.")
        ask("\n-- press enter --")
        return
    line("EXACTLY WHERE IT WILL GO")
    line("  to whichever machine types the code croc is about to print.")
    line("  Nowhere else -- the code is one use.")
    line()
    line("  Sending: %s" % what)
    if not ask("\ngo ahead? (y/n) ").lower().startswith("y"):
        return
    run(["croc", "send", what])
    remember(what, "croc", "a machine that typed the code")
    ask("\n-- press enter --")


# ==========================================================================
#  THE MENUS
# ==========================================================================

def show_sent(pause=True):
    """`pause` only when this came from the menu.

    From the command line it is a read-only listing, and pausing
    there means `send.py --sent | head` hangs forever waiting for a
    keypress that is not coming.
    """
    whole = book()
    line()
    if not whole:
        line("Nothing has been sent from this machine yet.")
        line()
        line("Once something has, this says where it went, so the next")
        line("send can update the same place instead of making another")
        line("copy somewhere you will not find.")
        ask("\n-- press enter --")
        return
    for name in sorted(whole):
        line("\n  %s" % name)
        for row in whole[name]:
            line("    %-18s %s" % (row.get("when", "?"), row.get("exactly", "?")))
            line("    %-18s by %s" % ("", row.get("how", "?")))
    if pause:
        ask("\n-- press enter --")


def send_one(what):
    before = went_before(what)
    choices = []
    if before:
        last = before[-1]
        choices.append(("same place as last time -- %s" % last["exactly"],
                        "again:" + last["how"]))
    choices += [
        ("github -- into a repository you have here", "github"),
        ("Google Drive", "drive"),
        ("another of your machines -- croc", "croc"),
    ]
    while True:
        got = choose("Send %s where?" % os.path.basename(what), choices)
        if got is None:
            return
        if got.startswith("again:"):
            got = got.split(":", 1)[1]
            got = {"drive-rclone": "drive", "drive-sharesheet": "drive"}.get(got, got)
        if got == "github":
            to_github(what)
        elif got == "drive":
            to_drive(what)
        elif got == "croc":
            to_machine(what)


def main(argv=()):
    argv = list(argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    if "--sent" in argv:
        show_sent(pause=False)
        return 0

    given = argv[0] if argv and not argv[0].startswith("-") else None
    line()
    line("  send -- a file, somewhere else, and it says exactly where")

    while True:
        what = pick_file(given)
        given = None
        if what is None:
            line("\n  bye.\n")
            return 0
        line("\n  %s" % what)
        send_one(what)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
