#!/bin/sh
# get-claude.sh -- one command, and this phone can run Claude.
#
# THE ONE COMMAND. Paste this whole line into Termux:
#
#   pkg install -y git && git clone --depth 1 -b claude/new-session-y0nuxy https://github.com/DarkPhilosopher/WebrowserTheme ~/wakeup && sh ~/wakeup/get-claude.sh
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
step "Ubuntu inside Termux"
# Do NOT read `proot-distro list` for this. It prints every distro
# there is, and an uninstalled one says "not installed" -- which
# contains the word "installed". Matching on that answers yes on a
# phone with no Ubuntu at all, and every step after it then fails
# with: container 'ubuntu' is not installed. That exact bug shipped
# in claude-ready.py and cost Gabriel a morning.
#
# So ask the thing itself: open the same door the later steps use.
if [ -d "$PREFIX/var/lib/proot-distro/installed-rootfs/$DISTRO/etc" ] \
   && $PD login "$DISTRO" -- true >/dev/null 2>&1; then
  skip "$DISTRO"
else
  say "installing it -- this is the slow part, a few hundred megabytes"
  $PD install "$DISTRO"
fi

# ----------------------------------------------------- inside ubuntu: node
inside() { $PD login "$DISTRO" -- sh -lc "$1"; }

step "Node.js, inside Ubuntu"
if inside "command -v node >/dev/null && node --version" 2>/dev/null | grep -q '^v'; then
  skip "node $(inside 'node --version' 2>/dev/null | tr -d '\r')"
else
  say "installing curl and Node.js"
  inside "apt-get update -y"
  inside "apt-get install -y curl ca-certificates"
  inside "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -"
  inside "apt-get install -y nodejs"
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
exec $PD login $DISTRO \\
  --bind $SDCARD:/sdcard \\
  --bind "\$HOME:/root/phone" \\
  -- claude "\$@"
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
