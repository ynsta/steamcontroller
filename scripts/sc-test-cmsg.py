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

"""Steam Controller USB Dumper"""

import sys
import struct
import time
from steamcontroller import SteamController

def dump(sc, sci):
    print(sci)

def _main():

    try:
        sc = SteamController(callback=dump)
        sc.handleEvents()
        sc._sendControl(struct.pack('>' + 'I' * 1, 0x81000000))
        sc._sendControl(struct.pack('>' + 'I' * 6, 0x87153284, 0x03180000, 0x31020008, 0x07000707, 0x00301400, 0x2f010000))

        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xad020000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xad020000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xa1000000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xad020000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0x8e000000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0x85000000))

        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xa1000000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xb4000000))
        #sc._sendControl(struct.pack('>' + 'I' * 5, 0x9610730b, 0xc7191248, 0x074eff14, 0x464e82d6, 0xaa960000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xa1000000))
        #sc._sendControl(struct.pack('>' + 'I' * 5, 0x9610e0b5, 0xda3a1e90, 0x5b325088, 0x0a6224d2, 0x67690000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xa1000000))
        #sc._sendControl(struct.pack('>' + 'I' * 5, 0x96107ef6, 0x0e193e8c, 0xe61d2eda, 0xb80906eb, 0x9fe90000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0xa1000000))
        #sc._sendControl(struct.pack('>' + 'I' * 5, 0x96106e4a, 0xa4753ef0, 0x017ab50a, 0x24390f1f, 0x71fa0000))
        #sc._sendControl(struct.pack('>' + 'I' * 1, 0x83000000))

       #sc._sendControl(struct.pack('>' + 'I' * 6, 0xae150100, 0x00000001, 0x02110000, 0x02030000, 0x000a6d92, 0xd2550400))
        sc.run()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(str(e) + '\n')

    print("Bye")


if __name__ == '__main__':
    _main()
