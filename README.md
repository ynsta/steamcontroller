# Standalone Steam Controller Driver

This project is a standalone userland driver for the steam controller to be used where the steam client can't be installed.

Two modes are already working with haptic feedback:
 - xbox360: gamepad emulator
 - desktop: mouse, keyboard mode

The final purpose is to have support for custom mapping created with a stand-alone tool or imported from steam vdf files.

The initial target is *GNU/Linux*, but I'll welcome any contributor that want to port input generation for other OS (OSX, Windows, *BSD, Android/Linux, ...)

This project is licensed under MIT.

## Installation

 1. Install dependencies
   * for python 3.4+:
     - Install python libusb1 `sudo pip install libusb1`
   * for python 2.7+ (you might have to use pip2 for python2.7 or pip3 for python3):
     - Install python libusb1 `sudo pip install libusb1`
     - Install python enum backport `sudo pip install enum34`

 2. Get the project [tarbal](https://github.com/ynsta/steamcontroller/archive/master.tar.gz) or clone it from github:
 
# Get from tarbal:

 1. `wget https://github.com/ynsta/steamcontroller/archive/master.tar.gz`
 2. `tar xf master.tar.gz`
 3. `cd steamcontroller-master`
 
 
# or clone it:
 1. `git clone https://github.com/ynsta/steamcontroller.git`
 2. `cd steamcontroller`
 3. Install python modules and scripts with `sudo python setup.py install`
 4. Install udev rules (if not already done for steam) in `/etc/udev/rules.d/99-steam-controller.rules`:
 ```shell
 # replace game group by a valid group on your system
 # Steam controller keyboard/mouse mode
 SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", GROUP="games", MODE="0660"

 # Steam controller gamepad mode
 KERNEL=="uinput", MODE="0660", GROUP="games", OPTIONS+="static_node=uinput"
 ```

 5. Reload udev `sudo udevadm control --reload`

## Usage

 1. Exit Steam.
 2. Start:
   * `sc-xbox.py start` for the simple xbox360 emulator.
   * `sc-desktop.py start` for the desktop keyboard/mouse mode.
 3. Stop: `sc-xbox.py stop` or `sc-desktop.py stop`

Other test tools are installed:
 - `sc-dump.py` : Dump raw message from the controller.
 - `sc-gyro-plot.py` : Plot curves from gyro data (require pyqtgraph and pyside installed).
 - `sc-test-cmsg.py` : Permit to send control message to the contoller. For example:
   `echo 8f07005e 015e01f4 01000000 | sc-test-cmsg.py` will make the controller beep.
 - `vdf2json.py` : Convert Steam VDF file to JSON.
 - `json2vdf.py` : Convert back JSON to VDF file.


## TODO / Status

 1. Finish to guess each bytes/bits roles in the usb message (**Done**).
 2. Understand how to configure haptic feed backs (**Done**).
 3. Understand how to enable gyroscopes (**Done**).
 4. Redirect inputs to userland events via uinput (**Done**).
    - Xbox360 uintput device (**Done**)
    - Keyboard uintput device (**Done**)
    - Mouse uintput device with trackball model (**Done**)
 5. Create a simple xbox event mapper (**Done**)
 6. Create a configurable event mapper (**Paused**):
   - Create an event mapper that reads steam vdf files and maps usb inputs to uinput events.
   - Create fallback mappings for unsupported config options.
   - Get all possible configurations of steam config file.
 7. Create a haptic feedback Manager (**Paused**)
 8. Measure latencies.
 9. Support multiple controller in wireless mode (**Done**)
 10. Support multiple controller in wired mode
 11. Support correct deconnexion of controllers (with 2sec press on steam button) (**Done**)
 12. Add support to control light intensity
 13. Add support for gyroscopes in the event mapper:
     - Enable gyro condition (always on, or on specific button event)
     - Use gyro as mouse (add yaw, pitch, roll accell to mouse event with a scale factor).
     - Use gyro as an axis (compute yawn, pitch or roll from quaternion, normalize to -32768 32768 and use it as an axe)
 14. Optimize event mapper.
 15. Verify if pairing between a controller and a dongle is possible without steam or add a tools to do it.
 16. Add support to change "music" for power on off.
 17. Create an tool to convert musical notes, to haptic messages.

## Control Messages Capture

 1. `sudo modprobe usbmon`
 2. `lsusb -d 28de:1142` and look at bus and device numbers (B & D)
 3. `sudo cat /sys/kernel/debug/usb/usbmon/Bu | grep Co:B:D:0` (B=3 and D=003 for example)

### Disable auto feedback on rpad:

 - `81000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000`

### Enable Gyro

 - `87153284 03180000 31020008 07000707 00301400 2f010000 00000000 00000000`

### Disable Gyro

 - `87153284 03180000 31020008 07000707 00300000 2f010000 00000000 00000000`

### Stop Controller
 - `9f046f66 66210000 ...`


## Control Messages formats

### Haptic feedback format:

 - u8  : `8f`
 - u8  : `07`
 - u8  : `00` for Right `01` for Left
 - u16 : Amplitude
 - u16 : Period
 - u16 : count
 - pads the end with `00`
