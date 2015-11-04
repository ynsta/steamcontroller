#!/usr/bin/env python

# The MIT License (MIT)
#
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

import os
import ctypes
from enum import IntEnum
from steamcontroller.cheader import defines

from distutils.sysconfig import get_config_var

_def = defines('/usr/include', 'linux/uinput.h')

# Keys enum contains all keys and button from linux/uinput.h (KEY_* BTN_*)
Keys = IntEnum('Keys', { i: _def[i] for i in _def.keys() if (i.startswith('KEY_') or
                                                             i.startswith('BTN_')) })

# Axes enum contains all axes from linux/uinput.h (ABS_*)
Axes = IntEnum('Axes', { i: _def[i] for i in _def.keys() if (i.startswith('ABS_')) })

class UInput(object):

    def __init__(self, vendor, product, name, keys, axes):

        self._k = keys
        self._a, self._amin, self._amax, self._afuzz, self._aflat = zip(*axes)

        lib = os.path.abspath(
            os.path.normpath(
                os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'libuinput' + get_config_var('SO'))))
        self._lib = ctypes.CDLL(lib)

        ck = (ctypes.c_int * len(self._k))(*self._k)
        ca     = (ctypes.c_int * len(self._a))(*self._a)
        camin  = (ctypes.c_int * len(self._amin ))(*self._amin )
        camax  = (ctypes.c_int * len(self._amax ))(*self._amax )
        cafuzz = (ctypes.c_int * len(self._afuzz))(*self._afuzz)
        caflat = (ctypes.c_int * len(self._aflat))(*self._aflat)

        _name = ctypes.c_char_p(name)
        self._fd = self._lib.uinput_init(ctypes.c_int(len(self._k)), ck,
                                         ctypes.c_int(len(self._a)), ca,
                                         camin,
                                         camax,
                                         cafuzz,
                                         caflat,
                                         ctypes.c_int(vendor),
                                         ctypes.c_int(product),
                                         _name)

    def keyEvent(self, key, val):
        self._lib.uinput_key(self._fd,
                             ctypes.c_int(key),
                             ctypes.c_int(val))


    def axisEvent(self, axis, val):
        self._lib.uinput_abs(self._fd,
                             ctypes.c_int(axis),
                             ctypes.c_int(val))

    def synEvent(self):
        self._lib.uinput_syn(self._fd)

    def __del__(self):
        self._lib.uinput_destroy(self._fd)


class Xbox360(UInput):

    def __init__(self):
        super(Xbox360, self).__init__(vendor=0x045e,
                                      product=0x028e,
                                      name=b"Microsoft X-Box 360 pad",
                                      keys=[Keys.BTN_START,
                                            Keys.BTN_MODE,
                                            Keys.BTN_SELECT,
                                            Keys.BTN_A,
                                            Keys.BTN_B,
                                            Keys.BTN_X,
                                            Keys.BTN_Y,
                                            Keys.BTN_TL,
                                            Keys.BTN_TR,
                                            Keys.BTN_THUMBL,
                                            Keys.BTN_THUMBR],
                                      axes=[(Axes.ABS_X, -32768, 32767, 16, 128),
                                            (Axes.ABS_Y, -32768, 32767, 16, 128),
                                            (Axes.ABS_RX, -32768, 32767, 16, 128),
                                            (Axes.ABS_RY, -32768, 32767, 16, 128),
                                            (Axes.ABS_Z, 0, 255, 0, 0),
                                            (Axes.ABS_RZ, 0, 255, 0, 0),
                                            (Axes.ABS_HAT0X, -1, 1, 0, 0),
                                            (Axes.ABS_HAT0Y, -1, 1, 0, 0)])
