# EDOS
E-DOS is a refreshed Disk Utility Package (DUP) that sits on
top of a regular DOS, such as MyDOS or SpartaDOS to provide a
menu based disk operations in a friendly user interface.

I have created this softare to provide me withthe best disk
management experience that is simple yet full of missing
functions classical interfaces do not have, such as sector
copier, memory dump and more.

## The story behind the project
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

The default drive can be selected using the New Drive command drive is specified, either in the full filename or a specific
selection (as in Duplicate Disk command)

## File Structure
The project contains several files, eachone focuses on
different parts and with extensiblity in mind.

Here is a rundown of the contained files and their purpose:

- EDOS.M65 - The main application codebase
- EDOSVARS.M65 - Main application variables and string constants
- UTILS.M65 - A set of general purpose utilities that can be used in other projects
- MACROS.M65 - A set of general purpose Mac/65 macros to simplify development
- SYSTEM.M65 - System wide constants and defaults
