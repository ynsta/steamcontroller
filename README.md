# Standalone Steam Controller Portable Driver

For the moment it only dumps the usb message with some decoded fields.

I plan to make it work on platform where steam is not working (ARM linux boards for example).

## Usage

 * Get code on github
 * Install python libusb1 `sudo pip2 install libusb1`
 * Close Steam
 * python dump.py

## TODO

 1. Finish to guess each bytes/bits roles in the usb message (almost finished),
 2. Understand how to configure haptic feed backs,
 3. Understand how to enable gyroscopes,
 4. Redirect inputs to userland events via uinput:
   * Create a C library that permit to create, a uinput device and send events 
     (python-uinput might be a candidate but I prefer to stick to MIT/BSD projects)
   * Create a python binding to this library.
 5. Create a simple xbox event mapper.
 6. Create a configurable event mapper:
   * Create an event mapper that reads steam vdf files and maps usb inputs to uinput events.
   * Create fallback mappings for unsupported config options.
   * Get all possible configurations of steam config file.
