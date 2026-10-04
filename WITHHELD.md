# Withheld — the directory of what is not here

Every gap in this repository that was made on purpose is listed below,
by name, with where it went and why.

**Nothing on this page is private.** It names the *field*, never the
*value*. "date of birth" is here; the date is not. That is the whole
idea: you can see exactly what is missing and go and get it, without
the page itself carrying the thing it is describing.

Borrowed from how an archive handles a withdrawn document. They do not
quietly thin the folder and they do not black the page out — they leave
a **withdrawal sheet** in the gap saying what was taken, when, and who
to ask. A reader is never left wondering whether something is missing.

## How to read a marker

Where something was taken out, this is left in its place:

```
⟦W-03 birthplace⟧
```

`W-03` is the row below. The words are so you know what it was without
looking it up. The marker is deliberately small — it marks the gap, it
does not re-tell the story.

## The states

| State | Means | What to do |
|---|---|---|
| **refused** | A system would not carry it. Not a choice either of us made | Read `why`. It names which system and what it objected to |
| **withheld** | It exists, it is private, and it is deliberately not here | Needs Gabriel's permission, and usually the repo going private |
| **elsewhere** | It exists and is not secret — it just lives somewhere else | Follow `where` |
| **not collected** | Could have been recorded, and deliberately was not | Read `why`. Usually it should stay that way |
| **unknown** | Something is missing and we do not know what | The honest state. Better than a guess |
| **out of order** | It was here and it is broken. The gap is a fault, not a decision | Fix it |

`out of order` is the one that should never sit still. The others are
settled; that one is a job.

## The directory

| Tag | Name | State | Where it went | Why |
|---|---|---|---|---|
| `W-01` | date of birth | refused | not committed; it is in Gabriel's hands and in the session scratchpad only | A safety classifier refused the push of `ABOUT.md` to a **public** repository. The refusal was not worked around |
| `W-02` | birthplace | refused | same as `W-01` | same as `W-01` |
| `W-03` | family details | refused | same as `W-01` | same as `W-01` |
| `W-04` | personal description | refused | same as `W-01` | same as `W-01` |
| `W-05` | `wakeup-notes/` — the tagged notes | withheld | not committed | Waits on the repository going private. Only Gabriel can do that |
| `W-06` | the fourth public repository | unknown | — | GitHub says he has 4 public repositories; 3 are known. Name it and it gets a real entry |
| `W-07` | where each piece of work was done | not collected | — | No location device in a cloud container, and his whereabouts are not something to go looking for. The *machine* is recorded; the *place* is not |
| `W-08` | the second Google Drive, `lewisgabe33@gmail.com` | elsewhere | that account | There is a connector for `xzg4b3xz@gmail.com` only. This session cannot reach the other one at all |

## Where the private material actually lives

**Not in this repository, and not in any copy of it.**

This repository is **public**. Until that changes, nothing private may
be committed here, including in history — a deleted file is still in
the history, so "commit then remove" is not a way round it.

| | |
|---|---|
| `private/` | A folder in the working copy, in `.gitignore`, that **git will not take**. Scratch space while something is being written. It is not storage — this container is wiped when the session ends |
| Gabriel's own hands | Where `ABOUT.md` is. Delivered to him directly rather than committed |
| A private repository | Does not exist yet. The obvious home, once he wants one |
| Google Drive | `xzg4b3xz@gmail.com`. Durable and private, and reachable from here |

### Why not just make this repo private and be done

Because that is **his** decision and nobody else's, and because the
material is already out of the repository either way. The directory
above works whether or not he ever makes it private — which is the
point of writing the gap down rather than waiting for permission to
fill it.

## Keeping it honest

```bash
python3 check-withheld.py
```

Every marker must have a row, every row must say where and why, and no
file under `private/` may ever be tracked by git. A directory nobody
checks drifts, and a drifted withdrawal sheet is worse than none — it
tells you something is somewhere it is not.

## Layout

```
WITHHELD.md          this page: the directory, and nothing private
│
├─ ⟦W-nn name⟧       the marker left in the gap, anywhere in the repo
├─ the states        refused · withheld · elsewhere ·
│                    not collected · unknown · out of order
└─ check-withheld.py the guard
    ├─ markers_have_rows()    no marker points at nothing
    ├─ rows_are_complete()    no row is missing where or why
    ├─ rows_are_used()        no row describes a gap that is gone
    ├─ states_are_known()     no invented state
    └─ nothing_private_tracked()  git is not carrying private/
```
