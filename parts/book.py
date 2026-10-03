#!/usr/bin/env python3
"""book -- write the whole language out as JSON, for other panels to read.

    python3 -m parts json > panel/catalogue.json

There are three ways into this project and they must never disagree
about what the blocks are:

    the terminal panel      panel/panel.py     Windows, Termux, anywhere
    the browser panel       panel/panel.html   Chrome, no server
    Python itself           import parts

Two of those cannot import Python modules, so the truth is written out
here in a form anything can read. One file, one source, and `python3 -m
parts check` makes sure it still matches the blocks it came from.
"""

import inspect
import json
import sys


def settings_of(cls):
    """What a block takes, in the order you would type it."""
    try:
        sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return []
    out = []
    for name, p in list(sig.parameters.items())[1:]:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        needed = p.default is inspect.Parameter.empty
        default = None if needed else p.default
        if default is not None and not isinstance(
                default, (str, int, float, bool, list, dict)):
            default = str(default)
        out.append({"name": name, "needed": needed, "default": default})
    return out


def one_line(cls):
    doc = (cls.__doc__ or "").strip()
    return doc.split("\n")[0] if doc else ""


def whole_doc(cls):
    doc = (cls.__doc__ or "").strip()
    return "\n".join(line.strip() for line in doc.split("\n")[1:]).strip()


def book():
    """The whole language, as plain data."""
    from . import CATALOGUE, blocks
    from . import connect as _connect
    from .script import FANWAYS, HOLDERS

    out = {
        "what": "Claude WakUp -- the parts language",
        "blocks": {},
        "modules": {},
        "holders": sorted(HOLDERS),
        "fanways": list(FANWAYS),
        "count": 0,
    }

    def add(mod, kind, cls):
        name = cls.__name__
        out["blocks"][name.lower()] = {
            "name": name,
            "module": mod,
            "kind": kind,
            "says": one_line(cls),
            "more": whole_doc(cls),
            "holds": name.lower() in HOLDERS,
            "settings": settings_of(cls),
        }
        out["modules"].setdefault(mod, {}).setdefault(kind, []).append(
            name.lower())

    for mod, groups in CATALOGUE.items():
        for kind, group in groups.items():
            for cls in group:
                add(mod, kind, cls)
    for name in ("Words", "Urls", "Shared", "Among"):
        cls = getattr(_connect, name, None)
        if cls is not None:
            add("connect", "compare", cls)

    out["count"] = len(out["blocks"])
    return out


OPEN  = '<script id="catalogue" type="application/json">'
SHUT  = "</scr" + "ipt>"


def into_html(path, text):
    """Replace the baked catalogue inside panel.html.

    The browser panel is opened as a file, and Chrome will not let a
    file:// page fetch its own folder -- so the catalogue has to live
    inside the page. This is the only thing that writes it.
    """
    with open(path) as fh:
        page = fh.read()
    start = page.find(OPEN)
    if start < 0:
        return False, "no catalogue block in %s" % path
    from_ = start + len(OPEN)
    to    = page.find(SHUT, from_)
    if to < 0:
        return False, "the catalogue block in %s is not closed" % path
    with open(path, "w") as fh:
        fh.write(page[:from_] + "\n" + text + "\n" + page[to:])
    return True, None


def main(argv=()):
    argv = list(argv)
    text = json.dumps(book(), indent=1, sort_keys=True)
    count = book()["count"]

    if "--html" in argv:
        argv.remove("--html")
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        page = argv[0] if argv else os.path.join(here, "panel", "panel.html")
        done, why = into_html(page, text)
        print(("baked into %s -- %d blocks" % (page, count)) if done
              else ("could not: %s" % why))
        return 0 if done else 1

    if argv and not argv[0].startswith("-"):
        with open(argv[0], "w") as fh:
            fh.write(text + "\n")
        print("wrote %s -- %d blocks" % (argv[0], count))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
