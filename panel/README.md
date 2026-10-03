# The control panels

Three ways in, so a broken one never blocks you.

| | Where | Needs |
|---|---|---|
| **`panel.py`** | Windows `cmd.exe`, PowerShell, Termux, anywhere a prompt is | Python, nothing else |
| **`panel.html`** | Chrome, by opening the file | A browser. No server, no install |
| **`python3 -m parts menu` / `pad`** | A terminal with colour and touch | Python + the package |

All three build the same `.parts` program. Save in one, open in another.

## What makes them redundant rather than three programs

They read **one catalogue**, written out of the Python:

```bash
python3 -m parts json panel/catalogue.json   # for panel.py
python3 -m parts json --html                 # baked into panel.html
```

`panel.html` has it baked inside the page because **Chrome will not let
a `file://` page fetch its own folder** — so a copy has to live in the
HTML. Nothing else writes it.

Either copy can be left behind when the blocks change, so
`python3 -m parts check` compares both against the live language and
says which to rerun:

```
FAIL the panels agree               2 checked
       panel/catalogue.json: has 122 blocks, the language has 123
       -- rerun `python3 -m parts json`
```

## `panel.py` — the one that always works

```bash
python3 panel.py
```

Nothing but `print` and `input`. No colours, no cursor moving, no
mouse, no curses, no `termios`. That is the point: where the pad and
the coloured menus will not run, this will.

It degrades rather than failing. With the package importable it can run
what you build; without it, it reads `catalogue.json`, still knows every
block, and still builds and saves the program — it just says so:

```
 Windows, 123 blocks, read from catalogue.json.
 Cannot run programs here -- build and save, run elsewhere.
```

## `panel.html` — buttons and depictions

Open it in Chrome. Two modes, switchable at any time:

- **buttons** — eight squares, the last always back, the same rule
  everywhere else keeps. Press through module → kind → block.
- **terminal** — type the lines yourself, with a prompt. `help`, `run`,
  `list`, `undo`, `blocks`, and `light?` to explain one.

The program is listed down the side the whole time, and it **runs the
drawing blocks right in the page** — a cube really does spin.

Blocks that touch files or the network cannot run in a browser. They are
marked `not in browser` in the list, refuse by name rather than failing
oddly, and the program still saves for the terminal to run.

### advanced — write code and watch it apply

The third button. A made-up terminal that takes code and applies it to
the page, live. Three tabs:

| Tab | What it does with what you write |
|---|---|
| **javascript** | Runs it, with `panel` handed in. Ctrl+Enter also runs |
| **style** | Adds it to the page as CSS |
| **html** | First line names a part, the rest replaces its insides |

**It can rearrange the panel itself**, which is the point:

```js
panel.order('draw', 'strip', 'pad')   // put them in this order
panel.move('draw', 'top')             // one of them to the top
panel.side('draw')                    // into the right-hand column
panel.hide('pad')   panel.show('pad')
panel.wide()                          // one column instead of two
```

The parts are `strip` `pad` `draw` `program` `code` `terminal`. Name one
that does not exist and it says so, and lists the ones that do.

It can also drive the panel:

```js
panel.program = ['screen 20 10', 'ball 2', 'flat', 'plot', 'draw']
panel.run()    panel.stop()    panel.draw()
panel.add('box 3 3 3')
panel.grid()   panel.book      panel.parts
```

**keep on reload** writes what you wrote into this browser, so it comes
back next time you open the file. **forget** throws all of it away and
reloads clean — this is the one pane that can break the panel, so there
is always a way back.

Broken code is caught and shown in red rather than stopping the page.

## Layout

```
panel/
│
├─ catalogue.json    the language as data — written, never hand-edited
│
├─ panel.py          THE PLAIN ONE. print and input, nothing else
│   ├─ load_book()     catalogue.json, or the package, or nothing
│   ├─ have_parts()    can we RUN things here, or only build them
│   ├─ choose()        eight, the last always back
│   ├─ pick_block()    module → kind → block
│   ├─ type_settings() the one place you type
│   └─ main()          add · edit · run · save · open · explain · browser
│
└─ panel.html        THE BROWSER ONE. one file, no server
    ├─ <script id=catalogue>   the baked copy, because file:// cannot fetch
    ├─ BUTTONS   topScreen → modScreen → kindScreen → pickBlock
    ├─ TERMINAL  terminalLine()   help · run · list · undo · blocks · name?
    ├─ ADVANCED  applyCode()      js runs · css is added · html replaces
    │            panel.order/move/side/hide/wide   rearrange the page
    └─ RUNNING   step()  a small reading of the same language, enough to draw
```

**The page's own parts**, which the advanced pane can rearrange by name:

```
  ┌─────────────────────────────┬───────────┐
  │ strip    the question       │ program   │
  ├─────────────────────────────┤ the lines │
  │ pad      eight squares      │ you built │
  │ terminal type instead       │           │
  │ code     the advanced pane  │ as a      │
  ├─────────────────────────────┤ .parts    │
  │ draw     the depiction      │ file      │
  └─────────────────────────────┴───────────┘
```

```js
panel.order('draw', 'strip', 'pad')
panel.side('draw')
panel.wide()
```

### It agrees with the Python

The page carries a small reading of the same language. Run the same
program in both and the output is identical — checked, character for
character:

```
screen 12 6        ........................
put hot 0.8        ........................
var hot            ....##..................
light 2 2 at=0.5   ........................
light 4 2 at=0.9   ################........
meter 0 4 10       ........................
```

```
screen 24 12       ......................########..................
box 3 3 3          ..................######..######................
spin y 35          ..............######......##..####..............
spin x 20          ..............##..################..............
flat               ..............##......##..##......##............
plot               ............########################............
```
