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

from steamcontroller import \
    SteamController, \
    SCButtons
from steamcontroller.events import \
    EventMapper, \
    Pos
from steamcontroller.uinput import \
    Keys, \
    Axes
from steamcontroller.daemon import Daemon

import gc

def evminit():
    evm = EventMapper()

    evm.setStickAxes(Axes.ABS_X, Axes.ABS_Y)
    evm.setPadAxes(Pos.RIGHT, Axes.ABS_RX, Axes.ABS_RY)
    evm.setPadAxesAsButtons(Pos.LEFT, [Axes.ABS_HAT0X,
                                       Axes.ABS_HAT0Y])

    evm.setTrigAxis(Pos.LEFT, Axes.ABS_Z)
    evm.setTrigAxis(Pos.RIGHT, Axes.ABS_RZ)

    evm.setButtonAction(SCButtons.A, Keys.BTN_A)
    evm.setButtonAction(SCButtons.B, Keys.BTN_B)
    evm.setButtonAction(SCButtons.X, Keys.BTN_X)
    evm.setButtonAction(SCButtons.Y, Keys.BTN_Y)
    evm.setButtonAction(SCButtons.LB, Keys.BTN_TL)
    evm.setButtonAction(SCButtons.RB, Keys.BTN_TR)
    evm.setButtonAction(SCButtons.BACK, Keys.BTN_SELECT)
    evm.setButtonAction(SCButtons.START, Keys.BTN_START)
    evm.setButtonAction(SCButtons.STEAM, Keys.BTN_MODE)
    evm.setButtonAction(SCButtons.LPAD, Keys.BTN_THUMBL)
    evm.setButtonAction(SCButtons.RPAD, Keys.BTN_THUMBR)
    evm.setButtonAction(SCButtons.LGRIP, Keys.BTN_A)
    evm.setButtonAction(SCButtons.RGRIP, Keys.BTN_B)

    return evm

class SCDaemon(Daemon):
    def run(self):
        evm = evminit()
        sc = SteamController(callback=evm.process)
        sc.run()
        del sc
        del evm
        gc.collect()

if __name__ == '__main__':
    import argparse

    def _main():
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('command', type=str, choices=['start', 'stop', 'restart', 'debug'])
        parser.add_argument('-i', '--index', type=int, choices=[0,1,2,3], default=None)
        args = parser.parse_args()
        if args.index != None:
            daemon = SCDaemon('/tmp/steamcontroller{:d}.pid'.format(args.index))
        else:
            daemon = SCDaemon('/tmp/steamcontroller.pid')

        if 'start' == args.command:
            daemon.start()
        elif 'stop' == args.command:
            daemon.stop()
        elif 'restart' == args.command:
            daemon.restart()
        elif 'debug' == args.command:
            try:
                evm = evminit()
                sc = SteamController(callback=evm.process)
                sc.run()

            except KeyboardInterrupt:
                pass

    _main()
