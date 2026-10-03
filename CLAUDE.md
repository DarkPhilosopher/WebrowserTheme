# CLAUDE.md

**This project is called Wakeup** — one word, with the `e`. The
repository it lives in is still named `WebrowserTheme`, from before it
had a name.

## Before anything else: know which machine you are on

**This is the highest-priority rule in this file.**

You have no memory between sessions and cannot see the screen. In one
earlier conversation you were told four separate times that you were on
a machine you were not on — a cloud container was mistaken for a Dell
laptop, then for a phone. Work was done against the wrong assumption.

So, at the start of any session where the machine matters:

```bash
python3 whereami.py
```

Then **say which machine you think it is, and wait for Gabriel to
agree.** Not as a formality — the answer changes what is possible:

**He has three machines and only three.** Anything else that turns up
is not his.

| Machine | What changes |
|---|---|
| cloud container | No reach to any of his machines. Say so plainly rather than offering workarounds |
| Dell i7 laptop | Modified, bought on Facebook Marketplace. Windows paths. Two profiles, `sauve` and `xzg4b`, on the one machine. Also has an `S:` drive |
| A33 | Samsung Galaxy A33, 64-bit. Usually the one he is on. Claude Code runs, but only inside `proot-distro ubuntu` |
| A17 | His other Android phone. Architecture not yet confirmed — run `whereami.py` there |

His 32-bit phone was a **Hotpepper ACP** and he has **disposed of it**,
so neither remaining phone has that limitation. The 32-bit entry stays
on the register because the warning is still true of any 32-bit phone.

The **Lenovo tower** on the register is a **friend's**, not his, and is
listed only to carry the reminder that he wants it removed. Ask before
removing it.

If `whereami.py` says the machine is not on the register, **ask**. Do
not pick the closest one and carry on.

### There is more than one phone

Gabriel has **three or more** Android devices. Two of them can be the
same architecture, both carry Termux, and look identical in every sign
a program can read — so the register alone will never tell them apart.

The cure is a name written on each machine, once:

```bash
python3 whereami.py --name "Revvl 7"
```

The two phones are the **A33** and the **A17**, and the signs alone
cannot tell them apart. That writes `~/.whereami`, and **a written name beats every
other sign**. When a machine has one, `whereami.py` reports it as fact rather
than as a guess. When a phone has no name yet, offer to name it.

### The session and the person are two different machines

The session usually runs in the cloud container. Gabriel is typing from
something else — a phone, or the Dell. `whereami.py` can only ever see
the first. **Which machine he is at is something only he can tell you,
so ask.** Most of the confusion in the earlier conversation came from
treating those two as one.

## Confirming before writing to the register

The register is the `REGISTER` list in `whereami.py`. Most entries are
marked `"sure": False` — they were written from what was said in
conversation, not from being run on the machine itself.

**Never change or remove an entry without asking first.** Say which
entry, what it says now, and what you want it to say. Adding a new
entry for a machine that matched nothing is fine to offer, but Gabriel
confirms the name before it is written.

`"sure": True` means Gabriel has confirmed that entry himself. Do not
set it because the entry looks right.

The same guard applies to `~/.whereami`. Renaming a machine that
already has a name requires `--force`, and the tool refuses without it
and says why — every earlier note about the old name would point at
nothing. Do not reach for `--force` on his behalf; ask.

## What is in this repository

| Folder | What it is |
|---|---|
| `parts/` | A language of interchangeable blocks. See `parts/README.md` |
| `house/` | Multiplayer ASCII house builder, over a shared GitHub repo |
| `ttt/` | Tic-tac-toe between two phones, over a shared GitHub repo |
| `tfind.sh` | File search for Termux on Android |
| `whereami.py` | Which machine am I on |
| `claude-ready.py` | Is this phone ready to run Claude in Termux, and if not, why |
| `tfind.md` | Documentation for `tfind.sh` — it used to be the root README |
| `panel/` | Three control panels: plain terminal, browser, and the fancier ones in `parts` |
| `INDEX.md` | Every piece: where it belongs, what it is for, what it runs on, and what is not built yet |
| `rustbuild/` | **Gabriel's, not mine.** A Rust-style ASCII construction editor, here before this work |

Gabriel also has `DarkPhilosopher/spark` (a game engine, `when`/`do`
rules) and `DarkPhilosopher/ASC` (a 16×16 ASCII grid). **`spark` and
`parts` are deliberately separate languages.** He has said so directly.
Do not propose bridging them.

## Working on `parts/`

Run this after any change:

```bash
python3 -m parts check
```

It checks the rules the language quietly depends on — including that
`panel/catalogue.json` and the copy baked into `panel/panel.html` still
match the blocks. **After adding or renaming a block, rerun both:**

```bash
python3 -m parts json panel/catalogue.json
python3 -m parts json --html
```
 `parts/README.md`
explains the three steps for adding a block, and the one rule worth
knowing: never store a setting called `step`, because it shadows the
method every block must have.

## The rule everything here follows

**Make everything out of parts, and make every part able to join any
other part by the same hand.** Not a philosophy — the way a body runs
its organs together. Organs are not interchangeable, but they all speak
the same few things: blood, nerve, hormone. That is why one can be put
into a different body.

So: do not make everything the same. **Make everything speak the same
few things.**

### A part fails for what it is, never for where it was plugged in

A valve that will not fit because the port is in the wrong place is a
fault of the *system*, not the valve.

Here, one contract means a block can never fail to **fit** — only to
**do**. And every block carries a **datasheet** saying what it needs,
so nothing that holds blocks has to guess:

```python
class Run(Doing):
    """Run a command and hand on what it said."""
    fits = {"needs": ["shell"], "changes": "anything", "waits": True}
```

`needs` is from `shell files network world body grid terminal touch
person`. `changes` is `nothing vars files DELETES world screen network
anything`. A module states what is usual; a block states only what
differs.

**Nothing may keep its own list of what works where.** The browser
panel used to, and it was wrong the moment a block was added. It now
reads the datasheets, and tells two failures apart: *this needs files,
which a browser does not have* versus *this page has not learnt it yet*.

### When you add anything

1. Does it have **one way in**, the same as everything else?
2. Does it **say what it needs**, so nothing must guess?
3. If two things share a shape, is the shape **written once**?
4. Is there a **manual with a layout map**?
5. Is it in **`INDEX.md`** and boxed in **`BOXES.md`** — and if it is
   missing, is there an **empty box** saying where it belongs?

`python3 -m parts check` enforces 1, 2 and 3. You have to do 4 and 5.

## How he wants programs built

**A launcher opens a terminal first, and the big picture mode from
there.** This is a standing preference for everything he makes, not
just this project. The terminal is the thing that always works; the
graphical mode is reached from inside it, never instead of it.

`panel/panel.py` is the shape to copy: it runs anywhere a prompt does,
and carries *open the browser panel* as one of its own choices.

Three consequences worth keeping:

- **Never make the graphical way the only way.** If the colours, the
  mouse or the browser are missing, the terminal still does the job.
- **Degrade, do not fail.** `panel.py` without the Python package still
  reads its catalogue, still builds, still saves — and says plainly
  that it cannot run anything here.
- **Eight choices at most, the last always back.** This holds in the
  numbered menu, the touch pad, the plain panel and the browser squares.
  It is the one interface rule the whole project keeps.

## Before changing something that looks wrong

`INDEX.md` section 7 lists every place this project departs from common
practice **and why**. No dependencies, no pytest, nothing that raises,
eight choices everywhere, the repo name not matching the project — all
deliberate. Read it before "fixing" one of them.

## Waiting on Gabriel

Things only he can do, which other work is held back by. Written here
so a session asks rather than stalling quietly. Full detail in
`BOXES.md`.

| | Blocks |
|---|---|
| **Make the repo private** | `ABOUT.md` and `wakeup-notes/` both wait on it |
| **Name each phone** — `whereami.py --name "A33"` | `whereami.py` cannot tell the A33 from the A17 |
| **Run `whereami.py --facts` on the A17** | Its entry says `sure: False` until then |
| **Run `python3 -m parts pad` on a real phone** | Touch has never been tried. The whole pad rests on it |
| **Decide about the three 3D engines** | Two of the three are his and predate this work |
| **Name his fourth public repository** | GitHub says 4; only 3 are known |

## He wants to draw this

A chart and visual depictions of the whole idea — the fundamentals and
what is interesting about them — **for making machines with the best
searching engines.** That is what the rest is building toward.

The written material is there already: `INDEX.md`, `BOXES.md`, and the
layout map in every manual. Nothing is drawn yet. **Remind him**, and
offer to help turn the maps into a diagram when he comes to it.

## Notes worth keeping

- **`spark` and `parts` stay separate languages.** He has said so
  twice. Do not propose bridging them.
- **He was right and I was wrong about the 32-bit build.** The answer
  was in the npm package metadata, not in memory. When he pushes back
  on a limit, go and check.
- **His Google Drive connector is `xzg4b3xz@gmail.com`**, which is not
  the address his git commits use (`lewisgabe33@gmail.com`). Two
  accounts. `xzg4b` is also the second Windows profile on the Dell.
- **The repository is public.** He asked for personal details to be
  written into it and confirmed after being told; a safety classifier
  refused the push. That file is `ABOUT.md` and is **not** committed.
  It goes in only if he makes the repository private.

## How Gabriel works

- He is often on a phone, where typing is slow. Keep commands short and
  paste-able, one per line.
- Say plainly when something cannot be done, and why. Do not offer a
  workaround that does not work — he will try it.
- When he pushes back on a limit, check it properly rather than
  repeating yourself. He was right about the 32-bit build; the answer
  was in the package metadata, not in memory.
- Build things a young child could use. Plain words over jargon, in the
  code and out of it.
