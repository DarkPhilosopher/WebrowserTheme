# Index of everything

What each thing is, **where it belongs**, what it is *for*, what data it
needs, and what physical thing it needs to run on. Things that are not
here yet are listed too, with where they would go.

The repository is meant to be usable as storage: clone it, or download
the zip, and everything is accounted for.

---

## 1. Getting Claude onto a machine

| Thing | Belongs | What it is for | Data it needs | Runs on |
|---|---|---|---|---|
| `claude-ready.py` | root | Names the **first** thing missing before Claude will run, then offers to install it by number | The machine itself | A phone or PC with Python |
| `whereami.py` | root | Says which of your machines this is, from the signs it carries. Holds the register of all of them | `~/.whereami` if named; otherwise system, architecture, hostname | Anything with Python |
| `get.sh` | root | **The one that makes the rest available.** Off github with Termux and nothing else: installs git and python, clones, makes `import sparkblocks` work anywhere, makes `wakeup` a word you can type. Safe to run again — it pulls | A network, and git | `/bin/sh`: Termux, Linux, mac |
| `wakeup.py` | root | The front door. Eight choices, the last always back; starts everything else and does no work of its own | — | Any terminal with Python |
| `WITHHELD.md` | root | The directory of what is deliberately not here: by name, with its state, where it went and why. Names the field, never the value, which is what makes it safe to publish | — | Read anywhere |
| `check-withheld.py` | root | The guard on that directory. No marker pointing at nothing, no row without a reason, no invented state, no value leaked onto the page, and git not carrying `private/` | The repo itself | Any machine with Python and git |
| `SETUP.md` | root | The steps, split by device, because they genuinely differ | — | Read anywhere |
| `CLAUDE.md` | root | What a future Claude session must know first — above all, *ask which machine* | — | Read by Claude |

## 2. The block language

| Thing | Belongs | What it is for | Data it needs | Runs on |
|---|---|---|---|---|
| `sparkblocks/core.py` | `sparkblocks/` | The one contract, and blocks for any value: links, numbers, text, lists | Whatever runs through it | Anything with Python |
| `sparkblocks/files.py` | `sparkblocks/` | Folders and files: look, read, copy, move, rename, remove | A filesystem | Any machine |
| `sparkblocks/net.py` | `sparkblocks/` | Other machines: fetch, reach, download | A network | Any machine online |
| `sparkblocks/space.py` | `sparkblocks/` | A 3D world: bodies, sensors, motors | Nothing outside itself | Any machine |
| `sparkblocks/screen.py` | `sparkblocks/` | Pixels, XYZ shapes, and touch | A terminal; touch needs a real one | A terminal, ideally Termux |
| `sparkblocks/pad.py` | `sparkblocks/` | The window as eight squares you press | Terminal size, touch reporting | **Termux, or any real terminal** |
| `sparkblocks/tool.py` | `sparkblocks/` | What a program needs to *be* a tool: ask, run, show a table | Your answers; the shell | Any machine with a prompt |
| `sparkblocks/script.py` | `sparkblocks/` | Reads a `.parts` text file and builds the chain | A `.parts` file | Any machine |
| `sparkblocks/menu.py` | `sparkblocks/` | Build a program with numbers only | — | Any terminal |
| `sparkblocks/connect.py` | `sparkblocks/` | Find what touches a thing, by ten routes at once | Files, and git history if there is any | Any machine; `git` for one route |
| `sparkblocks/book.py` | `sparkblocks/` | Writes the whole language out as JSON for the panels | — | Any machine |
| `sparkblocks/check.py` | `sparkblocks/` | 855 checks that the language still hangs together | — | Any machine |
| `sparkblocks/install.py` | `sparkblocks/` | Makes `import sparkblocks` work from any folder, for good | A writable site-packages | Any machine |
| `sparkblocks/outside.py` | `sparkblocks/` | The adapter: blocks somebody else wrote, used exactly like the ones that shipped. Making the folder is the consent; a name already taken is refused loudly, never quietly swapped | `~/.sparkblocks/`, `$SPARKBLOCKS_PATH`, `./sparkblocks-extra/` | Any machine |
| `sparkblocks/examples/*.parts` | `sparkblocks/examples/` | Ten working programs to copy and change | Varies by program | Varies |

## 3. The control panels

| Thing | Belongs | What it is for | Data it needs | Runs on |
|---|---|---|---|---|
| `panel/panel.py` | `panel/` | The plain panel. Nothing but print and input, so it works where nothing else does | `catalogue.json` | **Windows `cmd.exe`, PowerShell, Termux, anything** |
| `panel/panel.html` | `panel/` | Buttons, a terminal, and a live code pane. Draws for real | Its own baked catalogue | **Chrome. No server** |
| `panel/catalogue.json` | `panel/` | The whole language as data, so panels that cannot import Python still know it | Written by `parts json` | — |

## 4. The games and the older tools

| Thing | Belongs | What it is for | Data it needs | Runs on |
|---|---|---|---|---|
| `house/house.sh` | `house/` | Build one ASCII house together, many phones, over a shared GitHub repo | A repo everyone can push to | Termux or iSH; `bash` + `git` |
| `house/termux.properties` | `house/` | A three-row button bar over the Termux keyboard, one tap per house command | — | **Termux only** |
| `ttt/ttt.sh` | `ttt/` | Tic-tac-toe between two phones, over a shared GitHub repo | A repo both can push to | Termux or iSH |
| `tfind.sh` | root | Search every file on the phone by name, contents, size or age | Shared storage | **Termux**; faster with `ripgrep` |
| `rustbuild/rustbuild.py` | `rustbuild/` | A Rust-style construction-block editor: foundations, walls, stairs, roofs, with an isometric 3D view | Its own saved plans | Termux, or any terminal |

> **`rustbuild` is yours, not mine** — it was in the repository before
> this work and I have not touched it. Listed so the index is complete.
> It overlaps `house/` (both build things in ASCII) and `sparkblocks/screen.py`
> (both do isometric 3D), and nothing connects the three. That is a
> decision waiting to be made, not a problem.

---

## 5. Here but not in the repository

Each gap here carries its marker. **[`WITHHELD.md`](WITHHELD.md)** is
the directory those point into — it says, for every one, where it went
and why, and `python3 check-withheld.py` makes sure it stays true.

| Thing | Where it belongs | Why it is not there | To put it there |
|---|---|---|---|
| `ABOUT.md` — ⟦W-01 date of birth⟧ ⟦W-02 birthplace⟧ ⟦W-03 family details⟧ ⟦W-04 personal description⟧ | root | A safety classifier refused the push to a **public** repo. The refusal was not worked around | Make the repo private, then it goes in |
| ⟦W-05 wakeup-notes⟧ | its own repo, or a `notes/` folder | Never offered to the repo — it was built as a download | Unzip it into `notes/` and commit, once the repo is private |
| ⟦W-06 the fourth public repository⟧ | unknown | GitHub says 4; three are known | Name it, and it gets a real row |
| The zips | nowhere — they are built, not stored | A zip in git is dead weight that git cannot diff | Leave them out. Rebuild from source |

## 6. Not built yet

| Thing | Where it would go | What it would be for | What it needs |
|---|---|---|---|
| **Run-time errors naming the line** | `sparkblocks/script.py` | Today a parse error says `line 3:` but a failure *while running* gives a raw Python traceback. A child cannot act on that | A wrapper that catches and reports which line was running |
| **`use myprogram`** | `sparkblocks/script.py` | Make a saved `.parts` file usable as a block, so your own programs become Lego beside the built-in ones | A block that loads and runs another file |
| **An index for `connect`** | `sparkblocks/connect.py` | It rescans every file every run. Writing down what it learned once would make a phone-wide search fast | A file of filenames, sizes, dates and words; a way to tell when it is stale |
| **Mega sync** | `sync/mega.py` or a `.parts` program | Back things up to Mega | **There is no Mega connector** — it has to be a script on your machine, with your own credentials |
| **Google Drive sync** | `sync/drive.py` | Push and pull files from Drive | A connector exists, on `xzg4b3xz@gmail.com`. It can read, create, rename, move, copy, trash — **it cannot permanently delete, and cannot edit a file's contents** |
| **Undo in the menus** | `sparkblocks/menu.py`, `sparkblocks/pad.py` | Delete is final today, and a child will delete something | A stack of past programs |

---

## 7. Where this departs from common practice, and why

Written down because every one of these is a deliberate choice, and
somebody — including a future me — will otherwise assume it was an
oversight and "fix" it.

| Here | What is usual | Why |
|---|---|---|
| **No dependencies at all. Standard library only** | pip install whatever you need | It has to run on a phone, possibly 32-bit, possibly offline, with no build tools |
| **`check.py` instead of pytest** | A test framework | Another dependency, and it must run on the phone too. It also checks things a test framework would not: that every block has a *description*, that the catalogue matches the blocks |
| **Nothing in `files` or `net` raises** | Exceptions on failure | A run over a thousand files must not stop at one bad one. A dead link gives `""`, an unreachable host `False` |
| **Eight choices, the last always back** | Menus as long as they need to be | One rule across four interfaces that share no code. You never look to find *back* |
| **The `.parts` format** | YAML, JSON, TOML | Those need brackets and quoting. This is a block a line, and a child can move a line |
| **Blocks named in lower case in text, capitalised in Python** | One or the other | `walk /sdcard` reads like a sentence; `Walk` reads like a class, because it is |
| **Twelve shared shapes instead of flat classes** | Whatever each block needs | A shape is somewhere to put a rule so nobody has to remember it. `Number` passing `None` through was a *bug* before it was a shape |
| **The catalogue baked into the HTML** | Fetch the JSON at load | Chrome will not let a `file://` page fetch its own folder, and the panel must work with no server |
| **`⟦W-02 birthplace⟧` markers, and a directory behind them** | Black bars, or silent deletion | Taken from how archives leave a withdrawal sheet: the gap names itself and says where to ask. The directory names the *field*, never the *value*, so the record of what is private is itself safe to publish |
| **A launcher opens a terminal first** | Launch straight into the GUI | The terminal always works. The graphical mode is reached from inside it, never instead of it |
| **The repo is still called `WebrowserTheme`** | Rename it to match the project | Renaming breaks every clone and every link already written down. The mismatch is cheaper than the breakage |
| **Updates are optional, one module at a time** | One version, newest, take it or leave it | Gabriel calls this a moral. An update is a shelf, not a bundle, and *no* is a complete answer |
| **Versions branch like species; old ones stay alive** | A single line where only the newest is supported | A machine that cannot run the latest is not behind, it is on another branch. "Too old" is not something this project says to anybody |
| **There is always a minimal whole version** | A free tier, or a stripped demo | Not crippled — small and complete. It is a promise made to the user, so it is not dropped when keeping it gets inconvenient |

---

## 8. Where the manual for each thing is

Every program has one, and every manual has a **layout map** of its
insides — what it is made of and how the pieces connect.

| Program | Manual |
|---|---|
| `get.sh` and `wakeup.py` | [`SETUP.md`](SETUP.md) |
| `check-withheld.py` | [`WITHHELD.md`](WITHHELD.md) |
| `claude-ready.py` | [`claude-ready.md`](claude-ready.md) |
| `whereami.py` | [`whereami.md`](whereami.md) |
| the block language | [`sparkblocks/README.md`](sparkblocks/README.md) |
| the control panels | [`panel/README.md`](panel/README.md) |
| `house.sh` | [`house/README.md`](house/README.md) |
| `ttt.sh` | [`ttt/README.md`](ttt/README.md) |
| `tfind.sh` | [`tfind.md`](tfind.md) |
| `rustbuild.py` | [`rustbuild/README.md`](rustbuild/README.md) |

Short of a manual, every file also answers for itself:

```bash
python3 -m sparkblocks <BlockName>     what one block does
python3 <anything>.py --help     what that program does
```

## 9. Using this as storage

Everything, onto a phone, with Termux and nothing else:

```bash
pkg install git -y
```
```bash
git clone -b claude/new-session-y0nuxy https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup
```
```bash
sh ~/wakeup/get.sh
```

Then `wakeup` and pick a number. To take it off the phone again, or to
see it in the Files app: `wakeup` → **more** → **save a copy to
storage**, which puts it in `Download/wakeup`.

Just the files, nothing set up:

```bash
git clone https://github.com/DarkPhilosopher/WebrowserTheme.git
```

Everything above comes down with it. Nothing here needs installing to
read, and the only thing that needs installing to *run* is Python.

**What is deliberately not stored here:** the zips (built, not kept),
`ABOUT.md` (until the repo is private), and anything with a password in
it — ⟦M-07 the GitHub token → GitHub, Settings, Developer settings,
regenerate⟧.
