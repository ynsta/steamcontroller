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

import json

def main():
    """
    Read json and write Steam vdf conversion
    """
    import sys
    import argparse
    import steamcontroller.config
    parser = argparse.ArgumentParser(prog='json2vdf', description=main.__doc__)
    parser.add_argument('-i', '--input',
                        default=sys.stdin,
                        type=argparse.FileType('r'),
                        help='input json file (stdin if not specified)')
    parser.add_argument('-o', '--output',
                        default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='output vdf file (stdout if not specified)')

    args = parser.parse_args()
    args.output.write(steamcontroller.config.json2vdf(args.input))

if __name__ == '__main__':
    main()
