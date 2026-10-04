<!-- header -->
```
+----------------------------------------------------------------+
| WAKEUP · START HERE                                            |
+----------------------------------------------------------------+
| what       Four ways in — automatic, quick, in order, and how  |
|            to choose between them — and where your own things  |
|            live                                                |
| since      2026-10-04                                          |
| changed    2026-10-04                                          |
+----------------------------------------------------------------+
```
<!-- /header -->

# Start here

Four ways in, depending on how much you want to be asked. They all
end in the same place.

---

## The automatic one — nothing to decide

Paste this into Termux on the phone:

```bash
pkg i -y git && git clone -b get https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup && sh ~/wakeup/get.sh && python3 ~/wakeup/wizard.py --auto
```

It installs everything this machine can take, in order, without
stopping to ask. It still **names every command before it runs it** —
automatic means *do not interrupt me*, not *do it where I cannot see*.

Then:

```bash
wakeup
```

---

## The quick one — pick by number

Same thing, but you choose each part:

```bash
pkg i -y git && git clone -b get https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup && sh ~/wakeup/get.sh
```

```bash
python3 ~/wakeup/wizard.py
```

The first screen is the whole specification — what the smallest
version needs, what each part needs and costs, and what your machine
already has. **Nothing is written to disk until you press a number**,
and 8 leaves the machine exactly as you found it.

To see what it would do and do nothing at all:

```bash
python3 ~/wakeup/wizard.py --list
```

---

## Chronological — in order, the first time

Do them in this order. Each one works on its own; stopping part way
leaves you with something that still works.

| | What | How | Why here |
|---|---|---|---|
| **1** | Get the files | `pkg i -y git` then `git clone -b get https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup` | A fresh Termux has no git, no curl and no wget. Nothing in it can fetch a URL, so this has to be first |
| **2** | Make it reachable | `sh ~/wakeup/get.sh` | Installs python, makes `import sparkblocks` work from any folder, makes `wakeup` a word |
| **3** | Name this phone | `python3 ~/wakeup/whereami.py --name "A33"` | Do it **once per phone**. Two phones look identical to every sign a program can read. Without a name, nothing can tell them apart, ever |
| **4** | Let Termux see your files | `termux-setup-storage` | Only needed for the Chrome panel and for copying things into Download. Everything else works without it |
| **5** | Look around | `wakeup` | Eight choices, the last always back |
| **6** | Claude in the terminal | `wakeup` → **1** | Checks, offers to install what is missing, then starts it. The Ubuntu step is a few hundred MB and is the slow one |
| **7** | Sending files about | `pkg i -y croc` | Between your own machines, with a code phrase. See [`CROC.md`](CROC.md) |

**Steps 1 and 2 are the only ones that must happen in that order.**
Everything after is whenever you like.

---

## Heuristic — which one do I want

Read down the left until something is true of you.

| If… | Then |
|---|---|
| **You just want it working** | the automatic line at the top |
| **You want to know what it is taking first** | `wizard.py --list`, which changes nothing |
| **The phone is old, or nearly full** | `wizard.py` and install **only** the block language. It is 400 KB and needs nothing but Python |
| **The phone is 32-bit** | Everything here works **except Claude Code**, which has no 32-bit build at all. The wizard says so and does not offer it. Use claude.ai in the browser for Claude |
| **You are on the Dell, not a phone** | Same clone, but Claude installs the ordinary way: `npm install -g @anthropic-ai/claude-code`. None of the proot business applies |
| **An install stopped part way** | Run the same line again. Everything already done is skipped, so it picks up where it stopped |
| **It keeps stopping in the same place** | `wakeup` → **1** → **5**, *start over*. It throws the Ubuntu away and fetches a clean one. **Only after the ordinary way has failed** — it costs the whole download again, and it says so if you have not tried the gentle one yet |
| **`wakeup` is not a known word** | `python3 ~/wakeup/wakeup.py` always works. The word needs a folder on your PATH |
| **You want it on both phones** | Same line on each, then name each one in step 3. They are separate machines and should say so |
| **Something broke and you want to start again** | Delete `~/wakeup` and run the line again. **Your own programs are in `~/.wakeup/programs` and are not in there**, so nothing of yours is lost |
| **You want to move a file to the laptop** | `croc send FILE` on one, `croc THE-CODE` on the other. [`CROC.md`](CROC.md) |
| **It is something private** | `python3 check-withheld.py --ask` first. It asks where it is going and whether that place is actually locked, and stops if the answer is *not sure* |

---

## Quick options — what each number does

### `wakeup`

| | |
|---|---|
| **1** claude | check, install what is missing, then start it |
| **2** blocks | every block there is |
| **3** menu | build a program with numbers only |
| **4** pad | build one by pressing squares |
| **5** panel | the control panel, in this terminal |
| **6** run a program | pick a saved one and run it |
| **7** more | everything else, six at a time |
| **8** back | always 8, on every page |

### `wakeup` → more

check · send a file · receive a file · saves · outside blocks ·
whereami · claude-ready · connect · withheld · the Chrome panel ·
the wizard · save a copy to storage · update from github

### When something will not install — the ladder

Three rungs, gentlest first. Each one loses more than the last, and
nothing climbs on its own.

| | | |
|---|---|---|
| **update** | reuse what is there, fetch only what is not | the ordinary line, run again |
| **install** | add what is missing | `wakeup` → 1 → 4 |
| **replace** | remove it and start that part again | `wakeup` → 1 → 5, or `sh ~/wakeup/get-claude.sh --replace` |

**The same line works on a new phone and on one that has been tried
before.** It checks everything first and only does what is missing,
so there is no separate *already tried this* version to pick between.

`replace` asks you to type the word `replace` before it removes
anything, and it does not touch your saved programs, the wakeup
folder, or anything outside Termux.

### `wizard.py`

| | |
|---|---|
| no flags | the specification, then pick by number |
| `--auto` | all of it, no questions |
| `--list` | what it would do, and nothing else |

---

## Where your own things live

| | |
|---|---|
| `~/.wakeup/programs` | **yours.** Programs you save. No update ever touches this |
| `~/wakeup` | **ours.** The project. Safe to delete and re-download |
| `~/.sparkblocks` | blocks you wrote yourself, if you make the folder |
| `~/.whereami` | the name you gave this machine |

Every program you save begins with a line like

```
# wakeup program · hello · saved 2026-10-04 11:40 MDT · on A33
```

so it can be found by **what it is**, wherever it ends up. To see
them all, wherever they are:

```bash
python3 -m sparkblocks saves
```

---

## If something is wrong

```bash
python3 ~/wakeup/claude-ready.py      what is missing before Claude will run
python3 ~/wakeup/wizard.py --list     what is installed and what is not
python3 ~/wakeup/whereami.py          which machine this is
```

And the four that check the project itself still hangs together:

```bash
python3 -m sparkblocks check
python3 check-withheld.py
python3 sign.py --check
python3 claude-ready.py --selftest
```

---

## The manuals

| | |
|---|---|
| [`INDEX.md`](INDEX.md) | every piece: what it is for, what it needs, what it runs on |
| [`BOXES.md`](BOXES.md) | what is **not** built, sorted by how sure we are |
| [`BLUEPRINTS.md`](BLUEPRINTS.md) | why it is shaped this way, and how the parts connect |
| [`WITHHELD.md`](WITHHELD.md) | what is deliberately not here, and where it went |
| [`CROC.md`](CROC.md) | sending files between your machines |
| [`SETUP.md`](SETUP.md) | the long form of this page, per machine |

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
  2026-10-04 11:39 MDT written                  Claude Opus 5
                                                on cloud container
  2026-10-04 12:19 MDT the ladder added         Claude Opus 5
                                                on cloud container
-----------------------------------------------------------------
```
<!-- /footer -->
