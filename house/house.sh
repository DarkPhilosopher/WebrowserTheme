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
# Inside the builder type `help` for the command list. Type `3d` for a
# rotatable 3D wireframe view, then e.g. `rotate y 45`, `rotate x 22.5`, `spin`.
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

VIEW=2d          # 2d (flat art) | 3d (rotatable wireframe)
RX=20            # 3D view rotation about X (degrees) — LOCAL to your phone
RY=-30           # 3D view rotation about Y (degrees)
RZ=0             # 3D view rotation about Z (degrees)
ZOOM=1           # 3D view zoom factor (1 = default) — LOCAL to your phone

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

build_3d() {  # echo a rotatable 3D wireframe of the house (math done in awk)
    command -v awk >/dev/null 2>&1 || { echo "(3D view needs awk — in Termux: pkg install gawk)"; return; }
    awk -v rx="$RX" -v ry="$RY" -v rz="$RZ" -v roof="$ROOF" -v chim="$CHIMNEY" \
        -v door="$DOOR" -v win="$WINDOWS" -v W=48 -v H=24 -v SX=5.0 -v SY=2.4 -v zm="$ZOOM" '
    function abs(v){ return v<0?-v:v }
    function addedge(a,b,c,d,e,f){ ne++; X1[ne]=a;Y1[ne]=b;Z1[ne]=c;X2[ne]=d;Y2[ne]=e;Z2[ne]=f }
    function addcube(x0,y0,z0,x1,y1,z1){
        addedge(x0,y0,z0,x1,y0,z0); addedge(x1,y0,z0,x1,y0,z1); addedge(x1,y0,z1,x0,y0,z1); addedge(x0,y0,z1,x0,y0,z0);
        addedge(x0,y1,z0,x1,y1,z0); addedge(x1,y1,z0,x1,y1,z1); addedge(x1,y1,z1,x0,y1,z1); addedge(x0,y1,z1,x0,y1,z0);
        addedge(x0,y0,z0,x0,y1,z0); addedge(x1,y0,z0,x1,y1,z0); addedge(x1,y0,z1,x1,y1,z1); addedge(x0,y0,z1,x0,y1,z1);
    }
    function rot(x,y,z,   c,s,tx,ty,tz){
        c=cos(rxr);s=sin(rxr); ty=y*c-z*s; tz=y*s+z*c; y=ty; z=tz;   # about X
        c=cos(ryr);s=sin(ryr); tx=x*c+z*s; tz=-x*s+z*c; x=tx; z=tz;  # about Y
        c=cos(rzr);s=sin(rzr); tx=x*c-y*s; ty=x*s+y*c; x=tx; y=ty;   # about Z
        RXo=x; RYo=y; RZo=z;
    }
    function drawline(x1,y1,x2,y2,ch,   dx,dy,st,i,xx,yy){
        dx=x2-x1; dy=y2-y1; st=(abs(dx)>abs(dy))?abs(dx):abs(dy); if(st<1)st=1;
        for(i=0;i<=st;i++){ xx=int(x1+dx*i/st+0.5); yy=int(y1+dy*i/st+0.5);
            if(xx>=0 && xx<W && yy>=0 && yy<H) G[yy SUBSEP xx]=ch }
    }
    BEGIN{
        PI=atan2(0,-1); rxr=rx*PI/180; ryr=ry*PI/180; rzr=rz*PI/180;
        if(zm+0<=0) zm=1; SX=SX*zm; SY=SY*zm;     # apply zoom
        bx=2; by=1.5; bz=1;                       # body half-extents
        addcube(-bx,-by,-bz, bx,by,bz);           # walls
        if(roof=="peak"){ ap=3;
            addedge(0,ap,-bz, 0,ap,bz);
            addedge(0,ap,-bz,-bx,by,-bz); addedge(0,ap,-bz, bx,by,-bz);
            addedge(0,ap, bz,-bx,by, bz); addedge(0,ap, bz, bx,by, bz);
        } else if(roof=="flat"){ addcube(-bx,by,-bz, bx,by+0.4,bz);
        } else { ap=by+1.5;                       # dome -> hip/pyramid roof
            addedge(0,ap,0,-bx,by,-bz); addedge(0,ap,0, bx,by,-bz);
            addedge(0,ap,0, bx,by, bz); addedge(0,ap,0,-bx,by, bz);
        }
        if(chim=="on") addcube(0.8,2.0,-0.3, 1.2,3.0,0.1);   # chimney
        if(door!="none"){ dw=(door=="double")?0.6:0.35; z=bz; y0=-by; y1=-by+1.4;
            addedge(-dw,y0,z, dw,y0,z); addedge(dw,y0,z, dw,y1,z);
            addedge(dw,y1,z,-dw,y1,z); addedge(-dw,y1,z,-dw,y0,z);
            if(door=="double") addedge(0,y0,z, 0,y1,z);
        }
        wn=win+0;
        if(wn>0){ z=bz;
            for(k=0;k<wn;k++){ cx=-1.3 + 2.6*(k+0.5)/wn; wx=0.28; a=0.2; b=0.9;
                addedge(cx-wx,a,z, cx+wx,a,z); addedge(cx+wx,a,z, cx+wx,b,z);
                addedge(cx+wx,b,z, cx-wx,b,z); addedge(cx-wx,b,z, cx-wx,a,z);
                addedge(cx,a,z, cx,b,z); addedge(cx-wx,(a+b)/2,z, cx+wx,(a+b)/2,z);
            }
        }
        for(i=1;i<=ne;i++){
            rot(X1[i],Y1[i],Z1[i]); px=RXo; py=RYo;
            rot(X2[i],Y2[i],Z2[i]); qx=RXo; qy=RYo;
            sx1=int(W/2+px*SX+0.5); sy1=int(H/2-py*SY+0.5);
            sx2=int(W/2+qx*SX+0.5); sy2=int(H/2-qy*SY+0.5);
            ddx=sx2-sx1; ddy=sy2-sy1; a1=abs(ddx); a2=abs(ddy);
            if(a1>2*a2) ch="-"; else if(a2>2*a1) ch="|";
            else if((ddx>0)==(ddy>0)) ch="\\"; else ch="/";
            drawline(sx1,sy1,sx2,sy2,ch);
        }
        for(y=0;y<H;y++){ line="";
            for(x=0;x<W;x++){ kk=y SUBSEP x; line=line ((kk in G)?G[kk]:" ") }
            sub(/ +$/,"",line); print line;
        }
    }'
}

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
    if [ "$VIEW" = 3d ]; then
        printf '  3D view  rot x=%s y=%s z=%s  zoom=%s   (rotate y 45 · zoom in · spin · 2d)\n\n' "$RX" "$RY" "$RZ" "$ZOOM"
        while IFS= read -r line; do printf '   %s\n' "$line"; done < <(build_3d)
    else
        while IFS= read -r line; do printf '   %s\n' "$line"; done < <(build_lines)
    fi
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
house — all commands
====================

BUILD THE HOUSE (these sync to everyone in an online game)
  roof    <peak|flat|dome>           Choose the roof shape.
  walls   <brick|wood|stone>         Choose the wall material.
  door    <single|double|arch|none>  Choose the front door.
  windows <0-4>                      How many windows.
  chimney <on|off>                   Add or remove the chimney.
  ground  <grass|fence|none>         What surrounds the house.

VIEW & CAMERA (local to your phone; does not change what others see)
  3d                                 Rotatable 3D wireframe view.
  2d                                 Flat picture view.
  rotate  <x|y|z> <degrees>          Turn the 3D view any angle
                                     (rotate y 45 · rotate x 22.5 · rotate z -45).
  rotate  reset                      Recenter the 3D angles.
  zoom    <in|out|reset|number>      Zoom the 3D view (zoom in · zoom out · zoom 1.5).
  spin                               Auto-turn the house one full spin.
  show | draw                        Redraw now (also pulls in an online game).

MULTIPLAYER (online games only)
  sync                               Pull the latest shared house (see others).
  watch                              Live view; refreshes until you press Enter.

OTHER
  save [file]                        Save the ASCII art to a file (default house.txt).
  help | ?                           Show this list.
  quit | exit                        Leave.

Started from the shell, the script also takes:
  house.sh new <id> | join <id> <name> | watch <id> | solo | help
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
        3d)      VIEW=3d ;;
        2d)      VIEW=2d ;;
        rotate|rot) do_rotate "${1:-}" "${2:-}" || return ;;
        zoom)    do_zoom "${1:-}" || return ;;
        spin)    do_spin; return ;;
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

# rotate the local 3D view. Accepts any angle (45, 22.5, -45, ...).
do_rotate() {
    local axis="$1" deg="$2"
    if [ "$axis" = reset ]; then RX=20; RY=-30; RZ=0; VIEW=3d; return 0; fi
    case "$axis" in x|y|z) ;; *) echo "rotate: x|y|z <degrees>   e.g.  rotate y 45   rotate x 22.5"; return 1 ;; esac
    case "$deg" in ''|*[!0-9.+-]*) echo "rotate: degrees must be a number, e.g. 45, 22.5, -45"; return 1 ;; esac
    VIEW=3d
    case "$axis" in
        x) RX="$(awk "BEGIN{printf \"%g\", ($RX+($deg))%360}")" ;;
        y) RY="$(awk "BEGIN{printf \"%g\", ($RY+($deg))%360}")" ;;
        z) RZ="$(awk "BEGIN{printf \"%g\", ($RZ+($deg))%360}")" ;;
    esac
    return 0
}

# zoom the local 3D view.  `zoom in`, `zoom out`, `zoom reset`, or `zoom 1.5`.
do_zoom() {
    local arg="$1"
    VIEW=3d
    case "$arg" in
        in|'+')  ZOOM="$(awk "BEGIN{z=$ZOOM*1.3; if(z>6)z=6; printf \"%g\", z}")" ;;
        out|'-') ZOOM="$(awk "BEGIN{z=$ZOOM/1.3; if(z<0.3)z=0.3; printf \"%g\", z}")" ;;
        reset|'') ZOOM=1 ;;
        *[!0-9.]*) echo "zoom: in | out | reset | <number>   e.g.  zoom in   zoom 1.5"; return 1 ;;
        *) ZOOM="$(awk "BEGIN{z=$arg; if(z<0.3)z=0.3; if(z>6)z=6; printf \"%g\", z}")" ;;
    esac
    return 0
}

# quick auto-spin: eight 22.5-degree steps around Y (a full turn).
do_spin() {
    VIEW=3d; local i
    for i in 1 2 3 4 5 6 7 8; do
        RY="$(awk "BEGIN{printf \"%g\", ($RY+22.5)%360}")"
        render
        sleep 0.15 2>/dev/null || true
    done
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
