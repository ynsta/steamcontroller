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

"""Steam Controller XBOX Driver"""

import sys
from steamcontroller import \
    SteamController, \
    SteamControllerInput, \
    SCStatus, \
    SCButtons
import steamcontroller.uinput
from steamcontroller.uinput import Keys
from steamcontroller.uinput import Axes

prev_buttons = 0

button_map = {
    SCButtons.A      : Keys.BTN_A,
    SCButtons.B      : Keys.BTN_B,
    SCButtons.X      : Keys.BTN_X,
    SCButtons.Y      : Keys.BTN_Y,
    SCButtons.Back   : Keys.BTN_BACK,
    SCButtons.Start  : Keys.BTN_START,
    SCButtons.Steam  : Keys.BTN_MODE,
    SCButtons.LB     : Keys.BTN_TL,
    SCButtons.RB     : Keys.BTN_TR,
    SCButtons.Stick  : Keys.BTN_THUMBL,
    SCButtons.RPad   : Keys.BTN_THUMBR,
    SCButtons.LGrip  : Keys.BTN_A,
    SCButtons.RGrip  : Keys.BTN_B,
}


def lpad_func(x, btn, threshold, evstick, evtouch, clicked, invert):
    global prev_buttons

    removed = prev_buttons ^ btn

    if btn & SCButtons.LPadTouch != SCButtons.LPadTouch:
        return (evstick, x if not invert else -x)

    if btn & (SCButtons.LPad if clicked else SCButtons.LPadTouch):
        if x >= 0:
            if x >= threshold:
                x = 32767
            else:
                x = 0
        else:
            if x <= -threshold:
                x = -32767
            else:
                x = 0
        return (evtouch, x if not invert else -x)

    if removed & SCButtons.LPadTouch != SCButtons.LPadTouch:
        return (evstick,  0)

    if removed & (SCButtons.LPad if clicked else SCButtons.LPadTouch):
        return (evtouch, 0)

    return (None, None)

axis_map = {
    'ltrig'  : lambda x, btn: (Axes.ABS_Z,  int(-32767 + ((x*2.0*32767.0)/255.))),
    'rtrig'  : lambda x, btn: (Axes.ABS_RZ, int(-32767 + ((x*2.0*32767.0)/255.))),
    'lpad_x' : lambda x, btn: lpad_func(x, btn, 16384, Axes.ABS_X, Axes.ABS_HAT0X, True, False),
    'lpad_y' : lambda x, btn: lpad_func(x, btn, 16384, Axes.ABS_Y, Axes.ABS_HAT0Y, True, True),
    'rpad_x' : lambda x, btn: (Axes.ABS_RX, x),
    'rpad_y' : lambda x, btn: (Axes.ABS_RY, -x),
}


def scInput2Uinput(sci, xb):

    global prev_buttons

    if sci.status != SCStatus.Input:
        return

    removed = prev_buttons ^ sci.buttons

    for btn, ev in button_map.items():

        if btn == SCButtons.Stick and sci.buttons & SCButtons.LPadTouch:
            xb.keyEvent(ev, 0)
            continue

        if sci.buttons & btn:
            xb.keyEvent(ev, 1)
        if removed & btn:
            xb.keyEvent(ev, 0)

    for name, func in axis_map.items():
        ev, val = func(sci._asdict()[name], sci.buttons)
        if ev != None:
            xb.axisEvent(ev, val)

    xb.synEvent()
    prev_buttons = sci.buttons

def _main():


    try:
        xb = steamcontroller.uinput.Xbox360()
        sc = SteamController(callback=scInput2Uinput, callback_args=[xb, ])
        sc.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(str(e) + '\n')

    print("Bye")


if __name__ == '__main__':
    _main()
