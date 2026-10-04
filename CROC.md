<!-- header -->
```
+----------------------------------------------------------------+
| WAKEUP · SENDING FILES                                         |
+----------------------------------------------------------------+
| what       Moving a file between your own machines with a code |
|            phrase: croc, on Termux and on Windows, including   |
|            running your own relay                              |
| since      2026-10-04                                          |
| changed    2026-10-04                                          |
+----------------------------------------------------------------+
```
<!-- /header -->

# Sending files between your own machines

`croc` moves a file from one machine to another with a **code phrase**
and nothing else. No cable, no cloud account, no sign-in, no uploading
it somewhere first. The two machines find each other, the file goes
across, and it is over.

This is the answer to the thing that started a lot of this: *how do I
get a file off the phone and onto the computer.*

It works between any two of your machines — A33 to Dell, Dell to A17,
phone to phone — and in either direction.

---

## Getting it

### Termux, on either phone

```bash
pkg i -y croc
```

It is an official Termux package, so that is all.

### Windows, on the Dell

Whichever of these you already have:

```
winget install schollz.croc
```
```
scoop install croc
```
```
choco install croc
```

If none of them is installed, take the Windows `.exe` from
**github.com/schollz/croc/releases**, put it in a folder, and run it
from **Command Prompt** or **PowerShell** in that folder.

---

## Sending, and the code it gives you

On the machine that **has** the file:

```bash
croc send notes.txt
```

It prints a **code phrase** — three words, something like
`1234-fairy-tiger-saddle` — and then waits.

On the machine that **wants** it, type `croc` and that code:

```bash
croc 1234-fairy-tiger-saddle
```

It asks whether to accept, you say yes, and the file arrives in
whatever folder you were standing in.

A whole folder works the same way:

```bash
croc send ~/wakeup
```

### Choosing the code yourself

```bash
croc send --code mysecretword notes.txt
```

Minimum six characters. **Use the generated one when you can** — see
*How safe this is* below.

### Keeping the code out of sight

On Linux and Termux, anything you type as an argument can be seen by
other programs on the machine. To avoid that:

```bash
CROC_SECRET=mysecretword croc send notes.txt
```

and on the other end:

```bash
CROC_SECRET=mysecretword croc
```

---

## The relay, and running your own

The two machines do not talk directly. A **relay** introduces them and
passes the bytes along. By default that is a public one run by croc's
author.

**The relay cannot read your file.** The code phrase is turned into a
key on both ends, and the relay only ever forwards already-encrypted
bytes. It does not have the key and is never sent it.

### Your own relay

On a machine both ends can reach:

```bash
croc relay
```

That listens on **TCP 9009 to 9013**. It needs at least two of those
ports open.

Then both ends point at it:

```bash
croc --relay "mymachine.example.com:9009" send notes.txt
```
```bash
croc --relay "mymachine.example.com:9009" 1234-fairy-tiger-saddle
```

Worth doing when the two machines are on the same wifi — it is faster,
and nothing leaves the house. The Dell can be the relay for both
phones.

---

## How safe this is, said plainly

| | |
|---|---|
| **The file is encrypted end to end** | The relay forwards it and cannot open it |
| **The code phrase IS the key** | Anyone who has it can take the file. There is nothing else stopping them |
| **The generated code is three words** | Strong enough. Use it |
| **`--code yourword` is weaker** | Six characters is the minimum allowed, not a good idea. Use it for convenience between your own machines on your own wifi, not for anything that matters |
| **It is one use** | Once the transfer happens, that code is spent |

### Before sending anything private

**The route passes through a machine that is not yours.** Encrypted,
yes — but the question is worth asking properly rather than assumed,
and there is a program that asks it:

```bash
python3 check-withheld.py --ask
```

It will ask where the material is going, whether that place is really
locked, whether the route passes anywhere open, and what copies get
left behind. For private material over the **public** relay, the
honest answer to "does the route pass anywhere open" is *through
somebody else's machine, encrypted* — so run your own relay for that,
and say so in the row.

See **[`WITHHELD.md`](WITHHELD.md)** for the rest of it.

---

## The short version

| Doing | Typing |
|---|---|
| install, phone | `pkg i -y croc` |
| install, Windows | `winget install schollz.croc` |
| send | `croc send FILE` |
| receive | `croc THE-CODE` |
| send a folder | `croc send FOLDER` |
| pick your own code | `croc send --code SOMETHING FILE` |
| hide the code | `CROC_SECRET=... croc send FILE` |
| your own relay | `croc relay` — TCP 9009-9013 |
| use that relay | `croc --relay "host:9009" send FILE` |

From inside Wakeup: **`wakeup` → more → send a file**, which checks
croc is there, offers to install it if not, and runs the right line.

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
  2026-10-04 11:36 MDT written                  Claude Opus 5
                                                on cloud container
  2026-10-04 11:38 MDT wired into wakeup        Claude Opus 5
                                                on cloud container
-----------------------------------------------------------------
```
<!-- /footer -->
