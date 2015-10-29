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

"""Steam Controller XBOX360 Gamepad Emulator"""

import sys
from steamcontroller import \
    SteamController, \
    SteamControllerInput, \
    SCStatus, \
    SCButtons
import steamcontroller.uinput
from steamcontroller.uinput import Keys
from steamcontroller.uinput import Axes
from steamcontroller.daemon import Daemon

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

    rmv = prev_buttons ^ btn

    events = []

    if btn & SCButtons.LPadTouch != SCButtons.LPadTouch:
        events.append((evstick, x if not invert else -x))

    if (clicked and (btn & (SCButtons.LPad | SCButtons.LPadTouch)) == (SCButtons.LPad | SCButtons.LPadTouch) or
        not clicked and (btn & SCButtons.LPadTouch == SCButtons.LPadTouch)):

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
        events.append((evtouch, x if not invert else -x))

    if ((clicked and rmv & SCButtons.LPad == SCButtons.LPad) or
        (not clicked and rmv & SCButtons.LPadTouch == SCButtons.LPadTouch)):
        events.append((evtouch, 0))


    return events

axis_map = {
    'ltrig'  : lambda x, btn: [(Axes.ABS_Z,  int(-32767 + ((x*2.0*32767.0)/255.)))],
    'rtrig'  : lambda x, btn: [(Axes.ABS_RZ, int(-32767 + ((x*2.0*32767.0)/255.)))],
    'lpad_x' : lambda x, btn: lpad_func(x, btn, 15000, Axes.ABS_X, Axes.ABS_HAT0X, True, False),
    'lpad_y' : lambda x, btn: lpad_func(x, btn, 15000, Axes.ABS_Y, Axes.ABS_HAT0Y, True, True),
    'rpad_x' : lambda x, btn: [(Axes.ABS_RX, x)],
    'rpad_y' : lambda x, btn: [(Axes.ABS_RY, -x)],
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
        for ev, val in func(sci._asdict()[name], sci.buttons):
            if ev != None:
                xb.axisEvent(ev, val)

    xb.synEvent()
    prev_buttons = sci.buttons


class SCDaemon(Daemon):
    def run(self):
        while True:
            try:
                xb = steamcontroller.uinput.Xbox360()
                sc = SteamController(callback=scInput2Uinput, callback_args=[xb, ])
                sc.run()
            except KeyboardInterrupt:
                return
            except:
                pass

if __name__ == '__main__':
    import argparse

    def _main():
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('command', type=str, choices=['start', 'stop', 'restart', 'debug'])
        args = parser.parse_args()
        daemon = SCDaemon('/tmp/steamcontroller.pid')

        if 'start' == args.command:
            daemon.start()
        elif 'stop' == args.command:
            daemon.stop()
        elif 'restart' == args.command:
            daemon.restart()
        elif 'debug' == args.command:
            daemon.run()

    _main()
