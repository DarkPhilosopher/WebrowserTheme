#!/usr/bin/env bash
#
# house — build ONE ASCII house together, from many phones, over the Internet.
#
# The "channel" is a shared GitHub repo (like the tic-tac-toe game): every part
# you pick is written to a file, committed and pushed; every phone pulls to see
# the shared house update. Many players can build at once — each part of the
# house is its own file, so people editing different parts never collide.
#
# Runs in Termux (Android) and iSH (iPhone): just needs bash + git.
#
#   ./house.sh new  <house-id>            # create a shared house (do once)
#   ./house.sh join <house-id> <name>     # join and build together
#   ./house.sh watch <house-id>           # live view, no editing
#   ./house.sh solo                       # offline, no git (try the display)
#   ./house.sh help
#
# Inside the builder type `help` for the command list.
#
set -uo pipefail

# ---- current design (defaults) --------------------------------------------
ROOF=peak        # peak | flat | dome
WALLS=brick      # brick | wood | stone
DOOR=single      # single | double | arch | none
WINDOWS=2        # 0..4
CHIMNEY=on       # on | off
GROUND=grass     # grass | fence | none

IW=16            # interior width (chars between the walls)
POLL=3           # seconds between refreshes in `watch`

MODE=solo        # solo | net
DIR=""           # houses/<id> (net mode)
NAME="you"       # player name (net mode)
BR=""            # git branch (net mode)

# ===========================================================================
#  GIT CHANNEL HELPERS (net mode)
# ===========================================================================
have_upstream() { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; }

pull() {   # bring in everyone else's changes; auto-resolve in our favor
    git fetch -q origin "$BR" 2>/dev/null || return 0
    git merge -q -X ours "origin/$BR" >/dev/null 2>&1 || { git merge --abort 2>/dev/null; return 0; }
}

push() {   # commit our files and push; on rejection, pull + retry
    local msg="$1"
    git add "$DIR" >/dev/null 2>&1
    git commit -q -m "$msg" >/dev/null 2>&1 || return 0   # nothing changed
    local n=0
    while : ; do
        if have_upstream; then git push -q 2>/dev/null && return 0
        else git push -q -u origin "$BR" 2>/dev/null && return 0; fi
        n=$((n+1)); [ "$n" -ge 6 ] && { echo "(couldn't sync — will retry next action)"; return 1; }
        sleep 1; pull
    done
}

# ---- per-attribute state files --------------------------------------------
attr_file() { printf '%s/%s' "$DIR" "$1"; }
read_attr() { local f; f="$(attr_file "$1")"; [ -f "$f" ] && cat "$f" || printf '%s' "$2"; }

load_state() {   # net mode: refresh globals from the shared files
    [ "$MODE" = net ] || return 0
    ROOF="$(read_attr roof peak)"
    WALLS="$(read_attr walls brick)"
    DOOR="$(read_attr door single)"
    WINDOWS="$(read_attr windows 2)"
    CHIMNEY="$(read_attr chimney on)"
    GROUND="$(read_attr ground grass)"
}

set_attr() {     # net mode: write one part, log who did it
    local key="$1" val="$2"
    printf '%s' "$val" > "$(attr_file "$key")"
    mkdir -p "$DIR/feed"
    printf '%s\t%s set %s = %s\n' "$(date +%H:%M:%S)" "$NAME" "$key" "$val" >> "$DIR/feed/$NAME.log"
}

feed_lines() {   # merge everyone's feed logs, newest last, keep the last few
    [ -d "$DIR/feed" ] || return 0
    cat "$DIR"/feed/*.log 2>/dev/null | sort | tail -n 6
}

# ===========================================================================
#  RENDERER
# ===========================================================================
stamp() { local -n _row="$1"; local pos="$2" txt="$3"; local n=${#txt}; _row="${_row:0:pos}${txt}${_row:pos+n}"; }
fill_row() { printf '%*s' "$IW" '' | tr ' ' "$1"; }
fillchar() { case "$WALLS" in brick) printf '#';; wood) printf '=';; stone) printf '%%';; *) printf '#';; esac; }

build_lines() {  # echo the raw ASCII art lines (no chrome)
    local -a out=()
    if [ "$CHIMNEY" = on ]; then
        out+=("            __"); out+=("           |  |")
    fi
    case "$ROOF" in
        peak)
            out+=("        /\\"); out+=("      /    \\"); out+=("    /        \\")
            out+=("  /            \\"); out+=("/________________\\") ;;
        flat)
            out+=("/~~~~~~~~~~~~~~~~\\") ;;
        dome)
            out+=("      .----."); out+=("   .-'      '-."); out+=(" .'            '.")
            out+=("/________________\\") ;;
    esac
    out+=("+----------------+")

    local fc; fc="$(fillchar)"
    local -a rows=(); local i
    for i in 0 1 2 3 4; do rows[i]="$(fill_row "$fc")"; done

    local -a wcols=()
    case "$WINDOWS" in
        0) wcols=() ;; 1) wcols=(6) ;; 2) wcols=(2 11) ;; 3) wcols=(1 6 11) ;; *) wcols=(0 4 8 12) ;;
    esac
    local c; for c in "${wcols[@]}"; do stamp rows[1] "$c" "[+]"; done

    case "$DOOR" in
        single) stamp rows[2] 6 "____"; stamp rows[3] 6 "|  |"; stamp rows[4] 6 "|o |" ;;
        double) stamp rows[2] 5 "______"; stamp rows[3] 5 "| || |"; stamp rows[4] 5 "|o||o|" ;;
        arch)   stamp rows[2] 6 ".--."; stamp rows[3] 6 "|  |"; stamp rows[4] 6 "|o |" ;;
        none)   : ;;
    esac
    for i in 0 1 2 3 4; do out+=("|${rows[i]}|"); done
    out+=("+----------------+")
    case "$GROUND" in
        grass) out+=(",,.,,.,,.,,.,,.,,.,,") ;;
        fence) out+=("|=|=|=|=|=|=|=|=|=|") ;;
        none)  : ;;
    esac
    printf '%s\n' "${out[@]}"
}

render() {
    printf '\033[2J\033[H'
    if [ "$MODE" = net ]; then
        printf '  House "%s"  —  you are %s  (building live over GitHub)\n' "$HID" "$NAME"
    else
        printf '  Your house  (solo / offline)\n'
    fi
    printf '  [roof:%s walls:%s door:%s windows:%s chimney:%s ground:%s]\n\n' \
        "$ROOF" "$WALLS" "$DOOR" "$WINDOWS" "$CHIMNEY" "$GROUND"
    local line
    while IFS= read -r line; do printf '   %s\n' "$line"; done < <(build_lines)
    if [ "$MODE" = net ]; then
        local feed; feed="$(feed_lines)"
        if [ -n "$feed" ]; then
            printf '\n  Build feed:\n'
            while IFS= read -r line; do printf '   %s\n' "$line"; done <<< "$feed"
        fi
    fi
    printf '\n  (type `help` for commands, `quit` to exit)\n'
}

# ===========================================================================
#  HELP
# ===========================================================================
show_help() {
    cat <<'EOF'
house — commands
================
  roof    <peak|flat|dome>          Choose the roof shape.
  walls   <brick|wood|stone>        Choose the wall material.
  door    <single|double|arch|none> Choose the front door.
  windows <0-4>                     How many windows.
  chimney <on|off>                  Add or remove the chimney.
  ground  <grass|fence|none>        What surrounds the house.

  sync                              Pull the latest shared house (see others).
  watch                             Live view; refreshes until you press Enter.
  show                              Redraw now.
  save [file]                       Save the ASCII art to a file (house.txt).
  help                              Show this list.
  quit | exit                       Leave.

Everyone editing the same house sees each other's parts as they're pushed.
Different parts (roof vs walls vs door...) never collide, so build together!
EOF
}

save_house() { local f="${1:-house.txt}"; build_lines > "$f"; echo "Saved to $f"; }

# ===========================================================================
#  COMMAND DISPATCH
# ===========================================================================
in_list() { local v="$1"; shift; local x; for x in "$@"; do [ "$v" = "$x" ] && return 0; done; return 1; }

# apply a validated part change to the right place (globals in solo, files in net)
apply() {
    local key="$1" val="$2"
    case "$key" in
        roof) ROOF="$val";; walls) WALLS="$val";; door) DOOR="$val";;
        windows) WINDOWS="$val";; chimney) CHIMNEY="$val";; ground) GROUND="$val";;
    esac
    if [ "$MODE" = net ]; then set_attr "$key" "$val"; push "house($HID): $NAME set $key=$val"; fi
}

do_cmd() {
    local cmd="${1:-}"; shift || true
    case "$cmd" in
        roof)    in_list "${1:-}" peak flat dome         && apply roof "$1"    || { echo "roof: peak|flat|dome"; return; } ;;
        walls)   in_list "${1:-}" brick wood stone       && apply walls "$1"   || { echo "walls: brick|wood|stone"; return; } ;;
        door)    in_list "${1:-}" single double arch none && apply door "$1"   || { echo "door: single|double|arch|none"; return; } ;;
        windows) case "${1:-}" in [0-4]) apply windows "$1";; *) echo "windows: 0-4"; return;; esac ;;
        chimney) in_list "${1:-}" on off                 && apply chimney "$1" || { echo "chimney: on|off"; return; } ;;
        ground)  in_list "${1:-}" grass fence none        && apply ground "$1"  || { echo "ground: grass|fence|none"; return; } ;;
        sync)    [ "$MODE" = net ] && { pull; load_state; } ;;
        watch)   cmd_watch; return ;;
        show|draw) [ "$MODE" = net ] && { pull; load_state; } ;;
        save)    save_house "${1:-}"; return ;;
        help|h|'?') show_help; return ;;
        quit|exit|q) exit 0 ;;
        '') return ;;
        *) echo "unknown command '$cmd' — type 'help'"; return ;;
    esac
    render
}

cmd_watch() {
    [ "$MODE" = net ] || { render; return; }
    printf 'Live view — press Enter to stop.\n'; sleep 1
    while : ; do
        pull; load_state; render
        printf '  [watching — Enter to stop]'
        read -r -t "$POLL" _ && break
    done
}

# ===========================================================================
#  TOP-LEVEL COMMANDS (new / join / watch / solo)
# ===========================================================================
enter_repo() {
    local root
    root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
        echo "house: run inside your shared game repo (the channel)." >&2
        echo "       git clone <shared-repo> && cd into it first." >&2
        exit 1; }
    cd "$root"
    BR="$(git rev-parse --abbrev-ref HEAD)"
}

cmd_new() {
    HID="$1"; enter_repo; MODE=net; DIR="houses/$HID"
    mkdir -p "$DIR"; pull
    if [ -f "$(attr_file roof)" ]; then echo "house '$HID' already exists — join it:  house.sh join $HID <name>"; exit 1; fi
    NAME="host"
    set_attr roof peak; set_attr walls brick; set_attr door single
    set_attr windows 2; set_attr chimney on; set_attr ground grass
    push "house($HID): created"
    echo "Created house '$HID'. Everyone joins with:  house.sh join $HID <yourname>"
}

cmd_join() {
    HID="$1"; NAME="$2"; enter_repo; MODE=net; DIR="houses/$HID"
    pull
    [ -f "$(attr_file roof)" ] || { echo "house: no house '$HID' yet. One player runs:  house.sh new $HID"; exit 1; }
    load_state; render
    while : ; do
        printf '> '; read -r line || break
        pull; load_state          # see others' changes before/after each command
        # shellcheck disable=SC2086
        do_cmd $line
    done
}

cmd_watch_top() {
    HID="$1"; enter_repo; MODE=net; DIR="houses/$HID"; NAME="watcher"
    pull; [ -f "$(attr_file roof)" ] || { echo "house: no house '$HID' yet."; exit 1; }
    cmd_watch
}

cmd_solo() {
    MODE=solo; render
    while : ; do printf '> '; read -r line || break; do_cmd $line; done   # shellcheck disable=SC2086
}

usage() {
    cat <<'EOF'
house — build an ASCII house together over GitHub (many phones, online)

  house.sh new   <house-id>          Create a shared house (once).
  house.sh join  <house-id> <name>   Join and build with everyone.
  house.sh watch <house-id>          Live spectate (no editing).
  house.sh solo                      Offline single-player (try the display).
  house.sh help                      This message.

Run it inside a git repo that all players can push to (the "channel").
See house/README.md for the full setup.
EOF
}

main() {
    local sub="${1:-}"; shift || true
    case "$sub" in
        new)   [ "$#" -ge 1 ] || { echo "house: new needs a house-id"; exit 2; }; cmd_new "$1" ;;
        join)  [ "$#" -ge 2 ] || { echo "house: join needs <house-id> <name>"; exit 2; }; cmd_join "$1" "$2" ;;
        watch) [ "$#" -ge 1 ] || { echo "house: watch needs a house-id"; exit 2; }; cmd_watch_top "$1" ;;
        solo)  cmd_solo ;;
        help|-h|--help) usage ;;
        '')    cmd_solo ;;
        *)     echo "house: unknown command '$sub'"; usage; exit 2 ;;
    esac
}
main "$@"
