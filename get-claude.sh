#!/bin/sh
# get-claude.sh -- one command, and this phone can run Claude.
#
# THE ONE COMMAND. Paste this whole line into Termux:
#
#   pkg install -y git && git clone --depth 1 -b get https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup && sh ~/wakeup/get-claude.sh
#
# THE SAME LINE WORKS ON A NEW PHONE AND ON ONE THAT HAS BEEN TRIED
# BEFORE. It checks everything first and only does what is missing,
# so there is nothing to decide and no separate "already tried this"
# version of it.
#
# If it has been run twice and is still stuck, there is one more rung:
#
#   sh ~/wakeup/get-claude.sh --replace
#
# which throws the Ubuntu away and fetches a clean one. It asks before
# doing it, and is worth trying only after the ordinary line has
# failed -- it costs the whole download again.
#
# It cannot be shorter, and here is exactly why. A fresh Termux has no
# curl, no wget and no git -- I checked its own bootstrap list rather
# than trusting memory. Its whole base is: apt bash bzip2 proot
# coreutils dash diffutils findutils gawk grep gzip less procps psmisc
# sed tar termux-core termux-exec termux-keyring termux-tools
# util-linux ed debianutils dos2unix inetutils lsof nano net-tools
# patch unzip. Nothing in that list can fetch a URL. So the first
# thing has to install something that can, and `pkg install git` is
# the shortest honest start.
#
# WHAT IT LEAVES YOU WITH
#
#   claude              starts Claude
#   claude --continue   carries on the last conversation
#
# both as plain words you type, from anywhere, with no alias to source
# and no proot line to remember.
#
# Run it again any time. Everything it does, it checks first, so a
# second run only fills in what is missing.

set -e

# --replace  throw the Ubuntu away and fetch it again, even if it
#            works. The last rung of the ladder:
#
#              update   reuse what is there, fetch only what is not
#              install  add what is missing
#              replace  remove it and start that part again
#
#            Each rung loses more. Nothing here climbs to `replace`
#            on its own -- it is asked for, and asked about.
REPLACE=""
for a in "$@"; do
  case "$a" in
    --replace|--start-over) REPLACE=1 ;;
    --yes|-y) ALREADY_SAID_YES=1 ;;
  esac
done

PD="proot-distro"
DISTRO="ubuntu"
SDCARD="/storage/emulated/0"

say()  { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
skip() { printf '   already done: %s\n' "$*"; }

# ---------------------------------------------------------------- is this it
case "$PREFIX" in
  *com.termux*) ;;
  *)
    if [ ! -d /data/data/com.termux ]; then
      say ""
      say "This is for Termux on Android, and this is not that."
      say ""
      say "On Windows or Linux, Claude Code installs the ordinary way and"
      say "none of the proot business below is needed:"
      say ""
      say "    npm install -g @anthropic-ai/claude-code"
      say "    claude"
      say ""
      say "Node.js first, from nodejs.org."
      exit 1
    fi
    ;;
esac

say ""
say "Getting Claude onto this phone"
say ""

# ------------------------------------------------------------------ 32-bit?
step "can this phone run it at all"
BITS="$(uname -m 2>/dev/null || echo unknown)"
say "this phone is $BITS"
case "$BITS" in
  aarch64|arm64|x86_64)
    say "64-bit -- good, Claude Code has a build for this"
    ;;
  armv7l|armv7|armv8l|i686|i386)
    say ""
    say "This is a 32-bit phone, and Claude Code CANNOT run on one."
    say ""
    say "Not a missing package and not something proot fixes. The"
    say "program ships 64-bit binaries only, so Ubuntu inside proot is"
    say "still a 32-bit kernel underneath and the binary will not"
    say "start. Nothing below would help, so it stops here rather than"
    say "walking you through an install that was never going to work."
    say ""
    say "Everything else in Wakeup still works on this phone. For"
    say "Claude itself, use claude.ai in the browser."
    exit 1
    ;;
  *)
    say "I do not recognise that. Carrying on, but if the install fails"
    say "at the last step, this is the first thing to suspect."
    ;;
esac

# --------------------------------------------------------- what Termux needs
step "what Termux needs"
for pkg in git python proot-distro; do
  if command -v "$pkg" >/dev/null 2>&1; then
    skip "$pkg"
  else
    say "installing $pkg"
    pkg install -y "$pkg"
  fi
done

# ------------------------------------------------------------------- ubuntu
step "is there room"
FREE_KB="$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')"
if [ -n "$FREE_KB" ]; then
  say "$((FREE_KB / 1024)) MB free"
  if [ "$FREE_KB" -lt 1500000 ] 2>/dev/null; then
    say ""
    say "Ubuntu, Node and Claude together want about 1.5 GB, and there"
    say "is less than that. It will most likely stop part way, and a"
    say "half-finished container is more annoying than none."
    say ""
    say "Clear some space and run this again."
    say "If you want to try anyway:   WAKEUP_CRAMPED=1 sh $0"
    [ -n "$WAKEUP_CRAMPED" ] || exit 1
    say ""
    say "Carrying on because WAKEUP_CRAMPED is set."
  fi
else
  say "could not tell -- carrying on"
fi

step "Ubuntu inside Termux"
# THREE states, not two. This is the bit that caught us twice.
#
#   usable   you can log in. Nothing to do.
#   half     the folder is there but you cannot log in -- an install
#            that was interrupted. `install` REFUSES this with
#            "container 'ubuntu' already exists", so installing is
#            exactly the wrong move. It needs a reset.
#   absent   nothing there. Install it.
#
# Do NOT read `proot-distro list` to tell them apart. It prints every
# distro there is, and an uninstalled one says "not installed" --
# which contains the word "installed". That bug shipped once already.

rootfs_of() {
  for d in "$PREFIX/var/lib/proot-distro/installed-rootfs/$1" \
           "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/$1"; do
    if [ -d "$d" ]; then printf '%s' "$d"; return 0; fi
  done
  return 1
}

can_log_in() {
  $PD login "$1" -- true >/dev/null 2>&1
}

if [ -n "$REPLACE" ] && rootfs_of "$DISTRO" >/dev/null; then
  say "START OVER was asked for."
  say ""
  say "This throws away the Ubuntu that is here -- and everything"
  say "inside it, including anything you installed in there yourself"
  say "-- and fetches a clean one. A few hundred megabytes again."
  say ""
  say "It does NOT touch:"
  say "  your saved programs in ~/.wakeup/programs"
  say "  the wakeup folder itself"
  say "  anything on your phone outside Termux"
  say ""
  if [ -z "$ALREADY_SAID_YES" ]; then
    printf 'Type the word  replace  to go ahead: '
    read -r SURE
    if [ "$SURE" != "replace" ]; then
      say ""
      say "Not done. Nothing was removed."
      exit 0
    fi
  fi
  say ""
  $PD remove "$DISTRO" || true
  say "removed. Fetching a clean one."
  $PD install "$DISTRO"
  if ! can_log_in "$DISTRO"; then
    say ""
    say "A clean one still will not log in. That is not something"
    say "this script can fix -- proot itself is unhappy. Try:"
    say "    $PD install $DISTRO"
    say "and read what it says."
    exit 1
  fi
  say "replaced, and it logs in"
elif can_log_in "$DISTRO"; then
  skip "$DISTRO"
elif rootfs_of "$DISTRO" >/dev/null; then
  say "There is an Ubuntu here already, but it cannot be logged into."
  say "That is an install that was interrupted part way."
  say ""
  say "Installing over it is refused -- proot-distro says the container"
  say "already exists. So this resets it, which is its own word for"
  say "throwing the broken one away and fetching it again."
  say ""
  say "  $PD reset $DISTRO"
  say ""
  if ! $PD reset "$DISTRO"; then
    say ""
    say "The reset did not work either. The next rung down is to"
    say "remove it and start that part again:"
    say ""
    say "    sh $0 --replace"
    exit 1
  fi
  if ! can_log_in "$DISTRO"; then
    say ""
    say "Reset finished but it still will not log in. Something is"
    say "wrong underneath this script. Try by hand:"
    say "    $PD remove $DISTRO"
    say "    $PD install $DISTRO"
    exit 1
  fi
  say "reset, and it logs in now"
else
  say "installing it -- this is the slow part, a few hundred megabytes"
  $PD install "$DISTRO"
  if ! can_log_in "$DISTRO"; then
    say ""
    say "It installed but will not log in. Run this again -- it will"
    say "see the half-finished one and reset it."
    exit 1
  fi
fi

# ----------------------------------------------------- inside ubuntu: node
inside() { $PD login "$DISTRO" -- sh -lc "$1"; }
quietly() { $PD login "$DISTRO" -- sh -lc "$1" 2>/dev/null; }

# Claude Code's own package says: engines node >= 22. Checked against
# the npm registry, not remembered. Ubuntu's OWN nodejs package is
# 18, so `apt install nodejs` looks like it worked and then Claude
# refuses to start -- which is why there is a version test here and
# not just a "is node there" test.
NEED_NODE=22

node_major() {
  v="$(quietly 'node --version' | tr -d '\r' | head -1)"
  case "$v" in
    v*) echo "${v#v}" | cut -d. -f1 ;;
    *)  echo 0 ;;
  esac
}

step "can Ubuntu reach the network"
if quietly 'getent hosts deb.nodesource.com >/dev/null'; then
  say "yes"
else
  say "Ubuntu cannot look up a name. That is nearly always an empty"
  say "resolv.conf inside the container, which proot sometimes leaves."
  say "Writing one:"
  inside 'printf "nameserver 8.8.8.8\nnameserver 1.1.1.1\n" > /etc/resolv.conf' || true
  if quietly 'getent hosts deb.nodesource.com >/dev/null'; then
    say "fixed -- it resolves now"
  else
    say ""
    say "Still cannot. Check the phone is online and not on a network"
    say "that blocks it, then run this again."
    exit 1
  fi
fi

step "Node.js, inside Ubuntu"
HAVE_NODE="$(node_major)"
if [ "$HAVE_NODE" -ge "$NEED_NODE" ] 2>/dev/null; then
  skip "node v$HAVE_NODE"
else
  if [ "$HAVE_NODE" -gt 0 ] 2>/dev/null; then
    say "node v$HAVE_NODE is here, but Claude Code needs v$NEED_NODE or newer."
    say "Replacing it."
  else
    say "installing curl and Node.js"
  fi
  inside "apt-get update -y"
  inside "apt-get install -y curl ca-certificates"
  # setup_22.x by name, not setup_lts.x. LTS moves, and the day it
  # moves to something Claude does not accept this would break with
  # no clue why.
  inside "curl -fsSL https://deb.nodesource.com/setup_${NEED_NODE}.x | bash -"
  inside "apt-get install -y nodejs"

  HAVE_NODE="$(node_major)"
  if [ "$HAVE_NODE" -lt "$NEED_NODE" ] 2>/dev/null; then
    say ""
    say "Node is v$HAVE_NODE and Claude Code needs v$NEED_NODE or newer."
    say ""
    say "Do NOT use Ubuntu's own nodejs package for this -- it is v18,"
    say "which installs cleanly and then Claude refuses to start."
    say ""
    say "Try the nodesource step by hand and read what it says:"
    say "    $PD login $DISTRO"
    say "    curl -fsSL https://deb.nodesource.com/setup_${NEED_NODE}.x | bash -"
    say "    apt-get install -y nodejs"
    say ""
    say "If that gets nowhere, the last rung is a clean Ubuntu:"
    say "    sh $0 --replace"
    exit 1
  fi
  say "node v$HAVE_NODE"
fi

# --------------------------------------------------- inside ubuntu: claude
step "Claude Code, inside Ubuntu"
if inside "command -v claude >/dev/null" >/dev/null 2>&1; then
  skip "claude $(inside 'claude --version' 2>/dev/null | head -1 | tr -d '\r')"
else
  say "installing it"
  inside "npm install -g @anthropic-ai/claude-code"
fi

# ------------------------------------------------------------- the shortcut
step 'making `claude` and `claude --continue` plain words you can type'

SH="$(command -v sh)"
BIN="$PREFIX/bin"
WRAP="$BIN/claude"

# A script, not an alias. An alias only exists inside an interactive
# bash, so it is missing from scripts, from Termux:Widget, and from
# anything run with `sh -c`. A script in bin is the word itself.
cat > "$WRAP" <<WRAPEOF
#!$SH
# claude -- start Claude Code, which lives inside the proot Ubuntu.
#
# Written by get-claude.sh. Safe to delete; rerun that to get it back.
#
# Your Termux home is /root/phone inside, and the phone's shared
# storage is /sdcard, so Claude can see your own files either way.
# Options go BEFORE the container name. proot-distro's own
# synopsis is: login [OPTIONS] CONTAINER [-- COMMAND]
exec $PD login \\
  --bind $SDCARD:/sdcard \\
  --bind "\$HOME:/root/phone" \\
  $DISTRO -- claude "\$@"
WRAPEOF
chmod +x "$WRAP"
say "wrote $WRAP"

# No alias is written. An alias and a script are two mechanisms for
# one word, and in bash the alias silently wins -- so if an older
# version left one behind, say so rather than adding another.
BRC="$HOME/.bashrc"
if [ -f "$BRC" ] && grep -q "alias claude=" "$BRC" 2>/dev/null; then
  say ""
  say "Heads up: ~/.bashrc still has an \`alias claude=\` in it from an"
  say "older version. It does the same job, but in bash the alias wins"
  say "over the script above, so only one of the two is ever in use."
  say "Take that line out when you get a moment:   nano ~/.bashrc"
fi

# ---------------------------------------------------------------------- done
step "done"
say "Type either of these, from anywhere:"
say ""
say "    claude"
say "    claude --continue"
say ""
say "The first run asks you to log in, in the browser."
say ""
say "If anything above went wrong, this says which step and why:"
say ""
say "    python3 ~/wakeup/claude-ready.py"
say ""
