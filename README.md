# EDOS
E-DOS is a refreshed Disk Utility Package (DUP) that sits on
top of a regular DOS, such as MyDOS or SpartaDOS to provide a
menu based disk operations in a friendly user interface.
 
I have created this software to provide me with the best disk
management experience that is simple yet full of missing
functions classical interfaces do not have, such as sector
copier, memory dump and more.

As EDOS can work with many DOS solutions, it provides a
consistent interface for those who work with multiple DOS
solutions. Care was given to not rely on specific DOS APIs
and functionalty and most functions have been coded to the
core CIO or SIO building blocks.

Disk operations could be destructive at times, deleting
precious files or whole disks. EDOS tries to make that easier
via visual and colorful queues for read versus write
operations so that the user can avoid unwanted deletions.

EDOS is also offered in an Open Source fasion and all source
code is free to review and leverage, providing recognition is
properly mentioned.

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

## Main Concepts and Commands
As with any DOS menu program, the obvious set of functions are provided and a
few essentials have been added as well. This reduces the need to call for
external utilities.

A top line status bar provides additional information, such as connected
drives, default drive number, whether it is high speed enabled and the total
available extended memory.

Here's a list of provided commands with short explanation:
### Show Directory
Displays a two column directory list with files count and free space.
Clicking on keys 1-8 performs the same function irrespective of selected
drive.

### Go to Cartridge
Enters a cartridge if one is present.

### Go to Address
Enter a 4 digit hex address to jump.

### Copy Files
Copies one of more files between 2 disks. File name uses standard DOS
convention and can have source drive number a well (either D#: or #:). Target
drive number, or Y for same, needs to be selected.
The copy operation works for all files, alternating the background color for
Read (Green) or Write (Red) operations.
This operation uses extended memory in order to copy large files.

### Duplicate Disk
Duplicates a full disk between two drives using available extended memory. A
sector copy operation will be used and if the drive has Fast SIO
capabilities, its Fast IO code will be read and used. This ensures the fasted
sector copy operation irrespective of underlying DOS.
Source drive is selected and read. Once read operation is complete, the user
will be asked to input target disk number (or Y for same). The background
color will change to Red indicating a destructive operation.
Once the target disk is inserted, it will be determined if a format operation
is needed by assessing source/target density compatibility and whether there
target disk is formatted at all.

### Erase Files
Performs files erase using standard DOS file naming conventions. Signals
destructive operation by changing background color to Red.

### Initialize Disk
Formats a disk for Single, Enhanced or Double density.

### View File / Sector / Memory
A generic 80 byte viewer for files, sectors and memory addresses.

The use is asked for the following info:
- File - File name and starting position
- Sector - Sector number in decimal
- Memory - Memory address in Hex

Once 80 bytes are displayed on screen, there are provisions to navigate
forward or backwards (only for Sector and Memory).

### Protect / Unprotect Files
Performs files protect and unprotect using standard DOS file naming
conventions

### Load / Save Binary File
Loads or saves a binary file. Load will automatically executed loaded program
if possible.
Save will save a memory range and will add a run address vector.

### Compare Files
Compares two files to figure out if they are identical or not. File names
uses standard DOS file naming conventions.

### General
The default drive can be selected using the New Drive command and all
subsequent commands default to it unless another drive is specified, either
in the full file name or a specific selection (as in Duplicate Disk command)

A generic file naming function is available for all cases where the use needs
to input a file name.
D#:filename.ext, #:filename,ext, filename.ext, file*.* or any wildcard
combination can be used.
Prefixing with the drive number can support operations outside of the
selected drive.

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
- @SETRTNA - Caches the address to return from functions that have no RTS
