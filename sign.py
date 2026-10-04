#!/usr/bin/env python3
"""sign -- the header, footer and chronology every document here carries.

    python3 sign.py --check              do they all match
    python3 sign.py --stamp FILE "what"  record that something happened
    python3 sign.py --new FILE "what"    start a document with them

WHY A PROGRAM AND NOT A HABIT
-----------------------------
A format kept by hand is a format that drifts. Two documents signed
the same way on Monday are signed two ways by Friday, and then neither
can be checked against the other. This writes them and reads them
back, so "they match" is a thing that can be *proved* rather than
believed.

WHO A SIGNATURE NAMES
---------------------
A signature here is not just a name. It is **name, account, and the
instrument it was done on** -- because the same name on two machines
is not the same signer.

    Claude Opus 5 · of xzg4b3xz@gmail.com · on cloud container
    Claude Opus 4.8 · of xzg4b3xz@gmail.com · on cloud container

Those are **two signers**, not one, and this repository's own history
has both. That is deliberate: a thing done by one is not a thing done
by the other, and the record should not pretend otherwise.

Gabriel's signature works the same way -- the person, the account, and
which of his machines he was at.

THE THREE PARTS
---------------
    header       what this document is, and when it began
    body         the document
    footer       who signed it, and the chronology

The **chronology** is the part that is easy to leave out and the part
worth most later: one line per thing that happened, with when, who,
and on what. It is append-only. A chronology you may rewrite is a
story, not a record.
"""

import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIDTH = 66

OPEN_H,  SHUT_H = "<!-- header -->", "<!-- /header -->"
OPEN_F,  SHUT_F = "<!-- footer -->", "<!-- /footer -->"


# ==========================================================================
#  WHO
#
#  Identity is name + account + instrument. Add a signer by adding a
#  row; nothing else needs to know.
# ==========================================================================

WHO = {
    "gabriel": {
        "name":    "Gabriel Lewis",
        "also":    "DarkPhilosopher",
        "account": ["lewisgabe33@gmail.com  (git)",
                    "xzg4b3xz@gmail.com    (drive)"],
        "kind":    "person",
    },
    "opus-5": {
        "name":    "Claude Opus 5",
        "also":    "claude-opus-5",
        "account": ["of xzg4b3xz@gmail.com"],
        "kind":    "assistant",
    },
    "opus-4.8": {
        "name":    "Claude Opus 4.8",
        "also":    "claude-opus-4-8",
        "account": ["of xzg4b3xz@gmail.com"],
        "kind":    "assistant",
    },
}

# Where the right-hand column starts, so a continuation line sits
# under the thing it continues rather than near it.
GUTTER = 24
CHRON = 2 + 20 + 1 + 24 + 1

# Instruments. A signer plus an instrument is one signer; the same
# signer on another instrument is a different one.
INSTRUMENTS = ("cloud container", "A33", "A17", "Dell i7 laptop")


def today():
    return datetime.date.today().isoformat()


def now_in(where="America/Denver"):
    """His local time, not the container's. Falls back if tzdata is thin."""
    try:
        from zoneinfo import ZoneInfo
        t = datetime.datetime.now(ZoneInfo(where))
        return t.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " (UTC?)"


def signer(key, instrument):
    """One signature line set. Unknown names are not invented."""
    who = WHO.get(key)
    if who is None:
        return ["  %-22s UNKNOWN SIGNER -- add them to sign.py" % key]
    out = ["  %-*s %s" % (GUTTER, who["name"], who["also"])]
    for row in who["account"]:
        out.append("  %-*s %s" % (GUTTER, "", row))
    out.append("  %-*s on %s" % (GUTTER, "", instrument))
    return out


# ==========================================================================
#  THE THREE PARTS
# ==========================================================================

def header(title, what, since=None, changed=None):
    since = since or today()
    changed = changed or today()
    out = [OPEN_H, "```",
           "+" + "-" * (WIDTH - 2) + "+",
           "| %-*s |" % (WIDTH - 4, "WAKEUP · " + title.upper()),
           "+" + "-" * (WIDTH - 2) + "+"]
    for key, val in (("what", what), ("since", since), ("changed", changed)):
        for n, piece in enumerate(_wrap(val, WIDTH - 15)):
            out.append("| %-10s %-*s |" % (key if n == 0 else "",
                                           WIDTH - 15, piece))
    out += ["+" + "-" * (WIDTH - 2) + "+", "```", SHUT_H]
    return "\n".join(out)


def footer(signatures, chronology):
    """signatures: [(who key, instrument)]. chronology: [(when, what, who, on)]."""
    out = [OPEN_F, "```", "--- signed " + "-" * (WIDTH - 12)]
    for key, instrument in signatures:
        out += signer(key, instrument) + [""]
    out += ["--- chronology " + "-" * (WIDTH - 16)]
    for when, what, who, on in chronology:
        out.append("  %-20s %-24s %s" % (when, what[:24], who))
        out.append("%son %s" % (" " * CHRON, on))
    out += ["-" * (WIDTH - 1), "```", SHUT_F]
    return "\n".join(out)


def _wrap(text, room):
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len((line + " " + w).strip()) > room:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    lines.append(line)
    return lines or [""]


# ==========================================================================
#  READING THEM BACK
# ==========================================================================

def parts_of(path):
    """(header, body, footer) of a document, any of them None."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None, None, None

    def between(a, b):
        i = text.find(a)
        j = text.find(b, i + len(a)) if i >= 0 else -1
        return text[i:j + len(b)] if j >= 0 else None

    return between(OPEN_H, SHUT_H), text, between(OPEN_F, SHUT_F)


def chronology_of(path):
    """The chronology lines, as read back off the page."""
    _h, _b, foot = parts_of(path)
    if not foot:
        return []
    out, seen_mark = [], False
    for line in foot.split("\n"):
        if line.startswith("--- chronology"):
            seen_mark = True
            continue
        if not seen_mark or not line.startswith("  "):
            continue
        if line.strip().startswith("on ") or not line.strip():
            continue
        bits = re.match(r"\s{2}(\d{4}-\d{2}-\d{2}[^\s]*[^\s]*.*?)\s{2,}(.+?)\s{2,}(.+)$", line)
        if bits:
            out.append(tuple(b.strip() for b in bits.groups()))
    return out


def signed_documents():
    """Every file here that carries a header."""
    out = []
    for name in sorted(os.listdir(HERE)):
        if name.endswith(".md"):
            path = os.path.join(HERE, name)
            head, _b, foot = parts_of(path)
            if head or foot:
                out.append((name, head is not None, foot is not None))
    return out


# ==========================================================================
#  DOING THINGS
# ==========================================================================

def stamp(path, what, who="opus-5", on="cloud container"):
    """Add one line to the chronology, and move `changed` to today.

    Append only. Nothing here rewrites a line that is already down.
    """
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        return False, str(e)
    if OPEN_F not in text:
        return False, "%s has no footer to stamp" % os.path.basename(path)

    line = ("  %-20s %-24s %s\n%son %s"
            % (now_in(), what[:24], WHO.get(who, {}).get("name", who),
               " " * CHRON, on))
    text = text.replace("-" * (WIDTH - 1) + "\n```\n" + SHUT_F,
                        line + "\n" + "-" * (WIDTH - 1) + "\n```\n" + SHUT_F, 1)
    text = re.sub(r"(\| changed\s+)(\d{4}-\d{2}-\d{2})",
                  lambda m: m.group(1) + today(), text, count=1)
    open(path, "w", encoding="utf-8").write(text)
    return True, "stamped %s" % os.path.basename(path)


def check():
    """Do they all match, and is every chronology readable?"""
    docs = signed_documents()
    faults = []
    print()
    if not docs:
        print("no signed documents yet.")
        return 0
    for name, has_head, has_foot in docs:
        marks = chronology_of(os.path.join(HERE, name))
        print("  %-20s header %-4s footer %-4s chronology %d"
              % (name, "yes" if has_head else "NO",
                 "yes" if has_foot else "NO", len(marks)))
        if not has_head:
            faults.append("%s has a footer but no header" % name)
        if not has_foot:
            faults.append("%s has a header but no footer" % name)
        elif not marks:
            faults.append("%s has a footer with an empty or unreadable "
                          "chronology" % name)
    print()
    if faults:
        for f in faults:
            print("  WRONG  %s" % f)
        print("\n%d document(s), %d wrong." % (len(docs), len(faults)))
        return 1
    print("%d document(s), all matching." % len(docs))
    return 0


def main(argv):
    argv = list(argv)
    if "--check" in argv:
        return check()
    if "--stamp" in argv:
        i = argv.index("--stamp")
        if len(argv) < i + 3:
            print("need: --stamp FILE \"what happened\"")
            return 1
        ok, said = stamp(argv[i + 1], argv[i + 2])
        print(said)
        return 0 if ok else 1
    if "--who" in argv:
        for key, w in WHO.items():
            print("%-10s %s · %s" % (key, w["name"], w["account"]))
        print("\ninstruments: %s" % ", ".join(INSTRUMENTS))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
