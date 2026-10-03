# Wakeup

Getting Claude running on your own machines, knowing which machine you
are on, and a language of blocks that works even where Claude will not.

Python standard library only. No installs, no 64-bit requirement — it
runs on a phone.

## Start here

```bash
pkg install python -y          # Termux
python3 claude-ready.py
```

| | |
|---|---|
| **`claude-ready.py`** | Checks everything Claude Code needs on a phone, in the order you hit it, and names the first thing you are stuck on. What is missing becomes a numbered menu — pick a number, nothing to type. It will tell you plainly when a phone **cannot** run Claude Code, rather than walking you through an install that was never going to work |
| **`whereami.py`** | Which machine is this? Claude has no memory between sessions and cannot see your screen, so it reads the signs a machine carries and matches them against a register. Two phones can look identical to every sign a program can read, so each one can also be named on itself: `whereami.py --name "A33"` |

## The control panels

Three ways in, so a broken one never blocks you.

```bash
python3 panel/panel.py          # Windows cmd, PowerShell, Termux, anything
```
Nothing but `print` and `input` — no colours, no mouse, no curses. Where
the fancier menus will not run, this will. Without the Python package it
still reads the catalogue, still builds and saves, and says plainly that
it cannot run anything here.

**`panel/panel.html`** — open it in Chrome. No server, no install. Eight
squares to press, or a terminal to type in, switchable at any time; and
it **runs the drawing blocks in the page**, so a cube really does spin.
Blocks that touch files or the network are marked and refuse by name.

All three read one catalogue written out of the Python, and
`python3 -m parts check` catches it if any copy falls behind.

See **[panel/README.md](panel/README.md)**.

## The block language

```bash
python3 parts/install.py       # so `import parts` works from anywhere
python3 -m parts               # every block there is
```

A signal running down a chain, the way a wire runs from a sensor,
through some electronics, into a motor. Every block has the same shape,
which is why any one fits any slot:

```python
part.step(ctx) -> value
```

119 blocks, across six modules: numbers, text and lists; a 3D world;
files and folders; the network; a screen of pixels; and the window as
eight squares you press.

A program can be plain text, one block a line, with no Python at all:

```
walk /sdcard
keep ext .md
keep
    read
    contains spark
say found
```

```bash
python3 -m parts run find-notes.parts   # run it
python3 -m parts menu                   # build one with numbers
python3 -m parts pad                    # build one by pressing squares
python3 -m parts check                  # is it all still sound
```

See **[parts/README.md](parts/README.md)** for the whole of it.

### What touches what

```bash
python3 -m parts connect spark /sdcard
```

Asks the same question of every file along ten routes at once — name,
contents, backlinks, neighbours, kind, timing, shared words, shared
addresses, and what git committed alongside it — then ranks by how many
routes agreed. A route that matches nearly everything stops counting,
because it is telling you nothing.

## The rest

| | |
|---|---|
| [`tfind.md`](tfind.md) | Search every file on the phone, from Termux |
| [`house/`](house/README.md) | Build one ASCII house together, from many phones, over a shared GitHub repo |
| [`ttt/`](ttt/README.md) | Tic-tac-toe between two phones, the same way |
