<!-- header -->
```
+----------------------------------------------------------------+
| WAKEUP · BLUEPRINTS                                            |
+----------------------------------------------------------------+
| what       What was learned rather than decided, how a part    |
|            plugs into another, the common standard they all    |
|            speak, and the shape of anything either of us signs |
| since      2026-10-04                                          |
| changed    2026-10-04                                          |
+----------------------------------------------------------------+
```
<!-- /header -->

# Blueprints

What has been **learned** rather than decided, how a part **plugs into**
another, the **common standard** they all speak, and the shape of any
document either of us signs.

`INDEX.md` says what exists. `BOXES.md` says what does not. This says
**why any of it is shaped the way it is** — so a future session can
extend it without being told, and so a part written years apart still
fits.

---

## 1. Philosophy, as it was actually discovered

None of these were decided in advance. Each one is here because
something went wrong first, and the rule is what was left over.

### 1.0 A part fails for what it IS, never for where it was plugged in

A valve that will not fit because the port is in the wrong place is a
fault of the **system**, not the valve.

Organs are not interchangeable, yet any one can go into another body,
because they all speak the same few things: blood, nerve, hormone. So
the goal is not to make everything the same. It is to **make
everything speak the same few things**.

### 1.1 Ask the thing itself, never a sentence about it

*Found when `claude-ready` said `ok Ubuntu installed` on a phone with
no Ubuntu.* It had read `proot-distro list` for the words `ubuntu` and
`installed` — but an uninstalled one says **`not installed`**, which
contains `installed`.

A check that asks the real thing cannot disagree with the real thing.
A check that reads a sentence *about* the real thing can, and
eventually will. The replacement opens the same door every later step
uses: `proot-distro login ubuntu -- true`.

### 1.2 Degrade, do not fail

A run over a thousand files must not stop at one bad one. A dead link
gives `""`, an unreachable host `False`, a bad URL `0`. The panel
without its package still builds and saves, and says plainly that it
cannot run anything here.

**Say what you cannot do. Never offer a workaround that does not
work** — he will try it.

### 1.3 An update is an offer, never a demand

Always a minimal **whole** version. One module at a time, or none.
Backwards compatible both ways. And **speciation**: versions branch
like species rather than queueing, and the old branch stays alive. A
machine that cannot run the latest is not behind — it is on another
branch, and that branch is supported.

*"Too old" is not something this project says to anybody.*

### 1.4 Say the requirements before the install, not during

A program should state what it needs, what it will cost, and what is
optional **on a plain screen, before anything is written to disk** —
so declining is a decision rather than an interruption. See `wizard.py`.

### 1.5 Name the field, never the value

A record of private things can itself be published, if it names *what*
is missing instead of carrying it. `date of birth` goes on the page;
the date does not. That one discipline is what makes `WITHHELD.md`
safe to put in a public repository.

### 1.6 Eight choices, and the last is always back

One rule across four interfaces that share no code — the numbered
menu, the touch pad, the plain panel, the browser squares. You never
have to look for *back*. When there are more than seven, the seventh
becomes `more`.

### 1.7 A check that cannot fail is not a check

Every guard here was tried against a deliberate break before being
trusted. A regression was introduced on purpose, the check was made to
fail, and only then was it kept. A green light nobody has ever seen go
red is a decoration.

### 1.8 The gap names itself

Taken from how an archive handles a withdrawn document: not a thinned
folder, not a blacked-out page, but a **withdrawal sheet** in the gap
saying what was taken and who to ask. A reader is never left wondering
whether something is missing.

---

## 2. Port routes — how one part reaches another

There is **one port**, and everything below is a way of reaching it.

```
                        the one port
                   part.step(ctx) -> value
                             |
   +---------+---------+-----+-----+---------+-----------+
   |         |         |           |         |           |
 Python   a .spark   the         the       outside     another
 import    file      numbered    catalogue  folder      person's
                     menu        (JSON)                 block
```

| Route | How a part is reached | What it needs to know |
|---|---|---|
| **Python import** | `from sparkblocks import Walk` | nothing |
| **Text** (`.spark`) | one block a line, lower case | the registry of names |
| **Menu / pad** | by number | the catalogue |
| **Catalogue** (`panel/catalogue.json`) | by name, as data | nothing — it *is* the data |
| **Outside folder** | `~/.sparkblocks/*.py` | nothing. Making the folder is the consent |
| **Somebody else's block** | identical to all of the above | nothing — that is the point |

**The rule that makes it one port and not six:** nothing may keep its
own list of what works where. A block carries its own datasheet and
every route reads it. The browser panel used to keep a list, and it
was wrong the moment a block was added.

### 2.1 The two things a part must declare

```python
class Run(Doing):
    """Run a command and hand on what it said."""
    fits = {"needs": ["shell"], "changes": "anything", "waits": True}
```

A sentence saying what it does, and a datasheet saying what it needs.
With those, nothing that holds parts ever has to guess.

---

## 3. The common standard — the few things everything speaks

Small closed vocabularies, on purpose. A word outside the list is a
mistake a checker can catch; free text is not.

| Vocabulary | The words | Used by |
|---|---|---|
| **needs** | `shell` `files` `network` `world` `body` `grid` `terminal` `touch` `person` | every block |
| **changes** | `nothing` `vars` `files` `DELETES` `world` `screen` `network` `anything` | every block |
| **state** | `refused` `withheld` `elsewhere` `not collected` `unknown` `out of order` | `WITHHELD.md` |
| **certainty** | `no way` `maybe` `certainly` `recently` `longing` | `BOXES.md` |
| **how** | `ok` `--` `n/a` | `claude-ready.py` |

`DELETES` is shouted because it is the only one you cannot undo.
`out of order` is the only `state` that is a **job** rather than a
settled fact.

---

## 4. The shape of anything signed

**This page is an example of itself** — the block above it and the
block below it are what every signed document here carries.

```
   header      what it is, when it began, when it last moved
   body        the document
   footer      who signed it, and the chronology
```

Written and read back by **`sign.py`**, not by hand, because a format
kept by hand drifts. Two documents signed the same way on Monday are
signed two ways by Friday, and then neither can be checked against the
other.

```bash
python3 sign.py --check                  do they all still match
python3 sign.py --stamp FILE "what"      add a line to the chronology
python3 sign.py --who                    who can sign, and on what
```

### 4.1 A signature is a name, an account, and an instrument

The same name on two machines is **not the same signer**:

```
  Claude Opus 5            claude-opus-5
                           of xzg4b3xz@gmail.com
                           on cloud container
```

This repository's history has both `Claude Opus 4.8` and
`Claude Opus 5` in it. Those are two signers, and the record does not
pretend otherwise. One self may run on several instruments and each is
separately accountable for what it did there.

Gabriel's signature has the same three parts — the person, the
accounts, and which of his machines he was at. **His sits above mine**,
always: he is the one the work is for.

### 4.2 The chronology is append-only

One line per thing that happened: when, what, who, on what instrument.
Easy to leave out, and worth most later.

**Nothing rewrites a line already down.** A chronology you may edit is
a story, not a record — and the whole value of it is that it is the
second kind.

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
  2026-10-04 11:09 MDT written                  Claude Opus 5
                                                on cloud container
  2026-10-04 11:09 MDT port routes written      Claude Opus 5
                                                on cloud container
  2026-10-04 11:12 MDT wizard and container bui Claude Opus 5
                                                on cloud container
-----------------------------------------------------------------
```
<!-- /footer -->
