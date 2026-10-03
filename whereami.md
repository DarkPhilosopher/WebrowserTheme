# whereami — which machine is this

Claude has no memory between sessions and cannot see your screen. In
one conversation it was told four separate times that it was on a
machine it was not on, and worked against the wrong assumption each
time. This is how a session finds out instead of assuming.

```bash
python3 whereami.py                     name this machine
python3 whereami.py --facts             the signs, matched or not
python3 whereami.py --all               the whole register
python3 whereami.py --name "A33"        tell this machine what it is
python3 whereami.py --name "A33" --force   rename one that already has a name
python3 whereami.py --remove            undo the naming
```

## Two ways it can know

**By the signs** — system, architecture, hostname, user, whether Termux
and `/sdcard` are there. Matched against the register inside the file.

**By a name written on the machine** — and this **beats every sign**,
because two phones of the same make are identical to everything a
program can read. Do it once per phone:

```bash
python3 whereami.py --name "A33"
```

That writes `~/.whereami`. Afterwards the machine *says* what it is:

```
This machine says it is: A33
  (from /root/.whereami -- a written name, not a guess)
```

## It never answers on its own authority

A match prints the machine and then says **ask Gabriel to confirm**. No
match says to ask rather than pick the closest one. An entry written
from conversation rather than from being run there says so.

Renaming a machine that already has a name **refuses** without
`--force`, and says why: every earlier note about the old name would
point at nothing.

## The register

Seven entries, in the `REGISTER` list in the file. It is a plain Python
list, meant to be edited by hand.

| Entry | |
|---|---|
| cloud container | Where Claude sessions run. No reach to any of your machines |
| Dell i7 laptop | Two profiles, `sauve` and `xzg4b`, on the one machine |
| A33 | Samsung Galaxy A33, 64-bit |
| A17 | The other phone — architecture unconfirmed |
| an unnamed Android phone | What matches when a phone has not been named |
| a 32-bit phone | Claude Code cannot run. Your Hotpepper ACP is gone |
| Lenovo tower — NOT GABRIEL'S | A friend's, carrying the reminder to remove it |

## Layout

```
whereami.py
│
├─ REGISTER             the list of machines — edit this by hand
│   └─ each entry: name, note, sure, signs
│       signs are  ("fact", what, value)      must equal
│                  ("anyfact", what, values)  must be one of
│                  ("file", path)             must exist
│                  ("nofile", path)           must NOT exist
│
├─ facts()              what this machine says about itself
│   └─ _user()          USER, USERNAME or LOGNAME, whichever there is
│
├─ written_name()       ~/.whereami, if a name was written
├─ write_name()         writes it; refuses a rename without force
│
├─ matches(entry, now)  how well one entry fits, and what did not
│                       a miss means it is NOT this machine
│
├─ identify()           the best match — but a written NAME wins
│                       outright, before any sign is looked at
│
└─ main()               --name writes · --all lists · --facts shows
                        otherwise: identify, then ask for confirmation
```

**`sure`** on an entry means Gabriel confirmed it himself. Do not set it
because an entry looks right.

## Related

- The rule that makes a session run this first: `CLAUDE.md`
- Readiness, once you know the machine: `claude-ready.py`
