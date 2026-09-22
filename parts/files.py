#!/usr/bin/env python3
"""files -- folders, files, and moving them about, as parts.

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


def _p(path):
    """Expand ~ and make it absolute."""
    return os.path.abspath(os.path.expanduser(str(path)))


def _pick(arg, ctx):
    """Use the argument if given, otherwise whatever is coming down the chain."""
    return _p(arg if arg is not None else ctx.value)


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


class Read(Part):
    """The text inside a file. Unreadable or binary gives ""."""
    def __init__(self, path=None, limit=2_000_000):
        self.path, self.limit = path, limit

    def step(self, ctx):
        try:
            with open(_pick(self.path, ctx), "r", errors="ignore") as fh:
                return fh.read(self.limit)
        except (OSError, ValueError):
            return ""


class Lines(Part):
    """The lines of a file, as a list."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx):
        return Read(self.path).step(ctx).splitlines()


class Exists(Part):
    def __init__(self, path=None): self.path = path
    def step(self, ctx): return os.path.exists(_pick(self.path, ctx))


class IsDir(Part):
    def __init__(self, path=None): self.path = path
    def step(self, ctx): return os.path.isdir(_pick(self.path, ctx))


class IsFile(Part):
    def __init__(self, path=None): self.path = path
    def step(self, ctx): return os.path.isfile(_pick(self.path, ctx))


class Size(Part):
    """Bytes. A missing file is 0."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx):
        try:    return os.path.getsize(_pick(self.path, ctx))
        except OSError: return 0


class Age(Part):
    """Days since it was last changed."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx):
        try:    return (time.time() - os.path.getmtime(_pick(self.path, ctx))) / 86400.0
        except OSError: return 1e9


class Name(Part):
    """Just the file's own name, no folders."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx): return os.path.basename(_pick(self.path, ctx))


class Parent(Part):
    """The folder a path sits in."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx): return os.path.dirname(_pick(self.path, ctx))


class Ext(Part):
    """With no argument: the extension. With one: True when it matches."""
    def __init__(self, is_=None, path=None): self.is_, self.path = is_, path
    def step(self, ctx):
        e = os.path.splitext(_pick(self.path, ctx))[1].lower()
        if self.is_ is None:
            return e
        want = [w if w.startswith(".") else "." + w
                for w in _as_list(self.is_)]
        return e in [w.lower() for w in want]


# ==========================================================================
#  SINKS -- change the disk
# ==========================================================================

class MakeDir(Part):
    """Create a folder, and any parent folders it needs."""
    def __init__(self, path=None): self.path = path
    def step(self, ctx):
        target = _pick(self.path, ctx)
        os.makedirs(target, exist_ok=True)
        return target


class Write(Part):
    """Write the signal into a file. Creates parent folders."""
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


class Copy(Part):
    """Copy whatever comes down the chain into a folder.

    Takes a single path or a whole list of them. Passes the new paths on.
    """
    def __init__(self, into): self.into = into
    def step(self, ctx):
        dest = _p(self.into)
        os.makedirs(dest, exist_ok=True)
        made = []
        for src in _as_list(ctx.value):
            src = _p(src)
            try:
                if os.path.isdir(src):
                    out = os.path.join(dest, os.path.basename(src))
                    shutil.copytree(src, out, dirs_exist_ok=True)
                else:
                    out = shutil.copy2(src, dest)
                made.append(out)
            except (OSError, shutil.Error):
                pass
        return made if isinstance(ctx.value, (list, tuple, set)) else \
            (made[0] if made else None)


class Move(Part):
    """Move whatever comes down the chain into a folder."""
    def __init__(self, into): self.into = into
    def step(self, ctx):
        dest = _p(self.into)
        os.makedirs(dest, exist_ok=True)
        made = []
        for src in _as_list(ctx.value):
            try:
                made.append(shutil.move(_p(src), dest))
            except (OSError, shutil.Error):
                pass
        return made if isinstance(ctx.value, (list, tuple, set)) else \
            (made[0] if made else None)


class Rename(Part):
    """Rename in place. `to` may use {name} {ext} {n}."""
    def __init__(self, to): self.to = to
    def step(self, ctx):
        made = []
        for n, src in enumerate(_as_list(ctx.value), 1):
            src = _p(src)
            base = os.path.basename(src)
            stem, ext = os.path.splitext(base)
            new = self.to.format(name=stem, ext=ext, n=n)
            out = os.path.join(os.path.dirname(src), new)
            try:
                os.rename(src, out)
                made.append(out)
            except OSError:
                pass
        return made if isinstance(ctx.value, (list, tuple, set)) else \
            (made[0] if made else None)


class Remove(Part):
    """Delete. Guarded on purpose.

    Files go quietly. A FOLDER is only removed when you pass folders=True,
    because deleting a tree by accident is the one mistake you cannot undo.
    """
    def __init__(self, folders=False): self.folders = folders
    def step(self, ctx):
        gone = []
        for src in _as_list(ctx.value):
            src = _p(src)
            try:
                if os.path.isdir(src):
                    if not self.folders:
                        continue
                    shutil.rmtree(src)
                else:
                    os.remove(src)
                gone.append(src)
            except OSError:
                pass
        return gone


class Make(Part):
    """Create an empty file if it isn't there; otherwise mark it changed now.

    (MakeDir is the folder version. Named Make, not Touch, because
    space.Touch already means "is something overlapping me".)
    """
    def __init__(self, path=None): self.path = path
    def step(self, ctx):
        target = _pick(self.path, ctx)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "a"):
            os.utime(target, None)
        return target


CATALOGUE = {
    "where":  [Here, Home, Parent, Name, Ext],
    "look":   [Ls, Walk, Glob, Exists, IsDir, IsFile, Size, Age],
    "read":   [Read, Lines],
    "change": [MakeDir, Make, Write, Copy, Move, Rename, Remove],
}
