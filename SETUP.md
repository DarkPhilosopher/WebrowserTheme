# Setting Wakeup up

Which steps you need depends on which machine. Find yours.

---

## The A33 or the A17 — an Android phone

**1. Termux, from F-Droid.** Not the Play Store — that build is
abandoned and `npm` fails on it oddly.

**2. Unzip this wherever you like**, Downloads is fine.

**3. Open Termux and run:**

```bash
pkg install python -y
```
```bash
cd ~/storage/shared/Download/wakeup
```
```bash
python3 claude-ready.py
```

That looks at the phone and names the **first** thing missing, then
offers to install it. Pick a number. Repeat until it says
`Everything is here. Type: claude`.

**4. Tell the phone its own name** — do this once per phone, or no
session will ever be able to tell your two apart:

```bash
python3 whereami.py --name "A33"
```

**5. Make the blocks reachable from anywhere:**

```bash
python3 sparkblocks/install.py
```

Now `import sparkblocks` works in any folder, with the folder staying where
it is. Check it took:

```bash
python3 -m sparkblocks where
```

### Then, on the phone

```bash
python3 -m sparkblocks                    every block there is
python3 -m sparkblocks menu               build a program with numbers
python3 -m sparkblocks pad                build one by pressing squares
python3 -m sparkblocks run prog.parts     run one
python3 -m sparkblocks connect spark /sdcard    what touches what
```

---

## The Dell i7 — Windows

**1. Python**, from python.org. Tick **"Add Python to PATH"** during
the install, or nothing below will be found.

**2. Unzip this.** Open **Command Prompt** or **PowerShell** and go to
where you put it:

```
cd C:\Users\sauve\Downloads\wakeup
```

**3. The control panel:**

```
python panel\panel.py
```

This one is built for Windows: no colours, no mouse, nothing that
`cmd.exe` cannot do. It will say whether it can run programs or only
build and save them.

**4. Make the blocks reachable:**

```
python sparkblocks\install.py
```

### Claude Code on Windows

Separate from all this, and it does work here:

```
npm install -g @anthropic-ai/claude-code
claude
```

Needs Node.js from nodejs.org first.

---

## Any machine with Chrome — including the phones

Open **`panel/panel.html`** by double-clicking it. No server, no
install, nothing to set up.

- **buttons** — eight squares, the last always back
- **terminal** — type the lines yourself; `help` lists the words
- **advanced** — write JavaScript, CSS or HTML and watch it apply to
  the page, including rearranging the panel itself

It draws for real: build a cube and press **run** and it spins. Blocks
that touch files or the network cannot run in a browser, are marked
`not in browser`, and still save for the terminal to run.

---

## A 32-bit phone

Claude Code **cannot run on one at all** — no 32-bit build exists, and
proot and Ubuntu do not change that. Your Hotpepper ACP was the 32-bit
one and it is gone, so this should not come up again.

Everything else here still works on one: Python, git, the blocks, the
panels, `tfind`. Use claude.ai in the browser for Claude itself.

---

## When you change anything

```bash
python3 -m sparkblocks check
```

718 checks. If you add or rename a block, it will also tell you to
rebuild the catalogue the panels read:

```bash
python3 -m sparkblocks json panel/catalogue.json
python3 -m sparkblocks json --html
```
