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

## Before private material moves, ask

Material does not just arrive and get filed. **Ask first, and write
the answers into the row.** If any answer is *I do not know*, the
state is `unknown` and the material does not move until it is not.

```bash
python3 check-withheld.py --ask
```

walks these questions and prints the row to paste in.

### Coming in — is it really from a locked place

1. **What is it, by name?** The field, not the value. If it cannot be
   named without writing the thing down, it does not belong on this
   page at all.
2. **Which container did it come out of?** Name it. "my notes" is not
   a container; `Drive/xzg4b3xz`, `the A33, Termux home` are.
3. **Is that container actually locked?** Not *felt* private —
   *locked*. Who else can open it? Is there a share link? Was it ever
   public, even briefly?
4. **Did Gabriel permit this material, specifically, to come here?**
   Permission for one thing is not permission for the next.
5. **Is it still needed in the open one?** If it is in two places and
   one is open, locking the second has done nothing.

### Going out — is the destination locked

1. **Where exactly is it going**, and is *that* a locked container?
2. **Does the route pass anywhere open?** A file handed over in a chat
   has been through the conversation. A commit has been through the
   history. Neither can be taken back.
3. **What copies get left behind?** The session scratchpad, a zip in
   Downloads, a branch, a reflog. Name them, and say who clears them.
4. **Is the destination his alone, or shared with anyone?**

### Places this project knows about, and whether they are locked

| Place | Locked | Worth knowing |
|---|---|---|
| This repository | **No — public** | Anyone can read it, and history keeps deleted files. There is no undo on a push |
| `private/` | Not shared, **not durable** | Gitignored, so git will not take it. Wiped when the session ends. Scratch space, never storage |
| A file handed over in the conversation | **No** | It has been through the chat to get to him. Fine for his own material going back to him; not a vault |
| Google Drive `xzg4b3xz@gmail.com` | Yes, unless shared | Reachable from here. Check it is not on a share link |
| Google Drive `lewisgabe33@gmail.com` | Unknown from here | No connector. This session cannot see it at all — ⟦W-08⟧ |
| Gabriel's own phone or laptop | His to say | Only he knows who else uses the machine |
| `croc`, through the **public** relay | Encrypted, but the route is not his | End to end encrypted, and the relay cannot open it — but it is somebody else's machine, and the code phrase is the whole key. Fine for ordinary files |
| `croc`, through **his own** relay | Yes, if both machines are his | `croc relay` on the Dell, both phones pointed at it. Nothing leaves the house. This is the one to use for anything private — see [`CROC.md`](CROC.md) |
| A private GitHub repository | Yes | **Does not exist yet.** The obvious home |

**The honest summary:** of everywhere *this session* can actually
reach, exactly one is locked — the `xzg4b3xz` Drive. Everything else
it can reach is public or temporary.

Between **his own machines** he has a better option than any of them:
`croc` over his own relay, which this session cannot touch at all.
That is the right route for private material, and it is worth saying
that the best answer here is one that does not involve me.

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
└─ check-withheld.py
    │
    ├─ the guard               python3 check-withheld.py
    │   ├─ every_marker_has_a_row()      no marker points at nothing
    │   ├─ every_row_says_where_and_why()
    │   ├─ every_state_is_a_real_one()   no invented state
    │   ├─ no_value_leaked_in()          the page names fields only
    │   ├─ git_is_not_carrying_private() the one that matters
    │   └─ rows_with_no_marker()         noted, not faulted
    │
    └─ the questions           python3 check-withheld.py --ask
        ├─ COMING_IN · GOING_OUT   what to ask, each way
        ├─ SAFE                    WHICH answer is the safe one, per
        │                          question. "locked? no" and "open
        │                          route? yes" are both bad news in
        │                          opposite words -- said once, here
        └─ worrying()              anything vague, or not the safe
                                   answer, stops the move
```
