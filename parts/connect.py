#!/usr/bin/env python3
"""connect -- find everything that touches a thing, by every means available.

    python3 -m parts.connect spark                 # a word
    python3 -m parts.connect ~/notes/plan.md       # a file
    python3 -m parts.connect spark /sdcard         # say where to look
    python3 -m parts.connect spark ~ --strict      # only 2+ routes agreeing

Give it a thing. It walks every folder below `where` and asks the same
question of each file along several different routes at once -- name,
contents, backlink, neighbourhood, kind, timing, shared vocabulary,
shared addresses. Every route that answers yes is one point. What comes
back is ranked by how many routes agreed.

THE POINT
---------
Each route is ONE CHAIN in the ROUTES list. Delete a line and that route
stops being consulted. Reorder them and nothing breaks. Write a new one
out of any blocks in the language and it joins the vote -- nothing else
in this file has to know it exists.

The means of connection are data, not code.
"""

import os
import re
import sys

# Run as a module (python3 -m parts.connect) the relative imports below are
# right. Run as a plain file (python3 parts/connect.py) there is no package
# around them, so put this file's parent folder on the path and import by
# name instead. Both ways work, from any folder, with no setup.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from parts.core import (Abs, Chain, Contains, Each, Field, Gate, Is,
                            Minus, Pack, Part, Threshold, Var, run, _as_list)
    from parts.files import Age, Ext, Name, Parent, Read, Size, Walk
else:
    from .core import (Abs, Chain, Contains, Each, Field, Gate, Is, Minus,
                       Pack, Part, Threshold, Var, run, _as_list)
    from .files import Age, Ext, Name, Parent, Read, Size, Walk

# Anything bigger than this is indexed by name only -- never read.
READABLE = 400_000

STOP = set("""
the a an and or but if then than that this these those for from with without
into onto over under about above below out off up down of in on at by to as
is are was were be been being have has had do does did will would can could
shall should may might must not no yes it its you your we our they them
his her he she me my mine ours theirs there here when where which who whom
whose what why how all any both each few more most other some such only own
same so too very just now also like get got new one two three
""".split())


# ==========================================================================
#  THREE BLOCKS THIS SCRIPT ADDS
#
#  Everything else it uses comes straight out of the language. These three
#  are here rather than in core because they are about *this* question --
#  comparing two bags of things.
# ==========================================================================

class Words(Part):
    """The uncommon words in a piece of text, as a set."""
    RX = re.compile(r"[a-z][a-z0-9_'-]{3,}")

    def step(self, ctx):
        found = self.RX.findall(str(ctx.value).lower())
        return {w for w in found if w not in STOP}


class Urls(Part):
    """Every web address and absolute path in a piece of text, as a set."""
    RX = re.compile(r"(?:https?://[^\s\"'<>)]+|/[\w./-]{4,})")

    def step(self, ctx):
        return set(self.RX.findall(str(ctx.value)))


class Shared(Part):
    """True when the signal has `least` items in common with a stashed list."""
    def __init__(self, key, least=1):
        self.key, self.least = key, least

    def step(self, ctx):
        mine  = set(_as_list(ctx.value))
        other = set(_as_list(ctx.vars.get(self.key) or []))
        return len(mine & other) >= self.least


class Among(Part):
    """True when the signal is one of a stashed collection."""
    def __init__(self, key):
        self.key = key

    def step(self, ctx):
        return ctx.value in (ctx.vars.get(self.key) or set())


def cochanged(path, commits=60):
    """Every file that has ever been committed alongside this one.

    Git already knows what belongs together -- two files edited in the
    same commit were, by someone's judgement at the time, one change.
    That is a stronger signal than any amount of guessing from names.
    Returns an empty set outside a repository.
    """
    import subprocess
    folder = os.path.dirname(path) or "."

    def git(*args):
        try:
            out = subprocess.run(("git", "-C", folder) + args,
                                 capture_output=True, text=True, timeout=20)
            return out.stdout.splitlines() if out.returncode == 0 else []
        except Exception:
            return []

    root = git("rev-parse", "--show-toplevel")
    if not root:
        return set()
    root = root[0]

    shas = git("log", "--format=%H", "-n", str(commits), "--", path)
    if not shas:
        return set()

    together = set()
    for sha in shas:
        for name in git("diff-tree", "--no-commit-id", "--name-only",
                        "-r", sha):
            together.add(os.path.join(root, name))
    together.discard(os.path.abspath(path))
    return together


# ==========================================================================
#  WHAT WE LEARN ABOUT EACH FILE
# ==========================================================================

# Read the text only when the file is small enough to be worth reading.
# Gate hands Read a None for anything larger, and Read answers "" to that.
TEXT = Chain([Gate(Chain([Size(), Threshold(READABLE, above=0, below=1)])),
              Read()])

RECORD = Pack({
    "path":   Part(),            # the bare part passes the path straight through
    "name":   Name(),
    "folder": Parent(),
    "ext":    Ext(),
    "age":    Age(),
    "text":   TEXT,
})


# ==========================================================================
#  THE ROUTES -- each one is a chain, and each one is a vote
# ==========================================================================

ROUTES = [

    ("name",
     "its filename carries the word",
     Chain([Field("name"), Contains(Var("word"))])),

    ("mentions",
     "its text says the word",
     Chain([Field("text"), Contains(Var("word"))])),

    ("backlink",
     "its text names the thing's own file",
     Chain([Field("text"), Contains(Var("file"))])),

    ("linked",
     "the thing's text names this file",
     Chain([Field("name"), Contains(Var("source"))])),

    ("sibling",
     "it sits in the same folder",
     Chain([Field("folder"), Is(Var("folder"))])),

    ("kind",
     "it is the same sort of file",
     Chain([Field("ext"), Is(Var("ext"))])),

    ("when",
     "it changed within a day of the thing",
     Chain([Field("age"), Minus(Var("age")), Abs(),
            Threshold(1.0, above=0, below=1)])),

    ("words",
     "it shares uncommon words with the thing",
     Chain([Field("text"), Words(), Shared("words", least=3)])),

    ("addresses",
     "it points at an address the thing also points at",
     Chain([Field("text"), Urls(), Shared("urls")])),

    ("git",
     "it was committed alongside the thing",
     Chain([Field("path"), Among("cochanged")])),
]


# ==========================================================================
#  THE SEARCH
# ==========================================================================

def about(thing):
    """Everything we can learn about the thing being asked about."""
    path = os.path.abspath(os.path.expanduser(str(thing)))
    if os.path.exists(path):
        stem = os.path.splitext(os.path.basename(path))[0]
        text = run(TEXT, path)
        return {
            "word":   stem,
            "file":   os.path.basename(path),
            "source": stem,
            "folder": os.path.dirname(path),
            "ext":    os.path.splitext(path)[1].lower(),
            "age":    run(Age(), path),
            "words":  run(Words(), text),
            "urls":   run(Urls(), text),
            "cochanged": cochanged(path),
            "self":   path,
        }
    # Not a file -- treat it as a plain word. Routes that compare against a
    # file's own folder, kind or age are given values nothing can match, so
    # they never vote. `file` and `source` get the same treatment: for a
    # bare word they would be the very same test as `word`, and a route
    # must not be able to vote twice for one reason.
    word = str(thing)
    return {"word": word, "file": "\0", "source": "\0",
            "folder": "\0", "ext": "\0", "age": -1e9,
            "words": {word.lower()}, "urls": set(), "cochanged": set(),
            "self": None}


def connect(thing, where="~", routes=ROUTES, least=1, limit=40,
            common=0.5, explain=False):
    """Return [(score, path, [route names]), ...], best first.

    A route that says yes to more than `common` of everything it looked at
    is carrying no information -- after a fresh clone `when` matches every
    file on disk, and in a folder of notes `kind` matches every one of
    them. Such a route is still shown, in brackets, but its votes do not
    count toward the score. Set common=1.0 to let every route vote.

    With explain=True, returns (results, {route: hit rate}) for the routes
    that were discounted.
    """
    facts   = about(thing)
    records = run(Chain([Walk(where), Each(RECORD)]))
    records = [r for r in records if r["path"] != facts["self"]]

    # 1. ask every route about every file
    raw = []
    for rec in records:
        hits = []
        for name, _why, chain in routes:
            try:
                if run(chain, rec, **facts):
                    hits.append(name)
            except Exception:
                pass
        raw.append((rec["path"], hits))

    # 2. find the routes that answered yes to nearly everything
    dropped = {}
    if records and len(records) >= 4:
        for name, _why, _chain in routes:
            rate = sum(1 for _, hits in raw if name in hits) / len(records)
            if rate > common:
                dropped[name] = rate

    # 3. score on what is left, but keep the weak hits visible
    scored = []
    for path, hits in raw:
        strong = [h for h in hits if h not in dropped]
        if len(strong) < least:
            continue
        shown = strong + ["(%s)" % h for h in hits if h in dropped]
        scored.append((len(strong), path, shown))

    scored.sort(key=lambda r: (-r[0], r[1]))
    scored = scored[:limit]
    return (scored, dropped) if explain else scored


def report(thing, where="~", least=1, limit=40, common=0.5):
    facts = about(thing)
    kind  = "file" if facts["self"] else "word"
    root  = os.path.abspath(os.path.expanduser(where))
    print("\nconnections to %r (%s), looking under %s\n" % (str(thing), kind, root))

    found, dropped = connect(thing, where, least=least, limit=limit,
                             common=common, explain=True)
    if not found:
        print("  nothing connected.")
        print("  routes tried: %s\n" % ", ".join(n for n, _, _ in ROUTES))
        return found

    width = max(len(os.path.basename(p)) for _, p, _ in found)
    for score, path, hits in found:
        print("  %d  %-*s  %s" % (score, width, os.path.basename(path),
                                  " ".join(hits)))
        print("     %s" % (os.path.dirname(path) or "."))

    ways = sorted({h for _, _, hs in found for h in hs if not h.startswith("(")})
    print("\n  %d connected, by: %s" % (len(found), ", ".join(ways) or "nothing"))
    if dropped:
        print("  not counted (matched nearly everything): %s" %
              ", ".join("%s %d%%" % (n, r * 100)
                        for n, r in sorted(dropped.items())))
    print()
    return found


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("routes:")
        for name, why, _ in ROUTES:
            print("  %-10s %s" % (name, why))
        return 0
    thing = argv[0]
    where = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else "~"
    report(thing, where, least=2 if "--strict" in argv else 1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
