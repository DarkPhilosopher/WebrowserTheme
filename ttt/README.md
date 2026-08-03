# ttt — play Tic-Tac-Toe over the Internet through GitHub

Two phones, anywhere in the world, no server and no local wifi. The **channel
is a shared GitHub repo**: every move is a git commit that gets pushed, and the
script polls (`git pull`) for your opponent's move. Works between **Android
(Termux)** and **iPhone (iSH)** — anything with `bash` + `git`.

> Termux is Android-only. On iPhone use **iSH** (a full Linux shell with real
> `bash` and `git`) — the same script runs unchanged.

---

## 1. Create the channel (once, by either player)

1. On GitHub, create a new **empty repo**, e.g. `ttt-match` (private is fine).
2. **Add your opponent as a collaborator** so they can push moves:
   repo → **Settings → Collaborators → Add people** → their GitHub username.
   They'll get an invite to accept.
3. Put `ttt.sh` in that repo (commit & push it once), so both players get it
   when they clone.

## 2. Set up each phone (once per player)

**Android — Termux**
```bash
pkg install git
git config --global user.name  "yourname"
git config --global user.email "you@example.com"
git clone https://github.com/<owner>/ttt-match.git
cd ttt-match
chmod +x ttt.sh
```

**iPhone — iSH** (install "iSH Shell" from the App Store, then)
```bash
apk add git bash
git config --global user.name  "yourname"
git config --global user.email "you@example.com"
git clone https://github.com/<owner>/ttt-match.git
cd ttt-match
chmod +x ttt.sh
```

> **Signing in to GitHub:** when git asks for a password on push, use a
> **Personal Access Token** (GitHub → Settings → Developer settings → Tokens),
> not your account password. Give it `repo` scope. Paste it as the password.

## 3. Play

One player creates the game, then each player joins with their mark
(**X always moves first**):

```bash
# Player A (host):
./ttt.sh new  friday
./ttt.sh play friday X

# Player B (on the other phone):
./ttt.sh play friday O
```

On your turn, type a cell number **1-9**:

```
   1 | 2 | 3
  ---+---+---
   4 | 5 | 6
  ---+---+---
   7 | 8 | 9
```

Then it waits for the other phone. When someone wins (or it's a draw) both
screens show the result and exit. Start another with a new game id.

### Commands

| Command | What it does |
|---|---|
| `./ttt.sh new  <game-id>` | Create a new game (once). |
| `./ttt.sh play <game-id> <X\|O>` | Join and play. |
| `./ttt.sh show <game-id>` | Print the current board and exit. |

You can have several games going at once — just use different game ids.

---

## How the channel works

- Game state lives in `games/<game-id>.ttt` (4 lines: board, whose turn,
  status, winner).
- On your turn the script writes the file, `git commit`s it, and `git push`es.
- While waiting, it does a quiet `git pull --rebase` every few seconds until the
  opponent's move arrives.
- Because it's strictly turn-based, only one side ever writes at a time, so
  there are no merge conflicts during normal play.

## Troubleshooting

- **"run this inside your shared game repo"** — you're not inside the cloned
  repo folder. `cd ttt-match` first.
- **Push asks for a password every time** — set up a Personal Access Token (see
  above), or use SSH keys / the GitHub CLI.
- **"no game 'friday' yet"** — the host hasn't run `ttt.sh new friday` yet, or
  your clone hasn't pulled it; it will appear on the next poll.
- **Moves feel slow** — polling is every 3 seconds by default; edit `POLL` near
  the top of `ttt.sh` to change it.

## Extending it

The same channel pattern (shared state file + commit/push/poll) works for any
turn-based text game — Connect Four, Battleship, chess, a dungeon crawler.
`ttt.sh` is a compact template to copy: swap out the board representation, the
move validation, and the win check.
