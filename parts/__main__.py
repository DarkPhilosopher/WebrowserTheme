#!/usr/bin/env python3
"""The package's own command line.

    python3 -m parts                    list every block
    python3 -m parts Ray                explain one block
    python3 -m parts install            make `import parts` work anywhere
    python3 -m parts where              say whether that is done
    python3 -m parts connect <thing>    find what touches a thing
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

    from . import describe, blocks
    if argv and not argv[0].startswith("-"):
        describe(argv[0])
        return 0

    describe()
    print("\n%d blocks. python3 -m parts <Name> explains one." % len(blocks()))
    print("python3 -m parts install   makes `import parts` work from anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
