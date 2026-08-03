#!/data/data/com.termux/files/usr/bin/bash
#
# tfind — a friendly file-search helper for Termux on Android.
#
# Searches your Termux home *and* your phone's shared storage (/sdcard:
# Downloads, DCIM, Documents, etc.) for files by name, by content, by
# type, by size, or by how recently they changed.
#
# Quick start (run these once inside Termux):
#   pkg install ripgrep        # optional, makes content search much faster
#   termux-setup-storage       # grant access to /sdcard (photos, downloads…)
#   chmod +x tfind.sh          # make this script executable
#   ./tfind.sh name "*.pdf"    # try it
#
# For everyday use, put it on your PATH:
#   mkdir -p ~/bin && cp tfind.sh ~/bin/tfind && chmod +x ~/bin/tfind
#   # then just:  tfind name invoice
#
set -euo pipefail

PROG="$(basename "$0")"

# ---------------------------------------------------------------------------
# Where to search.
#
# By default we look in your Termux home and, if it's been granted, your
# shared storage. Override with:  --in /some/path   (repeatable)
# ---------------------------------------------------------------------------
DEFAULT_ROOTS=()
[ -d "$HOME" ] && DEFAULT_ROOTS+=("$HOME")
# termux-setup-storage creates ~/storage/shared -> /sdcard. Prefer whichever exists.
if [ -d "$HOME/storage/shared" ]; then
    DEFAULT_ROOTS+=("$HOME/storage/shared")
elif [ -d /sdcard ]; then
    DEFAULT_ROOTS+=(/sdcard)
fi

ROOTS=()

usage() {
    cat <<EOF
$PROG — search your files in Termux / Android

USAGE
  $PROG name  <pattern>       Find files whose NAME matches (case-insensitive).
                              Pattern is a glob, e.g. "*.pdf", "invoice*", "notes".
  $PROG text  <pattern>       Search INSIDE text files for a word/phrase (regex ok).
  $PROG type  <ext> [ext...]  Find files with the given extension(s), e.g. jpg png.
  $PROG big   [N]             Show the N largest files (default 20).
  $PROG recent [DAYS]         Show files modified in the last DAYS days (default 7).
  $PROG all                   List every file under the search roots.

OPTIONS
  --in <dir>     Search only <dir> (repeatable). Default: \$HOME and shared storage.
  -h, --help     Show this help.

EXAMPLES
  $PROG name "*.pdf"
  $PROG name invoice
  $PROG text "TODO"
  $PROG type jpg png webp
  $PROG big 10
  $PROG recent 30
  $PROG --in ~/storage/shared/Download name "*.apk"

SEARCH ROOTS (default)
EOF
    if [ "${#DEFAULT_ROOTS[@]}" -eq 0 ]; then
        echo "  (none found — is this Termux? try: termux-setup-storage)"
    else
        printf '  %s\n' "${DEFAULT_ROOTS[@]}"
    fi
}

# Collect --in options from anywhere in the args; return the rest as positionals.
parse_common() {
    REST=()
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --in)
                [ "$#" -ge 2 ] || { echo "$PROG: --in needs a directory" >&2; exit 2; }
                ROOTS+=("$2"); shift 2 ;;
            -h|--help) usage; exit 0 ;;
            *) REST+=("$1"); shift ;;
        esac
    done
    if [ "${#ROOTS[@]}" -eq 0 ]; then
        ROOTS=("${DEFAULT_ROOTS[@]}")
    fi
    if [ "${#ROOTS[@]}" -eq 0 ]; then
        echo "$PROG: no search roots found. Run 'termux-setup-storage' or pass --in <dir>." >&2
        exit 1
    fi
}

cmd_name() {
    parse_common "$@"
    [ "${#REST[@]}" -ge 1 ] || { echo "$PROG: 'name' needs a pattern" >&2; exit 2; }
    local pattern="${REST[0]}"
    find "${ROOTS[@]}" -type f -iname "$pattern" 2>/dev/null
}

cmd_type() {
    parse_common "$@"
    [ "${#REST[@]}" -ge 1 ] || { echo "$PROG: 'type' needs at least one extension" >&2; exit 2; }
    # Build:  find ROOTS -type f \( -iname *.jpg -o -iname *.png \)
    local args=(-type f '(')
    local first=1
    local ext
    for ext in "${REST[@]}"; do
        ext="${ext#.}"  # tolerate leading dot
        if [ "$first" -eq 0 ]; then args+=(-o); fi
        args+=(-iname "*.$ext")
        first=0
    done
    args+=(')')
    find "${ROOTS[@]}" "${args[@]}" 2>/dev/null
}

cmd_text() {
    parse_common "$@"
    [ "${#REST[@]}" -ge 1 ] || { echo "$PROG: 'text' needs a pattern" >&2; exit 2; }
    local pattern="${REST[0]}"
    if command -v rg >/dev/null 2>&1; then
        # ripgrep: fast, skips binaries, shows file:line:match
        rg --hidden --no-messages --line-number "$pattern" "${ROOTS[@]}"
    else
        echo "(tip: 'pkg install ripgrep' for much faster content search)" >&2
        grep -rIn --color=never "$pattern" "${ROOTS[@]}" 2>/dev/null
    fi
}

cmd_big() {
    parse_common "$@"
    local n="${REST[0]:-20}"
    # Print size (human) + path, largest first.
    find "${ROOTS[@]}" -type f -printf '%s\t%p\n' 2>/dev/null \
        | sort -rn \
        | head -n "$n" \
        | awk -F'\t' '{
            s=$1; u="B";
            if (s>=1073741824){s/=1073741824;u="G"}
            else if (s>=1048576){s/=1048576;u="M"}
            else if (s>=1024){s/=1024;u="K"}
            printf "%8.1f%s\t%s\n", s, u, $2
          }'
}

cmd_recent() {
    parse_common "$@"
    local days="${REST[0]:-7}"
    find "${ROOTS[@]}" -type f -mtime "-$days" -printf '%TY-%Tm-%Td %TH:%TM\t%p\n' 2>/dev/null \
        | sort -r
}

cmd_all() {
    parse_common "$@"
    find "${ROOTS[@]}" -type f 2>/dev/null
}

main() {
    [ "$#" -ge 1 ] || { usage; exit 0; }
    local sub="$1"; shift
    case "$sub" in
        name)   cmd_name   "$@" ;;
        type)   cmd_type   "$@" ;;
        text)   cmd_text   "$@" ;;
        big)    cmd_big    "$@" ;;
        recent) cmd_recent "$@" ;;
        all)    cmd_all    "$@" ;;
        -h|--help|help) usage ;;
        *) echo "$PROG: unknown command '$sub'" >&2; echo "Try: $PROG --help" >&2; exit 2 ;;
    esac
}

main "$@"
