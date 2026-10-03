# claude-ready — what this phone still needs

Checks everything Claude Code needs, **in the order you actually hit
it**, and names the first thing you are stuck on rather than listing
faults. What is missing becomes a numbered menu.

```bash
python3 claude-ready.py            look, then offer to fix what is missing
python3 claude-ready.py --check    look and say, fix nothing
```

## What it checks, in order

| | What it means if it says `--` |
|---|---|
| **Termux** | Install it from F-Droid, not the Play Store |
| **Python** | You could not be running this, so it never fails |
| **this phone** | 32-bit. **Claude Code cannot run here at all** — the list stops |
| **storage access** | `termux-setup-storage`, then tap Allow |
| **git** | For fetching your projects |
| **curl** | For fetching the Node installer |
| **proot-distro** | Runs a small Ubuntu, which supplies the glibc Android lacks |
| **Ubuntu** | A few minutes to download |
| **Node, in Ubuntu** | Claude Code is a Node program |
| **Claude Code** | The thing itself |
| **the `claude` word** | An alias so you need not log into Ubuntu by hand |

## The menu

Only what is **missing** is offered. Six at most, then *do all of it*,
then *quit* — eight, the last one out, the rule the whole project keeps.

```
  1) grant storage access
  2) install proot-distro
  3) install Ubuntu (a few minutes)
  7) do all of it, in order
  8) quit
```

Each fix prints the command before running it, so nothing happens
unseen. After each one it looks again from the top.

## On a 32-bit phone it stops early, on purpose

The list ends after `curl`. proot, Ubuntu, Node and Claude Code are
**never offered**, because no 32-bit build of Claude Code exists and no
amount of proot changes that. It says so and points at claude.ai in a
browser instead.

## Layout

```
claude-ready.py
│
├─ look()                 every check, in the order you hit them
│   ├─ arch()             64-bit or 32-bit — decides what is even possible,
│   │                     and truncates the list when the answer is 32
│   ├─ have(prog)         is it on the PATH
│   ├─ _ubuntu_installed()
│   ├─ _node_version()    ┐ these three log into the proot Ubuntu,
│   ├─ _claude_version()  │ so they only run once there is one
│   └─ _alias_set()       ┘
│
├─ show(checks)           the table, then the FIRST thing missing
│   └─ _fold()            wraps long lines instead of cutting them,
│                         so a narrow phone screen still reads
│
├─ fixable(stuck)         of what is missing, what can be installed
├─ menu(todo)             six + do-all + quit
│
├─ do(check)              runs the fix, step by step, stopping at the
│   ├─ run()              first one that fails
│   └─ set_alias()        the one fix that writes a file, not a command
│
└─ main()                 look → show → menu → do → look again
```

**The shape of a check.** Everything hangs off one dict, which is why
adding a check is a few lines and nothing else needs to know:

```python
{"name": "git",                      # what it is called
 "how":  "ok" | "--" | "n/a",        # how it is
 "says": "git version 2.43.0",       # what to show
 "fix":  ["pkg", "install", "git"],  # how to put it right, or None
 "doing": "install git",             # what the menu calls it
 "fixtell": "..."}                   # anything to say first
```

`n/a` is the third state and it matters: *Node, in Ubuntu* is not
missing when there is no Ubuntu — it is **not yet askable**.

## Related

- The same job in blocks: `parts/examples/claude-ready.parts`
- Which machine this is: `whereami.py`
- The steps by hand: `SETUP.md`
