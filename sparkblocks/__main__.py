#!/usr/bin/env python3
"""The package's own command line.

    python3 -m sparkblocks                    list every block
    python3 -m sparkblocks Ray                explain one block
    python3 -m sparkblocks install            make `import sparkblocks` work anywhere
    python3 -m sparkblocks where              say whether that is done
    python3 -m sparkblocks connect <thing>    find what touches a thing
    python3 -m sparkblocks run prog.parts     run a plain-text program
    python3 -m sparkblocks menu               build one with numbers only
    python3 -m sparkblocks pad                build one by pressing squares
    python3 -m sparkblocks saves             your own programs, and where they live
    python3 -m sparkblocks outside           blocks from somewhere else, and where from
    python3 -m sparkblocks check              make sure it all still hangs together
    python3 -m sparkblocks json <file>        write the language out as JSON
"""

import sys


def main(argv):
    if argv and argv[0] == "install":
        from .install import main as go
        return go(argv[1:])

    if argv and argv[0] in ("where", "status"):
        from .install import where
        return where()

    if argv and argv[0] == "connect":
        from .connect import main as go
        return go(argv[1:])

    if argv and argv[0] == "run":
        from .script import main as go
        return go(argv[1:])

    if argv and argv[0] in ("json", "book"):
        from .book import main as go
        return go(argv[1:])

    if argv and argv[0] in ("check", "test"):
        from .check import main as go
        return go(argv[1:])

    if argv and argv[0] == "pad":
        from .pad import main as go
        return go(argv[1:])

    if argv and argv[0] in ("saves", "mine"):
        from .saves import main as go
        return go(argv[1:])

    if argv and argv[0] in ("outside", "extra"):
        from .outside import main as go
        return go(argv[1:])

    if argv and argv[0] == "menu":
        from .menu import main as go
        return go(argv[1:])

    from . import describe, blocks
    if argv and not argv[0].startswith("-"):
        describe(argv[0])
        return 0

    describe()
    print("\n%d blocks. python3 -m sparkblocks <Name> explains one." % len(blocks()))
    print("python3 -m sparkblocks install   makes `import sparkblocks` work from anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
