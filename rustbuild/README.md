# rustbuild — a construction-block editor in ASCII

> **This one is Gabriel's.** It was in the repository before the Wakeup
> work and nothing here has changed it. This manual was written by
> reading the code, so that `INDEX.md` is complete and nothing in the
> repository is undocumented.

Build the way Rust does: one fixed tile size, pieces that snap to it.
Lay out a floor plan from above, stack levels, then flip to isometric
3D and turn it.

```bash
pkg install python -y
python rustbuild.py
```

A grid and a `>` prompt. Type `help` for everything.

```
f            square foundation under the cursor
e            move east   (n/e/s/w; add a number: e 3)
f
wall n       a wall on the north edge
3d           isometric view   (rotate y 45 / zoom in / 2d)
```

## Every command

**Move** — `n` `e` `s` `w` with an optional count · `go X Y` to jump

**Place** — `f` square foundation, or floor on an upper level ·
`tri ne|nw|se|sw` triangle · `stairs l|u` · `roof` ·
`del` clear the base, keep the walls · `clear` the whole tile

**Walls**, on tile edges — `wall n|e|s|w` full · `door` · `window` ·
`low` half-height · `open` removes one

**Levels** — `up` · `down`

**View** — `2d` the plan · `3d` isometric · `rotate y <deg>` ·
`rotate x <deg>` · `zoom in|out|reset` · `color on|off`

**Files** — `save [name]` (`build.rust`) · `load [name]` ·
`new [w] [h]` · `help` · `quit`

## Layout

```
rustbuild.py
│
├─ class Editor          the whole state
│     base[(level,x,y)]  what is on a tile: sq, tri, floor, stairs, roof
│     edges[...]         what is on a tile's EDGE: wall, door, window, low
│     cx, cy, level      where the cursor is, and which floor
│
├─ render_2d(ed)         the plan, looking down
├─ collect_edges(ed)     every piece turned into 3D lines
├─ render_3d(ed, cw, ch) those lines, projected isometric
├─ colorize(line)        ANSI colour, skipped when not a terminal
├─ show(ed)              draws whichever view is on
│
├─ place_base(ed, code)  put a piece under the cursor
│                        `f` means foundation at level 0, floor above
├─ do_cmd(ed, line)      one typed line
├─ save_build / load_build   JSON, next to the script
└─ main()                read a line, do it, draw
```

**Tiles and edges are kept apart**, which is the design worth noticing:
a wall belongs to the *boundary between* two tiles, not to a tile. That
is why `del` can take a floor out and leave its walls standing.

## It overlaps two other things here, and nothing joins them

| | Also does |
|---|---|
| `house/house.sh` | Builds in ASCII, with a 3D wireframe, shared over GitHub |
| `parts/screen.py` | XYZ shapes, rotation matrices, projection to a grid |

Three separate pieces of isometric-3D code in one repository. That is a
decision waiting to be made, not a fault — but it is worth knowing
before writing a fourth.
