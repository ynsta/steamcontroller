# Copyright (c) 2015 Stany MARCEL <stanypub@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import usb1
from collections import namedtuple
import struct
from enum import IntEnum

VENDOR_ID  = 0x28de
PRODUCT_ID = 0x1142
ENDPOINT   = 2

STEAM_CONTROLER_FORMAT = [
    ('B',   'ukn_00'),
    ('B',   'ukn_01'),
    ('H',   'status'),
    ('H',   'seq'),
    ('B',   'ukn_02'),
    ('I',   'buttons'),
    ('B',   'ltrig'),
    ('B',   'rtrig'),
    ('B',   'ukn_03'),
    ('B',   'ukn_04'),
    ('B',   'ukn_05'),
    ('h',   'lpad_x'),
    ('h',   'lpad_y'),
    ('h',   'rpad_x'),
    ('h',   'rpad_y'),
    ('40p', 'ukn_06'),
]

_FORMATS, _NAMES = zip(*STEAM_CONTROLER_FORMAT)

SteamControllerInput = namedtuple('SteamController', ' '.join(_NAMES))


class SCStatus(IntEnum):
    Idle = 2820
    Input = 15361
    Exit = 259

class SCButtons(IntEnum):
    A = 32768
    B = 8192
    X = 16384
    Y = 4096
    Back = 1048576
    Start = 4194304
    Steam = 2097152
    LGrip = 8388608
    RGrip = 16777216
    LPadTouch = 134217728
    RPadTouch = 268435456
    LPad = 33554432
    RPad = 67108864
    Stick = 33554432
    LB = 2048
    RB = 1024
    LT = 5012
    RT = 256


class SteamController(object):

    def __init__(self, callback, callback_args=None):
        """
        Constructor

        callback: function called on usb message must take at lead a
        SteamControllerInput as first argument

        callback_args: Optional arguments passed to the callback afer the
        SteamControllerInput argument
        """
        self._handle = None
        self._cb = callback
        self._cb_args = callback_args

        self._ctx = usb1.USBContext()
        self._handle = self._ctx.openByVendorIDAndProductID(
            VENDOR_ID, PRODUCT_ID,
            skip_on_error=True,
        )

        if self._handle is None:
            raise ValueError('SteamControler Device not found')

        dev = self._handle.getDevice()
        cfg = dev[0]

        for inter in cfg:
            for setting in inter:
                number = setting.getNumber()
                if self._handle.kernelDriverActive(number):
                    self._handle.detachKernelDriver(number)
                if (setting.getClass() == 3 and
                    setting.getSubClass() == 0 and
                    setting.getProtocol() == 0):
                    self._handle.claimInterface(number)

        self._transfer_list = []
        transfer = self._handle.getTransfer()
        transfer.setInterrupt(
            usb1.ENDPOINT_IN | ENDPOINT,
            64,
            callback=self._processReceivedData,
        )
        transfer.submit()
        self._transfer_list.append(transfer)


    def __del__(self):
        if self._handle:
            self._handle.close()


    def _processReceivedData(self, transfer):
        """Private USB async Rx function"""

        if transfer.getStatus() != usb1.TRANSFER_COMPLETED or transfer.getActualLength() != 64:
            return

        data = transfer.getBuffer()
        tup = SteamControllerInput._make(struct.unpack('<' + ''.join(_FORMATS), data))

        if isinstance(self._cb_args, (list, tuple)):
            self._cb(tup, *self._cb_args)
        else:
            self._cb(tup)

        transfer.submit()

    def run(self):
        """Fucntion to run in order to process usb events"""
        if self._handle:
            try:
                while any(x.isSubmitted() for x in self._transfer_list):
                    self._ctx.handleEvents()
            except usb1.USBErrorInterrupted:
                pass
