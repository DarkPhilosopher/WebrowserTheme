#!/usr/bin/env python3
"""outside -- blocks that did not come with this folder.

    python3 -m sparkblocks outside        what is loaded, and from where

A block from somewhere else -- yours, a friend's, one you wrote on the
bus -- should work exactly like one that shipped here. Same menus, same
`.spark` files, same panels, same checks. Nothing should have to know
where it came from.

That is the whole of the rule this project keeps: a part fails for what
it IS, never for where it was plugged in. A block written by someone
else is not plugged in anywhere different.

WHERE THEY COME FROM
--------------------
Three places, searched in this order:

    ~/.sparkblocks/              your own, on this machine
    $SPARKBLOCKS_PATH            folders you name, separated by :
    ./sparkblocks-extra/         beside whatever you are running

Any `.py` file in one of those is read, and every `Part` in it joins the
language. **Creating the folder is the consent.** Nothing is searched
that you did not make on purpose, and nothing is downloaded, ever.

WRITING ONE
-----------
A file with a block in it, and nothing else required:

    from sparkblocks import Part

    class Shout(Part):
        '''Make the text loud and excited.'''
        fits = {"changes": "nothing"}
        def step(self, ctx):
            return str(ctx.value).upper() + "!"

Drop it in `~/.sparkblocks/mine.py` and `shout` is a block:

    const "hello"
    shout
    say

NAMES
-----
Two blocks cannot share a name -- the text format looks them up by one.
An outside block taking a name this folder already uses is **refused,
loudly, and told what to call it instead**. It is never silently
shadowed, because then a program would do something different depending
on which machine it ran on, which is exactly the fault this project
exists to avoid.
"""

import os
import sys
import traceback

HOME_FOLDER = os.path.join(os.path.expanduser("~"), ".sparkblocks")
ENV         = "SPARKBLOCKS_PATH"
BESIDE      = "sparkblocks-extra"


def places():
    """Every folder that may hold outside blocks, in the order searched."""
    out = [HOME_FOLDER]
    named = os.environ.get(ENV, "")
    out.extend(p for p in named.split(os.pathsep) if p.strip())
    out.append(os.path.join(os.getcwd(), BESIDE))
    seen, unique = set(), []
    for p in out:
        full = os.path.abspath(os.path.expanduser(p))
        if full not in seen and os.path.isdir(full):
            seen.add(full)
            unique.append(full)
    return unique


def files():
    """Every .py file in those folders, with the folder it came from."""
    out = []
    for folder in places():
        for name in sorted(os.listdir(folder)):
            if name.endswith(".py") and not name.startswith("_"):
                out.append((folder, os.path.join(folder, name)))
    return out


def _read(path):
    """Import one file on its own, without putting it on the import path."""
    import importlib.util
    name = "sparkblocks_outside_" + os.path.basename(path)[:-3]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot read %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_REMEMBERED = None


def forget():
    """Read the folders again next time. Call this after editing a file."""
    global _REMEMBERED
    _REMEMBERED = None


def load(quiet=True):
    """Find every outside block. Returns (blocks, trouble).

    `blocks` is {lower-case name: class}. `trouble` is a list of what
    went wrong, each a plain sentence -- a file that will not import,
    or a block whose name is already taken.

    A bad file is reported and skipped. It can never stop the language
    from starting, because then one broken file would lock you out of
    the editor you would fix it in.
    """
    global _REMEMBERED
    if _REMEMBERED is not None:
        return _REMEMBERED

    from .core import Part
    from . import blocks as mine

    taken = {n.lower(): n for n in mine()}
    found, trouble = {}, []

    for folder, path in files():
        where = os.path.relpath(path, os.path.dirname(folder))
        try:
            module = _read(path)
        except Exception as e:
            trouble.append("%s will not load: %s: %s"
                           % (where, type(e).__name__, e))
            if not quiet:
                traceback.print_exc()
            continue

        for name in dir(module):
            thing = getattr(module, name)
            if not (isinstance(thing, type) and issubclass(thing, Part)
                    and thing.__module__ == module.__name__):
                continue
            low = name.lower()
            if low in taken:
                trouble.append(
                    "%s calls a block %r, which this folder already uses. "
                    "Rename it -- two blocks cannot share a name, or a "
                    "program would mean different things on different "
                    "machines." % (where, name))
                continue
            if low in found:
                trouble.append("%s and an earlier file both call a block %r"
                               % (where, name))
                continue
            thing.came_from = path
            found[low] = thing

    _REMEMBERED = (found, trouble)
    return _REMEMBERED


def names():
    """Just the names of the outside blocks, lower case and sorted."""
    found, _trouble = load()
    return sorted(found)


def catalogue():
    """Outside blocks, shaped like a module's CATALOGUE."""
    found, _trouble = load()
    out = {}
    for low, cls in sorted(found.items()):
        folder = os.path.basename(os.path.dirname(getattr(cls, "came_from", "")))
        out.setdefault(folder or "outside", []).append(cls)
    return out


def main(argv=()):
    found, trouble = load(quiet=False)

    print("\nLooked in:")
    for folder in places():
        print("  %s" % folder)
    if not places():
        print("  nowhere -- none of these folders exist yet:")
        print("    %s" % HOME_FOLDER)
        print("    whatever $%s names" % ENV)
        print("    ./%s" % BESIDE)
        print("\n  Make one and put a .py file in it. Making the folder")
        print("  is the consent; nothing else is searched.")
        return 0

    print("\nFound %d block%s:" % (len(found), "" if len(found) == 1 else "s"))
    for low, cls in sorted(found.items()):
        doc = (cls.__doc__ or "").strip().split("\n")[0]
        print("  %-14s %s" % (low, doc[:48]))
        print("  %-14s from %s" % ("", cls.came_from))
    if not found:
        print("  none")

    if trouble:
        print("\nTrouble:")
        for line in trouble:
            print("  %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
