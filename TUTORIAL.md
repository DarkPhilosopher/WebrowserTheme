<!-- header -->
```
+----------------------------------------------------------------+
| WAKEUP · TUTORIAL                                              |
+----------------------------------------------------------------+
| what       Spark blocks from one pixel to a turning shape: the |
|            matrix, formations, extent in 3D, scaling and       |
|            angle, and numbers that watch and send              |
| since      2026-10-04                                          |
| changed    2026-10-04                                          |
+----------------------------------------------------------------+
```
<!-- /header -->

# Tutorial — Spark blocks, from one pixel to a turning shape

Everything here was run before it was written. Every program is in
`sparkblocks/examples/` and `python3 -m sparkblocks check` parses all
of them, so none of this can quietly rot.

On a phone:

```bash
cd ~/wakeup
python3 -m sparkblocks run sparkblocks/examples/t1-one-pixel.spark
```

---

## 1. The one idea

A program is **blocks in a line**, one per line. A value falls down
the line, and each block does something to it.

```
const 6
gain 7
say
```

→ `42`. That is the whole language. `const` makes a number, `gain`
multiplies, `say` prints.

**Controls.** A setting after the name is positional; `name=value`
is by name. Quote anything with a space.

```
gain 7                 the first setting
light 3 1 at=0.5       two positional, one named
```

`#` starts a comment. Indentation gives a block something to hold.

```bash
python3 -m sparkblocks            every block there is
python3 -m sparkblocks Gain       what one block does
python3 -m sparkblocks run f.spark --show    build it, do not run it
python3 -m sparkblocks run f.spark --loop    run it over and over
```

---

## 2. Turning a pixel on and off

`t1-one-pixel.spark`

```
screen 8 4
const 1
light 3 1
draw
```

```
................
......##........
................
................
```

`screen 8 4` makes the matrix. `light 3 1` turns on the pixel at
column 3, row 1 — **when the number coming down the line is over the
line** (0.5 unless you say otherwise). Change `const 1` to `const 0`
and it goes off instead.

So a pixel is not switched. It is **told a number**, and decides.

| | |
|---|---|
| `light x y at=` | on when the number is over the line |
| `dark x y at=` | the other way round |
| `fill` | every pixel at once, from one number |
| `lit x y` | is that one on? |
| `lights` | how many are on |
| `clear` | all off |
| `wipe` | blank the terminal, once, before a moving picture |

---

## 3. How many pixels you actually have

**Not phone pixels.** A terminal gives you *character cells*, and
Wakeup makes each pixel **two characters wide** so it looks square.
How many you get depends on your font size, not on the phone.

```bash
python3 -c "import os;c,r=os.get_terminal_size();print(c//2,'x',r-2)"
```

That is your exact matrix for `screen fit`. Make the Termux font
smaller and you get more. There is no way to address a phone pixel
from a terminal — that is what the browser panel is for, and the
wish below.

---

## 4. A formation: many pixels at once, by location

`t2-formation.spark`

```
screen 12 6

fan list
    - dot 2 1
    - dot 3 1
    - dot 4 1
    - dot 3 2
    - dot 3 3

flatten
plot
draw
```

```
............
..######....
....##......
....##......
............
```

A **T**, placed as a group. `fan list` runs every branch on the same
input and collects the answers. Each `dot x y` is one point.
**`plot` lights whichever pixel each point lands on** — you never
name a pixel, you say where things are.

**`flatten` matters.** Every branch hands back a *list* of points, so
the fan collects a list of lists. Without `flatten` nothing draws, and
nothing warns you.

---

## 5. Extent in 3D — location decides the pixels

`t3-extent-3d.spark`

```
screen fit
box 4 3 2
spin y 30
spin x 20
flat
plot
draw
```

`box 4 3 2` is **not a picture**. It is an extent — 4 wide, 3 high, 2
deep — handed over as points in space.

| | |
|---|---|
| `dot x y z` | one point |
| `box w h d gap=` | the twelve edges of a box |
| `ball r` | points over the surface of a ball |
| `flat zoom= near=` | drops xyz onto the grid. `near 0` removes perspective |
| `plot` | lights the pixel each point lands on |

This is the answer to *decide pixels by location*: give the extent,
and `flat` + `plot` work out the rest.

---

## 6. Scaling, and angle

`t4-scale-and-angle.spark`

```
tick angle by=6 wrap=360
screen fit
box 3 3 3
grow 1.5
spin y var=angle
flat
plot
draw
```

Run it with `--loop` and it turns by itself.

| | |
|---|---|
| `grow 2` | the scaling matrix. `grow 0.5 2 1` stretches one axis |
| `shift x y z` | the translation matrix |
| `spin y 40` | the rotation matrix, forty degrees |
| `spin y var=angle` | **the angle comes from a variable** |

That last one is the hinge. Anything that writes `angle` changes the
picture — a tick, a reading, a distance. The shape does not know or
care which.

---

## 7. Reserved numbers that watch, and send

`t5-watcher.spark`

```
put hp 4

const -5
gate
    var hp
    threshold 5 above=0 below=1

fan list
    - put ally1
    - put ally2
    - put ally3

var ally2
say
```

→ `-5`. Change `put hp 4` to `put hp 9` and it prints `None` —
nothing was sent, because the gate is shut.

| | |
|---|---|
| `put name value` | reserve a number under a name |
| `var name` | read it back |
| `threshold 5 above=0 below=1` | 1 when 5 or below, 0 when above |
| `gate` | let the rest through only while what it holds is true |
| `fan list` | send the same value to every target at once |

**When hp drops to 5 or below, send −5 to each of three targets.**
That is the shape of the idea, working today.

What is **not** here yet: targets chosen by *classification* or
*faction* rather than by name. Today you name each one. Picking out
"every ally within range, but not enemies" needs a register of
entities that does not exist. It is an empty box — see below.

---

## 8. Your own formation, as a block

A formation you use twice should be a block. You do not edit this
folder to add one — **make a folder, and that is the consent**:

```bash
mkdir -p ~/.sparkblocks
```

`~/.sparkblocks/mine.py`:

```python
from sparkblocks.screen import Shape


class Tee(Shape):
    """A T, three across and three down."""
    fits = {"changes": "nothing"}

    def __init__(self, size=3):
        self.size = int(size)

    def points(self):
        n = self.size
        across = [(x, 0, 0) for x in range(n)]
        down = [(n // 2, y, 0) for y in range(1, n)]
        return across + down
```

Now `tee` is a block like any other:

```
screen 12 6
tee 5
plot
draw
```

```bash
python3 -m sparkblocks outside     what is loaded, and from where
```

A name this folder already uses is **refused, loudly** — never
quietly swapped, because then a program would mean different things
on different machines.

---

## 9. Where things go — redirections

| | |
|---|---|
| `say` | print it |
| `put name` | into a named number |
| `write path` | into a file |
| `draw` | onto the screen |
| `do` | run a shell command with it |

A program with no sink still runs; `run` prints the last value so you
can see what came out.

Saved programs get a tag line and live in `~/.wakeup/programs`, found
wherever they end up:

```bash
python3 -m sparkblocks saves
```

---

## 10. Wishes, written down rather than implied

None of these exist. They are in `BOXES.md` so they are decisions,
not vague intentions.

| | |
|---|---|
| **The same program, graphical, in a browser** | His wish, noted. Real phone pixels instead of character cells, and the same blocks behind it. `panel/panel.html` is the start that exists |
| **Auto-render in 3D** | Today you write `flat` and `plot` yourself. A shape should be able to draw itself each frame without being told |
| **Targets by classification and faction** | Section 7 names each target. Choosing by *what something is* needs a register of entities |
| **ASC, the 16×16 grid** | A separate repository of his. `screen 16 16` is the same shape, and a bridge is worth considering — **but only if he says so.** `spark` and Spark blocks are deliberately separate, and this is near that line |

<!-- footer -->
```
--- signed ------------------------------------------------------
  Gabriel Lewis            DarkPhilosopher
                           lewisgabe33@gmail.com  (git)
                           xzg4b3xz@gmail.com    (drive)
                           on A33

  Claude Opus 5            claude-opus-5
                           of xzg4b3xz@gmail.com
                           on cloud container

--- chronology --------------------------------------------------
  2026-10-04 13:37 MDT written                  Claude Opus 5
                                                on cloud container
-----------------------------------------------------------------
```
<!-- /footer -->
