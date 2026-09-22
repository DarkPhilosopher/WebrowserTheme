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

**90 blocks.** `parts.describe()` prints them all; `parts.describe("Ray")`
explains one.

---

## core — works on any value

**Links** `Chain` `Fan` `Each` `Keep` `Drop` `Gate` `Try`

`Fan(branches, how=)` runs several chains on one input and combines them —
`"sum" "max" "min" "mul" "all" "any" "list" "first"`. Use `"all"` for AND,
`"any"` for OR.

**Sources** `Const` `Var` `Osc`

**Numbers** `Gain` `Bias` `Invert` `Clamp` `Threshold` `Smooth` `Delay`
`Integrate` `Derive` `PID`

**Text** `Lower` `Upper` `Strip` `Split` `Join` `Replace` `Contains`
`Match` `Grab` `Text`

**Lists** `Count` `First` `Last` `Sort` `Uniq` `Flatten` `Field`

**Sinks** `Say` `Put` `Do`

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
