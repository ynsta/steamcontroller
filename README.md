# Standalone Steam Controller Portable Driver

This project is a standalone userland driver for the steam controller to be used
where steam client can't be installed.

The Initial target is GNU/Linux if some developpers are insterred to add support
for Windows any contribution is welcomed.

For the moment only an xbox360 emulator is working without haptic feedback control.

This project is licenced under MIT Licence.

## Installation

 1. Get code on github `git clone https://github.com/ynsta/steamcontroller.git`
 2. for python 2.7+ (you might have to use pip2 for python2.7 or pip3 for python3):
   - Install python libusb1 `sudo pip install libusb1`
   - Install python enum backport `sudo pip install enum34`
 3. for python 3.4+
   - Install python libusb1 `sudo pip install libusb1`
 4. sudo python setup.py install
 5. Install udev rules (if not already done for steam) in `/etc/udev/rules.d/99-steam-controller.rules`:
    ```
# replace game group by a valid group on your system
# Steam controller keyboard/mouse mode
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", GROUP="games", MODE="0660"

# Steam controller gamepad mode
KERNEL=="uinput", MODE="0660", GROUP="games", OPTIONS+="static_node=uinput"
```
 6. Reload udev `sudo udevadm control --reload`


## Usage

 1. Exit Steam.
 2. run `sc-xbox.py start` for the simple xbox360 emulator or run `sc-dump.py` for the dumper

## TODO

 1. Finish to guess each bytes/bits roles in the usb message (*Done*).
 2. Understand how to configure haptic feed backs (*Not Started*).
 3. Understand how to enable gyroscopes (*Not Started*).
 4. Redirect inputs to userland events via uinput (*Done*).
 5. Create a simple xbox event mapper (*Done* but to be improved).
 6. Create a configurable event mapper:
   - Create an event mapper that reads steam vdf files and maps usb inputs to uinput events.
   - Create fallback mappings for unsupported config options.
   - Get all possible configurations of steam config file.
