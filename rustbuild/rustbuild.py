#!/usr/bin/env python3
r"""
rustbuild - a Rust-style construction-block editor for Termux (ASCII).

Same grid/piece idea as Rust building: one fixed TILE size, snapped pieces.
  * Foundations (square + triangle) on the ground level
  * Floors/ceilings (square + triangle) on upper levels
  * Walls on tile EDGES: full wall, doorway, window-wall, low (half) wall
  * Stairs (L and U) and pitched Roof pieces
Build the floor plan top-down, stack levels, then flip to an isometric 3D view.

RUN (Termux):
    pkg install python -y
    python rustbuild.py

You get a grid and a ">" prompt. Type "help" for all commands. Quick start:
    f            place a square foundation under the cursor
    e            move cursor east   (n/e/s/w move; add a number: e 3)
    f
    wall n       put a wall on the north edge  (door/window/low too)
    3d           isometric view    (rotate y 45 / zoom in / 2d)
"""

import json
import math
import sys

# ---------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------
class Editor:
    def __init__(self, w=12, h=12):
        self.w, self.h = w, h
        self.cx, self.cy = 0, 0
        self.level = 0
        self.maxlevel = 0
        # per level: base[(x,y)]=code ; hwall[(x,y)]=code (north edge of tile x,y,
        # i.e. line between rows y-1 and y) ; vwall[(x,y)] (west edge of tile x,y)
        self.base = {}      # (level,x,y) -> 'sq'|'floor'|'tri_ne'..|'stairs_l'|'stairs_u'|'roof'
        self.hwall = {}     # (level,x,y) -> wall code   (x in 0..w-1, y in 0..h)
        self.vwall = {}     # (level,x,y) -> wall code   (x in 0..w,   y in 0..h-1)
        # view
        self.view = "2d"
        self.yaw = 45.0     # isometric default
        self.pitch = 0.5    # 0.5 = classic 2:1 iso tilt
        self.zoom = 1.0
        self.color = True

    # -- helpers -----------------------------------------------------------
    def in_grid(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def wall_targets(self, side):
        """Return the (dict, key) for the shared edge on `side` of the cursor."""
        x, y = self.cx, self.cy
        if side == "n":  return self.hwall, (self.level, x, y)
        if side == "s":  return self.hwall, (self.level, x, y + 1)
        if side == "w":  return self.vwall, (self.level, x, y)
        if side == "e":  return self.vwall, (self.level, x + 1, y)
        return None, None


# ---------------------------------------------------------------------------
# glyphs
# ---------------------------------------------------------------------------
BASE2 = {
    None: "  ", "sq": "##", "floor": "::",
    "tri_ne": "//", "tri_sw": "//", "tri_nw": "\\\\", "tri_se": "\\\\",
    "stairs_l": "Sl", "stairs_u": "Su", "roof": "^^",
}
HED = {None: "··", "wall": "==", "door": "dd", "window": "ww", "low": "--"}
VED = {None: "·", "wall": "|", "door": "d", "window": "w", "low": ":"}


# ---------------------------------------------------------------------------
# 2D top-down render of the current level
# ---------------------------------------------------------------------------
def render_2d(ed):
    W, H = ed.w, ed.h
    cols = W * 3 + 1
    rows = H * 2 + 1
    grid = [[" "] * cols for _ in range(rows)]

    # corners
    for gy in range(H + 1):
        for gx in range(W + 1):
            grid[gy * 2][gx * 3] = "+"

    # horizontal edges (north edge of each tile row, plus final south border)
    for y in range(H + 1):
        for x in range(W):
            g = HED[ed.hwall.get((ed.level, x, y))]
            grid[y * 2][x * 3 + 1] = g[0]
            grid[y * 2][x * 3 + 2] = g[1]

    # vertical edges (west edge of each tile col, plus final east border)
    for y in range(H):
        for x in range(W + 1):
            grid[y * 2 + 1][x * 3] = VED[ed.vwall.get((ed.level, x, y))]

    # tile centres / cursor
    for y in range(H):
        for x in range(W):
            if x == ed.cx and y == ed.cy:
                c = "@@"
            else:
                c = BASE2[ed.base.get((ed.level, x, y))]
            grid[y * 2 + 1][x * 3 + 1] = c[0]
            grid[y * 2 + 1][x * 3 + 2] = c[1]

    return ["".join(r) for r in grid]


# ---------------------------------------------------------------------------
# 3D isometric wireframe of the whole build
# ---------------------------------------------------------------------------
def collect_edges(ed):
    """Return list of 3D segments ((x1,y1,z1),(x2,y2,z2)). Z up = level."""
    seg = []
    def line(a, b): seg.append((a, b))
    Hh = 1.0   # wall / level height

    for (lvl, x, y), code in ed.base.items():
        z = lvl * Hh
        if code in ("sq", "floor"):
            c = [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]
            for i in range(4):
                line(c[i], c[(i + 1) % 4])
        elif code and code.startswith("tri"):
            # triangle = square minus one corner; draw the two legs + hypotenuse
            d = code.split("_")[1]
            pts = {
                "ne": [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z)],
                "nw": [(x + 1, y, z), (x, y, z), (x, y + 1, z)],
                "se": [(x + 1, y + 1, z), (x + 1, y, z), (x, y + 1, z)],
                "sw": [(x, y + 1, z), (x, y, z), (x + 1, y + 1, z)],
            }[d]
            for i in range(3):
                line(pts[i], pts[(i + 1) % 3])
        elif code == "roof":
            apex = (x + 0.5, y + 0.5, z + Hh)
            for cc in [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]:
                line(cc, apex)
        elif code and code.startswith("stairs"):
            line((x, y + 1, z), (x + 1, y, z + Hh))  # a simple diagonal run

    # walls: vertical rectangles on the shared edges
    for (lvl, x, y), code in ed.hwall.items():
        if not code:
            continue
        z = lvl * Hh
        a, b = (x, y, z), (x + 1, y, z)
        line((a[0], a[1], z + Hh), (b[0], b[1], z + Hh))  # top
        line(a, (a[0], a[1], z + Hh))                     # left post
        line(b, (b[0], b[1], z + Hh))                     # right post
    for (lvl, x, y), code in ed.vwall.items():
        if not code:
            continue
        z = lvl * Hh
        a, b = (x, y, z), (x, y + 1, z)
        line((a[0], a[1], z + Hh), (b[0], b[1], z + Hh))
        line(a, (a[0], a[1], z + Hh))
        line(b, (b[0], b[1], z + Hh))
    return seg


def render_3d(ed, cw=72, ch=32):
    segs = collect_edges(ed)
    if not segs:
        return ["(nothing built yet - place a foundation with 'f', then '3d')"]

    ya = math.radians(ed.yaw)
    ca, sa = math.cos(ya), math.sin(ya)

    def proj(p):
        X, Y, Z = p
        x1 = X * ca - Y * sa
        y1 = X * sa + Y * ca
        sx = x1                      # rotate in the ground plane by yaw,
        sy = y1 * ed.pitch - Z       # then tilt the ground down and lift by height
        return sx, sy

    pts = [proj(a) for a, b in segs] + [proj(b) for a, b in segs]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    spanx = (maxx - minx) or 1.0
    spany = (maxy - miny) or 1.0
    scale = min((cw - 2) / spanx, (ch - 2) / spany) * ed.zoom

    def to_screen(p):
        sx, sy = proj(p)
        gx = int((sx - minx) * scale) + 1
        gy = int((maxy - sy) * scale) + 1     # flip y for screen
        return gx, gy

    canvas = [[" "] * cw for _ in range(ch)]
    def plot(x, y, ch_):
        if 0 <= x < cw and 0 <= y < ch:
            canvas[y][x] = ch_
    def draw(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        adx, ady = abs(dx), abs(dy)
        if adx > 2 * ady: ic = "-"
        elif ady > 2 * adx: ic = "|"
        elif (dx > 0) == (dy > 0): ic = "\\"
        else: ic = "/"
        steps = max(adx, ady, 1)
        for i in range(steps + 1):
            plot(round(x1 + dx * i / steps), round(y1 + dy * i / steps), ic)

    for a, b in segs:
        ax, ay = to_screen(a); bx, by = to_screen(b)
        draw(ax, ay, bx, by)
    return ["".join(r).rstrip() for r in canvas]


# ---------------------------------------------------------------------------
# colour (optional, auto-off when piped)
# ---------------------------------------------------------------------------
def colorize(line):
    out, esc, rst = [], "\033[", "\033[0m"
    cmap = {"#": "38;5;131", ":": "38;5;109", "=": "33", "|": "33",
            "d": "36", "w": "36", "@": "1;31", "^": "38;5;173",
            "/": "38;5;250", "\\": "38;5;250", "S": "35"}
    for chn in line:
        if chn in cmap:
            out.append(esc + cmap[chn] + "m" + chn + rst)
        else:
            out.append(chn)
    return "".join(out)


def show(ed):
    print("\033[2J\033[H", end="")
    use_color = ed.color and sys.stdout.isatty()
    if ed.view == "3d":
        print("  rustbuild  [3D iso]  yaw=%.0f pitch=%.2f zoom=%.2f   (rotate y 45 / zoom in / 2d)"
              % (ed.yaw, ed.pitch, ed.zoom))
        body = render_3d(ed)
    else:
        print("  rustbuild  [top-down]  level %d   cursor (%d,%d)   (help for commands)"
              % (ed.level, ed.cx, ed.cy))
        body = render_2d(ed)
    print()
    for ln in body:
        print("  " + (colorize(ln) if use_color else ln))
    if ed.view == "2d":
        b = ed.base.get((ed.level, ed.cx, ed.cy))
        walls = []
        for s in ("n", "e", "s", "w"):
            d, k = ed.wall_targets(s)
            if d.get(k):
                walls.append("%s:%s" % (s.upper(), d[k]))
        print("\n  under cursor: base=%s  walls=%s" % (b or "-", ",".join(walls) or "-"))
        print("  legend: ## found  :: floor  // \\\\ triangle  == wall  dd door  "
              "ww window  -- low  Sl/Su stairs  ^^ roof  @@ you")
    print("\n  > ", end="", flush=True)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------
HELP = """rustbuild - commands
====================
MOVE      n / e / s / w  [count]     move the cursor (e.g. e 3)
          go X Y                     jump the cursor to a tile

PLACE     f                          square foundation (lvl 0) / floor (upper)
          tri <ne|nw|se|sw>          triangle foundation / floor
          stairs <l|u>               L- or U-stairs
          roof                       pitched roof piece
          del                        clear the tile's base (keep walls)
          clear                      clear the whole tile (base + its edges)

WALLS     wall <n|e|s|w>             full wall on that edge
          door <n|e|s|w>             doorway
          window <n|e|s|w>           window-wall
          low <n|e|s|w>              half / low wall
          open <n|e|s|w>             remove the wall on that edge

LEVELS    up / down                  change the level you're editing

VIEW      2d                         top-down floor plan (default)
          3d                         isometric wireframe of the whole build
          rotate y <deg>             spin the 3D view   (also: rotate x <deg>)
          zoom <in|out|reset>        zoom the 3D view
          color <on|off>             toggle colour

FILE      save [name]                save the build (default build.rust)
          load [name]                load a build
          new [w] [h]                start over (optional grid size)
          help                       this list
          quit                       leave
"""


def place_base(ed, code):
    key = (ed.level, ed.cx, ed.cy)
    if code == "f":
        code = "floor" if ed.level > 0 else "sq"
    ed.base[key] = code
    ed.maxlevel = max(ed.maxlevel, ed.level)


def do_cmd(ed, line):
    p = line.split()
    if not p:
        return True
    c = p[0].lower()
    arg = p[1].lower() if len(p) > 1 else ""

    if c in ("n", "e", "s", "w"):
        step = int(p[1]) if (len(p) > 1 and p[1].isdigit()) else 1
        dx, dy = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[c]
        ed.cx = min(ed.w - 1, max(0, ed.cx + dx * step))
        ed.cy = min(ed.h - 1, max(0, ed.cy + dy * step))
    elif c == "go" and len(p) >= 3 and p[1].isdigit() and p[2].isdigit():
        if ed.in_grid(int(p[1]), int(p[2])):
            ed.cx, ed.cy = int(p[1]), int(p[2])
    elif c == "f":
        place_base(ed, "f")
    elif c == "tri":
        if arg in ("ne", "nw", "se", "sw"):
            place_base(ed, "tri_" + arg)
        else:
            print("  tri needs a corner: ne|nw|se|sw"); return None
    elif c == "stairs":
        if arg in ("l", "u"):
            place_base(ed, "stairs_" + arg)
        else:
            print("  stairs l | u"); return None
    elif c == "roof":
        place_base(ed, "roof")
    elif c == "del":
        ed.base.pop((ed.level, ed.cx, ed.cy), None)
    elif c == "clear":
        ed.base.pop((ed.level, ed.cx, ed.cy), None)
        for s in ("n", "e", "s", "w"):
            d, k = ed.wall_targets(s); d.pop(k, None)
    elif c in ("wall", "door", "window", "low", "open"):
        if arg not in ("n", "e", "s", "w"):
            print("  %s needs an edge: n|e|s|w" % c); return None
        d, k = ed.wall_targets(arg)
        if c == "open":
            d.pop(k, None)
        else:
            d[k] = c
    elif c == "up":
        ed.level += 1; ed.maxlevel = max(ed.maxlevel, ed.level)
    elif c == "down":
        ed.level = max(0, ed.level - 1)
    elif c == "2d":
        ed.view = "2d"
    elif c == "3d":
        ed.view = "3d"
    elif c in ("rotate", "rot") and len(p) >= 3:
        try:
            v = float(p[2])
        except ValueError:
            print("  rotate y|x <degrees>"); return None
        ed.view = "3d"
        if p[1].lower() == "y":
            ed.yaw = (ed.yaw + v) % 360
        elif p[1].lower() == "x":
            ed.pitch = max(0.05, min(1.5, ed.pitch + v / 100.0))
    elif c == "zoom":
        ed.view = "3d"
        if arg in ("in", "+"): ed.zoom = min(6.0, ed.zoom * 1.3)
        elif arg in ("out", "-"): ed.zoom = max(0.3, ed.zoom / 1.3)
        else: ed.zoom = 1.0
    elif c == "color":
        ed.color = (arg != "off")
    elif c == "save":
        save_build(ed, p[1] if len(p) > 1 else "build.rust"); return None
    elif c == "load":
        load_build(ed, p[1] if len(p) > 1 else "build.rust"); return None
    elif c == "new":
        w = int(p[1]) if len(p) > 1 and p[1].isdigit() else ed.w
        h = int(p[2]) if len(p) > 2 and p[2].isdigit() else ed.h
        ed.__init__(w, h)
    elif c in ("help", "h", "?"):
        print(HELP); return None
    elif c in ("quit", "exit", "q"):
        return False
    else:
        print("  unknown command '%s' - type help" % c); return None
    return True


def save_build(ed, name):
    data = {"w": ed.w, "h": ed.h, "maxlevel": ed.maxlevel,
            "base": {"%d,%d,%d" % k: v for k, v in ed.base.items()},
            "hwall": {"%d,%d,%d" % k: v for k, v in ed.hwall.items()},
            "vwall": {"%d,%d,%d" % k: v for k, v in ed.vwall.items()}}
    try:
        with open(name, "w") as fh:
            json.dump(data, fh)
        print("  saved to %s" % name)
    except OSError as e:
        print("  save failed:", e)


def load_build(ed, name):
    try:
        with open(name) as fh:
            data = json.load(fh)
    except OSError as e:
        print("  load failed:", e); return
    ed.__init__(data["w"], data["h"])
    ed.maxlevel = data.get("maxlevel", 0)
    def unpack(d):
        return {tuple(int(n) for n in k.split(",")): v for k, v in d.items()}
    ed.base = unpack(data["base"]); ed.hwall = unpack(data["hwall"]); ed.vwall = unpack(data["vwall"])
    print("  loaded %s" % name)


# ---------------------------------------------------------------------------
def main():
    ed = Editor()
    show(ed)
    for line in sys.stdin:
        r = do_cmd(ed, line.strip())
        if r is False:
            break
        if r is True:
            show(ed)
        else:
            print("\n  > ", end="", flush=True)   # a message was printed; keep prompt
    print("\nbye")


if __name__ == "__main__":
    main()
