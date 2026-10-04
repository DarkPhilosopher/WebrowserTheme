#!/usr/bin/env python3
"""check-withheld -- make sure the directory of what is missing is honest.

    python3 check-withheld.py          is the directory still true
    python3 check-withheld.py --ask    something private is moving

`WITHHELD.md` says what has been left out of this repository, where it
went, and why. This checks that it still tells the truth.

A directory nobody checks drifts, and a drifted withdrawal sheet is
worse than having none at all: it sends you looking for something in a
place it is not, and you trust it while it does.

WHAT IT CHECKS
--------------
    every marker has a row     no ⟦W-nn⟧ points at nothing
    every row says where and why   a gap with no reason is not recorded
    every state is a real one  no invented words
    no value leaked in         the page names FIELDS, never values
    git is not carrying private/   the one that actually matters

It reads the repository it sits in, needs nothing installed, and says
what it looked at as well as what was wrong.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, "WITHHELD.md")

MARKER = re.compile(r"⟦(W-\d+)([^⟧]*)⟧")

STATES = ("refused", "withheld", "elsewhere",
          "not collected", "unknown", "out of order")

# The page promises to name the field and never the value. These are
# what a value tends to look like when one slips in.
LOOKS_LIKE_A_VALUE = [
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "a date"),
    (re.compile(r"\b(?:19|20)\d{2}\b"),          "a year"),
    (re.compile(r"\b\d{3}[- ]\d{3}[- ]\d{4}\b"), "a phone number"),
    (re.compile(r"\b\d+\s+[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road)\b"),
     "a street address"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "an email address"),
]

SKIP_DIRS = {".git", "__pycache__", "node_modules", "private", ".cache"}
READABLE = (".md", ".py", ".sh", ".html", ".json", ".txt", ".spark", ".parts")


class Report:
    def __init__(self):
        self.checks, self.faults, self.notes = 0, [], []

    def looked(self, n=1):
        self.checks += n

    def fault(self, where, why):
        self.faults.append((where, why))

    def note(self, line):
        self.notes.append(line)

    @property
    def ok(self):
        return not self.faults


# ==========================================================================
#  READING WHAT THERE IS
# ==========================================================================

def rows():
    """The directory, as [{tag, name, state, where, why}].

    Reads the one table whose first column is a `W-nn` tag, so the
    other tables on the page -- the states, the places -- are left
    alone.
    """
    out = []
    try:
        text = open(SHEET, encoding="utf-8").read()
    except OSError as e:
        return out, "cannot read WITHHELD.md: %s" % e

    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("`", "") for c in line.strip("|").split("|")]
        if len(cells) < 5 or not re.fullmatch(r"W-\d+", cells[0]):
            continue
        out.append({"tag": cells[0], "name": cells[1], "state": cells[2],
                    "where": cells[3], "why": cells[4]})
    return out, None


def markers():
    """Every ⟦W-nn⟧ in the repository, as {tag: [(file, line)]}."""
    found = {}
    for here, dirs, names in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if not name.endswith(READABLE):
                continue
            path = os.path.join(here, name)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for n, line in enumerate(text.split("\n"), 1):
                for tag, _words in MARKER.findall(line):
                    where = os.path.relpath(path, HERE)
                    # The sheet explains the format; its own example is
                    # not a gap in anything.
                    if where == "WITHHELD.md":
                        continue
                    found.setdefault(tag, []).append((where, n))
    return found


# ==========================================================================
#  THE CHECKS
# ==========================================================================

def every_marker_has_a_row(r, sheet, marks):
    known = {row["tag"] for row in sheet}
    for tag, places in sorted(marks.items()):
        r.looked()
        if tag not in known:
            at = ", ".join("%s:%d" % p for p in places)
            r.fault(tag, "is marked at %s but has no row in WITHHELD.md. "
                         "A marker that points at nothing is worse than no "
                         "marker: it says the thing is written down "
                         "somewhere, and it is not." % at)


def every_row_says_where_and_why(r, sheet):
    for row in sheet:
        r.looked(2)
        if not row["why"] or row["why"] == "—":
            r.fault(row["tag"], "has no reason. A gap with no reason is not "
                                "recorded, it is just missing")
        if (not row["where"] or row["where"] == "—") and \
                row["state"] not in ("unknown", "not collected"):
            r.fault(row["tag"],
                    "is %r but does not say where it went. Only `unknown` "
                    "and `not collected` are allowed to have nowhere to "
                    "point." % row["state"])


def every_state_is_a_real_one(r, sheet):
    for row in sheet:
        r.looked()
        if row["state"] not in STATES:
            r.fault(row["tag"],
                    "has the state %r, which is not one of: %s"
                    % (row["state"], ", ".join(STATES)))


def no_value_leaked_in(r, sheet):
    """The page names the FIELD, never the VALUE. Hold it to that.

    `where` is exempt, and only `where`. That column exists to say
    where to GO -- an account, a folder, a machine. A location there
    is the column doing its job, not a leak. `name` and `why` have no
    such excuse: a name is what the thing is, and a reason is why it
    is absent, and neither needs the thing itself to say it.
    """
    for row in sheet:
        r.looked()
        blob = " ".join((row["name"], row["why"]))
        for pattern, what in LOOKS_LIKE_A_VALUE:
            hit = pattern.search(blob)
            if hit:
                r.fault(row["tag"],
                        "looks like it contains %s (%r). This page names "
                        "what is missing, never the thing itself -- that is "
                        "what makes it safe to publish."
                        % (what, hit.group(0)))


def is_a_git_repo():
    """Is git even in play here?

    An unpacked zip is not a repository, and in that case there is
    nothing that could commit anything by accident. Saying `private/
    is NOT in .gitignore` there is a false alarm, and a checker that
    cries wolf stops being read.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                             cwd=HERE, capture_output=True, text=True,
                             timeout=30)
        return out.returncode == 0 and out.stdout.strip() == "true"
    except Exception:
        return False


def git_is_not_carrying_private(r):
    """The one that actually matters."""
    if not is_a_git_repo():
        r.note("this is not a git repository -- an unpacked copy, most "
               "likely. Nothing here can be committed by accident, so "
               "the two git checks were not run.")
        return

    r.looked()
    try:
        out = subprocess.run(["git", "ls-files", "private/"], cwd=HERE,
                             capture_output=True, text=True, timeout=30)
    except Exception as e:
        r.note("could not ask git (%s) -- checked nothing" % e)
        return
    carried = [f for f in out.stdout.split("\n") if f.strip()]
    if carried:
        r.fault("private/", "git is tracking %d file(s) in there: %s\n"
                            "       Take them out with: git rm --cached <file>"
                            % (len(carried), ", ".join(carried[:5])))

    r.looked()
    ignored = subprocess.run(["git", "check-ignore", "-q", "private/x"],
                             cwd=HERE, capture_output=True)
    if ignored.returncode != 0:
        r.fault("private/", "is NOT in .gitignore. Anything put there could "
                            "be committed by accident, and a public history "
                            "cannot be taken back")


def rows_with_no_marker(r, sheet, marks):
    """Noted, not faulted -- some gaps are a whole missing thing."""
    for row in sheet:
        if row["tag"] not in marks:
            r.note("%s (%s) has no marker anywhere. Fine when the whole "
                   "thing is absent -- there is no page left to mark."
                   % (row["tag"], row["name"]))


# ==========================================================================
#  ASKING, BEFORE SOMETHING MOVES
#
#  Material does not arrive and get filed. The point of these is to
#  make "I assumed it was private" impossible to say by accident.
# ==========================================================================

COMING_IN = [
    ("name", "What is it, by name? The FIELD, not the value.",
     "If you cannot name it without writing the thing down, it does "
     "not belong on that page at all."),
    ("from", "Which container did it come out of? Name it.",
     "`my notes` is not a container. `Drive/xzg4b3xz` is. "
     "`the A33, Termux home` is."),
    ("locked", "Is that container actually LOCKED? (yes/no/not sure)",
     "Not felt private -- locked. Who else can open it? Is there a "
     "share link? Was it ever public, even briefly?"),
    ("allowed", "Did Gabriel permit THIS material to come here? (yes/no)",
     "Permission for one thing is not permission for the next."),
]

GOING_OUT = [
    ("name", "What is it, by name? The FIELD, not the value.", ""),
    ("to", "Where exactly is it going?",
     "Name the container, not the person."),
    ("locked", "Is THAT container locked? (yes/no/not sure)", ""),
    ("route", "Does the route pass anywhere open? (yes/no/not sure)",
     "A file handed over in the chat has been through the "
     "conversation. A commit has been through the history. Neither "
     "can be taken back."),
    ("copies", "What copies get left behind, and who clears them?",
     "The session scratchpad, a zip in Downloads, a branch, a reflog."),
]

VAGUE = ("not sure", "dunno", "?", "unsure", "don't know",
         "dont know", "unknown", "maybe", "")

# Which answer is the SAFE one differs per question, and getting that
# backwards is the whole danger. "Is it locked? -- no" and "does the
# route pass anywhere open? -- yes" are both bad news, but they are
# opposite words. Say so once, here, rather than in an if.
SAFE = {
    "locked":  ("yes", "y"),          # anything else, including no
    "allowed": ("yes", "y"),
    "route":   ("no", "n"),           # yes means it goes through the open
}

TROUBLE = {
    "locked":  "that the container is locked",
    "allowed": "that Gabriel permitted it",
    "route":   "that the route stays out of the open",
}


def worrying(key, answer):
    """Is this answer a reason to stop?"""
    if key not in SAFE:
        return False
    said = answer.strip().lower()
    return said in VAGUE or said not in SAFE[key]


def ask_about(which, questions):
    print("\n%s\n%s" % (which, "-" * len(which)))
    answers, doubt = {}, []
    for key, question, note in questions:
        print("\n  %s" % question)
        if note:
            for bit in note.split(". "):
                print("    %s" % bit.rstrip("."))
        try:
            got = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  stopped. Nothing moves.")
            return None
        answers[key] = got
        if worrying(key, got):
            doubt.append(key)
    return answers, doubt


def ask(argv=()):
    """Walk the questions, then print the row to paste in."""
    print(__doc__.split("WHAT IT CHECKS")[0].strip())
    print("\nWhich way is it moving?")
    print("  1. coming in  -- something private is arriving here")
    print("  2. going out  -- something private is leaving")
    try:
        way = input("\n  1 or 2: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0

    got = ask_about("Coming in", COMING_IN) if way == "1" else \
          ask_about("Going out", GOING_OUT)
    if got is None:
        return 1
    answers, doubt = got

    print("\n" + "=" * 58)
    if doubt:
        print("\nSTOP. These are not settled:")
        for key in doubt:
            print("    %-8s you answered %r" % (key, answers[key]))
        print("""
Then the state is `unknown`, and the material does not move until it
is not. `unknown` is an honest row. A guess is not, and a wrong guess
about whether somewhere is locked is the one mistake here that cannot
be taken back.

Add this row to WITHHELD.md and leave the material where it is:
""")
        print("| `W-nn` | %s | unknown | %s | not moved: could not confirm "
              "%s |"
              % (answers.get("name", "?"),
                 answers.get("from") or answers.get("to") or "—",
                 ", and ".join(TROUBLE[k] for k in doubt)))
        return 1

    print("\nNothing unanswered. The row to add:\n")
    if way == "1":
        print("| `W-nn` | %s | withheld | %s | came from %s, confirmed "
              "locked; Gabriel permitted it |"
              % (answers["name"], answers["from"], answers["from"]))
    else:
        print("| `W-nn` | %s | elsewhere | %s | confirmed locked, route "
              "stays closed; copies left: %s |"
              % (answers["name"], answers["to"],
                 answers.get("copies") or "none stated"))
    print("\nThen: python3 check-withheld.py")
    return 0


# ==========================================================================
#  SAYING IT
# ==========================================================================

def main(argv=()):
    if "--ask" in argv:
        return ask(argv)

    sheet, trouble = rows()
    if trouble:
        print("\n%s\n" % trouble)
        return 1

    marks = markers()
    r = Report()

    every_marker_has_a_row(r, sheet, marks)
    every_row_says_where_and_why(r, sheet)
    every_state_is_a_real_one(r, sheet)
    no_value_leaked_in(r, sheet)
    git_is_not_carrying_private(r)
    rows_with_no_marker(r, sheet, marks)

    print()
    print("%d row%s in WITHHELD.md, %d marker%s in the repository"
          % (len(sheet), "" if len(sheet) == 1 else "s",
             sum(len(v) for v in marks.values()),
             "" if sum(len(v) for v in marks.values()) == 1 else "s"))

    for row in sheet:
        used = len(marks.get(row["tag"], ()))
        print("  %-5s %-34s %-14s %s"
              % (row["tag"], row["name"][:34], row["state"],
                 ("marked %dx" % used) if used else "no marker"))

    if r.notes:
        print("\nnoted:")
        for line in r.notes:
            print("  %s" % line)

    print()
    if r.ok:
        print("%d checked, all well." % r.checks)
        return 0
    for where, why in r.faults:
        print("  WRONG  %s %s" % (where, why))
    print("\n%d checked, %d wrong." % (r.checks, len(r.faults)))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
