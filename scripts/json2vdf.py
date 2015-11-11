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

def json2vdf(stream):

    """
    Read a json file and return a string in Steam vdf format
    """

    def _istr(ident, string):
        return (ident * '\t') + string

    data = json.loads(stream.read(), object_pairs_hook=list)

    def _json2vdf(data, indent):
        out = ''
        for k, val in data:
            if isinstance(val, list):
                if indent:
                    out += '\n'
                out += _istr(indent, '"{}"\n'.format(k))
                out += _istr(indent, '{\n')
                out += _json2vdf(val, indent + 1)
                out += _istr(indent, '}\n')
            else:
                out += _istr(indent, '"{}" "{}"\n'.format(k, val))
        return out

    return  _json2vdf(data, 0)


def main():
    """
    Read json and write Steam vdf conversion
    """
    import sys
    import argparse
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
    args.output.write(json2vdf(args.input))

if __name__ == '__main__':
    main()
