#!/usr/bin/env python3
"""make-private -- build the container that private material goes in.

    python3 make-private.py              make it here, as private/
    python3 make-private.py --into PATH  make it somewhere else
    python3 make-private.py --zip        build it as a folder to carry away

It makes **an empty container with a labelled slot for every gap**
`WITHHELD.md` records. Nothing private is put in it and nothing
private is read to build it — the shape comes from the directory, so
the two can never drift apart.

Each slot holds one file saying what belongs there and nothing else.
You fill them, or you do not.

WHERE TO PUT IT
---------------
`--zip` builds it as a plain folder you can carry off and place by
hand, wherever you decide is actually locked. That is on purpose:
this session can only reach one locked place, so choosing where it
lives is yours and not mine.

**The `private/` folder made here is not storage.** It is ignored by
git so nothing in it can be committed by accident, but the machine
this runs on is wiped when the session ends. It is a workbench, not a
safe.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, "WITHHELD.md")


def rows():
    """The gaps, read off WITHHELD.md. The field names only, never values."""
    out = []
    try:
        text = open(SHEET, encoding="utf-8").read()
    except OSError:
        return out
    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("`", "") for c in line.strip("|").split("|")]
        if len(cells) < 5 or not re.fullmatch(r"W-\d+", cells[0]):
            continue
        out.append({"tag": cells[0], "name": cells[1], "state": cells[2],
                    "where": cells[3], "why": cells[4]})
    return out


def slug(text):
    keep = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return keep[:40] or "unnamed"


# Only these states describe something that could ever be put in a
# slot. `not collected` means we decided not to have it, and making a
# slot for it would invite filling it.
WANTED = ("refused", "withheld", "unknown", "elsewhere")


def build(into, carryable=False):
    rooms = [r for r in rows() if r["state"] in WANTED]
    os.makedirs(into, exist_ok=True)

    made = []
    for r in rooms:
        folder = os.path.join(into, "%s-%s" % (r["tag"].lower(), slug(r["name"])))
        os.makedirs(folder, exist_ok=True)
        note = os.path.join(folder, "WHAT-BELONGS-HERE.txt")
        with open(note, "w", encoding="utf-8") as fh:
            fh.write(
                "%s  %s\n%s\n\n"
                "WHAT BELONGS HERE\n  %s\n\n"
                "STATE\n  %s\n\n"
                "WHERE IT IS NOW\n  %s\n\n"
                "WHY IT IS NOT IN THE REPOSITORY\n  %s\n\n"
                "This slot is empty on purpose. Nothing was copied into\n"
                "it, because this was built from the DIRECTORY of what is\n"
                "missing, not from the material itself.\n\n"
                "Before you put anything in, ask the questions:\n"
                "    python3 check-withheld.py --ask\n"
                % (r["tag"], r["name"], "=" * 60,
                   r["name"], r["state"], r["where"], r["why"]))
        made.append((r, folder))

    readme = os.path.join(into, "READ-ME-FIRST.txt")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write(CARRY_NOTE if carryable else WORKBENCH_NOTE)
        fh.write("\n\nTHE SLOTS\n%s\n" % ("-" * 60))
        for r, folder in made:
            fh.write("  %-10s %-34s %s\n"
                     % (r["tag"], os.path.basename(folder), r["state"]))
        fh.write("\n%d slot%s, all empty.\n"
                 % (len(made), "" if len(made) == 1 else "s"))
    return made, readme


WORKBENCH_NOTE = """\
THE PRIVATE CONTAINER -- the copy inside the working folder
============================================================

This one is a WORKBENCH, NOT A SAFE.

  * git will not take it. It is in .gitignore, so nothing in here
    can be committed by accident, and this repository is PUBLIC.

  * It does not survive. If this is a cloud session, the whole
    machine is wiped when the session ends and this goes with it.

So: work in here, then move anything worth keeping somewhere that
is actually locked. `WITHHELD.md` lists every place this project
knows about and says plainly which of them are locked. Of the ones
a session can reach, exactly one is.

To get a copy you can carry away and place by hand:

    python3 make-private.py --zip
"""

CARRY_NOTE = """\
THE PRIVATE CONTAINER -- the copy you carry away
=================================================

This folder is yours to PLACE BY HAND, or not place at all.

Nothing private is in it. Every slot is empty and labelled with what
belongs there, because it was built from the directory of what is
missing rather than from the material.

WHERE TO PUT IT -- your decision, and deliberately not mine

  A locked place      your own phone or laptop, a private
                      repository, or a drive only you can open
  Not here            do not put it back inside the public
                      repository. A deleted file stays in the
                      history, and there is no undo on a push

Before you put anything into a slot, the questions are worth asking,
and there is a program that walks them:

    python3 check-withheld.py --ask

It asks where the material came out of, whether that place is really
LOCKED rather than merely feeling private, and what copies get left
behind. If any answer is "not sure", it says so and stops.
"""


def main(argv=()):
    argv = list(argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    carry = "--zip" in argv
    into = os.path.join(HERE, "private-container" if carry else "private")
    if "--into" in argv:
        i = argv.index("--into")
        if i + 1 < len(argv):
            into = os.path.abspath(os.path.expanduser(argv[i + 1]))

    made, readme = build(into, carryable=carry)
    print()
    print("made %d empty slot%s in %s"
          % (len(made), "" if len(made) == 1 else "s", into))
    for r, folder in made:
        print("  %-8s %s" % (r["tag"], os.path.basename(folder)))
    print()
    print("Nothing was copied in. Read %s first."
          % os.path.basename(readme))
    if carry:
        print("\nThis copy is yours to place by hand. It is not in")
        print(".gitignore, so do not leave it inside the repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
