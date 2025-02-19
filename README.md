# kbsplitter
A graphical tool to map keyboard keys to Xbox controller inputs, inspired by [kb2xbox](https://github.com/mPyKen/kb2xbox).

## Description
This application provides a user-friendly interface to map keyboard inputs to Xbox controller outputs. It's particularly useful for:
- Playing games that only support controllers using your keyboard
- Setting up local co-op games using multiple keyboards
- Creating custom keyboard mappings for different games

## Features
- Graphical user interface for easy configuration
- Multiple configuration support
- Real-time controller mapping
- Visual key mapping display
- Support for multiple keyboards
- Network keyboard support

## Requirements
- Linux (Tested on Arch Linux)
- Python 3.6+
- GTK 3
- python-libevdev
- python-gobject

## Installation

### Arch Linux (and derivatives)

# kbsplitter
Convert a keyboard to (multiple) gamepads.

## Description
Usually, a second or third keyboard is treated the same way as the first keyboard.
kbsplitter allows you to emulate as many XBox Controllers as you like with your keyboards.
This is useful when you want to play local co-op games (aka couch games) with multiple players.

# Requirements
- Linux
- [python-libevdev](https://python-libevdev.readthedocs.io/en/latest/)

# Run
Check your available keyboards with `kbsplitter.py --list`

Make sure /dev/uinput is writable `sudo chmod 666 /dev/uinput`

## Syntax
`python kbsplitter.py -d KEYBOARD_DEVICE CONFIGS`

### Example
`python kbsplitter.py -d /dev/input/event<KeyboardEventID> config/xbox.cfg config/xbox2.cfg`

This lets you emulate 2 XBox Controllers:
- Arrow keys for the analogue stick (Controller 1)
- Right Alt, HENKAN and KATAKANAHIRAGANA keys for additional buttons (Controller 1)
- E,S,D,F keys for the analogue stick (Controller 2)
- Left Shift, Caps Lock and Tab keys for additional buttons (Controller 2)

## Keyboard over the Network
To connect a built-in keyboard from e.g. notebooks and turn them into Gamepads, use: (taken from [here](https://superuser.com/questions/67659/linux-share-keyboard-over-network))
- keyboard receiver:  
`nc -l -p 4444 > /dev/input/by-path/platform-i8042-serio-0-event-kbd`
- keyboard sender:  
`cat /dev/input/by-path/platform-i8042-serio-0-event-kbd | nc <IP> 4444`
