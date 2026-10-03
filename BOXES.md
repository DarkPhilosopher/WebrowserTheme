# Boxes

Every thing gets a box. **A thing that is missing gets a box too** —
empty, saying what is absent, where it belongs, and how to fill it.

A gap with no box is the only real disorder. Everything else is just
work not done yet.

```
┌─ name ────────────────────────────┐
│ what     what it is for           │
│ manual   where to read about it   │
│ map      where its insides are drawn │
│ needs    data, and physical thing │
│ joins    what it connects to      │
└───────────────────────────────────┘
```

Every **block** has a smaller box of the same kind, which it declares
itself and which the catalogue carries:

```python
fits = {"needs": ["shell"], "changes": "anything", "waits": True}
```

So nothing that holds a block has to keep a list of what works where —
it reads the box. A part fails for what it is, never for where it was
plugged in.

---

## Full boxes — here, documented, working

```
┌─ parts/ ───────────────────────────────────────────────────┐
│ what    133 blocks. One contract: part.step(ctx) -> value  │
│ manual  parts/README.md                                    │
│ map     parts/README.md § Layout                           │
│ needs   Python. Nothing else, ever                         │
│ joins   EVERYTHING. This is the blood supply               │
└────────────────────────────────────────────────────────────┘

┌─ panel/ ───────────────────────────────────────────────────┐
│ what    Three ways in: plain terminal, Chrome, and the     │
│         fancier menus in parts                             │
│ manual  panel/README.md                                    │
│ map     panel/README.md § Layout                           │
│ needs   catalogue.json · a prompt or a browser             │
│ joins   parts, through the catalogue — never by import     │
└────────────────────────────────────────────────────────────┘

┌─ claude-ready.py ──────────────────────────────────────────┐
│ what    Names the first thing missing before Claude runs   │
│ manual  claude-ready.md                                    │
│ map     claude-ready.md § Layout                           │
│ needs   the machine itself · Python                        │
│ joins   whereami (which machine) · SETUP.md (by hand)      │
│ also as parts/examples/claude-ready.parts, in blocks       │
└────────────────────────────────────────────────────────────┘

┌─ whereami.py ──────────────────────────────────────────────┐
│ what    Which of your machines this is                     │
│ manual  whereami.md                                        │
│ map     whereami.md § Layout                               │
│ needs   ~/.whereami if named · system facts otherwise      │
│ joins   CLAUDE.md (the rule to run it first)               │
└────────────────────────────────────────────────────────────┘

┌─ house/ ───────────────────────────────────────────────────┐
│ what    One ASCII house, many phones, over a shared repo   │
│ manual  house/README.md                                    │
│ map     house/README.md § Layout                           │
│ needs   a repo everyone can push to · bash + git           │
│ joins   nothing yet — see the empty box below              │
└────────────────────────────────────────────────────────────┘

┌─ ttt/ ─────────────────────────────────────────────────────┐
│ what    Tic-tac-toe between two phones, over a repo        │
│ manual  ttt/README.md   map  § Layout                      │
│ needs   a repo both can push to · bash + git               │
│ joins   house, in method — the same channel idea           │
└────────────────────────────────────────────────────────────┘

┌─ tfind.sh ─────────────────────────────────────────────────┐
│ what    Search every file on the phone                     │
│ manual  tfind.md   map  § Layout                           │
│ needs   shared storage · Termux · ripgrep makes it fast    │
│ joins   nothing — and parts/files.py now does most of it   │
└────────────────────────────────────────────────────────────┘

┌─ rustbuild/ ───────────────────────────────────────────────┐
│ what    Rust-style construction editor, isometric 3D       │
│ manual  rustbuild/README.md   map  § Layout                │
│ needs   its own saved plans · a terminal                   │
│ joins   NOTHING. Gabriel's, predates this work             │
└────────────────────────────────────────────────────────────┘
```

---

## Empty boxes — the thing is missing, the box is not

### Elsewhere, and known

```
┌─ ABOUT.md ─────────────────────────── EMPTY ───┐
│ what     Who Gabriel is; which machines        │
│ where    In your hands, and in wakeup-notes    │
│ why out  A classifier refused date of birth    │
│          and birthplace in a PUBLIC repo       │
│ to fill  Make the repo private, then commit it │
│ belongs  the root, beside CLAUDE.md            │
└────────────────────────────────────────────────┘

┌─ wakeup-notes/ ────────────────────── EMPTY ───┐
│ what     Decisions, bugs, what cannot be done  │
│ where    A zip in your downloads               │
│ why out  Built as a download, never offered    │
│ to fill  Unzip into notes/ and commit, once    │
│          the repo is private                   │
│ belongs  notes/                                │
└────────────────────────────────────────────────┘

┌─ spark · ASC ──────────────────────── EMPTY ───┐
│ what     Your other two repositories           │
│ where    github.com/DarkPhilosopher            │
│ why out  SEPARATE ON PURPOSE. You said twice   │
│          that spark and parts stay apart       │
│ to fill  Do not. This box stays empty          │
└────────────────────────────────────────────────┘
```

### Unknown — nobody has looked

```
┌─ the A17's architecture ───────────── EMPTY ───┐
│ what     64-bit or 32-bit? It decides whether  │
│          Claude Code can run on it at all      │
│ where    unknown                               │
│ to fill  python3 whereami.py --facts   on it   │
│ belongs  whereami.py REGISTER, entry "A17"     │
└────────────────────────────────────────────────┘

┌─ ~/.whereami, on each phone ───────── EMPTY ───┐
│ what     The name a phone calls itself         │
│ where    NOWHERE YET. No phone has been named  │
│ why      Until then, no session can tell your  │
│          two phones apart — the signs cannot   │
│ to fill  python3 whereami.py --name "A33"      │
│ belongs  ~/.whereami, one per phone            │
└────────────────────────────────────────────────┘

┌─ your fourth public repository ────── EMPTY ───┐
│ what     unknown                               │
│ where    GitHub says you have 4 public repos.  │
│          I can see spark, ASC, WebrowserTheme  │
│ to fill  Tell me its name, or list them        │
│ belongs  INDEX.md, and a box here              │
└────────────────────────────────────────────────┘

┌─ does touch actually work in Termux ─ EMPTY ───┐
│ what     parts/pad.py reads the terminal's own │
│          touch reporting. Never tried on a     │
│          real phone — only reasoned about      │
│ where    unknown                               │
│ to fill  python3 -m parts pad   on the A33     │
│ belongs  a line in parts/README.md either way  │
└────────────────────────────────────────────────┘
```

### Not built

```
┌─ sync/mega.py ─────────────────────── EMPTY ───┐
│ what     Back things up to Mega                │
│ needs    YOUR credentials, on YOUR machine     │
│ why out  There is no Mega connector. It cannot │
│          be done from a session — only written │
│ belongs  sync/                                 │
└────────────────────────────────────────────────┘

┌─ sync/drive.py ────────────────────── EMPTY ───┐
│ what     Push and pull files from Drive        │
│ needs    the connector — xzg4b3xz@gmail.com    │
│ limits   can read, create, rename, move, copy, │
│          trash. CANNOT permanently delete, and │
│          CANNOT edit a file's contents         │
│ belongs  sync/                                 │
└────────────────────────────────────────────────┘

┌─ run-time errors naming their line ── EMPTY ───┐
│ what     A parse error says `line 3:`. A       │
│          failure WHILE RUNNING gives a raw     │
│          Python traceback. A child is stuck    │
│ belongs  parts/script.py                       │
└────────────────────────────────────────────────┘

┌─ use myprogram ────────────────────── EMPTY ───┐
│ what     Make a saved .parts file usable AS a  │
│          block — your programs become Lego     │
│          beside the built-in ones              │
│ belongs  parts/script.py                       │
└────────────────────────────────────────────────┘
```

---

## The one real mess

```
┌─ THREE 3D ENGINES, NOTHING JOINING THEM ───────────────────┐
│                                                            │
│   house/house.sh      wireframe house, maths in awk        │
│   parts/screen.py     XYZ points, matrices, projection     │
│   rustbuild/*.py      isometric building, its own maths    │
│                                                            │
│ Three separate pieces of isometric-3D code, in one         │
│ repository, by one author, that cannot use each other.     │
│                                                            │
│ This is the thing the whole "organs" idea exists to        │
│ prevent, and it is already here.                           │
│                                                            │
│ to fill  Decide. Either                                    │
│          (a) parts/screen.py is the one, and the other     │
│              two call it — house loses its awk, rustbuild  │
│              loses its projection, both keep their look    │
│          (b) they stay apart and this box says why         │
│                                                            │
│ belongs  a decision from you. I will not pick for you —    │
│          two of these are yours and predate this work      │
└────────────────────────────────────────────────────────────┘
```
