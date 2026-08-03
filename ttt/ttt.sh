#!/usr/bin/env bash
#
# ttt — two-player Tic-Tac-Toe played OVER THE INTERNET through a shared
# GitHub repo. No server: each move is a git commit that gets pushed, and
# the script polls (git pull) for your opponent's move.
#
# Works on Android (Termux) and iPhone (iSH) — anywhere with bash + git.
#
# THE "CHANNEL" is just a git repo both players can push to:
#   1. One player creates a repo on GitHub (e.g. "ttt-match").
#   2. Adds the other player as a Collaborator (repo Settings > Collaborators).
#   3. Both players clone it and cd into it.
#   4. Both put this script somewhere handy (or on PATH).
#
# PLAY:
#   Player A:   ./ttt.sh new  friday        # create a game called "friday"
#   Player A:   ./ttt.sh play friday X      # play as X (X always moves first)
#   Player B:   ./ttt.sh play friday O      # play as O
#
# On your turn you type a cell number 1-9. Then it waits for the other phone.
#
set -euo pipefail

POLL=3   # seconds between checks while waiting for the opponent

# --- locate the shared repo -------------------------------------------------
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "ttt: run this inside your shared game repo (the 'channel')." >&2
    echo "     git clone <your-shared-repo> && cd into it first." >&2
    exit 1
}
cd "$ROOT"
GAMES_DIR="games"

# --- git helpers ------------------------------------------------------------
have_upstream() { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; }

pull() {
    # Get the latest state from the channel. Quiet; tolerate "already up to date".
    if have_upstream; then
        git pull --rebase --quiet 2>/dev/null || {
            # a rebase conflict here means both sides wrote at once (rare, only
            # ever at game start). Bail cleanly rather than leave a mess.
            git rebase --abort >/dev/null 2>&1 || true
            echo "ttt: sync conflict — someone else wrote at the same time. Try again." >&2
            return 1
        }
    fi
}

push() {
    local msg="$1"
    git add "$FILE"
    git commit -q -m "$msg" || return 0   # nothing to commit
    local n=0
    until git push -q 2>/dev/null; do
        n=$((n+1))
        [ "$n" -ge 5 ] && { echo "ttt: push failed after retries." >&2; return 1; }
        sleep 2
        pull || return 1
    done
}

# --- state file: 4 lines = board / turn / status / winner -------------------
# board: 9 chars, '.' = empty, else X or O.  status: playing|won|draw.
load() { { read -r BOARD; read -r TURN; read -r STATUS; read -r WINNER; } < "$FILE"; }
save() { printf '%s\n%s\n%s\n%s\n' "$BOARD" "$TURN" "$STATUS" "$WINNER" > "$FILE"; }

char_at() { printf '%s' "${BOARD:$1:1}"; }
set_cell() {  # set_cell <index 0-8> <mark>
    BOARD="${BOARD:0:$1}$2${BOARD:$(($1+1))}"
}

winner_of() {  # echoes X or O if someone has won on $BOARD, else nothing
    local b="$1" a
    local lines=(012 345 678 036 147 258 048 246)
    for a in "${lines[@]}"; do
        local i="${a:0:1}" j="${a:1:1}" k="${a:2:1}"
        local ci="${b:$i:1}" cj="${b:$j:1}" ck="${b:$k:1}"
        if [ "$ci" != "." ] && [ "$ci" = "$cj" ] && [ "$cj" = "$ck" ]; then
            printf '%s' "$ci"; return
        fi
    done
}

draw() {  # render the board with a 1-9 position guide for empty cells
    local cells=() i c
    for i in 0 1 2 3 4 5 6 7 8; do
        c="${BOARD:$i:1}"
        [ "$c" = "." ] && c=$((i+1))   # show the number you'd type
        cells+=("$c")
    done
    echo
    printf '   %s | %s | %s\n'  "${cells[0]}" "${cells[1]}" "${cells[2]}"
    echo   '  ---+---+---'
    printf '   %s | %s | %s\n'  "${cells[3]}" "${cells[4]}" "${cells[5]}"
    echo   '  ---+---+---'
    printf '   %s | %s | %s\n'  "${cells[6]}" "${cells[7]}" "${cells[8]}"
    echo
}

# --- commands ---------------------------------------------------------------
cmd_new() {
    local id="$1"
    FILE="$GAMES_DIR/$id.ttt"
    mkdir -p "$GAMES_DIR"
    pull || exit 1
    if [ -e "$FILE" ]; then
        echo "ttt: game '$id' already exists. Use: ttt play $id X" >&2
        exit 1
    fi
    BOARD="........."; TURN="X"; STATUS="playing"; WINNER="-"
    save
    push "ttt: start game $id" || exit 1
    echo "Created game '$id'. Now run:  ttt play $id X"
}

cmd_play() {
    local id="$1" me="$2"
    case "$me" in X|O) ;; *) echo "ttt: your mark must be X or O." >&2; exit 2 ;; esac
    FILE="$GAMES_DIR/$id.ttt"
    pull || exit 1
    if [ ! -e "$FILE" ]; then
        echo "ttt: no game '$id' yet. One player runs:  ttt new $id" >&2
        exit 1
    fi

    echo "You are '$me' in game '$id'. Playing over the shared repo channel."
    while : ; do
        pull || { sleep "$POLL"; continue; }
        load

        if [ "$STATUS" != "playing" ]; then
            draw
            if [ "$STATUS" = "draw" ]; then
                echo "Game over: it's a draw."
            elif [ "$WINNER" = "$me" ]; then
                echo "Game over: you ($me) win! 🎉"
            else
                echo "Game over: $WINNER wins. Better luck next time."
            fi
            exit 0
        fi

        if [ "$TURN" != "$me" ]; then
            draw
            printf 'Waiting for %s to move… (Ctrl-C to quit)\r' "$TURN"
            sleep "$POLL"
            continue
        fi

        # It's my turn.
        draw
        local cell idx
        while : ; do
            printf 'Your move (%s), pick a free cell 1-9: ' "$me"
            read -r cell || { echo; exit 0; }
            case "$cell" in
                [1-9]) ;;
                q|Q) echo "Quit."; exit 0 ;;
                *) echo "  Enter a number 1-9 (or q to quit)."; continue ;;
            esac
            idx=$((cell-1))
            if [ "$(char_at "$idx")" != "." ]; then
                echo "  Cell $cell is taken — choose another."
                continue
            fi
            break
        done

        set_cell "$idx" "$me"
        local w; w="$(winner_of "$BOARD")"
        if [ -n "$w" ]; then
            STATUS="won"; WINNER="$w"
        elif [ "${BOARD//[^.]/}" = "" ]; then   # no dots left
            STATUS="draw"; WINNER="-"
        else
            TURN=$([ "$me" = "X" ] && echo O || echo X)
        fi
        save
        push "ttt($id): $me plays $cell" || { echo "Couldn't send move."; exit 1; }
    done
}

usage() {
    cat <<EOF
ttt — Tic-Tac-Toe over a shared GitHub repo (Internet play, no server)

  ttt new  <game-id>          Create a new game (do this once).
  ttt play <game-id> <X|O>    Join and play. X moves first.
  ttt show <game-id>          Print the current board and exit.

Run it inside a git repo that BOTH players can push to (that's the "channel").
Example:
  ttt new  friday
  ttt play friday X      # on one phone
  ttt play friday O      # on the other phone
EOF
}

cmd_show() {
    local id="$1"
    FILE="$GAMES_DIR/$id.ttt"
    pull || true
    [ -e "$FILE" ] || { echo "ttt: no game '$id'." >&2; exit 1; }
    load; draw
    if [ "$STATUS" = "playing" ]; then echo "Turn: $TURN"
    elif [ "$STATUS" = "draw" ]; then echo "Result: draw"
    else echo "Result: $WINNER wins"; fi
}

main() {
    [ "$#" -ge 1 ] || { usage; exit 0; }
    local sub="$1"; shift || true
    case "$sub" in
        new)  [ "$#" -ge 1 ] || { echo "ttt: new needs a game-id" >&2; exit 2; }; cmd_new "$1" ;;
        play) [ "$#" -ge 2 ] || { echo "ttt: play needs <game-id> <X|O>" >&2; exit 2; }; cmd_play "$1" "$2" ;;
        show) [ "$#" -ge 1 ] || { echo "ttt: show needs a game-id" >&2; exit 2; }; cmd_show "$1" ;;
        -h|--help|help) usage ;;
        *) echo "ttt: unknown command '$sub'" >&2; usage; exit 2 ;;
    esac
}

main "$@"
