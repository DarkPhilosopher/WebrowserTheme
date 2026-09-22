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

from .core import (Abs, Chain, Contains, Each, Field, Gate, Is, Minus, Pack,
                   Part, Threshold, Var, run, _as_list)
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
            "words": {word.lower()}, "urls": set(), "self": None}


def connect(thing, where="~", routes=ROUTES, least=1, limit=40):
    """Return [(score, path, [route names]), ...], best first."""
    facts   = about(thing)
    records = run(Chain([Walk(where), Each(RECORD)]))

    scored = []
    for rec in records:
        if rec["path"] == facts["self"]:
            continue
        hits = []
        for name, _why, chain in routes:
            try:
                if run(chain, rec, **facts):
                    hits.append(name)
            except Exception:
                pass
        if len(hits) >= least:
            scored.append((len(hits), rec["path"], hits))

    scored.sort(key=lambda r: (-r[0], r[1]))
    return scored[:limit]


def report(thing, where="~", least=1, limit=40):
    facts = about(thing)
    kind  = "file" if facts["self"] else "word"
    root  = os.path.abspath(os.path.expanduser(where))
    print("\nconnections to %r (%s), looking under %s\n" % (str(thing), kind, root))

    found = connect(thing, where, least=least, limit=limit)
    if not found:
        print("  nothing connected.")
        print("  routes tried: %s\n" % ", ".join(n for n, _, _ in ROUTES))
        return found

    width = max(len(os.path.basename(p)) for _, p, _ in found)
    for score, path, hits in found:
        print("  %d  %-*s  %s" % (score, width, os.path.basename(path),
                                  " ".join(hits)))
        print("     %s" % (os.path.dirname(path) or "."))
    ways = sorted({h for _, _, hs in found for h in hs})
    print("\n  %d connected, by: %s\n" % (len(found), ", ".join(ways)))
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
