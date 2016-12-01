#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2015 Paul Wachendorf <paul.wachendorf@web.de>
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

"""Steam Controller Callback Mode example"""
import sys

from steamcontroller import SteamController, SCButtons
from steamcontroller.events import EventMapper, Pos
from steamcontroller.uinput import Keys


def button_pressed_callback(evm, btn, pressed):
    print "Button {} was {}.".format(btn, 'pressed' if pressed else 'released')

    if btn == SCButtons.STEAM and not pressed:
        print "pressing the STEAM button terminates the programm"
        sys.exit()

def touchpad_click_callback(evm, pad, pressed):
    print "Tochpad {} was {}".format(pad, 'pressed' if pressed else 'released')

def touchpad_touch_callback(evm, pad, x, y):
    print "Tochpad {} was touched @{},{}".format(pad, x, y)

def stick_pressed_callback(evm):
    print "Stick pressed"

def stick_axes_callback(evm, x, y):
    print "Stick Position is {}, {}".format(x, y)

def tigger_axes_callback(evm, pos, value):
    print "Trigger axes {} has value {}".format(pos, value)

def evminit():
    evm = EventMapper()
    evm.setButtonCallback(SCButtons.STEAM, button_pressed_callback)
    evm.setButtonCallback(SCButtons.A, button_pressed_callback)
    evm.setButtonCallback(SCButtons.B, button_pressed_callback)
    evm.setButtonCallback(SCButtons.X, button_pressed_callback)
    evm.setButtonCallback(SCButtons.Y, button_pressed_callback)
    evm.setButtonCallback(SCButtons.LB, button_pressed_callback)
    evm.setButtonCallback(SCButtons.RB, button_pressed_callback)
    evm.setButtonCallback(SCButtons.LT, button_pressed_callback)
    evm.setButtonCallback(SCButtons.RT, button_pressed_callback)
    evm.setButtonCallback(SCButtons.LGRIP, button_pressed_callback)
    evm.setButtonCallback(SCButtons.RGRIP, button_pressed_callback)
    evm.setButtonCallback(SCButtons.START, button_pressed_callback)
    evm.setButtonCallback(SCButtons.BACK, button_pressed_callback)
    evm.setPadButtonCallback(Pos.LEFT, touchpad_touch_callback)
    evm.setPadButtonCallback(Pos.RIGHT, touchpad_click_callback, clicked=True)
    evm.setStickAxesCallback(stick_axes_callback)
    evm.setStickPressedCallback(stick_pressed_callback)
    evm.setTrigAxesCallback(Pos.RIGHT, tigger_axes_callback)
    evm.setTrigAxesCallback(Pos.LEFT, tigger_axes_callback)
    return evm


if __name__ == '__main__':
    evm = evminit()
    sc = SteamController(callback=evm.process)
    sc.run()


