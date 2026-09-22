#!/usr/bin/env python3
"""parts -- one small language of interchangeable blocks.

    from parts import *

THE ONE CONTRACT
----------------
Every block is an object with exactly this:

    part.step(ctx) -> value

`ctx.value` is the signal running down a chain. It may be a number, text,
a path, a list, or a dict. That single rule is what lets any block sit in
any slot, and it is the whole of the language.

    Chain([Walk("~/notes"), Keep(Ext(".md")), Count(), Say()])

FOUR MODULES, ONE TONGUE
------------------------
    core    the contract, and blocks that work on any value
    space   a 3D world: bodies, sensors, motors
    files   folders, files, copying and moving
    net     other machines: fetching, reaching, downloading
    screen  a grid of pixels, shapes in 3D, and touch
    pad     the window as eight squares you press

Import the lot with `from parts import *`, or take one module at a time
with `from parts.files import Walk, Copy` when you want to be exact.

Standard library only. No installs, no threads, no 64-bit requirement.
"""

from . import core, files, net, pad, screen, space

from .core import (  # noqa: F401
    # the contract
    Part, Ctx, run,
    # links
    Chain, Fan, Each, Keep, Drop, Gate, Try,
    # sources
    Const, Var, Osc,
    # numbers
    Gain, Bias, Invert, Minus, Abs, Is, Clamp, Threshold, Smooth, Delay,
    Integrate, Derive, PID,
    # text
    Lower, Upper, Strip, Split, Join, Replace, Contains, Match, Grab, Text,
    # lists
    Count, First, Last, Sort, Uniq, Flatten, Field, Pack,
    # sinks
    Say, Put, Tick, Do,
)

from .space import (  # noqa: F401
    V, ZERO, UP, FWD, Body, World,
    Clock, Height, Speed, Heading, Level, Near, Touch, Ray, Bearing,
    Thrust, Lift, Turn, Tilt, Store, Drain, Spawn, Expire, Die,
)

from .files import (  # noqa: F401
    Here, Home, Ls, Walk, Glob, Read, Lines,
    Exists, IsDir, IsFile, Size, Age, Name, Parent, Ext,
    MakeDir, Make, Write, Copy, Move, Rename, Remove,
)

from .net import (  # noqa: F401
    Fetch, Json, Status, Reach, Host, Address, Links, Mine,
    Send, Download,
)

from .pad import (  # noqa: F401
    Pad, Button, Banner, Press,
)

from .screen import (  # noqa: F401
    Grid, Screen, Draw, Clear, Wipe,
    Light, Dark, Meter, Fill, Lit, Lights,
    Dot, Box, Ball, Spin, Shift, Grow, Flat, Plot, Tap, Spot,
)


# Every block, by module and kind -- for menus, editors, and browsing.
CATALOGUE = {
    "core":  core.CATALOGUE,
    "space": space.CATALOGUE,
    "files": files.CATALOGUE,
    "net":    net.CATALOGUE,
    "screen": screen.CATALOGUE,
    "pad":    pad.CATALOGUE,
}


def blocks():
    """Every block in the language, as a flat sorted list of names."""
    out = set()
    for mod in CATALOGUE.values():
        for group in mod.values():
            out.update(c.__name__ for c in group)
    return sorted(out)


def describe(name=None):
    """Print the catalogue, or one block's own documentation."""
    if name:
        cls = globals().get(name)
        if cls is None:
            print("no block called %r" % name)
            return
        print(name, "--", (cls.__doc__ or "").strip().split("\n")[0])
        doc = (cls.__doc__ or "").strip()
        if "\n" in doc:
            print("\n".join("   " + l for l in doc.split("\n")[1:]))
        return
    for mod, groups in CATALOGUE.items():
        print("\n%s" % mod.upper())
        for kind, group in groups.items():
            print("  %-8s %s" % (kind, "  ".join(c.__name__ for c in group)))
