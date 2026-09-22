#!/usr/bin/env python3
"""script -- write a program as plain text, one block a line.

    walk /sdcard
    keep ext .md
    keep
        read
        contains spark
    say found

No brackets, no commas, no Python. Each line names a block and gives it
its settings. The lines run top to bottom, the answer of each feeding the
next -- exactly like a Chain, because that is what it builds.

    python3 -m parts run find-notes.parts
    python3 -m parts run find-notes.parts --show     # print it, run nothing

THE RULES, ALL OF THEM
----------------------
1. A line is  `blockname setting setting`.
2. Blank lines are ignored. Anything after `#` is a note to yourself.
3. A block that holds another block -- keep, drop, each, gate, try --
   takes it either on the same line or indented underneath:

       keep ext .md                 # same line, one block
       keep                         # indented, a whole chain
           read
           contains spark

4. `fan` holds several branches, each marked with `-`, and combines them:

       fan all                      # all | any | sum | max | min | mul | list
           - ext .md
           - read
             contains spark

5. A setting that is a number becomes a number. `true`, `false` and
   `none` become themselves. Quote anything with a space in it.
6. `name=value` sets a setting by name: `copy into=~/out`.

Every block in the language is available, under its own name in lower
case. `python3 -m parts` lists them; `python3 -m parts Walk` explains one.
"""

import os
import re
import shlex
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import parts as _parts
    from parts import connect as _connect
    from parts.core import Chain, Fan, Part, run
else:
    _parts = sys.modules[__package__]
    from . import connect as _connect
    from .core import Chain, Fan, Part, run


# Blocks that hold another block rather than a plain setting.
HOLDERS = {"keep", "drop", "each", "gate", "try"}

# How a fan combines its branches.
FANWAYS = ("sum", "max", "min", "mul", "all", "any", "list", "first")


class ScriptError(Exception):
    """A problem in the text, with the line number that caused it."""


# ==========================================================================
#  READING THE TEXT
# ==========================================================================

class Line:
    __slots__ = ("n", "indent", "branch", "name", "args", "kids")

    def __init__(self, n, indent, branch, name, args):
        self.n, self.indent, self.branch = n, indent, branch
        self.name, self.args = name, args
        self.kids = []

    def __repr__(self):
        return "%s%s" % ("- " if self.branch else "", self.name)


def _split(raw):
    """Strip a trailing note, honouring quotes so a # inside one survives."""
    out, quote = [], None
    for ch in raw:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _value(word):
    """Turn a written setting into the thing it means."""
    low = word.lower()
    if low == "true":  return True
    if low == "false": return False
    if low == "none":  return None
    try:
        return int(word)
    except ValueError:
        pass
    try:
        return float(word)
    except ValueError:
        pass
    return word


ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}


def _clean(word):
    """Take the quotes off a setting, if it has any.

    Quotes only group words together. A backslash is left exactly as
    written -- `match \\.pdf$` must reach the regex with its backslash
    intact -- except inside quotes, where \\n and \\t mean what they look
    like, so a separator can be a newline.
    """
    if len(word) >= 2 and word[0] == word[-1] and word[0] in "\"'":
        body, out, i = word[1:-1], [], 0
        while i < len(body):
            if body[i] == "\\" and i + 1 < len(body) and body[i + 1] in ESCAPES:
                out.append(ESCAPES[body[i + 1]])
                i += 2
            else:
                out.append(body[i])
                i += 1
        return "".join(out)
    return word


def _words(text, n):
    """Split a line into its block name and settings."""
    try:
        # posix=False so a backslash is never eaten; quotes are stripped
        # afterwards by _clean, which is the only thing that may touch one.
        raw = shlex.split(text, posix=False)
    except ValueError as e:
        raise ScriptError("line %d: %s (an unclosed quote?)" % (n, e))
    return [_clean(w) for w in raw]


def _read_line(n, raw):
    body = _split(raw)
    if not body.strip():
        return None
    indent = len(body) - len(body.lstrip())
    text   = body.strip()

    branch = False
    if text.startswith("- "):
        branch, text = True, text[2:].strip()
    elif text == "-":
        raise ScriptError("line %d: a `-` on its own has no block after it" % n)

    words = _words(text, n)
    if not words:
        return None
    return Line(n, indent, branch, words[0].lower(), words[1:])


def _nest(lines):
    """Turn a flat list into a tree, by how far each line is indented."""
    root, stack = [], []
    for ln in lines:
        while stack and stack[-1].indent >= ln.indent:
            stack.pop()
        (stack[-1].kids if stack else root).append(ln)
        stack.append(ln)
    return root


# ==========================================================================
#  TURNING IT INTO BLOCKS
# ==========================================================================

def _registry():
    """Every block in the language, by its lower-case name."""
    out = {}
    for name in _parts.blocks():
        block = getattr(_parts, name, None)
        if block is not None:
            out[name.lower()] = block
    # connect's own four, so a program can use them too
    for extra in ("Words", "Urls", "Shared", "Among"):
        block = getattr(_connect, extra, None)
        if block is not None:
            out[extra.lower()] = block
    return out


def _near(name, known):
    """Names close enough to be what was meant."""
    import difflib
    hits = difflib.get_close_matches(name, list(known), n=5, cutoff=0.6)
    for k in sorted(known):
        if len(hits) >= 5:
            break
        if (k.startswith(name[:3]) or name in k or k in name) and k not in hits:
            hits.append(k)
    return hits


def _settings(args, n):
    """Split written settings into positional and named."""
    loose, named = [], {}
    for a in args:
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", a):
            key, _, val = a.partition("=")
            named[key] = _value(val)
        else:
            loose.append(_value(a))
    return loose, named


def _build(ln, known):
    """One line (and whatever is nested under it) becomes one block."""
    name = ln.name

    if name == "fan":
        how = "sum"
        if ln.args:
            how = str(ln.args[0]).lower()
            if how not in FANWAYS:
                raise ScriptError("line %d: fan cannot combine with %r. Use: %s"
                                  % (ln.n, how, ", ".join(FANWAYS)))
        branches = [k for k in ln.kids if k.branch]
        if not branches:
            raise ScriptError("line %d: fan needs branches, each starting `- `"
                              % ln.n)
        return Fan([_chain_of(b, known) for b in branches], how=how)

    if name not in known:
        near = _near(name, known)
        raise ScriptError("line %d: there is no block called %r.%s"
                          % (ln.n, name,
                             ("\n  Did you mean: " + ", ".join(near)) if near else ""))

    cls = known[name]
    loose, named = _settings(ln.args, ln.n)

    if name in HOLDERS:
        if ln.args and ln.kids:
            raise ScriptError("line %d: %s has a block on its own line AND "
                              "indented under it -- pick one" % (ln.n, name))
        if ln.args:
            inner = _build(Line(ln.n, ln.indent, False,
                                str(ln.args[0]).lower(), ln.args[1:]), known)
        elif ln.kids:
            inner = _chain_of(ln, known)
        else:
            raise ScriptError("line %d: %s needs a block to hold, either after "
                              "it or indented under it" % (ln.n, name))
        return cls(inner)

    if ln.kids:
        raise ScriptError("line %d: %s does not hold other blocks, but lines "
                          "are indented under it" % (ln.n, name))

    try:
        return cls(*loose, **named)
    except TypeError as e:
        raise ScriptError("line %d: %s does not take those settings (%s).\n"
                          "  Try: python3 -m parts %s"
                          % (ln.n, name, e, cls.__name__))


def _chain_of(parent, known):
    """The indented lines under a parent, as one chain."""
    kids = [k for k in parent.kids if not k.branch]
    if not kids:
        raise ScriptError("line %d: nothing is indented under %s"
                          % (parent.n, parent.name))
    return Chain([_build(k, known) for k in kids])


def parse(text):
    """Plain text in, one Chain out."""
    known = _registry()
    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        ln = _read_line(n, raw)
        if ln:
            lines.append(ln)
    if not lines:
        raise ScriptError("there are no blocks in this file")
    tree = _nest(lines)
    return Chain([_build(ln, known) for ln in tree])


def load(path):
    """Read a program off disk."""
    with open(os.path.expanduser(path)) as fh:
        return parse(fh.read())


def show(text):
    """Print what the text builds, without running it."""
    def walk(part, depth=0):
        pad = "    " * depth
        if isinstance(part, Chain):
            print("%sChain" % pad)
            for p in part.parts:
                walk(p, depth + 1)
        elif isinstance(part, Fan):
            print("%sFan how=%s" % (pad, part.how))
            for b in part.branches:
                walk(b, depth + 1)
        else:
            held = getattr(part, "test", None) or getattr(part, "part", None) \
                or getattr(part, "control", None)
            print("%s%s" % (pad, type(part).__name__))
            if isinstance(held, Part):
                walk(held, depth + 1)
    walk(parse(text))


# ==========================================================================
#  COMMAND LINE
# ==========================================================================

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    path = argv[0]
    if not os.path.exists(os.path.expanduser(path)):
        print("no such file: %s" % path)
        return 1

    try:
        text = open(os.path.expanduser(path)).read()
        if "--show" in argv:
            show(text)
            return 0
        answer = run(parse(text))
    except ScriptError as e:
        print("\n%s\n" % e)
        return 1

    # A program that ends in `say` has already spoken for itself.
    if answer is not None and not isinstance(answer, (list, tuple)):
        print(answer)
    elif isinstance(answer, (list, tuple)) and "--quiet" not in argv:
        print("%d item%s" % (len(answer), "" if len(answer) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
