#!/bin/sh
# Build EDOS: assemble, run the 6502 unit tests, and make disk images.
#
#   build/EDOS.COM      binary load file (same format MAC/65 writes)
#   build/EDOS.LST      listing with addresses and bytes
#   build/EDOS.SYM      symbol table
#   build/EDOS.ATR      SpartaDOS disk: tools/disk/BASE.ATR + EDOS.COM + sources
#   build/EDOSTEST.ATR  bootable SpartaDOS test disk + TESTPLAN.TXT
#   build/EDOS-D2.ATR   DOS 2/MyDOS data disk holding EDOS.COM
#   build/EDOS-BOOT.ATR bootable disk, only if a DOS master is found:
#                       $DOS_ATR or tools/dos/DOS.ATR (DOS 2.5 or MyDOS,
#                       720 sectors). Set EDOS_AS_DUP=1 to also install
#                       EDOS as DUP.SYS.
set -e
cd "$(dirname "$0")/.."
mkdir -p build

python3 xl/tools/mac65.py EDOS.M65 -o build/EDOS.COM -l build/EDOS.LST -s build/EDOS.SYM

if python3 -c 'import py65' 2>/dev/null; then
    python3 tools/test_edos.py
    python3 tools/test_commands.py
else
    echo "py65 not installed (pip install py65): skipping unit tests"
fi

python3 tools/test_sources.py
python3 tools/make_disks.py
python3 tools/test_sparta.py

python3 xl/tools/atr.py new build/EDOS-D2.ATR >/dev/null
python3 xl/tools/atr.py put build/EDOS-D2.ATR build/EDOS.COM

master=${DOS_ATR:-tools/dos/DOS.ATR}
if [ -f "$master" ]; then
    cp "$master" build/EDOS-BOOT.ATR
    python3 xl/tools/atr.py put build/EDOS-BOOT.ATR build/EDOS.COM
    if [ "${EDOS_AS_DUP:-0}" = 1 ]; then
        python3 xl/tools/atr.py put build/EDOS-BOOT.ATR build/EDOS.COM DUP.SYS
    fi
fi
