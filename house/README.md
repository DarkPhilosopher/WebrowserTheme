# house — build one ASCII house together, from many phones, online

Many players, each on their own phone, build **one shared ASCII house** over the
Internet. The "channel" is a shared GitHub repo (same idea as the tic-tac-toe
game): every part you pick is written to a file, committed, and pushed; every
phone pulls to see the house update. Because **each part of the house is its own
file**, people editing different parts never collide — you can all build at once.

Runs in **Termux (Android)** and **iSH (iPhone)** — just `bash` + `git`.

```
               __
              |  |
         .----.
      .-'      '-.
    .'            '.
   /________________\
   +----------------+
   |%%%%%%%%%%%%%%%%|
   |%%[+]%%%%%%[+]%%|
   |%%%%%%____%%%%%%|
   |%%%%%%|  |%%%%%%|
   |%%%%%%|o |%%%%%%|
   +----------------+
   ,,.,,.,,.,,.,,.,,.,,
```

## 1. Make the channel (once)

1. Create an empty GitHub repo, e.g. `house-party` (private is fine).
2. **Add every player as a collaborator** so they can push:
   repo → **Settings → Collaborators** → add their GitHub usernames.
3. Commit `house.sh` into the repo so everyone gets it on clone.

## 2. Set up each phone (once per player)

**Android — Termux**
```bash
pkg install git
git config --global user.name  "yourname"
git config --global user.email "you@example.com"
git clone https://github.com/<owner>/house-party.git
cd house-party && chmod +x house.sh
```

**iPhone — iSH** (install "iSH Shell" from the App Store)
```bash
apk add git bash
git config --global user.name  "yourname"
git config --global user.email "you@example.com"
git clone https://github.com/<owner>/house-party.git
cd house-party && chmod +x house.sh
```

> When git asks for a password on push, use a **Personal Access Token** (GitHub →
> Settings → Developer settings → Tokens, `repo` scope), not your account password.

## 3. Build together

One player creates the house; everyone else joins with a name:

```bash
./house.sh new  party            # host, once
./house.sh join party alice      # each player, on their own phone
./house.sh join party bob
./house.sh watch party           # just spectate, no editing
```

At the `>` prompt, type commands (type `help` any time):

```
roof    peak | flat | dome
walls   brick | wood | stone
door    single | double | arch | none
windows 0-4
chimney on | off
ground  grass | fence | none

3d      switch to the rotatable 3D wireframe view
2d      switch back to the flat picture
rotate  <x|y|z> <degrees>   turn the 3D view, any angle
                            e.g. rotate y 45 · rotate x 22.5 · rotate z -45
                            rotate reset   puts the view back
spin    auto-turn the house one full spin

sync    pull the latest shared house (see others' changes)
watch   live view; refreshes until you press Enter
show    redraw now
save    write the ASCII art to a file
help    command list
quit    leave
```

### 3D view

Type `3d` to see the house as a rotatable wireframe (body, roof, door, windows,
and chimney are all real 3D geometry), then turn it to any angle:

```
3d
rotate y 45      # spin 45 degrees around the vertical axis
rotate x 22.5    # tip it up 22.5 degrees
rotate z -45     # roll it
spin             # one automatic full turn
2d               # back to the flat picture
```

Angles accumulate and accept any number (45, 22.5, -30, ...). The 3D view is
**local to your phone** — rotating doesn't change what anyone else sees; it's
just your camera. The shared build (roof/walls/door/...) still syncs as normal.
It needs `awk` (already in Termux/iSH; if missing: `pkg install gawk`).

Each command you enter is pushed to the channel, and the house redraws with
everyone's latest parts. Use `watch` to sit back and see the house change live as
others build.

## Want to try the display first, no setup?

```bash
./house.sh solo
```

Offline single-player: same builder and ASCII display, no git, no channel — handy
for checking it looks right in your Termux window.

## How the shared build works

- Each part lives in its own file under `houses/<id>/` (`roof`, `walls`, `door`,
  `windows`, `chimney`, `ground`), so edits to **different** parts merge with no
  conflicts.
- Your move is `git commit` + `git push`; `sync`/`watch`/each command does a
  `git pull` to bring in everyone else's parts.
- If two people set the **same** part at the same instant, it settles on one
  value (last push wins) — no stuck state.
- A per-player `houses/<id>/feed/<name>.log` records who changed what; the
  builder shows a short **build feed** so you can see the room's activity.

## Troubleshooting

- **"run inside your shared game repo"** — `cd` into the cloned repo first.
- **"no house 'party' yet"** — the host hasn't run `house.sh new party`, or your
  clone hasn't pulled it yet; run `sync`.
- **Push keeps asking for a password** — set up a Personal Access Token (above).
- **Refresh feels slow** — `watch` refreshes every few seconds; edit `POLL` near
  the top of `house.sh` to change it.
