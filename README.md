# Standalone Steam Controller Driver

This project is a standalone userland driver for the steam controller to be used where steam client can't be installed.

Two modes are already working with haptic feedback:
 - xbox360: gamepad emulator
 - desktop: mouse, keyboard mode

The final purpose is to have support for custom mapping created with a stand-alone tool or imported from steam vdf files.

The initial target is *GNU/Linux*, but I'll welcome any contributor that want to port input generation for other OS (OSX, Windows, *BSD, Android/Linux, ...)

This project is licensed under MIT.

## Installation

 1. Get code on github `git clone https://github.com/ynsta/steamcontroller.git`
`2. for python 3.4+
   - Install python libusb1 `sudo pip install libusb1`
 3. for python 2.7+ (you might have to use pip2 for python2.7 or pip3 for python3):
   - Install python libusb1 `sudo pip install libusb1`
   - Install python enum backport `sudo pip install enum34
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
 2. run `sc-xbox.py start` for the simple xbox360 emulator
 3. run `sc-xbox.py stop` to stop the driver

Replace `xbox` by `desktop` for the desktop keyboard/mouse mode.

Other test tools are installed:
 - `sc-dump.py` : Dump raw message from the controller.
 - `sc-gyro-plot.py` : Plot curves from gyro data (require pyqtgraph and pyside installed).
 - `sc-test-cmsg.py` : Permit to send control message to the contoller. For example `echo 8f07005e 015e01f4 01000000 | sc-test-cmsg.py` will make the controller beep.
 - `vdf2json.py` : Convert Steam VDF file to JSON.
 - `json2vdf.py` : Convert back JSON to VDF file.


## TODO / Status

 1. Finish to guess each bytes/bits roles in the usb message (Mostly *Done*).
    - Verify that Gyroscope data 4 to 7 are a quaternion as suspected
 2. Understand how to configure haptic feed backs (*Done*).
 3. Understand how to enable gyroscopes (*Done*).
 4. Redirect inputs to userland events via uinput (*Done*).
    - Xbox360 uintput device (*Done*)
    - Keyboard uintput device (*Done*)
    - Mouse uintput device with trackball model (*Done*)
 5. Create a simple xbox event mapper (*Done*)
 6. Create a configurable event mapper (Work in Progress):
   - Create an event mapper that reads steam vdf files and maps usb inputs to uinput events.
   - Create fallback mappings for unsupported config options.
   - Get all possible configurations of steam config file.
 7. Create a haptic feedback Manager (TBD)
 8. Measure latencies.

## Control Message Capture

 1. `sudo modprobe usbmon`
 2. `lsusb -d 28de:1142` and look at bus and device numbers (B & D)
 3. `sudo cat /sys/kernel/debug/usb/usbmon/Bu | grep Co:B:D:0` B=3 and D=003 on my setup.

### Disable auto feedback on rpad:

 - `81000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000`

### Enable Gyro

 - `87153284 03180000 31020008 07000707 00301400 2f010000 00000000 00000000`

### Disable Gyro

 - `87153284 03180000 31020008 07000707 00300000 2f010000 00000000 00000000`

### Haptic feedback format:

 - u8  : `8f`
 - u8  : `07`
 - u8  : `00` for Right `01` for Left
 - u16 : Amplitude
 - u16 : Period
 - u16 : count
 - pads the end with `00`
