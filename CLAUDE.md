# CLAUDE.md

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

| Machine | What changes |
|---|---|
| cloud container | No reach to any of his machines. Say so plainly rather than offering workarounds |
| Dell laptop | Windows paths, `C:\Users\sauve`, also has an `S:` drive |
| phone, 64-bit | Claude Code runs, but only inside `proot-distro ubuntu` |
| phone, 32-bit | Claude Code **cannot run at all**. No build exists. Do not suggest proot |

If `whereami.py` says the machine is not on the register, **ask**. Do
not pick the closest one and carry on.

## Confirming before writing to the register

The register is the `REGISTER` list in `whereami.py`. Most entries are
marked `"sure": False` — they were written from what was said in
conversation, not from being run on the machine itself.

**Never change or remove an entry without asking first.** Say which
entry, what it says now, and what you want it to say. Adding a new
entry for a machine that matched nothing is fine to offer, but Gabriel
confirms the name before it is written.

When an entry is confirmed by actually running `whereami.py` on that
machine, set `"sure": True` and say that you did.

## What is in this repository

| Folder | What it is |
|---|---|
| `parts/` | A language of interchangeable blocks. See `parts/README.md` |
| `house/` | Multiplayer ASCII house builder, over a shared GitHub repo |
| `ttt/` | Tic-tac-toe between two phones, over a shared GitHub repo |
| `tfind.sh` | File search for Termux on Android |
| `whereami.py` | Which machine am I on |

Gabriel also has `DarkPhilosopher/spark` (a game engine, `when`/`do`
rules) and `DarkPhilosopher/ASC` (a 16×16 ASCII grid). **`spark` and
`parts` are deliberately separate languages.** He has said so directly.
Do not propose bridging them.

## Working on `parts/`

Run this after any change:

```bash
python3 -m parts check
```

It checks the rules the language quietly depends on. `parts/README.md`
explains the three steps for adding a block, and the one rule worth
knowing: never store a setting called `step`, because it shadows the
method every block must have.

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
