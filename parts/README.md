# parts — one small language of interchangeable blocks

Not `when X do Y`. This is the other way: a **signal running down a chain**,
the way a wire runs from a sensor, through some electronics, into a motor.

```python
from parts import *

Chain([Walk("~/notes"), Keep(Ext(".md")), Count(), Say()])
```

Python standard library only. No installs, no threads, no 64-bit
requirement — runs on a 32-bit phone.

## The one contract

Every block is an object with exactly this:

```python
part.step(ctx) -> value
```

`ctx.value` is the signal. It may be a **number, text, a path, a list, or
a dict** — whatever the block before it returned. That single rule is the
whole language, and it is why any block fits any slot.

A `Chain` is itself a block, so chains nest without limit.

## Four kinds

| Kind | Shape | Role |
|---|---|---|
| **Source** | → value | Ignores its input (a sensor) |
| **Conduit** | value → value | The glue |
| **Sink** | value → effect | Ignores its output (a motor) |
| **Link** | holds blocks | `Chain` `Fan` `Each` `Keep` |

## Four modules, one tongue

```python
from parts import *                      # everything
from parts.files import Walk, Copy       # or be exact
```

| Module | Covers |
|---|---|
| `core` | The contract, and blocks that work on any value |
| `space` | A 3D world: bodies, sensors, motors |
| `files` | Folders, files, copying and moving |
| `net` | Other machines: fetching, reaching, downloading |
| `screen` | A grid of pixels, shapes in 3D, and touch |
| `pad` | The window as eight squares you press |

**119 blocks.** `parts.describe()` prints them all; `parts.describe("Ray")`
explains one.

---

## core — works on any value

**Links** `Chain` `Fan` `Each` `Keep` `Drop` `Gate` `Try`

`Fan(branches, how=)` runs several chains on one input and combines them —
`"sum" "max" "min" "mul" "all" "any" "list" "first"`. Use `"all"` for AND,
`"any"` for OR.

**Sources** `Const` `Var` `Osc`

**Numbers** `Gain` `Bias` `Invert` `Minus` `Abs` `Is` `Clamp` `Threshold` `Smooth` `Delay`
`Integrate` `Derive` `PID`

**Text** `Lower` `Upper` `Strip` `Split` `Join` `Replace` `Contains`
`Match` `Grab` `Text`

**Lists** `Count` `First` `Last` `Sort` `Uniq` `Flatten` `Field` `Pack`

**Sinks** `Say` `Put` `Tick` `Do`

`Say` is the debugger of this language — drop it anywhere in a chain to
see what is passing through.

## space — a 3D world

**Properties.** On a body: `pos` `vel` `yaw` `pitch` `spin` `mass` `drag`
`radius` `solid` `alive` `tags` `store` `parts` `force`. On the world:
`gravity` `bounds` `time` `bodies` `store`.

**Sensors** `Clock` `Height` `Speed` `Heading` `Level` `Near` `Touch`
`Ray` `Bearing`

**Motors** `Thrust` `Lift` `Turn` `Tilt` `Store` `Drain` `Spawn` `Expire` `Die`

`Ray` is the rangefinder. `Bearing` is the steering sensor — 0 means dead
ahead, ±π directly behind.

## files — folders and files

Every block takes its path **either as an argument or from the signal**,
which is what lets them sit anywhere in a line:

```python
Chain([Const("~/notes"), Walk(), Keep(Ext(".md"))])
Chain([Walk("~/notes"),  Keep(Ext(".md"))])        # identical
```

**Where** `Here` `Home` `Parent` `Name` `Ext`
**Look** `Ls` `Walk` `Glob` `Exists` `IsDir` `IsFile` `Size` `Age`
**Read** `Read` `Lines`
**Change** `MakeDir` `Make` `Write` `Copy` `Move` `Rename` `Remove`

`Walk` skips `.git`, `node_modules`, `__pycache__`, `.cache`, `.venv` by
default. `Age` is in days. `Remove` deletes files freely but needs
`folders=True` before it will delete a tree — that is the one mistake you
cannot undo.

## net — other machines

**Ask** `Fetch` `Status` `Reach` `Address` `Mine`
**Read** `Json` `Links` `Host`
**Put** `Send` `Download`

Nothing here raises. A dead link gives `""`, an unreachable host gives
`False`, a bad URL gives `0` — so one broken address never stops a run
over a thousand of them.

---

## Worked examples

**Every markdown file that mentions a word**
```python
run(Chain([
    Walk("~/notes"),
    Keep(Ext(".md")),
    Keep(Chain([Read(), Contains("spark")])),
    Say("found"),
]))
```

**Copy them somewhere, then write an index**
```python
run(Chain([
    Walk("~/notes"), Keep(Ext(".md")),
    Keep(Chain([Read(), Contains("spark")])),
    Put("hits"), Copy(into="~/out"),
    Var("hits"), Each(Name()), Join("\n"), Write("~/out/index.txt"),
]))
```

**Everything on the phone bigger than 100 MB**
```python
run(Chain([
    Walk("/sdcard"),
    Keep(Chain([Size(), Threshold(100_000_000)])),
    Say("big"),
]))
```

**Pull every link off a page and download the PDFs**
```python
run(Chain([
    Fetch("https://example.com/papers"),
    Links(base="https://example.com/papers"),
    Keep(Match(r"\.pdf$")),
    Download(into="~/papers"),
    Say("saved"),
]))
```

**A creature, in the 3D world**
```python
hunter.parts = [
    Chain([Bearing("prey"), PID(p=2.0, d=0.1), Clamp(-2, 2), Turn()]),
    Chain([Ray(reach=12), Gain(1/12), Clamp(0.15, 1), Gain(4), Thrust()]),
    Chain([Near(radius=10, tag="prey"), Invert(), Bias(10), Threshold(0.5),
           Spawn(bullet, speed=14, cooldown=0.3)]),
]
```

Three chains, each independent. Delete one and the rest still work.

## Putting it anywhere

Keep the folder wherever you like — Downloads, a memory card, anywhere —
and run this once:

```bash
python3 /wherever/parts/install.py
```

`import parts` then works from **any folder, in any script**, with nothing
copied and no `PYTHONPATH` to remember. It writes a one-line `.pth` file
into Python's site-packages naming the folder; Python reads those at
startup. Move the folder later and run it again.

```bash
python3 -m parts where      # is it installed, and pointing where?
python3 -m parts install    # same as install.py
python3 /wherever/parts/install.py --remove
```

Without installing, these still work:

```bash
python3 /wherever/parts/connect.py spark /sdcard   # point at the file
cd /the/folder/holding/parts && python3 -m parts connect spark
```

## Changing it later

Run this after changing anything:

```bash
python3 -m parts check
```

```
ok   the one contract             123 checked
ok   names do not clash           123 checked
ok   all blocks reachable         119 checked
ok   all blocks described         123 checked
ok   the text format knows them   123 checked
ok   the examples still parse      10 checked
ok   things actually work           7 checked

628 checked, all well -- 119 blocks
```

It is not a test of clever behaviour. It checks the rules the language
quietly depends on — the ones that break without saying anything:

| Check | Catches |
|---|---|
| **the one contract** | A block whose `step()` cannot be called — including one shadowed by a setting of the same name |
| **names do not clash** | Two blocks sharing a lower-case name, which the text format cannot tell apart |
| **all blocks reachable** | A block in a catalogue that nobody exported from `__init__` |
| **all blocks described** | A block the menus would show as "no description" |
| **the text format knows them** | A block that cannot be named in a `.parts` program |
| **the examples still parse** | An example that stopped working |
| **things actually work** | Seven real behaviours, end to end |

A failure names the block and the rule, so you know what to change:

```
FAIL all blocks described        123 checked
       core.Sort: has no description
       files.IsDir: has no description
```

Every one of these catches a mistake that was actually made while
building this. `Box` once stored its spacing as `self.step` and shadowed
the method every block must have; `Count`, `Move`, `Size` and `Strip`
each collided with a name already taken. The check finds both in a
second.

### Adding your own block

Subclass `Part`, give it a sentence, override `step`:

```python
class Newer(Part):
    """Keep only paths changed in the last few days."""
    def __init__(self, days=7): self.days = days
    def step(self, ctx):
        return Age().step(ctx) < self.days
```

Then three things, and `check` will tell you if you miss one:

1. Add it to its module's `CATALOGUE`, under a kind.
2. Export it from `parts/__init__.py`.
3. Make sure its name is not already taken.

It is then usable everywhere every other block is — in Python, in a
`.parts` file, in the numbered menu, and on the pad.

**One rule worth knowing:** never store a setting called `step`. It
would shadow the `step()` method and the block would break at run time
rather than when you wrote it. `Box` takes `gap` and `Ray` takes `step`
but keeps it as `self.stride` for exactly this reason.

## The command line

```bash
python3 -m parts                  # every block, by module and kind
python3 -m parts Ray              # explain one block
python3 -m parts connect <thing>  # find what touches a thing
python3 -m parts install          # make import work anywhere
python3 -m parts run prog.parts   # run a plain-text program
python3 -m parts menu             # build one with numbers only
python3 -m parts pad              # build one by pressing squares
python3 -m parts check            # make sure it all still hangs together
```

## pad — the window as eight squares you press

```bash
python3 -m parts pad
```

The window is divided into a strip across the top and eight squares
below it, sized to whatever window Termux gives them:

```
 parts -- press a square
 1. walk /sdcard


+-1----------------++-2----------------+
|                  ||                  |
|   add a block    ||   change lines   |
|                  ||                  |
+------------------++------------------+
+-3----------------++-4----------------+
|                  ||                  |
|      run it      ||       save       |
|                  ||                  |
+------------------++------------------+
+-5----------------++-6----------------+
|                  ||                  |
|       open       ||    see it all    |
|                  ||                  |
+------------------++------------------+
+-7----------------++-8----------------+
|                  ||                  |
|       more       ||       back       |
|                  ||                  |
+------------------++------------------+
```

**Eight squares, because that is the same rule the numbered menu keeps:**
never more than eight choices, the last always goes back, and a longer
list turns the seventh into `more`. The pad is that menu with the numbers
replaced by places to press.

**The strip is the top two squares joined.** It is where the program
speaks — the question being asked, and the last lines of what you have
built. When a block needs a setting typed, the pad steps aside and you
type at the ordinary Termux prompt, then it redraws.

Press squares to walk module → kind → block, and the block joins your
program. Save it and it is an ordinary `.parts` file: the pad, the
numbered menu and the text file are three views of one thing.

### The pad is made of blocks

Nothing about it is special. A program can lay out its own:

```
pad
banner "press a square"
button 1 "find files"
button 2 "spin a cube"
button 8 "back"
press
say "you pressed"
```

| Block | Does |
|---|---|
| `Pad` | Divide the window into squares and clear it |
| `Button` | Draw one square, with words in it |
| `Banner` | Write into the strip across the top |
| `Press` | Wait for a square to be pressed; answers its number |

`pad 2 4` sets how many across and down; `pad 3 4 strip=1` gives twelve
squares instead of eight. `button 3 "" on=true` fills a square in, so it
can show something being on as well as being pressable.

**Touch, with a way out.** `press` reads the terminal's own touch
reporting. Where that is not available it takes a typed digit instead, so
the same program works either way — and with no terminal at all it
answers `None` rather than hanging.

## screen — pixels, shapes, and touch

A grid of pixels you can light from a number, shapes in XYZ, and touch.

### A number turning a pixel on

This is the point of the module, and it is three lines:

```
screen 12 6
put hot 0.8

var hot
light 2 2 at=0.5
light 4 2 at=0.9
meter 0 4 10 most=1.0
draw
```

```
........................
........................
....##..................       hot is 0.8
........................       so the 0.5 pixel is ON
################........       and the 0.9 pixel is OFF
........................       and the meter is 80% full
```

Change `0.8` to `0.3` and both pixels go out and the bar shrinks. The
number keeps travelling down the chain, so **one number can drive any
number of pixels, each at its own threshold**. That number can come from
anywhere in the language — a file's size, a sensor in the 3D world, a
reading off the network.

### The blocks

| Group | Blocks |
|---|---|
| **screen** | `Screen` `Draw` `Clear` `Wipe` |
| **pixels** | `Light` `Dark` `Meter` `Fill` `Lit` `Lights` |
| **shapes** | `Dot` `Box` `Ball` |
| **matrix** | `Spin` `Shift` `Grow` `Flat` `Plot` |
| **touch** | `Tap` `Spot` |

`screen fit` makes the grid as big as the terminal window. Each pixel
draws two characters wide, because a character is taller than it is wide
— two side by side come out square.

### Shapes and the XYZ matrices

```
screen 24 12
box 3 3 3
spin y 35
spin x 20
flat
plot
draw
```

```
......................########..................
..................######..######................
..............######......##..####..............
..............######......##....##..............
..............##..################..............
..............##......######......##............
..............##......##..##......##............
..............##......##..##......##............
............##........##..##......##............
............##..####################............
............########################............
```

A shape is a list of XYZ points. `spin` `shift` `grow` are the rotation,
translation and scaling matrices — they turn the points. `flat` drops
them onto the grid (with perspective; `flat near=0` for none). `plot`
lights whatever pixels they land on.

### Making it move

`tick` counts up in a variable, `spin ... var=` reads it, and `--loop`
runs the program over and over:

```
tick angle by=12 wrap=360
screen fit
box 3 3 3
spin y var=angle
flat
plot
draw
```

```bash
python3 -m parts run spin-a-cube.parts --loop
python3 -m parts run spin-a-cube.parts --loop 50 --fps 20
```

One run of the loop remembers the last, so `tick`, `smooth`, `delay` and
`integrate` all carry on where they left off. Ctrl-c stops it.

### Touch

`tap` waits for a touch and answers `{"x": .., "y": ..}` — the pixel you
touched. `spot` lights the pixel the signal names. Together they are a
painting program:

```
screen fit
tap
spot
draw
```

Touch is read straight from the terminal, so it works in Termux itself
but not through a pipe. Where there is no terminal, `tap` answers `None`
at once rather than hanging.

### Locking the screen upright

**A program cannot do this** — screen rotation is an Android setting, not
something Python can reach. Set it once, by hand:

- **Android:** open quick settings and turn **auto-rotate off** while the
  phone is upright.
- **Termux:** Settings → Terminal → **Orientation → portrait** pins
  Termux itself regardless of the system setting.

`screen fit` then measures whatever window it is given, so the grid fills
the area either way.

## The menu — building with numbers only

For a phone, where typing is the hard part:

```bash
python3 -m parts menu
python3 -m parts menu mine.parts     # start from a file
```

```
==============================================
 parts -- build with blocks
==============================================
 your program:
   1  walk /tmp/lab
   2  keep ext .md
   3  say found
----------------------------------------------
  1) add a block
  2) edit the lines
  3) run it
  4) see its shape
  5) save to a file
  6) open a file
  7) explain a block
  8) quit
 1-8:
```

**Never more than eight options, and the last always goes back.** When a
list is longer than fits, the seventh becomes `more...` so the count on
screen never changes:

```
 core / number  (1 of 3)
----------------------------------------------
  1) Gain
  2) Bias
  3) Invert
  4) Minus
  5) Abs
  6) Is
  7) more...
  8) back
```

You walk module → kind → block, and only type when a block wants a
setting. The screen always shows the program as it stands, so you can see
what you are connecting to what.

**The menu and the text are two views of one thing.** What you build here
saves as an ordinary `.parts` file, which you can then edit by hand, run
from the command line, and open in the menu again:

```bash
python3 -m parts menu              # build it with numbers
python3 -m parts run mine.parts    # run what it saved
```

Two things the menu will not do, because one line cannot say them: a
holder is never offered another holder, and `fan` can only be added as
`fan all` — indent its `- ` branches underneath in a text editor.

## Writing a program as plain text

A program can be a plain text file, one block a line — no brackets, no
commas, no Python. Edit it in any text editor.

```
# every markdown file on the phone that talks about spark
walk /sdcard
keep ext .md
keep
    read
    contains spark
say found
```

```bash
python3 -m parts run find-notes.parts
python3 -m parts run find-notes.parts --show    # print the shape, run nothing
```

### The rules, all of them

1. A line is `blockname setting setting`.
2. Blank lines are ignored. Anything after `#` is a note to yourself.
3. A block that holds another — `keep` `drop` `each` `gate` `try` — takes
   it on the same line, or indented underneath:

   ```
   keep ext .md                 # same line, one block
   keep                         # indented, a whole chain
       read
       contains spark
   ```

4. `fan` holds branches, each marked `-`, and combines them with
   `all` `any` `sum` `max` `min` `mul` `list`:

   ```
   fan any
       - read
         contains spark
       - name
         contains engine
   ```

5. Numbers become numbers; `true`, `false` and `none` become themselves.
6. `name=value` sets a setting by name: `copy into=~/out`.
7. Quotes only group words. **A backslash is left alone**, so
   `match \.pdf$` reaches the regex intact — except inside quotes, where
   `\n` and `\t` mean what they look like: `join "\n"`.

Every block in the language works, under its own name in lower case.

### When you get it wrong

The error names the line and, for a misspelling, what you probably meant:

```
line 3: there is no block called 'saay'.
  Did you mean: say

line 2: keep needs a block to hold, either after it or indented under it

line 2: threshold does not take those settings (takes from 1 to 4
  positional arguments but 6 were given).
  Try: python3 -m parts Threshold
```

### Examples to start from

`parts/examples/` holds six working programs — copy one and change the
paths:

| File | Does |
|---|---|
| `find-notes.parts` | Markdown files that mention a word |
| `big-files.parts` | Everything over 100 MB |
| `tidy-pdfs.parts` | Gather scattered PDFs into one folder |
| `index.parts` | Write a list of your notes to a file |
| `page-links.parts` | Pull every PDF linked from a web page |
| `recent-work.parts` | Anything touched in the last two days |

## connect — a script written in this language

```bash
python3 -m parts.connect spark                # a word
python3 -m parts.connect ~/notes/plan.md      # a file
python3 -m parts.connect spark /sdcard        # say where to look
python3 -m parts.connect spark ~ --strict     # only 2+ routes agreeing
python3 -m parts.connect --help               # list the routes
```

Give it a thing. It walks every folder below `where` and asks the same
question of each file along **ten different routes at once**. Every route
that answers yes is one point; results come back ranked by how many routes
agreed.

| Route | Says yes when |
|---|---|
| `name` | Its filename carries the word |
| `mentions` | Its text says the word |
| `backlink` | Its text names the thing's own file |
| `linked` | The thing's text names this file |
| `sibling` | It sits in the same folder |
| `kind` | It is the same sort of file |
| `when` | It changed within a day of the thing |
| `words` | It shares uncommon words with the thing |
| `addresses` | It points at an address the thing also points at |
| `git` | It was committed alongside the thing |

`git` is the strongest of them. Two files edited in the same commit were,
by someone's judgement at the time, **one change** — that beats any amount
of guessing from names. It reads real history (`git log` on the file, then
`git diff-tree` on each commit) and quietly returns nothing outside a
repository.

### A route that matches everything is ignored

After a fresh clone every file has the same timestamp, so `when` answers
yes to all of them. In a folder of notes, `kind` does the same. A route
like that carries no information, so **any route matching more than half
of what it looked at stops counting** — it still shows, in brackets, but
its votes do not score.

```
  3  tiles.md  mentions sibling words (kind) (when)
  1  diary.md  sibling (kind) (when)

  not counted (matched nearly everything): kind 100%, when 100%
```

Without that rule the same search returns three unrelated files scoring 2
apiece on nothing but `kind` and `when`. Pass `common=1.0` to let every
route vote regardless.

```
connections to 'parts/files.py' (file), looking under ~/WebrowserTheme

  5  README.md    mentions backlink sibling when git (words) (addresses)
  5  __init__.py  mentions sibling kind when git (words) (addresses)
  4  connect.py   mentions sibling kind when (words) (addresses)
  1  house.sh     mentions (words) (addresses)
```

**Each route is one chain in the `ROUTES` list**, and that is the whole
design:

```python
("sibling",
 "it sits in the same folder",
 Chain([Field("folder"), Is(Var("folder"))])),

("when",
 "it changed within a day of the thing",
 Chain([Field("age"), Minus(Var("age")), Abs(),
        Threshold(1.0, above=0, below=1)])),
```

Delete a line and that route stops being consulted. Reorder them and
nothing breaks. Write a new one out of any blocks in the language and it
joins the vote — nothing else in the file has to know it exists. Or pass
your own list in:

```python
from parts.connect import connect, ROUTES
only = [r for r in ROUTES if r[0] in ("name", "addresses")]
connect("spark", "~/notes", routes=only)
```

The means of connection are data, not code.

`connect.py` adds four blocks of its own — `Words`, `Urls`, `Shared` and
`Among` — because comparing two bags of things is its own question.
Everything else in it comes straight out of the language.

## Rearranging

Editing behaviour means reordering names in a list. Nothing else changes,
because every block has the same shape.

- Swap `Thrust()` for `Lift()` — it climbs instead of advancing.
- Drop `Clamp` — it stalls against walls.
- Put `Smooth(0.2)` anywhere in the line — the whole thing gets less twitchy.
- Swap `Expire(after=1.5)` for `Chain([Near(radius=0.5), Threshold(0.4), Die()])`
  — the shot dies on contact instead of on a timer.

The same conduits work in every domain. A `PID` does not care whether it
is steering a ship or pacing a download; `Keep` does not care whether it
is filtering bodies or filenames. That is the reason the language is
split the way it is.

## Adding your own

Subclass `Part`, override `step`. It is now usable everywhere every other
block is.

```python
class Newer(Part):
    """Keep only paths changed in the last n days."""
    def __init__(self, days=7): self.days = days
    def step(self, ctx):
        return Age().step(ctx) < self.days
```
