# The MIT License (MIT)
#
# Copyright (c) 2017 Mike Cronce <mike@quadra-tec.net>
#					Stany MARCEL <stanypub@gmail.com>
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

import shlex

def vdf2json(stream): # {{{
	"""
	Read a Steam vdf file and return a string in json format
	"""

	def _istr(ident, string):
		return (ident * '  ') + string

	jbuf = '{\n'
	lex = shlex.shlex(stream)
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
# }}}

def json2vdf(stream): # {{{

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
# }}}

