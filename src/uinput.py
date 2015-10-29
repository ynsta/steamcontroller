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

        self._keys = set(keys)
        self._axes = set(axes)

        lib = os.path.abspath(
            os.path.normpath(
                os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'libuinput' + get_config_var('SO'))))
        self._lib = ctypes.CDLL(lib)

        _k = (ctypes.c_int * len(keys))(*keys)
        _a = (ctypes.c_int * len(axes))(*axes)
        _name = ctypes.c_char_p(name)
        self._fd = self._lib.uinput_init(ctypes.c_int(len(keys)), _k,
                                         ctypes.c_int(len(axes)), _a,
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
                                      name=b"Microsoft Corp. Xbox360 Controller",
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
                                      axes=[Axes.ABS_X,
                                            Axes.ABS_Y,
                                            Axes.ABS_RX,
                                            Axes.ABS_RY,
                                            Axes.ABS_Z,
                                            Axes.ABS_RZ,
                                            Axes.ABS_HAT0X,
                                            Axes.ABS_HAT0Y])
