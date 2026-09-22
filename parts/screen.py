#!/usr/bin/env python3
"""screen -- a grid of pixels you can light from a number, and shapes in 3D.

Same one contract as everything else: `step(ctx) -> value`.

THE SMALLEST THING THAT WORKS
-----------------------------
A pixel that comes on when a number gets big enough:

    screen 16 16
    put hot 0.8
    var hot
    light 3 4 at=0.5
    draw

`light 3 4 at=0.5` means: the number coming down the chain turns the
pixel at 3 across, 4 down ON when it is over 0.5, and OFF when it is
under. That is the whole idea. Any number can drive any pixel -- from a
file's size, from a sensor in the 3D world, from anything.

SHAPES
------
    screen fit
    box 3 3 3
    spin y 40
    spin x 20
    flat
    plot
    draw

A shape is just a list of points. `spin`, `shift` and `grow` turn those
points (that is the matrix work). `flat` drops them from XYZ onto the
grid. `plot` lights whatever pixels they land on.

TOUCH
-----
`tap` waits for you to touch the screen and answers with the pixel you
touched, as {"x": .., "y": ..}. It needs a real terminal; anywhere else
it answers None rather than getting stuck.

Standard library only.
"""

import math
import os
import sys

from .core import Part, _as_list

HOLD = "#screen"           # where the grid lives in a run's scratch space


# ==========================================================================
#  THE GRID
# ==========================================================================

class Grid:
    """A rectangle of pixels, each on or off."""

    def __init__(self, w, h):
        self.w, self.h = max(1, int(w)), max(1, int(h))
        self.cells = [[0] * self.w for _ in range(self.h)]

    def set(self, x, y, on=1):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = 1 if on else 0

    def get(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return 0

    def clear(self):
        self.cells = [[0] * self.w for _ in range(self.h)]

    def lit(self):
        return sum(sum(row) for row in self.cells)


def room():
    """How much of the terminal there is, in pixels two characters wide."""
    try:
        cols, rows = os.get_terminal_size()
    except OSError:
        cols, rows = 40, 20
    return max(4, cols // 2), max(4, rows - 2)


def grid_of(ctx, make=True):
    """The run's grid, made to fit the screen if there isn't one yet."""
    g = ctx.vars.get(HOLD)
    if g is None and make:
        g = Grid(*room())
        ctx.vars[HOLD] = g
    return g


# ==========================================================================
#  MAKING AND SHOWING IT
# ==========================================================================

class Screen(Part):
    """Make the grid. `screen 16 16`, or `screen fit` for the whole window."""
    def __init__(self, w="fit", h=None):
        self.w, self.h = w, h

    def step(self, ctx):
        if str(self.w).lower() in ("fit", "full", "all") or self.h is None:
            g = Grid(*room())
        else:
            g = Grid(self.w, self.h)
        ctx.vars[HOLD] = g
        return ctx.value


class Clear(Part):
    """Turn every pixel off."""
    def step(self, ctx):
        grid_of(ctx).clear()
        return ctx.value


class Draw(Part):
    """Show the grid.

    Each pixel is drawn two characters wide, because a character is
    taller than it is wide -- two of them side by side come out square.
    """
    def __init__(self, on="##", off="..", wide=True, top=True):
        self.on, self.off, self.wide, self.top = on, off, wide, top

    def step(self, ctx):
        g = grid_of(ctx)
        on  = self.on  if self.wide else self.on[:1]
        off = self.off if self.wide else self.off[:1]
        if self.top:
            sys.stdout.write("\033[H")          # back to the corner, no flicker
        out = []
        for row in g.cells:
            out.append("".join(on if c else off for c in row))
        sys.stdout.write("\n".join(out) + "\n")
        sys.stdout.flush()
        return ctx.value


class Wipe(Part):
    """Blank the whole terminal. Use once before a moving picture."""
    def step(self, ctx):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        return ctx.value


# ==========================================================================
#  A NUMBER DRIVING PIXELS  -- the point of all this
# ==========================================================================

class Light(Part):
    """Turn one pixel on when the number is over the line, off when under.

        var hot
        light 3 4 at=0.5

    The number keeps travelling, so several lights can share one number.
    """
    def __init__(self, x, y, at=0.5):
        self.x, self.y, self.at = x, y, at

    def step(self, ctx):
        v = ctx.value
        grid_of(ctx).set(self.x, self.y, _over(v, self.at))
        return v


class Dark(Part):
    """The other way round: on when the number is UNDER the line."""
    def __init__(self, x, y, at=0.5):
        self.x, self.y, self.at = x, y, at

    def step(self, ctx):
        v = ctx.value
        grid_of(ctx).set(self.x, self.y, not _over(v, self.at))
        return v


class Meter(Part):
    """A row of pixels that fills up as the number grows.

        var loud
        meter 0 7 10 most=100
    """
    def __init__(self, x, y, length=10, most=1.0):
        self.x, self.y, self.length, self.most = x, y, int(length), most

    def step(self, ctx):
        v = ctx.value
        try:
            share = float(v) / float(self.most or 1)
        except (TypeError, ValueError):
            share = 0.0
        share = max(0.0, min(1.0, share))
        full = int(round(share * self.length))
        g = grid_of(ctx)
        for i in range(self.length):
            g.set(self.x + i, self.y, i < full)
        return v


class Fill(Part):
    """Every pixel at once, on or off, from one number."""
    def __init__(self, at=0.5):
        self.at = at

    def step(self, ctx):
        g, on = grid_of(ctx), _over(ctx.value, self.at)
        for y in range(g.h):
            for x in range(g.w):
                g.set(x, y, on)
        return ctx.value


class Lit(Part):
    """Is that pixel on? A source, for asking the grid questions."""
    def __init__(self, x, y):
        self.x, self.y = x, y

    def step(self, ctx):
        return grid_of(ctx).get(self.x, self.y)


class Lights(Part):
    """How many pixels are on."""
    def step(self, ctx):
        return grid_of(ctx).lit()


def _over(v, line):
    """Is this number past the line? Anything unnumbered counts as off."""
    try:
        return float(v) > float(line)
    except (TypeError, ValueError):
        return bool(v)


# ==========================================================================
#  SHAPES, AND THE MATRICES THAT TURN THEM
# ==========================================================================

class Dot(Part):
    """One point in space. The start of a shape."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.p = (float(x), float(y), float(z))

    def step(self, ctx):
        return [self.p]


class Box(Part):
    """The twelve edges of a box, as points."""
    def __init__(self, w=2.0, h=2.0, d=2.0, gap=0.25):
        # NB: not `self.step` -- that would shadow the step() method every
        # block in this language must have.
        self.w, self.h, self.d, self.gap = w / 2.0, h / 2.0, d / 2.0, gap

    def step(self, ctx):
        w, h, d = self.w, self.h, self.d
        corners = [(-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d),
                   (-w, -h,  d), (w, -h,  d), (w, h,  d), (-w, h,  d)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0),
                 (4, 5), (5, 6), (6, 7), (7, 4),
                 (0, 4), (1, 5), (2, 6), (3, 7)]
        out = []
        for a, b in edges:
            out.extend(_line(corners[a], corners[b], self.gap))
        return out


class Ball(Part):
    """Points spread over the surface of a ball."""
    def __init__(self, r=1.5, rings=9):
        self.r, self.rings = float(r), int(rings)

    def step(self, ctx):
        out = []
        for i in range(self.rings):
            lat = math.pi * (i + 0.5) / self.rings
            n = max(3, int(self.rings * 2 * math.sin(lat)))
            for j in range(n):
                lon = 2 * math.pi * j / n
                out.append((self.r * math.sin(lat) * math.cos(lon),
                            self.r * math.cos(lat),
                            self.r * math.sin(lat) * math.sin(lon)))
        return out


def _line(a, b, step):
    """Points along a straight line between two corners."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    far = max(abs(dx), abs(dy), abs(dz))
    n = max(1, int(far / max(step, 1e-6)))
    return [(a[0] + dx * i / n, a[1] + dy * i / n, a[2] + dz * i / n)
            for i in range(n + 1)]


class Spin(Part):
    """Turn the shape around an axis. `spin y 40` is forty degrees.

    This is the rotation matrix, written out. Spins add up, so `spin y 40`
    then `spin x 20` leans it over after turning it.

    `spin y var=angle` takes the angle from a variable instead, so a
    `tick angle by=10` earlier in the program makes it turn by itself.
    """
    def __init__(self, axis="y", degrees=0.0, var=None):
        self.axis, self.degrees, self.var = str(axis).lower(), float(degrees), var

    def step(self, ctx):
        turn = self.degrees
        if self.var is not None:
            try:
                turn = float(ctx.vars.get(self.var, self.degrees))
            except (TypeError, ValueError):
                turn = self.degrees
        a = math.radians(turn)
        c, s = math.cos(a), math.sin(a)
        out = []
        for x, y, z in _points(ctx.value):
            if self.axis == "x":
                y, z = y * c - z * s, y * s + z * c
            elif self.axis == "z":
                x, y = x * c - y * s, x * s + y * c
            else:                                    # y
                x, z = x * c + z * s, -x * s + z * c
            out.append((x, y, z))
        return out


class Shift(Part):
    """Shift the shape. The translation matrix."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.d = (float(x), float(y), float(z))

    def step(self, ctx):
        dx, dy, dz = self.d
        return [(x + dx, y + dy, z + dz) for x, y, z in _points(ctx.value)]


class Grow(Part):
    """Make it bigger or smaller. The scaling matrix."""
    def __init__(self, k=1.0, y=None, z=None):
        self.kx = float(k)
        self.ky = float(k if y is None else y)
        self.kz = float(k if z is None else z)

    def step(self, ctx):
        return [(x * self.kx, y * self.ky, z * self.kz)
                for x, y, z in _points(ctx.value)]


class Flat(Part):
    """Drop the shape from XYZ onto the grid: 3D becomes 2D.

    `near` decides how much closer things look bigger. Set it to 0 for a
    flat, engineering-drawing look with no perspective at all.
    """
    def __init__(self, zoom=None, near=6.0):
        self.zoom, self.near = zoom, float(near)

    def step(self, ctx):
        g = grid_of(ctx)
        zoom = self.zoom if self.zoom is not None else min(g.w, g.h) / 5.0
        cx, cy = g.w / 2.0, g.h / 2.0
        out = []
        for x, y, z in _points(ctx.value):
            if self.near > 0:
                depth = self.near + z
                if depth <= 0.1:
                    continue
                k = self.near / depth
            else:
                k = 1.0
            out.append((cx + x * zoom * k, cy - y * zoom * k))
        return out


class Plot(Part):
    """Light every pixel the flattened points land on."""
    def step(self, ctx):
        g = grid_of(ctx)
        pts = ctx.value
        for p in _as_list(pts):
            try:
                if len(p) >= 2:
                    g.set(round(p[0]), round(p[1]), 1)
            except TypeError:
                pass
        return pts


def _points(v):
    """Whatever came down the chain, as a list of (x, y, z)."""
    out = []
    for p in _as_list(v):
        try:
            if len(p) == 3:
                out.append((float(p[0]), float(p[1]), float(p[2])))
            elif len(p) == 2:
                out.append((float(p[0]), float(p[1]), 0.0))
        except (TypeError, ValueError):
            pass
    return out


# ==========================================================================
#  TOUCH
# ==========================================================================

class Spot(Part):
    """Light the pixel the signal names -- {"x": .., "y": ..} or (x, y).

    Put it straight after `tap` and touching the screen paints on it.
    `spot on=false` rubs out instead.
    """
    def __init__(self, on=True):
        self.on = on

    def step(self, ctx):
        v = ctx.value
        x = y = None
        if isinstance(v, dict):
            x, y = v.get("x"), v.get("y")
        elif isinstance(v, (list, tuple)) and len(v) >= 2:
            x, y = v[0], v[1]
        if x is not None and y is not None:
            grid_of(ctx).set(x, y, self.on)
        return v


class Tap(Part):
    """Wait for a touch and answer with the pixel touched: {"x":.., "y":..}.

    Needs a real terminal. Anywhere else -- a pipe, a test -- it answers
    None straight away rather than hanging.
    """
    def __init__(self, seconds=None):
        self.seconds = seconds

    def step(self, ctx):
        spot = read_tap(self.seconds)
        if spot is None:
            return None
        col, row = spot
        return {"x": col // 2, "y": row}          # two characters per pixel


def read_tap(seconds=None):
    """One touch, as (column, row), counting from zero. None if none came."""
    if not sys.stdin.isatty():
        return None
    try:
        import select
        import termios
        import tty
    except ImportError:
        return None

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # ask the terminal to report touches, in the form that copes with
        # a screen wider than 223 characters
        sys.stdout.write("\033[?1000h\033[?1006h")
        sys.stdout.flush()

        got = ""
        while True:
            if seconds is not None:
                ready, _, _ = select.select([fd], [], [], seconds)
                if not ready:
                    return None
            ch = os.read(fd, 1).decode("latin-1")
            if not ch:
                return None
            got += ch
            if ch in "Mm" and got.startswith("\033[<"):
                bits = got[3:-1].split(";")
                if len(bits) == 3:
                    try:
                        return int(bits[1]) - 1, int(bits[2]) - 1
                    except ValueError:
                        return None
                return None
            if ch == "\003":                      # ctrl-c
                raise KeyboardInterrupt
            if len(got) > 32:
                got = ""
    finally:
        sys.stdout.write("\033[?1006l\033[?1000l")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


CATALOGUE = {
    "screen": [Screen, Draw, Clear, Wipe],
    "pixels": [Light, Dark, Meter, Fill, Lit, Lights],
    "shapes": [Dot, Box, Ball],
    "matrix": [Spin, Shift, Grow, Flat, Plot],
    "touch":  [Tap, Spot],
}
