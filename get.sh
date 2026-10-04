#!/bin/sh
# get.sh -- put Wakeup on this machine, from github, with nothing else needed.
#
# TWO WAYS IN. Either works; pick whichever you can paste.
#
#   One line, if you have curl:
#
#     curl -fsSL https://raw.githubusercontent.com/DarkPhilosopher/WebrowserTheme/refs/heads/claude/new-session-y0nuxy/get.sh | sh
#
#   Three lines, if you do not -- Termux ships without curl:
#
#     pkg install git -y
#     git clone -b claude/new-session-y0nuxy https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup
#     sh ~/wakeup/get.sh
#
# Run it again any time. It pulls instead of cloning, and changes
# nothing it has already done, so there is no way to run it twice and
# make a mess.
#
# Plain /bin/sh on purpose. Termux has bash, but a phone that is part
# way through being set up may not, and this is the thing that sets it up.

set -e

REPO="https://github.com/DarkPhilosopher/WebrowserTheme"

# If this script is already sitting inside a clone, THAT clone is the
# one meant -- not a second copy at the default path. Without this,
# cloning to ~/w and running ~/w/get.sh quietly made a whole second
# copy in ~/wakeup and set everything up to point at the wrong one.
#
# Piped from curl, $0 is not a path, so the dirname is only trusted
# when get.sh is actually found in it.
SELF_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)" || SELF_DIR=""
if [ -n "$SELF_DIR" ] && [ -f "$SELF_DIR/get.sh" ] && [ -d "$SELF_DIR/.git" ]; then
  INTO="${WAKEUP_INTO:-$SELF_DIR}"
else
  INTO="${WAKEUP_INTO:-$HOME/wakeup}"
fi

# Follow whichever branch this copy was cloned from, rather than a
# name written in here. Clone from `get` and updates come from `get`;
# clone from the working branch and they come from that. A hardcoded
# name would quietly drag one into the other on the first update.
BRANCH="$WAKEUP_BRANCH"
if [ -z "$BRANCH" ] && [ -d "$INTO/.git" ]; then
  BRANCH="$(git -C "$INTO" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
fi
# Written as a plain `if`, not as `[ ] || [ ] && x`. Whether that
# chain aborts under `set -e` depends on the shell, and this file
# runs on a phone where a silent early exit is very hard to see.
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
  BRANCH="get"
fi

say() { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }

# ---------------------------------------------------------------- where am I
IS_TERMUX=no
case "$PREFIX" in
  *com.termux*) IS_TERMUX=yes ;;
esac
[ -d /data/data/com.termux ] && IS_TERMUX=yes

say
say "Wakeup -- getting it onto this machine"
say "  from    $REPO"
say "  branch  $BRANCH"
say "  into    $INTO"
[ "$IS_TERMUX" = yes ] && say "  this looks like Termux on Android"

# ------------------------------------------------------------- what it needs
step "the two things it needs: git and python"
if [ "$IS_TERMUX" = yes ]; then
  # pkg is happy to be asked for something already installed.
  pkg install -y git python || {
    say "pkg could not install them. Try once by hand:"
    say "    pkg update"
    say "    pkg install git python -y"
    exit 1
  }
else
  for need in git python3; do
    command -v "$need" >/dev/null || {
      say "This machine has no $need, and I will not guess how to install it."
      say "On Debian or Ubuntu:   sudo apt install git python3"
      say "On Windows:            get them from git-scm.com and python.org"
      exit 1
    }
  done
  say "both already here"
fi

PY=python3
command -v python3 >/dev/null || PY=python

# ------------------------------------------------------------------ the files
step "the files"
if [ -d "$INTO/.git" ]; then
  say "already there -- updating instead"
  cd "$INTO"

  # Your own programs come out first. Saving used to land them in
  # this folder, where a pull can collide with them and where they
  # look like changes to the project. They are moved to
  # ~/.wakeup/programs, which no update ever touches, and nothing of
  # the project's own is moved -- git is asked which is which.
  "$PY" "$INTO/sparkblocks/saves.py" --adopt "$INTO" 2>/dev/null || true

  # Never force. If there is something here worth keeping that git
  # does not know about, it stays, and the pull says so rather than
  # rolling over it.
  git fetch origin "$BRANCH"
  git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" "origin/$BRANCH"
  if ! git pull origin "$BRANCH"; then
    say ""
    say "The update stopped, and nothing was thrown away."
    say "Usually that means a file here has been changed by hand."
    say "See what:    cd $INTO && git status"
    say "Keep yours:  git stash        (then run this again)"
    exit 1
  fi
elif [ -d "$INTO" ] && [ "$(ls -A "$INTO" 2>/dev/null)" ]; then
  say "$INTO already has things in it and is not a git copy."
  say "I will not write over it. Move it, or name somewhere else:"
  say "    WAKEUP_INTO=\$HOME/wakeup2 sh $0"
  exit 1
else
  git clone --depth 20 -b "$BRANCH" "$REPO" "$INTO"
  cd "$INTO"
fi
say "got it: $INTO"

# Programs you save live outside this folder on purpose, so deleting
# the whole thing and starting again never loses them.
if [ -d "$HOME/.wakeup/programs" ]; then
  say "your own programs stay in ~/.wakeup/programs -- untouched"
fi

# ------------------------------------------- make `import sparkblocks` work
step "making the blocks reachable from any folder"
"$PY" "$INTO/sparkblocks/install.py" || say "  (carrying on without it)"

# --------------------------------------------------------- the `wakeup` word
step 'making the word `wakeup` work'
# Termux's own bin, or yours. Never a system folder -- this is your
# program, and it should not need root or write on anybody else's machine.
if [ "$IS_TERMUX" = yes ] && [ -w "$PREFIX/bin" ]; then
  BIN="$PREFIX/bin"
else
  BIN="$HOME/.local/bin"
  mkdir -p "$BIN"
fi

cat > "$BIN/wakeup" <<WRAP
#!/bin/sh
# Opens the terminal front door. Written by get.sh; safe to delete.
exec $PY "$INTO/wakeup.py" "\$@"
WRAP
chmod +x "$BIN/wakeup"
say "wrote $BIN/wakeup"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    say ""
    say "$BIN is not on your PATH yet. Add it once:"
    say "    echo 'export PATH=\"$BIN:\$PATH\"' >> ~/.bashrc"
    say "    . ~/.bashrc"
    ;;
esac

# -------------------------------------------------------------- shared files
if [ "$IS_TERMUX" = yes ] && [ ! -d "$HOME/storage/shared" ]; then
  step "seeing your own files"
  say "Termux cannot see the phone's storage until you let it. Run this"
  say "once and say yes to the box the phone shows:"
  say "    termux-setup-storage"
  say ""
  say "You only need it to open the Chrome panel or to copy the folder"
  say "into Download. Everything else works without it."
fi

# ---------------------------------------------------------------------- done
step "done"
say "Type this, and pick a number:"
say ""
say "    wakeup"
say ""
say "If the word is not found yet, this always works:"
say ""
say "    $PY $INTO/wakeup.py"
say ""
