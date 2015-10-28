# Standalone Steam Controller Portable Driver

For the moment it only dumps the usb message with some decoded fields.

I plan to make it work on platform where steam is not working (ARM linux boards for example).

## Usage

 * Get code on github
 * Install python libusb1 `sudo pip2 install libusb1`
 * Close Steam
 * python dump.py

## TODO

 - finish to guess each bytes/bits roles in the usb message (almost finished),
 - understand how to configure haptic feed backs,
 - understand how to enable gyroscopes,
 - redirect inputs to userland events via uinput using a mapping file.
