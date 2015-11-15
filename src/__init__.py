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
    ('x',   'ukn_00'),
    ('x',   'ukn_01'),
    ('H',   'status'),
    ('H',   'seq'),
    ('x',   'ukn_02'),
    ('I',   'buttons'),
    ('B',   'ltrig'),
    ('B',   'rtrig'),
    ('x',   'ukn_03'),
    ('x',   'ukn_04'),
    ('x',   'ukn_05'),
    ('h',   'lpad_x'),
    ('h',   'lpad_y'),
    ('h',   'rpad_x'),
    ('h',   'rpad_y'),
    ('10x', 'ukn_06'),
    ('h',   'gpitch'),
    ('h',   'groll'),
    ('h',   'gyaw'),
    ('h',   'q1'),
    ('h',   'q2'),
    ('h',   'q3'),
    ('h',   'q4'),
    ('16x', 'ukn_07'),
]

_FORMATS, _NAMES = zip(*STEAM_CONTROLER_FORMAT)

SteamControllerInput = namedtuple('SteamController', ' '.join([x for x in _NAMES if not x.startswith('ukn_')]))

SCI_NULL = SteamControllerInput._make(struct.unpack('<' + ''.join(_FORMATS), b'\x00' * 64))

class SCStatus(IntEnum):
    Idle  = 2820
    Input = 15361
    Exit  = 259

class SCButtons(IntEnum):
    RPadTouch = 0b00010000000000000000000000000000
    LPadTouch = 0b00001000000000000000000000000000
    RPad      = 0b00000100000000000000000000000000
    LPad      = 0b00000010000000000000000000000000 # Same for stick but without LPadTouch
    RGrip     = 0b00000001000000000000000000000000
    LGrip     = 0b00000000100000000000000000000000
    Start     = 0b00000000010000000000000000000000
    Steam     = 0b00000000001000000000000000000000
    Back      = 0b00000000000100000000000000000000
    A         = 0b00000000000000001000000000000000
    X         = 0b00000000000000000100000000000000
    B         = 0b00000000000000000010000000000000
    Y         = 0b00000000000000000001000000000000
    LB        = 0b00000000000000000000100000000000
    RB        = 0b00000000000000000000010000000000
    LT        = 0b00000000000000000000001000000000
    RT        = 0b00000000000000000000000100000000


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
        self._cmsg = []
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

        # Disable Haptic auto feedback

        self._ctx.handleEvents()
        self._sendControl(struct.pack('>' + 'I' * 1,
                                      0x81000000))
        self._ctx.handleEvents()
        self._sendControl(struct.pack('>' + 'I' * 6,
                                      0x87153284,
                                      0x03180000,
                                      0x31020008,
                                      0x07000707,
                                      0x00300000,
                                      0x2f010000))
        self._ctx.handleEvents()


    def __del__(self):
        if self._handle:
            self._handle.close()

    def _sendControl(self, data, timeout=0):

        zeros = b'\x00' * (64 - len(data))

        self._handle.controlWrite(request_type=0x21,
                                  request=0x09,
                                  value=0x0300,
                                  index=0x0001,
                                  data=data + zeros,
                                  timeout=timeout)

    def addFeedback(self, name):
        if not name:
            return
        elif name[:2] == 'rp':
            self._cmsg.insert(0, struct.pack('>' + 'I' * 2, 0x8f0700ff, 0x03000001))
        elif name[:2] == 'lp':
            self._cmsg.insert(0, struct.pack('>' + 'I' * 2, 0x8f0701ff, 0x03000001))


    def _processReceivedData(self, transfer):
        """Private USB async Rx function"""

        if (transfer.getStatus() != usb1.TRANSFER_COMPLETED or
            transfer.getActualLength() != 64):
            return

        data = transfer.getBuffer()
        tup = SteamControllerInput._make(struct.unpack('<' + ''.join(_FORMATS), data))

        if isinstance(self._cb_args, (list, tuple)):
            self._cb(self, tup, *self._cb_args)
        else:
            self._cb(self, tup)

        transfer.submit()

    def run(self):
        """Fucntion to run in order to process usb events"""
        if self._handle:
            try:
                while any(x.isSubmitted() for x in self._transfer_list):
                    self._ctx.handleEvents()
                    if len(self._cmsg) > 0:
                        cmsg = self._cmsg.pop()
                        self._sendControl(cmsg)

            except usb1.USBErrorInterrupted:
                pass


    def handleEvents(self):
        """Fucntion to run in order to process usb events"""
        if self._handle and self._ctx:
            self._ctx.handleEvents()
