#!/usr/bin/env python3
"""check -- make sure the language still hangs together.

    python3 -m sparkblocks check

Run this after changing anything. It is not a test of clever behaviour;
it is a check of the rules the language depends on, the ones that break
quietly:

  * every block keeps the one contract -- a step() you can call
  * no block shadows step() with a setting of the same name
  * no two blocks share a name, because the text format is flat
  * every block in a module's catalogue is reachable from `parts`
  * every block has a sentence saying what it does
  * every block the text format offers can actually be built
  * every example program still parses
  * a handful of things actually do what they claim
  * the awkward cases answer sensibly rather than lying
  * every block says what it needs, in words the holders understand
  * and the panels still describe the blocks that actually exist

That last one is the only check that can catch a block which keeps every
rule perfectly and is still wrong. An empty list handed to First, limits
given the wrong way round, a shut gate feeding the block behind it --
each of those was a real fault, found by trying it rather than by any
rule. New ones belong there.

Each check says what it looked at and what it found. A failure names the
block and the rule, so you know what to change.
"""

import inspect
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import sparkblocks as _parts
    from sparkblocks import connect as _connect
    from sparkblocks.core import Chain, Const, Count, Delay, First, Gain, Gate, Bias, Minus, Invert, Threshold, Clamp, Ctx, Last, Part, Sort
else:
    _parts = sys.modules[__package__]
    from . import connect as _connect
    from .core import (Chain, Const, Count, Delay, First, Gain, Gate, Bias, Minus, Invert, Threshold, Clamp, Ctx, Last, Part, Sort)

HERE = os.path.dirname(os.path.abspath(__file__))


class Report:
    """What every check hands back: what it looked at, and what was wrong."""

    def __init__(self):
        self.checks = 0
        self.faults = []

    def looked(self, n=1):
        self.checks += n

    def fault(self, where, why):
        self.faults.append((where, why))

    @property
    def ok(self):
        return not self.faults


# ==========================================================================
#  WHAT THERE IS TO CHECK
# ==========================================================================

def every_block():
    """[(module, kind, name, class)] for every block in every catalogue."""
    out = []
    for mod, groups in _parts.CATALOGUE.items():
        for kind, group in groups.items():
            for cls in group:
                out.append((mod, kind, cls.__name__, cls))
    for name in ("Words", "Urls", "Shared", "Among"):
        cls = getattr(_connect, name, None)
        if cls is not None:
            out.append(("connect", "compare", name, cls))
    return out


def buildable(cls):
    """Make one with nothing but defaults, if its settings allow it."""
    try:
        sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return None, "has no readable settings"
    need = []
    for name, p in list(sig.parameters.items())[1:]:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is inspect.Parameter.empty:
            need.append(name)
    if need:
        # something is required; hand it a harmless stand-in
        stand_in = {"test": Part(), "part": Part(), "control": Part(),
                    "branches": [Chain([])], "fields": {"a": Part()},
                    "make": (lambda: None), "fn": (lambda v: v),
                    "parts": [], "key": "k", "other": 0, "n": 1,
                    "x": 0, "y": 0, "pattern": "a", "text": "a",
                    "tag": "a", "into": ".", "path": ".", "url": "x",
                    "value": 1, "days": 1}
        try:
            return cls(*[stand_in.get(a, 1) for a in need]), None
        except Exception as e:
            return None, "cannot be built even with stand-ins: %s" % e
    try:
        return cls(), None
    except Exception as e:
        return None, "cannot be built with its own defaults: %s" % e


# ==========================================================================
#  THE CHECKS
# ==========================================================================

def keeps_the_contract(r):
    """Every block must have a step() that can be called."""
    for mod, _kind, name, cls in every_block():
        r.looked()
        if not hasattr(cls, "step"):
            r.fault("%s.%s" % (mod, name), "has no step()")
            continue
        made, why = buildable(cls)
        if made is None:
            r.fault("%s.%s" % (mod, name), why)
            continue
        if not callable(getattr(made, "step", None)):
            r.fault("%s.%s" % (mod, name),
                    "step is not callable on an instance -- a setting of the "
                    "same name is shadowing the method")


def names_do_not_clash(r):
    """The text format looks blocks up by lower-case name, so it is flat."""
    seen = {}
    for mod, _kind, name, cls in every_block():
        r.looked()
        low = name.lower()
        if low in seen and seen[low][1] is not cls:
            r.fault(name, "shares the name %r with %s -- the text format "
                          "cannot tell them apart" % (low, seen[low][0]))
        seen.setdefault(low, ("%s.%s" % (mod, name), cls))


def all_reachable(r):
    """Anything in a catalogue must be importable straight from `parts`."""
    for mod, _kind, name, cls in every_block():
        if mod == "connect":
            continue
        r.looked()
        got = getattr(_parts, name, None)
        if got is None:
            r.fault("%s.%s" % (mod, name),
                    "is in the catalogue but not exported from parts/__init__")
        elif got is not cls:
            r.fault("%s.%s" % (mod, name),
                    "exported from parts/__init__ is a different class")


def all_described(r):
    """Every block needs a sentence, because the menus show it."""
    for mod, _kind, name, cls in every_block():
        r.looked()
        doc = (cls.__doc__ or "").strip()
        if not doc:
            r.fault("%s.%s" % (mod, name), "has no description")
        elif len(doc.split("\n")[0]) < 12:
            r.fault("%s.%s" % (mod, name),
                    "its first line is too short to explain anything")


def text_format_knows_them(r):
    """Everything offered by name in a program must be findable."""
    from .script import _registry
    known = _registry()
    for mod, _kind, name, cls in every_block():
        r.looked()
        if name.lower() not in known:
            r.fault("%s.%s" % (mod, name),
                    "cannot be named in a .parts program")
        elif known[name.lower()] is not cls:
            r.fault("%s.%s" % (mod, name),
                    "the text format resolves its name to a different block")


def examples_parse(r):
    """Every shipped example must still be a valid program."""
    from .script import ScriptError, parse
    folder = os.path.join(HERE, "examples")
    if not os.path.isdir(folder):
        return
    for name in sorted(os.listdir(folder)):
        if not name.endswith((".spark", ".parts")):
            continue
        r.looked()
        try:
            parse(open(os.path.join(folder, name)).read())
        except ScriptError as e:
            r.fault("examples/%s" % name, str(e))
        except Exception as e:
            r.fault("examples/%s" % name, "%s: %s" % (type(e).__name__, e))


def things_actually_work(r):
    """A few real behaviours, so the checks are not only about shape."""
    from .script import parse
    from .core import run
    import tempfile
    import shutil

    tried = []

    # the text format builds what it says
    tried.append(("a chain reads top to bottom",
                  lambda: run(parse("const 6\ngain 7")) == 42))

    # a backslash survives, which shlex would otherwise eat
    tried.append(("a regex keeps its backslash",
                  lambda: parse(r"match \.pdf$").parts[0].pattern == r"\.pdf$"))

    # a number drives a pixel past a threshold, and not before it
    def pixel():
        from .screen import HOLD
        ctx = Ctx()
        parse("screen 4 4\nput hot 0.8\nvar hot\n"
              "light 1 1 at=0.5\nlight 2 2 at=0.9").step(ctx)
        g = ctx.vars[HOLD]
        return g.get(1, 1) == 1 and g.get(2, 2) == 0
    tried.append(("a number lights one pixel and not the other", pixel))

    # spin turns a point, and back again
    def spin():
        out = run(parse("dot 1 0 0\nspin y 90\nspin y -90"))
        x, y, z = out[0]
        return abs(x - 1) < 1e-9 and abs(y) < 1e-9 and abs(z) < 1e-9
    tried.append(("turning a point and back lands where it started", spin))

    # every square of the pad maps back to its own number
    def squares():
        from .pad import Layout
        lay = Layout()
        for n in range(1, lay.cols * lay.rows + 1):
            x, y, w, h = lay.box(n)
            if lay.which(x + w // 2, y + h // 2) != n:
                return False
        return lay.which(0, 0) is None
    tried.append(("every pad square maps back to itself", squares))

    # files: walk, filter by what is inside, and count
    def onfiles():
        folder = tempfile.mkdtemp()
        try:
            open(os.path.join(folder, "a.md"), "w").write("has spark in it")
            open(os.path.join(folder, "b.md"), "w").write("does not")
            got = run(parse("walk %s\nkeep ext .md\nkeep\n"
                            "    read\n    contains spark" % folder))
            return len(got) == 1 and got[0].endswith("a.md")
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    tried.append(("reading inside files to pick them", onfiles))

    # a route that matches everything is not allowed to score
    def routes():
        from .connect import connect
        folder = tempfile.mkdtemp()
        try:
            for name in ("one.md", "two.md", "three.md", "four.md", "five.md"):
                open(os.path.join(folder, name), "w").write("nothing alike")
            open(os.path.join(folder, "one.md"), "w").write("spark and tiles")
            _found, dropped = connect(os.path.join(folder, "one.md"),
                                      folder, explain=True)
            return "kind" in dropped          # every file is .md, so it cannot count
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    tried.append(("a route matching everything stops counting", routes))

    for what, doing in tried:
        r.looked()
        try:
            if not doing():
                r.fault(what, "did not come out right")
        except Exception as e:
            r.fault(what, "%s: %s" % (type(e).__name__, e))


def awkward_cases(r):
    """The things that run fine and answer wrongly.

    Every one of these was a real fault found by trying it, not by any
    rule above. A block can keep the contract perfectly and still lie,
    and this is the only check that notices.
    """
    from .core import Ctx, run

    def gives(what, chain, want):
        r.looked()
        try:
            got = run(chain)
        except Exception as e:
            r.fault(what, "stopped: %s: %s" % (type(e).__name__, e))
            return
        if got != want:
            r.fault(what, "answered %r, expected %r" % (got, want))

    # nothing at all, handed to blocks that expect a list
    gives("First on an empty list", Chain([Const([]), First()]), None)
    gives("Last on an empty list",  Chain([Const([]), Last()]),  None)
    gives("Count on an empty list", Chain([Const([]), Count()]), 0)
    gives("Sort on an empty list",  Chain([Const([]), Sort()]),  [])

    # settings given the wrong way round: do what was meant, do not lie
    gives("Clamp given its limits backwards",
          Chain([Const(5), Clamp(10, 0)]), 5)
    gives("Clamp the right way round still holds",
          Chain([Const(50), Clamp(0, 10)]), 10)

    # sorting by a field that is not there must not stop the program
    gives("Sort by a field nothing has",
          Chain([Const(["b", "a"]), Sort(by="nope")]), ["b", "a"])
    gives("Sort by a field that is there",
          Chain([Const([{"n": 2}, {"n": 1}]), Sort(by="n")]),
          [{"n": 1}, {"n": 2}])

    # a gate that shut, and a delay still filling, hand on nothing --
    # the blocks behind them must survive it
    gives("a shut gate does not break what follows",
          Chain([Const(5), Gate(Const(0)), Gain(2)]), None)
    gives("a delay still filling does not break what follows",
          Chain([Const(5), Delay(2), Gain(2)]), None)

    # ...and the delay must still be a delay
    r.looked()
    chain, ctx, outs = Chain([Const(5), Delay(2), Gain(2)]), Ctx(), []
    for _ in range(4):
        ctx.value = None
        outs.append(chain.step(ctx))
    if outs != [None, None, 10, 10]:
        r.fault("a delay hands on what came two steps ago",
                "gave %r, expected [None, None, 10, 10]" % outs)

    # the plain arithmetic, in case a refactor turns it around
    gives("Gain multiplies",        Chain([Const(6), Gain(7)]), 42)
    gives("Bias adds",              Chain([Const(6), Bias(4)]), 10)
    gives("Minus subtracts",        Chain([Const(6), Minus(4)]), 2)
    gives("Invert flips the sign",  Chain([Const(6), Invert()]), -6)
    gives("Threshold above is above", Chain([Const(9), Threshold(5)]), 1.0)
    gives("Threshold below is below", Chain([Const(1), Threshold(5)]), 0.0)


def every_block_has_a_datasheet(r):
    """A part must say what it needs, so nothing has to guess.

    A valve that will not fit because the port is in the wrong place is
    a fault of the system, not the valve. Nothing that holds blocks
    should ever have to keep its own list of what works where -- the
    block says, and the holder reads.
    """
    from .book import fits_of

    ALLOWED_NEEDS = {"shell", "files", "network", "world", "body",
                     "grid", "terminal", "touch", "person"}
    ALLOWED_CHANGES = {"nothing", "vars", "files", "DELETES", "world",
                       "screen", "network", "anything"}

    for mod, _kind, name, cls in every_block():
        r.looked()
        try:
            fits = fits_of(cls, mod)
        except Exception as e:
            r.fault("%s.%s" % (mod, name), "has no readable datasheet: %s" % e)
            continue
        odd = set(fits["needs"]) - ALLOWED_NEEDS
        if odd:
            r.fault("%s.%s" % (mod, name),
                    "says it needs %s, which is not one of: %s"
                    % (", ".join(sorted(odd)), ", ".join(sorted(ALLOWED_NEEDS))))
        if fits["changes"] not in ALLOWED_CHANGES:
            r.fault("%s.%s" % (mod, name),
                    "says it changes %r, which is not one of: %s"
                    % (fits["changes"], ", ".join(sorted(ALLOWED_CHANGES))))
        if not isinstance(fits["waits"], bool):
            r.fault("%s.%s" % (mod, name), "`waits` is not true or false")


def outside_blocks_fit_too(r):
    """Blocks from somewhere else are held to the same rules.

    This is the point of the whole arrangement: a block you wrote on
    the bus is checked exactly like one that shipped here -- the same
    contract, the same sentence saying what it does, the same
    datasheet. Nothing is let off for being yours.

    With no outside folders this check has nothing to look at and
    passes, which is the usual case and not a problem.
    """
    from .book import fits_of
    from . import outside as _outside

    found, trouble = _outside.load()
    for line in trouble:
        r.looked()
        r.fault("outside", line)

    for low, cls in sorted(found.items()):
        where = "outside.%s" % cls.__name__
        r.looked(4)
        if not callable(getattr(cls, "step", None)):
            r.fault(where, "has no step() -- it is not a block")
            continue
        if "step" in cls.__dict__ and not callable(cls.__dict__["step"]):
            r.fault(where, "stores a setting called `step`, which hides the "
                           "method every block must have. Call it something else")
        if not (cls.__doc__ or "").strip():
            r.fault(where, "has no sentence saying what it does")
        try:
            fits = fits_of(cls, "outside")
        except Exception as e:
            r.fault(where, "has no readable datasheet: %s" % e)
            continue
        if fits["changes"] not in ("nothing", "vars", "files", "DELETES",
                                   "world", "screen", "network", "anything"):
            r.fault(where, "says it changes %r, which is not a word the "
                           "holders know" % fits["changes"])


def the_panels_agree(r):
    """The panels read a catalogue, not the Python. It must still match.

    panel/panel.py reads catalogue.json; panel/panel.html has the same
    JSON baked inside it, because Chrome will not let a file:// page
    fetch its own folder. Both are written by `python3 -m sparkblocks json`,
    and either can be left behind by a change to the blocks.
    """
    import json
    import re
    from .book import book

    live = book()
    root = os.path.dirname(HERE)

    def same_as_live(what, got):
        r.looked()
        if got is None:
            return
        if got.get("count") != live["count"]:
            r.fault(what, "has %s blocks, the language has %s -- rerun "
                          "`python3 -m sparkblocks json`"
                    % (got.get("count"), live["count"]))
            return
        missing = sorted(set(live["blocks"]) - set(got.get("blocks", {})))
        extra   = sorted(set(got.get("blocks", {})) - set(live["blocks"]))
        if missing:
            r.fault(what, "is missing %s" % ", ".join(missing[:6]))
        if extra:
            r.fault(what, "still lists %s, which no longer exist"
                    % ", ".join(extra[:6]))

    path = os.path.join(root, "panel", "catalogue.json")
    if os.path.exists(path):
        try:
            same_as_live("panel/catalogue.json", json.load(open(path)))
        except ValueError as e:
            r.looked()
            r.fault("panel/catalogue.json", "is not readable JSON: %s" % e)

    page = os.path.join(root, "panel", "panel.html")
    if os.path.exists(page):
        text = open(page).read()
        m = re.search(r'<script id="catalogue" type="application/json">'
                      r'(.*?)</script>', text, re.S)
        if not m:
            r.looked()
            r.fault("panel/panel.html", "has no baked catalogue in it")
        else:
            try:
                same_as_live("panel/panel.html (baked)", json.loads(m.group(1)))
            except ValueError as e:
                r.looked()
                r.fault("panel/panel.html", "its baked catalogue is not "
                        "readable JSON: %s" % e)


CHECKS = [
    ("the one contract",        keeps_the_contract),
    ("names do not clash",      names_do_not_clash),
    ("all blocks reachable",    all_reachable),
    ("all blocks described",    all_described),
    ("the text format knows them", text_format_knows_them),
    ("the examples still parse", examples_parse),
    ("things actually work",    things_actually_work),
    ("the awkward cases",       awkward_cases),
    ("every block has a datasheet", every_block_has_a_datasheet),
    ("outside blocks fit too",  outside_blocks_fit_too),
    ("the panels agree",        the_panels_agree),
]


def main(argv=()):
    loud = "--quiet" not in argv
    total, bad = 0, 0

    for title, doing in CHECKS:
        r = Report()
        doing(r)
        total += r.checks
        bad += len(r.faults)
        if loud:
            mark = "ok  " if r.ok else "FAIL"
            print("%s %-28s %3d checked" % (mark, title, r.checks))
        for where, why in r.faults:
            print("       %s: %s" % (where, why))

    print()
    if bad:
        print("%d checked, %d wrong" % (total, bad))
        return 1
    print("%d checked, all well -- %d blocks" % (total, len(_parts.blocks())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
