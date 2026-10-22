# EDOS

<img src="https://raw.githubusercontent.com/whomper/AERA-Atari/main/brand/aera-star.jpg" width="96" align="right" alt="The AERA star, a four-point star in brushed metal, standing in for an icon">

A menu-driven Disk Utility Package for Atari 8-bit computers, written in 6502 assembly with MAC/65,
running on top of MyDOS, SpartaDOS or DOS 2.5.

**Highlights**

- **Every disk job on one screen:** directory, copy, duplicate, erase, rename, protect, format,
  binary load and save, compare. Each is one key from the menu, with no external utilities to find
- **The same on any DOS:** EDOS works through CIO and SIO, not a DOS's own calls, so it looks and
  behaves alike on MyDOS, SpartaDOS and DOS 2.5
- **Big copies in one pass:** Copy Files and Duplicate Disk go through the extended memory of an
  expanded XL or XE
- **Fast disk copies:** when a drive has its own fast SIO code, Duplicate Disk reads it from the drive
  and uses it, whatever DOS you run
- **Colour shows what's happening:** green while reading, red before anything is written or erased
- **Sectors and memory too:** view any file, sector or memory address 128 bytes at a time; jump to
  an address or into the cartridge
- **Small:** `EDOS.COM` is about 7.3K
- **Assembles on the Atari:** the MAC/65 sources are on the disk; a PC cross assembler and tests are
  here too

![The EDOS 3.7 main menu: drives 1 and 2, HIGH speed and 512K of extended memory on the status line, and the twenty commands](EDOS.png)

## The commands

Press the key in inverse on the menu; **RETURN** shows the menu again, and **HELP** (or **?**) shows
the About lines: the version, the copyright and licence, and where EDOS lives. The status line at
the top shows the drives connected (the current one in inverse), **HIGH** when that drive runs at
high speed (**NORM** when not), and the extended memory (**XMEM**).

- **Dir D1-D8** (1 to 8) and **Files on Disk** (F): a two-column directory with the number of files
  and the free space. 1 to 8 list that drive whichever is current.
- **Copy Files** (C): copies one or more files from one disk to another. Name the files, then the
  target drive, or Y for the same drive and swap disks when asked. The copy goes through extended
  memory, so large files go in one pass. Without extended memory, or for a file longer than it
  (EDOS uses up to 256K), EDOS says **Not enough memory!**
- **Duplicate Disk** (D): copies a whole disk, sector by sector, through extended memory. It reads
  the current drive (**N** picks it): press Y to start. Once it is read, give the target drive, or
  put the target disk in the same drive and press Y. EDOS checks whether the target disk is
  formatted and has the source's density, and formats it if it needs to. The whole disk must fit in
  extended memory: 96K for single density, 144K for enhanced, 192K for double, so a 130XE's own 64K
  is not enough.
- **Erase Files** (E), **Protect Files** (P), **Unprotect Files** (U), **Rename Files** (R): one or
  more files at a time, with wildcards.
- **Initialize Disk** (I): formats a disk in single, enhanced or double density.
- **View File** (V), **Analyze Sector** (A), **Memory Status** (M): one viewer, 128 bytes a screen.
  View File starts at a position you give in hex, Analyze Sector at a sector number in decimal, and
  Memory Status at a hex address, under `MEMLO` and `MEMTOP` (**LOW** and **HIGH**). Sectors and
  memory go forwards (+) and backwards (-).
- **Load Binary** (L): asks whether to run the program, then loads it and runs it if you said so. A
  small loader in page 6 ($0600-$06FF) does the reading, so a program may load over EDOS itself, its
  screen or its font. If it does, EDOS hands RESET back to DOS and you end up in DOS; otherwise you
  come back to the menu. Loading stops before anything is written to page 6.
- **Save Binary** (S): saves a memory range, with a run address.
- **Byte Compare** (B): tells you whether two files are the same: the same length and the same
  bytes.
- **Go To Address** (G): jumps to an address of one to four hex digits. **To Cartridge** (T): starts
  the cartridge, when there is one.
- **New Drive** (N): sets the current drive. Every command uses it unless you name another.
- **Write EDOS** (W): saves EDOS itself as `EDOS.COM` on the current drive: the program as it is in
  memory, without the check of `MEMLO` and `MEMTOP` that the release's file starts with.
- **Quit to DOS** (Q).

**ESC** (or **BREAK**) at any question or prompt is a "no": nothing is written, erased or changed,
what you typed is thrown away and you are back at the menu. During Duplicate Disk and Copy Files,
ESC stops the copy and EDOS says **Stopped**. Typed names and numbers take **DELETE BACK S**; the
arrow keys do nothing there. EDOS turns caps lock on before every key it reads, so names and hex
digits come in capitals.

File names follow the usual DOS rules: `D2:GAME.COM`, `2:GAME.COM`, `GAME.COM`, `D:GAME.COM`,
`*.COM`, `G*.*` and other wildcards. A drive number in the name works on that drive without changing
the current one; without one (`GAME.COM`, `D:GAME.COM`) the current drive is used.

## Getting started

Download from **[Releases](../../releases/latest)**:

| File | What it is |
|---|---|
| `EDOS.ATR` | a bootable SpartaDOS 3.2 disk with EDOS, its font and the current MAC/65 sources |
| `EDOS.COM` | the program: a binary load file for any DOS |
| `AERA.FNT` | the AERA family's character set; keep it next to `EDOS.COM` |
| `EDOSTEST.ATR` | a bootable test disk with the test files and `TESTPLAN.TXT`, 46 checks for a real Atari |

1. Boot `EDOS.ATR` and type `EDOS` at the SpartaDOS prompt.
2. Or copy `EDOS.COM` and `AERA.FNT` to your own DOS disk and load `EDOS.COM` (**L** in the DOS 2.5
   or MyDOS menu, `EDOS` at the SpartaDOS prompt). On DOS 2.5 and MyDOS, EDOS can also take the
   place of `DUP.SYS`: copy `EDOS.COM` to the DOS disk as `DUP.SYS`.
3. Press **N** to pick your drive, then any command's key.

**To update**, take the new release's `EDOS.COM` and `AERA.FNT` in place of the old ones, or its
`EDOS.ATR`. EDOS has no settings to keep. A release's `EDOS.ATR` and `EDOSTEST.ATR` may be renewed
after it is out, with newer sources; its `EDOS.COM` stays the same.

EDOS loads `AERA.FNT`, the font every AERA program uses, as `D:AERA.FNT` when it starts: from D1 on
DOS 2.5, from the current drive and folder on SpartaDOS. Without it, or without room for it above
$8000, EDOS keeps the Atari's own font. Any 1,024-byte Atari character set saved as `AERA.FNT`
works.

**Needs:** an Atari 400, 800, XL or XE with 48K and a disk drive, and MyDOS, SpartaDOS 3.x or DOS
2.5. Copy Files and Duplicate Disk need 130XE-style extended memory (above); the other commands
don't. EDOS runs at $1E00-$3FFF. It also needs free memory up to $8000: during copies the extended
memory banks appear at $4000-$7FFF, so the screen must be above them, and Byte Compare reads the
files into $4000-$50FF. When DOS ends above $1E00 (`MEMLO`) or memory ends below $8000 (`MEMTOP`),
EDOS says so as it loads and goes back to DOS before anything is overwritten. Any 48K Atari has
room.

## Building

```sh
pip install -r xl/requirements.txt   # py65, for the tests
make                                 # assembles and makes the disk images
make test                            # and runs every test
```

| `make` writes | What it is |
|---|---|
| `build/EDOS.COM`, `EDOS.LST`, `EDOS.SYM` | the program, its listing and its symbols |
| `build/AERA.FNT` | the family's font, as `xl/font/AERA.FNT` has it: `EREZ.FNT` moved one pixel right so inverse letters show as blocks |
| `build/EDOS.ATR` | the EDOS disk: SpartaDOS 3.2 and the utilities from `tools/disk/BASE.ATR`, with `EDOS.COM`, `AERA.FNT` and the sources numbered and tokenised as MAC/65 saves them; `make` checks they assemble to the same `EDOS.COM` |
| `build/EDOSTEST.ATR` | the test disk |
| `build/EDOS-D2.ATR` | a DOS 2/MyDOS disk with `EDOS.COM` |
| `build/EDOS-BOOT.ATR` | a bootable DOS 2.5 or MyDOS disk with `EDOS.COM`, when you put that DOS's master disk at `tools/dos/DOS.ATR` (`EDOS_AS_DUP=1` also installs EDOS as `DUP.SYS`) |

`xl/tools/mac65.py`, the family's cross assembler (from AERA-Atari's `xl` branch, in `xl/`), takes
the MAC/65 syntax used here. Fed the February 2025 sources, it makes the same `EDOS.COM` that MAC/65
made then, byte for byte. `build/` is what the build
writes; it is never committed.

**On the Atari**, with the sources from `EDOS.ATR` on D1:

```
LOAD #D:EDOS.M65
ASM ,,#D:EDOS.COM
```

`EDOS.M65` holds only the list of includes; MAC/65 reads the rest from disk as it assembles, which
leaves about 20K for the symbol table. Always give the object file: a plain `ASM` writes the program
into memory at $1E00, where MAC/65 keeps its own work area. `ASM #D:EDOS.M65,,#D:EDOS.COM` works on
DOS 2.5 and MyDOS but not on SpartaDOS: MAC/65 1.01 rewinds the main file for its second pass with a
POINT that SpartaDOS rejects, and stops with `ERROR -` and no number.

**Versions and releases.** The version is the one in the title bar (`TTL2` in `EDOSVARS.M65`); every
source file's header and the About lines repeat it, and the build fails when they differ. To release: change them, add
`release-notes/vX.Y.md`, commit and push, then run the Release workflow (Actions > Release > Run
workflow, on main; the family's, from `xl/`), or push a tag `vX.Y` made with `git tag -a`. GitHub
Actions runs `make test` and `make dist`, checks the tag against `make version`, tags the commit and
publishes `EDOS.COM`, `AERA.FNT`, `EDOS.ATR` and `EDOSTEST.ATR` as a GitHub Release with the notes.
The Withdraw workflow marks a bad release as withdrawn. From then on, each push
to main that leaves `EDOS.COM` as released replaces that release's `EDOS.ATR` and `EDOSTEST.ATR` with
the new build, so the disk always carries the current sources; a changed program waits for the next
release. To try a fix on a real Atari, release it; if a release doesn't work, revert on main, release
the next number and say in the bad release's notes that it is withdrawn.

## Source

```
EDOS.M65       the main file, the one MAC/65 loads: options, origin and the includes
EDOSMAIN.M65   start-up, the menu and Load Binary (with its page-6 loader)
EDOSCMD.M65    View, Analyze, Compare, Memory, New, Quit, Dir, Cartridge, Copy Files
EDOSDISK.M65   Duplicate, Erase, Initialize, Protect, Unprotect, Rename, Write EDOS, Save, Go To
EDOSSCRN.M65   the directory, the drive and status lines, the title bar, the About lines, the
               command table
EDOSVARS.M65   variables, the menu and the messages
UTILS.M65      general routines, usable in other programs (list below)
KEYS.M65       keys and typed lines: ESC and BREAK cancel
MACROS.M65     MAC/65 macros (list below)
SYSTEM.M65     EDOS's constants and zero page (the OS's names are xl's AXEQU.M65)
tools/         disks, screenshot, the tests and their DOS and drive (on xl's a8sim)
xl/            the AERA family's shared tools and includes (tools/sync-xl.sh updates it); EDOS
               includes AXEQU, AXLOAD (the load check), AXRESET (RESET back into EDOS),
               AXFONT (AERA.FNT below the screen, again after RESET) and AXERR (the error texts)
release-notes/ what each release changed
```

In git the sources have no line numbers; on the disk they are numbered 10, 20, ... and tokenised as
MAC/65's SAVE writes them (`xl/tools/atari_src.py`, `mac65tok.py`). A file changed on the Atari comes
back with `python3 xl/tools/atari_src.py import FILE.M65 FILE.M65`. `xl/tools/sparta.py` and `atr.py`
read and write SpartaDOS, DOS 2 and MyDOS disk images.
`tools/screenshot.py EDOS.png` draws the menu picture above by running `EDOS.COM` on the emulated 6502
(it needs Pillow).

**UTILS.M65**

| Routine | What it does |
|---|---|
| `DSPBIN`, `DRWHDR` | show up to 128 bytes, 8 a row, with their addresses; draw the header line |
| `DRAW` | draws a horizontal line in a special character |
| `RSTSCTCNT`, `INCSCTCNT` | reset and count up a four-digit decimal sector counter |
| `DTXMEM`, `BNK2DEC` | count the extended memory banks; show the count as text |
| `DTCDNS` | finds the density of the disk in a drive |
| `RESETFIO`, `READFIO` | forget the fast SIO code; read it from the drive into memory |
| `DOSIO`, `CALLSIO` | an SIO operation; the SIOV call, with the drive's fast SIO code when loaded |
| `WRTSCT` | writes one sector |
| `FXSCSZ` | sets the SIO sector size from the density and the sector number |
| `DOCIO`, `CLOSECHANNEL` | a CIO operation; close an IOCB |
| `DISKERR`, `ERRTXT` | handle an error and show its message; the text for a CIO error code (xl's `AXERRT`) |
| `INLINE` | points `RETADR` at the parameters after a `JSR` and returns past them |
| `GETCHR`, `GETKEY`, `GETTEXT`, `GETINP1`, `CHKESC` (in `KEYS.M65`) | read a key and show it, or not; read a line, key by key; a line into `INP1`; ESC or BREAK in a disk job |
| `GETADDR`, `INP2ADDR`, `A2HEX` | read an address; one to four hex digits in `INP1` to an address; one hex digit |
| `PRNTLN`, `PRNTDL`, `PRNTNL` | print text up to and with EOL; up to DEL; go down one line |
| `BIN2DEC` | `VALUE` to decimal text at A/Y: $FF → "255" |
| `DEC2HEX` | four decimal digits to a number: "1234" → $04D2 |
| `HEXOUT` | one byte to two hex digits at `FILE`,Y: $A0 → "A0" |
| `COPY`, `FILL` | copy text up to EOL; fill memory (used by `@CPYMEM` and `@FILLMEM`) |
| `HIDECURSOR`, `SHOWCURSOR`, `SETCOLRED` | hide and show the cursor; turn the border red |

**MACROS.M65**

| Macro | What it does |
|---|---|
| `@CPYMEM` | copies one buffer to another (with two parameters: `JSR COPY`) |
| `@FILLMEM` | fills memory with a character (`JSR FILL`) |
| `@PRNTLN` | calls `PRNTLN` or `PRNTDL` |
| `@DRAW`, `@DOSIO`, `@DOCIO` | call `DRAW`, `DOSIO` and `DOCIO` with their parameters |
| `@CLOSEIO` | closes an IOCB |
| `@INPRM` | sets where text input goes |
| `@SETSCT` | sets the sector number for an operation |
| `@POINT2TXT` | points `INDPTR` at a buffer |
| `@CHECURPOS`, `@RSTCURPOS` | keep the cursor position on the stack; put it back |
| `@HIDCUR`, `@SHWCUR` | hide and show the cursor |
| `@HIDCHR`, `@SHWCHR` | carry out control characters, or show them as characters |
| `@COLGRN`, `@COLRED`, `@COLDEF` | border green, red, or black |
| `@MKCAPS` | turns caps lock on |
| `@MKASCII`, `@RMASCII` | a digit to ASCII and back |
| `@SIOSNDOFF`, `@SIOSNDON` | turn the SIO beeps off and on |

## Tests

The tests run the real `EDOS.COM` on the family's emulated Atari (`xl/tools/a8sim`, on
[py65](https://github.com/mnaberez/py65)) with 256K of banked memory, and EDOS's own simulated DOS
(files on D1: and D2:), simulated disk drive and scripted keys and lines (`tools/difftest.py`):

```
make test                          # runs them all, and xl/'s own
python3 tools/test_commands.py     # every menu command, the menu keys, start-up, RESET and the
                                   # exits (Quit, Cartridge, Go To): files written, memory loaded,
                                   # sectors copied, screen text and where control goes
python3 tools/test_edos.py         # routines: conversions, error texts, the disk copy loop in
                                   # every density, fast SIO loading, the memory layout
python3 tools/test_sources.py      # the sources as git and MAC/65 need them
python3 tools/test_sparta.py       # the disk images: files read back, fsck, the sources on the
                                   # disk assemble to EDOS.COM
python3 tools/difftest.py OLD NEW  # 34 command runs on two builds: any change in the screens,
                                   # CIO and SIO calls, files or memory
```

`difftest.py` is how every size reduction was checked to change nothing. GitHub Actions runs the build
and the tests on every push; only releases are published. Before a release, `xl/tools/atari800/`
runs the disk in atari800 (with its own OS ROM, so no Atari ROMs are needed): `a8check.py start`
boots `EDOS.ATR` and starts EDOS, and `a8check.py mac65` has the real MAC/65 1.01 assemble the disk's
sources (the cartridge image is kept out of git) to the same bytes as `EDOS.COM`. On a real Atari,
boot `EDOSTEST.ATR` and follow `TESTPLAN.TXT` (`TYPE TESTPLAN.TXT`).

## The story behind it

I got my first Atari, a 600XL, in 1984, after afternoons at a friend's place programming his Atari
400. I taught myself assembly and wrote utilities and games, and spent hours in school lessons writing
assembly in my coding notebook.

A few years ago I came across that notebook again and found I had been writing my own Disk Utility
Package. I bought back an Atari setup, now a 1200XL with two 1050 drives, got a MAC/65 cartridge and
picked up my teenage project where I'd left it. EDOS is that project finished, with the functions I
missed in the others, and I use it on my Atari every day.

## Licence

EDOS is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 2 of the License, or (at your option)
any later version. It is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See [COPYING](COPYING).

Copyright (C) 2024-2026 AERA | Erez Yaary.

The disk images also carry SpartaDOS and the other DOS files they boot with; those stay under their
own authors' terms.

---

Part of **AERA** for Atari: [ECal](https://github.com/whomper/ECal) · [EContact](https://github.com/whomper/EContact) · [EMail](https://github.com/whomper/EMail) · [EFTP](https://github.com/whomper/EFTP) · [EHypView](https://github.com/whomper/EHypView) · [ClaudeST](https://github.com/whomper/ClaudeST) · 8-bit: [EDOS](https://github.com/whomper/EDOS) · [EFTP_XL](https://github.com/whomper/EFTP_XL)
