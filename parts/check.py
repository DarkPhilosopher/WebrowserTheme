#!/usr/bin/env python3
"""check -- make sure the language still hangs together.

    python3 -m parts check

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
  * and a handful of things actually do what they claim

Each check says what it looked at and what it found. A failure names the
block and the rule, so you know what to change.
"""

import inspect
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import parts as _parts
    from parts import connect as _connect
    from parts.core import Chain, Ctx, Part
else:
    _parts = sys.modules[__package__]
    from . import connect as _connect
    from .core import Chain, Ctx, Part

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
        if not name.endswith(".parts"):
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


CHECKS = [
    ("the one contract",        keeps_the_contract),
    ("names do not clash",      names_do_not_clash),
    ("all blocks reachable",    all_reachable),
    ("all blocks described",    all_described),
    ("the text format knows them", text_format_knows_them),
    ("the examples still parse", examples_parse),
    ("things actually work",    things_actually_work),
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
