#!/usr/bin/env python3
"""install -- teach Python where this folder is, once, forever.

    python3 /wherever/parts/install.py

After that, `import parts` works from any folder, in any script, without
PYTHONPATH and without copying anything. Move the folder later and just
run it again.

    python3 /wherever/parts/install.py --remove     # undo it
    python3 /wherever/parts/install.py --where      # say what is installed

HOW IT WORKS
------------
Python reads every `.pth` file in its site-packages folder at startup and
adds each line of them to the import path. So a one-line file naming this
folder's parent is all it takes. Nothing is copied, nothing is compiled,
and the blocks stay exactly where you keep them.
"""

import os
import site
import subprocess
import sys

NAME = "parts.pth"


def home_of_parts():
    """The folder that CONTAINS this package -- the line we need to add."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def candidates():
    """Places Python will read a .pth from, best first."""
    out = []
    try:
        user = site.getusersitepackages()
        if isinstance(user, str):
            out.append(user)
    except Exception:
        pass
    try:
        out.extend(site.getsitepackages())
    except Exception:
        pass
    # Termux and some builds report nothing useful; work it out by hand.
    guess = os.path.join(sys.prefix, "lib",
                         "python%d.%d" % sys.version_info[:2],
                         "site-packages")
    out.append(guess)
    seen, unique = set(), []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def installed():
    """Every .pth we have written, as (file, folder it points at)."""
    found = []
    for folder in candidates():
        path = os.path.join(folder, NAME)
        if os.path.exists(path):
            try:
                found.append((path, open(path).read().strip()))
            except OSError:
                pass
    return found


def works_from_elsewhere():
    """Start a fresh Python somewhere else and see if it can import parts."""
    where = os.path.expanduser("~")
    if where == home_of_parts():
        where = "/"
    try:
        out = subprocess.run(
            [sys.executable, "-c",
             "import parts; print(parts.__file__)"],
            cwd=where, capture_output=True, text=True, timeout=30)
        return out.returncode == 0, (out.stdout or out.stderr).strip()
    except Exception as e:
        return False, str(e)


def install():
    line = home_of_parts()
    for folder in candidates():
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, NAME)
            with open(path, "w") as fh:
                fh.write(line + "\n")
        except OSError:
            continue

        ok, said = works_from_elsewhere()
        if ok:
            print("installed.")
            print("  wrote  %s" % path)
            print("  naming %s" % line)
            print("  proved %s" % said)
            print("\n`import parts` now works from any folder.")
            return 0
        # written but not picked up -- clean it up and try the next place
        try:
            os.remove(path)
        except OSError:
            pass

    print("could not find a site-packages folder Python would read.")
    print("Use this instead, which does the same job:\n")
    print('  echo \'export PYTHONPATH="%s:$PYTHONPATH"\' >> ~/.bashrc' % line)
    print("  source ~/.bashrc")
    return 1


def remove():
    gone = 0
    for path, _line in installed():
        try:
            os.remove(path)
            print("removed %s" % path)
            gone += 1
        except OSError as e:
            print("could not remove %s: %s" % (path, e))
    if not gone:
        print("nothing was installed.")
    return 0


def where():
    here = home_of_parts()
    print("this copy lives in   %s" % here)
    found = installed()
    if not found:
        print("installed           no")
    for path, line in found:
        mark = "" if line == here else "   <-- points somewhere else"
        print("installed           %s%s" % (line, mark))
        print("  via               %s" % path)
    ok, said = works_from_elsewhere()
    print("imports from anywhere %s" % ("yes" if ok else "no"))
    if ok:
        print("  resolves to       %s" % said)
    return 0


def main(argv):
    if "--remove" in argv or "--uninstall" in argv:
        return remove()
    if "--where" in argv or "--status" in argv:
        return where()
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    return install()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
