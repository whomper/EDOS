# EDOS
E-DOS is a refreshed Disk Utility Package (DUP) that sits on
top of a regular DOS, such as MyDOS or SpartaDOS to provide a
menu based disk operations in a friendly user interface.

I have created this softare to provide me withthe best disk
management experience that is simple yet full of missing
functions classical interfaces do not have, such as sector
copier, memory dump and more.

## The Story Behind It
When I got my first Atari 600XL back in 1984 (after spending
time each afternoon at my friend's place programming his
Atari 400), I taught myself Assembly and have started
programming various utilities and games. I also spent hours
during school classes to write Assebly code snippets in my
coding notebook.

A few yers back I've stumbled across that same notebook and
noticed I've been working on my own version of Atari Disk
Utility Package, or DOS Menu.

Buying back my Atari setup and now migrting to the Atari
1200XL with 2 1050 disk drives and other peripherals, I
bought myself an Assembly MAC/65 cartridge and resumed my
teen project.

Presented here is my completed project.
I've added many functions that are  missing from similar
solutions and am also actively using it in my day to day
Atari activities.

## Main Conepts and Commands
As with any DOS menu program, the obvious set of funtions are
provided and a few essentials have been added as well. This
reduces the need to call for external utilities.

A top line status bar provides additonal information, such as
connected drives, default drive number, whether it is high
speed enabled and the total available extendd memory.

Here's a list of provided commands:
- Show Directory
- Goto Cartridge / Memory address
- Copy Files
- Duplcaite Disk
- Erase Files
- Initiatize Disk
- View File / Sector / Memory
- Protect / Unprotects Files
- Load / Save Binary File
- Compare Files

The default drive can be selected using the New Drive command and all subsequent commands defualt to it unless another
drive is specified, either in the full filename or a specific selection (as in Duplicate Disk command)

## File Structure
The project contains several files, eachone focuses on
different parts and with extensiblity in mind.

Here is a rundown of the contained files and their purpose:

- EDOS.M65 - The main application codebase
- EDOSVARS.M65 - Main application variables and string
constants
- UTILS.M65 - A set of general purpose utilities that can be
used in other projects
- MACROS.M65 - A set of general purpose Mac/65 macros to
simplify development
- SYSTEM.M65 - System wide constants and defaults

## UTILS.M65 Functions List
- DSPBIN - Display a 80 byte binary address on screen, nicely
formatted
- DRAW - Draw a horizontal line via special char
- RSTSCTCNT - Resets a 4 digit sector counter
- BNK2DEC - Convert # memory banks to display text
- INCSCTCNT - Increment a decimal sector counter by one
- DTCDNS - Detect inserted disk density
- RESETFIO - Resets FSIOV address location
- READFIO - Load fast IO code from Speedy into memory
- RDSCT - Reads one sector
- WRTSCT - Writes one sector
- INCCNTR - Incremets FILPOS counter
- INCPTR - Increment INDPTR page zero pointer
- DOSIO - Perform SIO operation
- CALLSIO - Calls the actual SIOV function, uses fast SIO
- FXSCSZ - Fix SIO sector size based on density and sector
number
- INP2ADDR - Convert INP1 to Hex address
- DOCIO - Perform CIO operation
- DISKERR - Handles error condition and display message
- GETCHR - Gets one character from user
- MUL16 - 16 bit multiplication
- GETTEXT - Gets a line of text fromte user
- PRNTLN - Prints one line on screen
- PRNTNL - Goes down one line
- BIN2DEC - 2 byte hex 2 ASCII decimal FF->"255"
- BIN2HEX - 1 byte binary to hex conversion A0->"A0"
- DTXMEM - Detect number of extended memory banks
- HEX2BIN - 1 byte ASCII hex to hex number conversion
"A0"->A0
- DEC2HEX - 4 digits decimal to HEX conversion "1234"->04C2


## MACROS.M65 Macros List
- @COPYMEM - Copies one memory buffer to another
- @WRD2STK - Pushes a word on the stack
- @PTR2STK - Pushes a pinter on the stack
- @CACHECURPOS - Caches the cursor position on the stack
- @HIDECURSOR - Hides the cursor
- @SHOWCURSOR - Shows the cursor
- @COLGRN - Background screen color to green
- @COLRED - Background screen color to red
- @COLDEF - Background screen color to black
- @MKBOLD - Makes a char bold
- @MKASCII - Makes a digit an ASCII one
- @GETRETADR - Get a stored return address to jump from the stack
- @SETRETADR - Caches address to return on the stack
- @SIOSNDOFF - Turns off SIO sounds
- @SIOSNDON - Turns on SIO sounds
- @HIDECHR - Do not display special characters
- @SHWCHR - Display special characters
- @RSTCURPOS - Restor cursor position
- @POINT2TXT - Points zero page pointer to buffer
- @FILLMEM - Fills memory with a character
- @INPRM - Set memory location for text input
- @MUL16PRM - Set MUL16 input paramters
- @DRAW - Draw function helper
- @PRNTLN - PRNTLN function helper
- @SETSCT - Sets sector numbe for operation
- @DOSIO - DOSIO function helper
- @DOCIO - DOCIO function helper
- @CLOSEIO - Closes all open IO channels
- SETRTNA - Caches the address to return from functions that have no RTS
