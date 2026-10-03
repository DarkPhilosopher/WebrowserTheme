#!/usr/bin/env python3
"""files -- folders, files, and moving them about, as blocks.

Same one contract as core: every part is `step(ctx) -> value`.

Every part here takes its path either as an argument or, when you leave
the argument out, from the signal coming down the chain. That is what
lets them sit anywhere in a line:

    Chain([Const("~/notes"), Walk(), Keep(Ext(".md")), Say()])
    Chain([Walk("~/notes"),  Keep(Ext(".md")), Say()])      # same thing

Standard library only.
"""

import os
import shutil
import time
import fnmatch

from .core import Part, _as_list

# What every block in this module needs, unless it says otherwise.
FITS = {"needs": ["files"], "changes": "nothing", "waits": False}


def _p(path):
    """Expand ~ and make it absolute."""
    return os.path.abspath(os.path.expanduser(str(path)))


def _dotted(word):
    """`.md` and `md` both mean the same extension."""
    w = str(word).lower()
    return w if w.startswith(".") else "." + w


def _pick(arg, ctx):
    """Use the argument if given, otherwise whatever is coming down the chain."""
    return _p(arg if arg is not None else ctx.value)


# ==========================================================================
#  THE SHAPES, WRITTEN ONCE
#
#  Most of what follows is one of two shapes. Each block is then the
#  smallest difference from its shape: a name, a sentence, one line.
# ==========================================================================

class Pather(Part):
    """A block that looks at ONE path. Override `about`.

    The path is the argument when you give one, and whatever is coming
    down the chain when you do not -- which is what lets these sit
    anywhere in a line. Anything the disk refuses answers `missing`
    rather than stopping the program.
    """
    missing = None

    def __init__(self, path=None):
        self.path = path

    def step(self, ctx):
        try:
            return self.about(_pick(self.path, ctx))
        except (OSError, ValueError):
            return self.missing

    def about(self, path):
        return path


class Changer(Part):
    """A block that changes MANY paths at once. Override `change`.

    Whatever comes down the chain -- one path or a whole list of them --
    is handled one at a time, and anything the disk refuses is skipped
    rather than stopping the rest. What comes back matches what went in:
    a list for a list, one path for one path.
    """
    def __init__(self, into=None):
        self.into = into

    def step(self, ctx):
        made = []
        for one in _as_list(ctx.value):
            try:
                got = self.change(_p(one), ctx)
                if got is not None:
                    made.append(got)
            except (OSError, shutil.Error, ValueError):
                pass
        if isinstance(ctx.value, (list, tuple, set)):
            return made
        return made[0] if made else None

    def change(self, path, ctx):
        return path


def _dest(into):
    """The folder a Changer puts things into, made if it is not there."""
    where = _p(into)
    os.makedirs(where, exist_ok=True)
    return where


# ==========================================================================
#  SOURCES -- look at the disk
# ==========================================================================

class Here(Part):
    """The folder the program is running in."""
    def step(self, ctx): return os.getcwd()


class Home(Part):
    """Your home folder."""
    def step(self, ctx): return os.path.expanduser("~")


class Ls(Part):
    """Everything directly inside a folder. One level, no recursion."""
    def __init__(self, path=None, folders=True, files=True):
        self.path, self.folders, self.files = path, folders, files

    def step(self, ctx):
        root = _pick(self.path, ctx)
        out = []
        try:
            names = sorted(os.listdir(root))
        except OSError:
            return []
        for n in names:
            full = os.path.join(root, n)
            isdir = os.path.isdir(full)
            if (isdir and self.folders) or (not isdir and self.files):
                out.append(full)
        return out


class Walk(Part):
    """Every file underneath a folder, all the way down.

    skip: folder names never descended into.
    """
    def __init__(self, path=None, folders=False, files=True, skip=None,
                 limit=200000):
        self.path, self.folders, self.files = path, folders, files
        self.skip = set(skip or (".git", "node_modules", "__pycache__",
                                 ".cache", ".venv"))
        self.limit = limit

    def step(self, ctx):
        root = _pick(self.path, ctx)
        out = []
        for here, dirs, names in os.walk(root, onerror=lambda e: None):
            dirs[:] = [d for d in dirs if d not in self.skip]
            if self.folders:
                out.extend(os.path.join(here, d) for d in dirs)
            if self.files:
                out.extend(os.path.join(here, n) for n in names)
            if len(out) >= self.limit:
                return out[:self.limit]
        return out


class Glob(Part):
    """Files underneath a folder whose NAME matches a pattern: *.pdf, note*"""
    def __init__(self, pattern, path=None, skip=None):
        self.pattern = pattern
        self.walk = Walk(path, skip=skip)

    def step(self, ctx):
        return [f for f in self.walk.step(ctx)
                if fnmatch.fnmatch(os.path.basename(f).lower(),
                                   self.pattern.lower())]


class Read(Pather):
    """The text inside a file. Unreadable or binary gives ""."""
    missing = ""
    def __init__(self, path=None, limit=2_000_000):
        self.path, self.limit = path, limit
    def about(self, p):
        with open(p, "r", errors="ignore") as fh:
            return fh.read(self.limit)


class Lines(Pather):
    """The lines of a file, as a list."""
    missing = []
    def about(self, p): return Read(p).about(p).splitlines()


class Exists(Pather):
    """Is there anything at this path -- a file or a folder?"""
    missing = False
    def about(self, p): return os.path.exists(p)


class IsDir(Pather):
    """Is this path a folder?"""
    missing = False
    def about(self, p): return os.path.isdir(p)


class IsFile(Pather):
    """Is this path a file, rather than a folder?"""
    missing = False
    def about(self, p): return os.path.isfile(p)


class Size(Pather):
    """How many bytes a file is. A missing one is 0."""
    missing = 0
    def about(self, p): return os.path.getsize(p)


class Age(Pather):
    """Days since it was last changed. A missing one is very old."""
    missing = 1e9
    def about(self, p): return (time.time() - os.path.getmtime(p)) / 86400.0


class Name(Pather):
    """Just the file's own name, with no folders in front of it."""
    missing = ""
    def about(self, p): return os.path.basename(p)


class Parent(Pather):
    """The folder a path sits in."""
    missing = ""
    def about(self, p): return os.path.dirname(p)


class Ext(Pather):
    """With no setting: the extension. With one: true when it matches."""
    def __init__(self, is_=None, path=None): self.is_, self.path = is_, path
    def about(self, p):
        got = os.path.splitext(p)[1].lower()
        if self.is_ is None:
            return got
        return got in [_dotted(w) for w in _as_list(self.is_)]


# ==========================================================================
#  SINKS -- change the disk
# ==========================================================================

class MakeDir(Pather):
    """Create a folder, and any folders above it that it needs."""
    fits = {"changes": "files"}
    def about(self, p):
        os.makedirs(p, exist_ok=True)
        return p


class Write(Part):
    """Write the signal into a file. Creates parent folders."""
    fits = {"changes": "files"}
    def __init__(self, path, append=False): self.path, self.append = path, append
    def step(self, ctx):
        target = _p(self.path)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        body = ctx.value
        if isinstance(body, (list, tuple)):
            body = "\n".join(str(x) for x in body)
        with open(target, "a" if self.append else "w") as fh:
            fh.write(str(body))
            if self.append:
                fh.write("\n")
        return ctx.value


class Copy(Changer):
    """Copy whatever comes down the chain into a folder, originals intact."""
    fits = {"changes": "files"}
    def change(self, path, ctx):
        into = _dest(self.into)
        if os.path.isdir(path):
            out = os.path.join(into, os.path.basename(path))
            shutil.copytree(path, out, dirs_exist_ok=True)
            return out
        return shutil.copy2(path, into)


class Move(Changer):
    """Move whatever comes down the chain into a folder, leaving nothing."""
    fits = {"changes": "files"}
    def change(self, path, ctx):
        return shutil.move(path, _dest(self.into))


class Rename(Changer):
    """Rename in place. The new name may use {name}, {ext} and {n}."""
    fits = {"changes": "files"}
    def __init__(self, to): self.to, self.into, self.n = to, None, 0
    def change(self, path, ctx):
        self.n += 1
        stem, ext = os.path.splitext(os.path.basename(path))
        out = os.path.join(os.path.dirname(path),
                           self.to.format(name=stem, ext=ext, n=self.n))
        os.rename(path, out)
        return out


class Remove(Changer):
    """Delete. Guarded on purpose.

    Files go quietly. A FOLDER is only removed when you pass
    folders=true, because deleting a tree by accident is the one mistake
    you cannot undo.
    """
    fits = {"changes": "DELETES"}
    def __init__(self, folders=False): self.folders, self.into = folders, None
    def step(self, ctx):
        # always a list, even for one path -- you want to see what went
        got = Changer.step(self, ctx)
        return got if isinstance(got, list) else ([got] if got else [])
    def change(self, path, ctx):
        if os.path.isdir(path):
            if not self.folders:
                return None
            shutil.rmtree(path)
        else:
            os.remove(path)
        return path


class Make(Pather):
    """Create an empty file, or mark an existing one as changed now.

    MakeDir is the folder version. Named Make and not Touch, because
    space.Touch already means "is something overlapping me".
    """
    fits = {"changes": "files"}
    def about(self, p):
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "a"):
            os.utime(p, None)
        return p


CATALOGUE = {
    "where":  [Here, Home, Parent, Name, Ext],
    "look":   [Ls, Walk, Glob, Exists, IsDir, IsFile, Size, Age],
    "read":   [Read, Lines],
    "change": [MakeDir, Make, Write, Copy, Move, Rename, Remove],
}
