# tfind — file search for Termux on Android

A single shell script to search **all the files on your phone** from Termux —
your Termux home *and* shared storage (Downloads, DCIM/photos, Documents, …).

## Setup (run once, inside Termux)

```bash
pkg install ripgrep       # optional, but makes content search much faster
termux-setup-storage      # grant access to /sdcard (photos, downloads, docs)
git clone https://github.com/DarkPhilosopher/WebrowserTheme.git
cd WebrowserTheme
chmod +x tfind.sh
```

To use it from anywhere as `tfind`:

```bash
mkdir -p ~/bin && cp tfind.sh ~/bin/tfind && chmod +x ~/bin/tfind
```

## Usage

```
tfind name  <pattern>       Find files by NAME (case-insensitive glob), e.g. "*.pdf"
tfind text  <pattern>       Search INSIDE text files for a word/phrase (regex ok)
tfind type  <ext> [ext...]  Find files by extension, e.g. jpg png webp
tfind big   [N]             Show the N largest files (default 20)
tfind recent [DAYS]         Files modified in the last DAYS days (default 7)
tfind all                   List every file under the search roots
```

Add `--in <dir>` (repeatable) to search a specific folder instead of the defaults.

## Examples

```bash
tfind name "*.pdf"                         # every PDF on the phone
tfind name invoice                         # anything with "invoice" in the name
tfind text "TODO"                          # find TODOs in your text files
tfind type jpg png webp                    # all images of these types
tfind big 10                               # 10 biggest space hogs
tfind recent 30                            # what changed in the last month
tfind --in ~/storage/shared/Download name "*.apk"   # APKs in Downloads only
```

## Notes

- **Default search roots** are your Termux home (`$HOME`) and shared storage
  (`~/storage/shared`, i.e. `/sdcard`). If shared storage isn't listed when you
  run `tfind --help`, run `termux-setup-storage` first.
- Content search (`text`) uses [ripgrep](https://github.com/BurntSushi/ripgrep)
  when installed and falls back to `grep` otherwise.
- Permission-denied paths (common under `/sdcard`) are skipped quietly.
