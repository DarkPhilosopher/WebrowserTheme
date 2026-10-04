# Boxes

Every thing gets a box. **A thing that is missing gets a box too** —
empty, saying what is absent, where it belongs, and how to fill it.

A gap with no box is the only real disorder. Everything else is just
work not done yet.

```
┌─ name ────────────────────────────┐
│ what     what it is for           │
│ manual   where to read about it   │
│ map      where its insides are    │
│          drawn                    │
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
┌─ sparkblocks/ ─────────────────────────────────────────────┐
│ what    133 blocks. One contract: part.step(ctx) -> value  │
│ manual   sparkblocks/README.md                             │
│ map      sparkblocks/README.md § Layout                    │
│ needs   Python. Nothing else, ever                         │
│ joins   EVERYTHING. This is the blood supply               │
└────────────────────────────────────────────────────────────┘

┌─ panel/ ───────────────────────────────────────────────────┐
│ what    Three ways in: plain terminal, Chrome, and the     │
│         fancier menus in sparkblocks                       │
│ manual  panel/README.md                                    │
│ map     panel/README.md § Layout                           │
│ needs   catalogue.json · a prompt or a browser             │
│ joins   the blocks, through the catalogue, never by import │
└────────────────────────────────────────────────────────────┘

┌─ claude-ready.py ──────────────────────────────────────────┐
│ what    Names the first thing missing before Claude runs   │
│ manual  claude-ready.md                                    │
│ map     claude-ready.md § Layout                           │
│ needs   the machine itself · Python                        │
│ joins   whereami (which machine) · SETUP.md (by hand)      │
│ also     as sparkblocks/examples/claude-ready.parts, in    │
│          blocks                                            │
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
│ joins    nothing — and sparkblocks/files.py now does most  │
│          of it                                             │
└────────────────────────────────────────────────────────────┘

┌─ rustbuild/ ───────────────────────────────────────────────┐
│ what    Rust-style construction editor, isometric 3D       │
│ manual  rustbuild/README.md   map  § Layout                │
│ needs   its own saved plans · a terminal                   │
│ joins   NOTHING. Gabriel's, predates this work             │
└────────────────────────────────────────────────────────────┘
```

---

## Empty boxes, by how sure we are

Five bands. Each box says **who is waiting on it** — which script is
held back, or nothing, which is its own kind of answer.

---

### NO WAY — settled, do not try again

```
┌─ a Mega connector ─────────────────── NO WAY ──┐
│ what     Reach Mega from a Claude session      │
│ why not  There is no Mega connector and none   │
│          can be added from here                │
│ instead  sync/mega.py, a script on YOUR machine│
│          with YOUR credentials. I can write it;│
│          I can never run it                    │
│ waited   nothing. Nothing here depends on it   │
└────────────────────────────────────────────────┘

┌─ permanently deleting from Drive ──── NO WAY ──┐
│ why not  trash_file only moves to trash. There │
│          is no permanent delete tool at all    │
│ silver   deletes are RECOVERABLE for 30 days,  │
│          which makes automating them safe      │
│ waited   nothing                               │
└────────────────────────────────────────────────┘

┌─ editing a Drive file's contents ──── NO WAY ──┐
│ why not  update_file changes the title and the │
│          parent folder only                    │
│ instead  create a new file                     │
│ waited   sync/drive.py would have to work this │
│          way round                             │
└────────────────────────────────────────────────┘

┌─ a verbatim transcript ────────────── NO WAY ──┐
│ why not  Two reasons, both standing. A         │
│          classifier refused it; and I would be │
│          RECONSTRUCTING, not copying           │
│ instead  claude.ai → Settings → Privacy →      │
│          Export data. The real one             │
│ waited   nothing. wakeup-notes is what I can   │
│          honestly give                         │
└────────────────────────────────────────────────┘

┌─ making the repo private from here ── NO WAY ──┐
│ why not  403: repository settings writes are   │
│          not permitted through this proxy      │
│ instead  you, in a browser. Not the GitHub app │
│ waited   ABOUT.md and wakeup-notes/ BOTH wait  │
│          on this one                           │
└────────────────────────────────────────────────┘
```

### CERTAINLY — will work, just not done

```
┌─ run-time errors naming their line ─ CERTAIN ──┐
│ what     A parse error says `line 3:`. A       │
│          failure WHILE RUNNING gives a raw     │
│          Python traceback                      │
│ how      Wrap the step loop, catch, report     │
│          which line was running                │
│ waited   sparkblocks/script.py. Every program  │
│          a child runs is held back by this     │
│ size     small                                 │
└────────────────────────────────────────────────┘

┌─ undo in the menus ────────────────── CERTAIN ─┐
│ what     Delete is final. A child will delete  │
│ how      A stack of past programs              │
│ waited   sparkblocks/menu.py ·                 │
│          sparkblocks/pad.py                    │
│ size     small                                 │
└────────────────────────────────────────────────┘

┌─ naming each phone ────────────────── CERTAIN ─┐
│ what     ~/.whereami, one per phone            │
│ how      python3 whereami.py --name "A33"      │
│ waited   whereami.py cannot tell your two      │
│          phones apart until you do it          │
│ size     ten seconds, by you, on each phone    │
└────────────────────────────────────────────────┘

┌─ the A17's architecture ───────────── CERTAIN ─┐
│ how      python3 whereami.py --facts   on it   │
│ waited   whereami.py REGISTER, entry "A17",    │
│          which says `sure: False` until then   │
└────────────────────────────────────────────────┘

┌─ the other 50 blocks in the browser ─ CERTAIN ─┐
│ what     50 blocks need nothing a browser      │
│          lacks and the page has not learnt     │
│          them: sort, uniq, each, keep, fan...  │
│ how      Add them to step() in panel.html      │
│ waited   panel/panel.html says so itself now   │
│ size     medium, and purely mechanical         │
└────────────────────────────────────────────────┘

┌─ a minimal mode in each program ───── CERTAIN ─┐
│ what     Every program here can grow. The      │
│          promise is that a small WHOLE version │
│          stays available -- not a crippled     │
│          demo                                  │
│ how      A --minimal flag and a minimal path   │
│          through each menu. panel.py half does │
│          it already: it degrades when the      │
│          package is missing                    │
│ waited   the first moral of the update rule. A │
│          promise nobody built is not a promise │
│ size     medium; it touches every program      │
└────────────────────────────────────────────────┘

┌─ one module at a time in get.sh ───── CERTAIN ─┐
│ what     get.sh pulls everything or nothing.   │
│          That breaks the rule outright -- an   │
│          update is a shelf, not a bundle       │
│ how      Let it take module names, offered by  │
│          number. `sh get.sh blocks panel` and  │
│          nothing else moves                    │
│ waited   get.sh. It is the one thing that      │
│          contradicts the moral it serves       │
│ size     medium                                │
└────────────────────────────────────────────────┘

┌─ NEWS.md, and a view onto it ──────── CERTAIN ─┐
│ what     Choosing is only real if you can see  │
│          the choice. Nothing yet says in plain │
│          words what an update changes          │
│ how      One NEWS.md, newest first, a short    │
│          paragraph per change, written WHEN    │
│          the change is. A `news` entry in      │
│          wakeup and the panels                 │
│ waited   the fifth moral. Declining should be  │
│          a decision, not a shrug               │
│ size     small to start, then a habit          │
└────────────────────────────────────────────────┘

┌─ proof that old programs still run ── CERTAIN ─┐
│ what     Backwards compatibility is a good     │
│          intention and nothing more. No test   │
│          would notice if a .spark file from    │
│          last month stopped parsing            │
│ how      Keep dated example programs and parse │
│          every one in check. An old one that   │
│          breaks becomes a failure with a name  │
│ waited   sparkblocks/check.py, and the third   │
│          moral                                 │
│ size     small, and it only gets more valuable │
└────────────────────────────────────────────────┘

┌─ a private home for the withheld ──── CERTAIN ─┐
│ what     WITHHELD.md records 8 gaps. The       │
│          material itself has nowhere durable   │
│          to be. private/ is gitignored but     │
│          this container is wiped when the      │
│          session ends                          │
│ how      A private repository is the obvious   │
│          home. Google Drive works today and is │
│          reachable from here                   │
│ waited   rows W-01 to W-05. Until there is     │
│          somewhere, `where it went` can only   │
│          say `Gabriel's hands`                 │
│ YOURS    only you can say which, and give      │
│          permission for the material to go in  │
└────────────────────────────────────────────────┘
```

### MAYBE — worth doing, not obviously right

```
┌─ use myprogram ─────────────────────── MAYBE ──┐
│ what     A saved .parts file usable AS a block │
│ for      Your own programs become Lego beside  │
│          the built-in ones. The real test of   │
│          whether the language is strong enough │
│ doubt    What is its datasheet? A program's    │
│          needs are the union of its blocks' —  │
│          workable, but it has to be worked out │
│ waited   sparkblocks/script.py                 │
└────────────────────────────────────────────────┘

┌─ an index for connect ──────────────── MAYBE ──┐
│ what     connect rescans every file every run  │
│ for      A phone-wide search in a moment       │
│ doubt    An index is stale the instant a file  │
│          changes. Needs a staleness answer     │
│ waited   sparkblocks/connect.py                │
└────────────────────────────────────────────────┘

┌─ joining the three 3D engines ──────── MAYBE ──┐
│ see      the box below. YOUR decision          │
└────────────────────────────────────────────────┘
```

### RECENTLY — just done, still settling

```
┌─ datasheets on every block ───────── RECENT ───┐
│ done     Every block says what it needs        │
│ settling 50 browser-runnable blocks are now    │
│          VISIBLY missing from the page         │
└────────────────────────────────────────────────┘

┌─ twelve shapes ───────────────────── RECENT ───┐
│ done     66 blocks on a shared shape           │
│ settling pad.py has 4 blocks on none. Is there │
│          a shape there, or only four things?   │
└────────────────────────────────────────────────┘

┌─ a manual and map for everything ─── RECENT ───┐
│ done     All nine programs                     │
│ settling rustbuild's manual was written by     │
│          reading it. You should check I have   │
│          not described your own program wrong  │
└────────────────────────────────────────────────┘
```

### LONGING — wanted, and the reason for the rest

```
┌─ charts and visual depictions ────── LONGING ──┐
│ what     The concept drawn: the fundamentals,  │
│          and what is interesting about them    │
│ for      MAKING MACHINES WITH THE BEST         │
│          SEARCHING ENGINES. This is the point  │
│          the rest is building toward           │
│ have     INDEX.md, BOXES.md and the layout     │
│          maps are the material — written, not  │
│          drawn                                 │
│ waited   nothing yet. It wants a shape first   │
│ YOURS    you said you want to make this        │
└────────────────────────────────────────────────┘

┌─ elsewhere and known ──────────────── LONGING ─┐
│ ABOUT.md         waits on the repo going       │
│                  private                       │
│ wakeup-notes/    same                          │
│ spark · ASC      SEPARATE ON PURPOSE. You have │
│                  said so twice. This box stays │
│                  empty unless you say otherwise│
│ your 4th repo    GitHub says 4 public; I can   │
│                  see 3. Name it and it gets a  │
│                  box                           │
└────────────────────────────────────────────────┘

┌─ does touch work in Termux ────────── LONGING ─┐
│ what     sparkblocks/pad.py reads the          │
│          terminal's own touch reporting. NEVER │
│          TRIED on a real phone — only reasoned │
│          about                                 │
│ how      python3 -m sparkblocks pad on the A33 │
│ waited   the whole pad idea rests on it        │
│ YOURS    ten minutes, and only you can do it   │
└────────────────────────────────────────────────┘
```

## The one real mess

```
┌─ THREE 3D ENGINES, NOTHING JOINING THEM ───────────────────┐
│                                                            │
│   house/house.sh      wireframe house, maths in awk        │
│          sparkblocks/screen.py XYZ points, matrices,       │
│          projection                                        │
│   rustbuild/*.py      isometric building, its own maths    │
│                                                            │
│ Three separate pieces of isometric-3D code, in one         │
│ repository, by one author, that cannot use each other.     │
│                                                            │
│ This is the thing the whole "organs" idea exists to        │
│ prevent, and it is already here.                           │
│                                                            │
│ to fill  Decide. Either                                    │
│          (a) sparkblocks/screen.py is the one, and the     │
│          other two call it — house loses its awk,          │
│          rustbuild loses its projection, both keep their   │
│          look (b) they stay apart and this box says why    │
│ belongs  a decision from you. I will not pick for you —    │
│          two of these are yours and predate this work      │
└────────────────────────────────────────────────────────────┘
```
