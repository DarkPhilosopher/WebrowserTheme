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
| `get.sh` | The one that makes the rest available: off github with Termux alone. Safe to run again — it pulls |
| `wakeup.py` | The front door. `wakeup`, then pick a number. It starts the others and does no work of its own |
| `sparkblocks/` | A language of interchangeable blocks. See `sparkblocks/README.md` |
| `house/` | Multiplayer ASCII house builder, over a shared GitHub repo |
| `ttt/` | Tic-tac-toe between two phones, over a shared GitHub repo |
| `tfind.sh` | File search for Termux on Android |
| `whereami.py` | Which machine am I on |
| `claude-ready.py` | Is this phone ready to run Claude in Termux, and if not, why |
| `tfind.md` | Documentation for `tfind.sh` — it used to be the root README |
| `panel/` | Three control panels: plain terminal, browser, and the fancier ones in `sparkblocks` |
| `INDEX.md` | Every piece: where it belongs, what it is for, what it runs on, and what is not built yet |
| `rustbuild/` | **Gabriel's, not mine.** A Rust-style ASCII construction editor, here before this work |

Gabriel also has `DarkPhilosopher/spark` (a game engine, `when`/`do`
rules) and `DarkPhilosopher/ASC` (a 16×16 ASCII grid). **`spark` and
**Spark blocks** are deliberately separate from it.** He has said so directly.
Do not propose bridging them.

## Working on `sparkblocks/`

Run this after any change:

```bash
python3 -m sparkblocks check
```

It checks the rules the language quietly depends on — including that
`panel/catalogue.json` and the copy baked into `panel/panel.html` still
match the blocks. **After adding or renaming a block, rerun both:**

```bash
python3 -m sparkblocks json panel/catalogue.json
python3 -m sparkblocks json --html
```
 `sparkblocks/README.md`
explains the three steps for adding a block, and the one rule worth
knowing: never store a setting called `step`, because it shadows the
method every block must have.

### Blocks somebody else wrote

They come in through `sparkblocks/outside.py`, from `~/.sparkblocks/`,
`$SPARKBLOCKS_PATH` or `./sparkblocks-extra/`. **Making the folder is
the consent** — nothing else is searched, and nothing is ever
downloaded.

A name this folder already uses is **refused, loudly, and never quietly
swapped in.** Do not soften that into a warning: a program that meant
different things on different machines is the exact fault this project
exists to avoid.

The catalogue the panels read leaves outside blocks out unless asked
(`json --outside`), so the committed file says the same thing on every
machine. Never bake one machine's own outside blocks into
`panel/panel.html`.

## Private things, and the gaps they leave

**This repository is public.** Nothing private goes in it — and not
into its history either, because a deleted file is still in the
history. "Commit it then remove it" is not a way round this. There is
no undo on a public push.

So private material lives in **a separate container**, and what stays
here is a **marker** naming the gap:

```
⟦W-02 birthplace⟧
```

`W-02` is a row in **`WITHHELD.md`**, which says what it was, its
state, where it went, and why. That page names the *field* and never
the *value* — which is exactly what makes it safe to publish.

| | |
|---|---|
| `WITHHELD.md` | the directory. Public and safe by construction |
| `private/` | gitignored working space. **Not storage** — this container is wiped when the session ends |
| `check-withheld.py` | the guard. Run it after touching any of this |

### The states

`refused` · `withheld` · `elsewhere` · `not collected` · `unknown` ·
`out of order`

`out of order` means the gap is a **fault**, not a decision. The others
are settled; that one is a job.

### What to do when something private comes up

1. **Do not commit it.** Not even briefly.
2. Give it a `W-nn` row in `WITHHELD.md` — the field, never the value.
3. Leave the marker where the gap is, if there is a page left to mark.
   When the whole thing is absent there is nowhere to put one, and the
   row alone is the record. The checker knows the difference.
4. Hand the material to Gabriel directly, or put it in Drive.
5. `python3 check-withheld.py`

**If a system refuses to carry something, that refusal stands.** A
safety classifier refused `ABOUT.md`; it was not worked around, and it
is not to be. The row says `refused` and names what objected. That is
the honest record, and it is also the useful one.

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

`python3 -m sparkblocks check` enforces 1, 2 and 3. You have to do 4 and 5.

### The four checks, and what each one is for

```bash
python3 -m sparkblocks check     the language still hangs together
python3 check-withheld.py        the record of what is missing is true
python3 sign.py --check          the signed documents still match
python3 claude-ready.py --selftest   the faults that bit before stay dead
```

Run all four before saying something is done.

## His own files are not ours

Programs he saves are **his**, and they must never live inside the
clone. `sparkblocks/saves.py` is the one place that knows this.

**The tag.** Every save begins with one ordinary `#` comment:

```
# wakeup program · hello · saved 2026-10-04 11:40 MDT · on A33
```

Readers ignore it, so the program runs the same. But it means a file
is found **by what it is**, not by remembering where it went — the
only thing that works on a phone, where everything ends up in
Downloads whatever anyone intended.

**Finding.** `saves.found()` looks in likely places, **most likely
first** — Downloads, then `~/.wakeup/programs`, the Termux home, the
project folder, Documents, shared storage, where you are standing —
shallowly, because a phone cannot walk the whole card. Results are
**newest first**.

**Moving is his choice.** Nothing is relocated on its own.
`saves --tidy` shows what it found and asks. No is a complete answer;
the tag means it will still be found next time.

**The project's own files are not his.** The examples that ship here
are programs too. `saves.theirs()` asks git which files the project
tracks and leaves those alone — without it, tidying would move the
examples out of the folder `check` reads and break it.

**Updating carries his work out first.** `get.sh` runs
`saves.py --adopt` before pulling, and never force-resets. If a pull
would collide it stops and says so rather than rolling over anything.

| | |
|---|---|
| `~/.wakeup/programs` | his. No update ever touches it |
| the clone | ours. Replaceable, and treated as replaceable |

## The two branches

| Branch | What it is |
|---|---|
| `claude/new-session-y0nuxy` | where the work goes |
| `get` | the same thing under a short name, so the install line is shorter |

**Push to both, every time.** `get` going stale means a fresh phone
installs something old and nobody finds out for a while.

`get.sh` takes the branch from the clone it is in, so whichever one he
cloned is the one he keeps getting. Do not put a branch name back into
that file.

## The second moral: an update is an offer, never a demand

He called this **a moral**, in those words, on 2026-10-04. It sits
beside the organ rule above, and it is the same moral turned from
*parts* toward *time*. The organ rule says a part must fit any body.
This one says a part must fit any **moment** — including an old one.

> *"It's a moral to me to release updates as optionally as possible...
> there will simply promise to be a part of or version of the expanse
> in what program we are making will always have a minimalism option
> and communication and news view into it, also speciation — even if
> you cannot seem to play a game or advanced software upon its final
> updates, but we wanna make backwards compatible with previous
> updates and install update one module at a time, optional which ones
> at all."*

Five things follow, and none of them is negotiable.

### 1. There is always a minimal option

However far the thing grows — he calls it **the expanse** — there is
always a small version that still does the job. Not a crippled demo: a
real, whole, smaller one. **This is a promise made to the user**, so it
is not something to drop when it becomes inconvenient to keep.

### 2. One module at a time, or none at all

An update is a shelf, not a bundle. He picks which pieces, and *no*
is a complete answer. Nothing may require the whole thing, and nothing
may quietly bring in a neighbour.

Never write an update that only applies entire. If a change needs two
modules at once, that is a sign those two were never properly separate
and the fault is ours, not his.

### 3. Backwards compatible, in both directions

New parts work with old ones. Old parts keep working. A program he
wrote a year ago still runs, and nothing made today may be the reason
it stops.

### 4. Speciation — versions are species, not a queue

The important word, and the one that makes this different from ordinary
versioning. A version is **not** a place in a line where the newest is
the only living one. Versions **branch**, like species, and the old
branch stays alive.

So when a machine cannot run the latest — a phone too old for the
advanced build, something that will not play the game at its final
updates — **that machine is not behind. It is on a different branch,
and that branch is supported.** "Too old" is never a thing this project
says to anybody.

This is already how the project behaves: the 32-bit answer is not *buy
a better phone*, it is *everything except Claude Code itself still runs
here.* Keep it that way on purpose.

### 5. A news view, so he can see what he is declining

Choosing is only real if he can see the choice. Whatever offers
updates must also say, in plain words, what each one changes — so
turning one down is a decision rather than a shrug.

### What this already obliges us to build

Written as empty boxes in `BOXES.md` rather than left as good
intentions:

| | |
|---|---|
| A minimal mode in each program | so the promise in 1 is kept, not just meant |
| Module-at-a-time updating in `get.sh` | today it pulls everything or nothing — it breaks rule 2 |
| A `NEWS.md`, and a view onto it | rule 5 has nothing behind it yet |
| Something that proves old programs still run | rule 3 is currently only a good intention |

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
| **Run `python3 -m sparkblocks pad` on a real phone** | Touch has never been tried. The whole pad rests on it |
| **Decide about the three 3D engines** | Two of the three are his and predate this work |
| **Name his fourth public repository** | GitHub says 4; only 3 are known |

## The daily greeting — start every day with this

Asked for on 2026-10-04, as a standing thing: **"Train me from now on
and daily."** Not a one-off. Every session that is the first of a day
opens this way, in this order:

1. **A greeting that says the time of day and the date.** Morning,
   afternoon or evening, in words, then the date.
2. **The weather outside** — where *he* is, not where the container is.
3. **A summary of yesterday** — what was done, what broke, what is
   waiting. Short. The ledger and the git log are the sources.
4. **Then ask** whether he wants more than the summary, rather than
   pouring out the detail unasked.

### What a session cannot know on its own

| | Why | How to get it |
|---|---|---|
| **His local time** | The container clock is UTC, and the session is not on his machine | His timezone, recorded below, or ask him |
| **The weather** | Needs a place name. A cloud container has no location, and his is not something to go looking for | His town, recorded below, or ask him |
| **Which machine he is on** | `whereami.py` only ever sees the container | Ask. Always |

He said plainly: **"use me if your must"** — asking him is the intended
fallback, not a failure. Ask once, write the answer here, and stop
asking.

| Fact | Value | Said |
|---|---|---|
| Timezone | **America/Denver** — Utah, Mountain Time | 2026-10-04 |
| Town, for weather | **Provo, Utah** | 2026-10-04 |

```bash
TZ=America/Denver date "+%A %-d %B %Y, %-I:%M %p %Z"
```

That is the line for his local time. The container clock is UTC and
saying a UTC hour to him is the same mistake as naming the wrong
machine.

### Getting the weather, from in here

**`curl` to a weather service does not work.** Both of the obvious
ones are refused by the container's egress policy, not by the sites:

| | |
|---|---|
| `wttr.in` | HTTP 403 through the agent proxy |
| `api.weather.gov` | `connect_rejected` — organization network policy |

**Use `WebSearch`** for it, which goes a different way and does work.
Do not spend the morning rediscovering this.

### The Routine

Armed on 2026-10-04. It fires **6:55 a.m. Mountain, every day**, and
starts a fresh session that pushes a notification to his phone.

| | |
|---|---|
| Trigger id | `trig_015PAxMgWN7LjNoWYUw1VU6k` |
| Schedule | `CRON_TZ=America/Denver 55 6 * * *` |

**Change that Routine, never add a second one.** Two greetings firing
each morning is exactly the kind of thing he would have to ask twice to
stop. `update_trigger` with the id above changes the hour or the words;
`list_triggers` finds it if the id is lost.

It carries **no connectors** — the fired sessions have no Google Drive
or other `mcp__*` tools, only the built-in ones. That is enough for the
greeting, which needs `git` and `WebSearch` and nothing else. If the
greeting ever needs a connector, he has to create the Routine from the
claude.ai Routines screen; a session cannot grant one it does not hold.

## He wants to draw this

A chart and visual depictions of the whole idea — the fundamentals and
what is interesting about them — **for making machines with the best
searching engines.** That is what the rest is building toward.

The written material is there already: `INDEX.md`, `BOXES.md`, and the
layout map in every manual. Nothing is drawn yet. **Remind him**, and
offer to help turn the maps into a diagram when he comes to it.

## Notes worth keeping

- **The `spark` repo and Spark blocks stay separate.** He has said so
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
  It goes in only if he makes the repository private. The gap it left
  is rows ⟦W-01⟧ to ⟦W-04⟧ in `WITHHELD.md`.

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
