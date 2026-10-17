# EDOS build: the MAC/65 sources, assembled with xl/'s mac65.py, which
# makes the same program as MAC/65 1.01 on the Atari.
#
#   make            build/EDOS.COM, its listing and symbols, the font
#                   and the disks
#   make test       every check: the 6502 tests, the sources, the disks
#                   and xl/'s tests
#   make dist       a release's files in dist/
#   make version    the version EDOS shows (x.y, TTL2 in EDOSVARS.M65)
#
# pip install -r xl/requirements.txt
#
#   build/EDOS.COM      the program (binary load file)
#   build/EDOS.LST      listing with addresses and bytes
#   build/EDOS.SYM      symbol table
#   build/EDOS.FNT      the font (xl/tools/font.py)
#   build/EDOS.ATR      tools/disk/BASE.ATR (SpartaDOS 3.2 and its tools)
#                       with EDOS.COM, the font and the sources, numbered
#                       and tokenised; they must give the same EDOS.COM
#   build/EDOSTEST.ATR  the test disk and TESTPLAN.TXT (tools/make_disks.py)
#   build/EDOS-D2.ATR   a DOS 2/MyDOS disk with EDOS.COM
#   build/EDOS-BOOT.ATR only when a DOS master is found: $DOS_ATR or
#                       tools/dos/DOS.ATR (DOS 2.5 or MyDOS, 720
#                       sectors); EDOS_AS_DUP=1 also installs EDOS as
#                       DUP.SYS
#
# build/ and dist/ are what make builds, never committed: releases carry
# the program (.github/workflows/release.yml).

PYTHON     ?= python3
MAC65      := $(PYTHON) xl/tools/mac65.py
SRC        := $(PYTHON) xl/tools/atari_src.py
ATR        := $(PYTHON) xl/tools/atr.py
PROGRAM    := build/EDOS.COM
FONTFILE   := build/EDOS.FNT
DISK       := build/EDOS.ATR
TESTDISK   := build/EDOSTEST.ATR
VERSION    := $(shell $(PYTHON) tools/version.py --source)
# the files EDOS.M65 includes: EDOS's own, and xl/'s shared ones (AX*)
INCLUDES   := $(shell sed -n 's/^ *\.INCLUDE #D:\([A-Z0-9]*\)\.M65.*/\1/p' EDOS.M65)
SRCS       := EDOS.M65 $(patsubst %,%.M65,$(filter-out AX%,$(INCLUDES)))
AXSRCS     := $(patsubst %,xl/src/%.M65,$(filter AX%,$(INCLUDES)))
MASTER     := $(or $(DOS_ATR),tools/dos/DOS.ATR)

.PHONY: all test dist version clean

all: $(PROGRAM) $(FONTFILE) $(DISK) $(TESTDISK) build/EDOS-D2.ATR \
     $(if $(wildcard $(MASTER)),build/EDOS-BOOT.ATR)

# mac65.py finds each .INCLUDE #D:NAME.M65 next to the main file, so
# EDOS's files and xl/'s go together in build/src
$(PROGRAM): Makefile $(SRCS) $(AXSRCS) xl/tools/mac65.py
	rm -rf build/src
	mkdir -p build/src
	cp $(SRCS) $(AXSRCS) build/src/
	$(MAC65) build/src/EDOS.M65 -o $@ -l build/EDOS.LST -s build/EDOS.SYM

$(FONTFILE): xl/tools/font.py xl/font/*
	mkdir -p build
	$(PYTHON) xl/tools/font.py fnt $@

# what is on the disk must build the same program
$(DISK): $(PROGRAM) $(FONTFILE) $(SRCS) $(AXSRCS) tools/disk/BASE.ATR xl/tools/*.py
	$(SRC) disk $@ --program EDOS --version $(VERSION) --base tools/disk/BASE.ATR \
	    $(SRCS) $(AXSRCS) $(PROGRAM) $(FONTFILE) > /dev/null
	rm -rf build/atr
	mkdir -p build/atr
	$(SRC) check --to build/atr $@ > /dev/null
	$(MAC65) build/atr/EDOS.M65 -o build/atr/CHECK.COM > /dev/null
	cmp build/atr/CHECK.COM $(PROGRAM)
	rm -rf build/atr
	@echo "$@: its sources give $(PROGRAM)"

$(TESTDISK): $(PROGRAM) $(FONTFILE) tools/make_disks.py tools/test_commands.py tools/disk/BASE.ATR
	$(PYTHON) tools/make_disks.py

build/EDOS-D2.ATR: $(PROGRAM)
	$(ATR) new $@ > /dev/null
	$(ATR) put $@ $(PROGRAM)

build/EDOS-BOOT.ATR: $(PROGRAM) $(MASTER)
	cp $(MASTER) $@
	$(ATR) put $@ $(PROGRAM)
	if [ "$${EDOS_AS_DUP:-0}" = 1 ]; then $(ATR) put $@ $(PROGRAM) DUP.SYS; fi

test: all
	test "$$($(PYTHON) tools/version.py)" = "$(VERSION)"
	$(PYTHON) tools/test_edos.py
	$(PYTHON) tools/test_commands.py
	$(PYTHON) tools/test_sources.py
	$(PYTHON) tools/test_sparta.py
	$(PYTHON) xl/tests/test_tools.py
	$(PYTHON) xl/tests/test_ax.py

dist: $(PROGRAM) $(FONTFILE) $(DISK) $(TESTDISK)
	rm -rf dist
	mkdir -p dist
	cp $(PROGRAM) $(FONTFILE) $(DISK) $(TESTDISK) dist/

version:
	@echo $(VERSION)

clean:
	rm -rf build dist
