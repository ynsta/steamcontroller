#!/usr/bin/env python

import time
from steamcontroller.uinput import Keys, Keyboard

k = Keyboard()

press = True
try:
    while True:
        input()

        if press:
            k.pressEvent([Keys.KEY_Q])
        else:
            k.releaseEvent()

        press = not press

except KeyboardInterrupt:
    pass
