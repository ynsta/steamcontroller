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
from shlex import shlex

def join_duplicate_keys(ordered_pairs): # {{{
	d = {}
	for k, v in ordered_pairs:
		if k in d:
			if(type(d[k]) == list):
				d[k].append(v)
			else:
				newlist = []
				newlist.append(d[k])
				newlist.append(v)
				d[k] = newlist
		else:
			d[k] = v
	return d
# }}}

def vdf2json(stream):

    """
    Read a Steam vdf file and return a string in json format
    """

    def _istr(ident, string):
        return (ident * '  ') + string

    jbuf = '{\n'
    lex = shlex(stream)
    indent = 1

    while True:
        tok = lex.get_token()
        if not tok:
            return jbuf + '}\n'
        if tok == '}':
            indent -= 1
            jbuf += _istr(indent, '}')
            ntok = lex.get_token()
            lex.push_token(ntok)
            if ntok and ntok != '}':
                jbuf += ','
            jbuf += '\n'
        else:
            ntok = lex.get_token()
            if ntok == '{':
                jbuf += _istr(indent, tok + ': {\n')
                indent += 1
            else:
                jbuf += _istr(indent, tok + ': ' + ntok)
                ntok = lex.get_token()
                lex.push_token(ntok)
                if ntok != '}':
                    jbuf += ','
                jbuf += '\n'

def vdf2sensible_json(stream):
	# Since /controller_mappings/group is a key duplicated numerous times, it
	#    makes it cumbersome to use.  This changes /controller_mappings/group
	#    to be a single-use key with a dict in it; each object in the dict is a
	#    one of these separate "group" objects, and the keys to the dict are
	#    the "id" fields of these objects.

	obj = json.loads(vdf2json(stream), object_pairs_hook = join_duplicate_keys)
	obj['controller_mappings']['group'] = {group['id'] : group for group in obj['controller_mappings']['group']}
	return json.dumps(obj)

def main():
    """
    Read Steam vdf and write json compatible conversion
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(prog='vdf2json', description=main.__doc__)
    parser.add_argument('-i', '--input',
                        default=sys.stdin,
                        type=argparse.FileType('r'),
                        help='input vdf file (stdin if not specified)')
    parser.add_argument('-o', '--output',
                        default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='output json file (stdout if not specified)')

    args = parser.parse_args()
    args.output.write(vdf2json(args.input))

if __name__ == '__main__':
    main()
