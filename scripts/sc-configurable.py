#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Mike Cronce <mike@quadra-tec.net>
#                    Stany MARCEL <stanypub@gmail.com>
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

"""Steam Controller VDF-configurable mode"""

from steamcontroller import SteamController, SCButtons
from steamcontroller.events import EventMapper, Pos
from steamcontroller.uinput import Keys

from steamcontroller.daemon import Daemon

import gc
import json

import vdf2json

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

def load_vdf(path): # {{{
	f = open(path, 'r')
	obj = json.loads(vdf2json.vdf2json(f), object_pairs_hook = join_duplicate_keys)

	# Since /controller_mappings/group is a key duplicated numerous times, it
	#    makes it cumbersome to use.  This changes /controller_mappings/group
	#    to be a single-use key with a dict in it; each object in the dict is a
	#    one of these separate "group" objects, and the keys to the dict are
	#    the "id" fields of these objects.
	obj['controller_mappings']['group'] = {group['id'] : group for group in obj['controller_mappings']['group']}

	return obj
# }}}

def evminit():
	evm = EventMapper()
	evm.setPadMouse(Pos.RIGHT)
	evm.setPadScroll(Pos.LEFT)
	evm.setStickButtons([
		Keys.KEY_UP,
		Keys.KEY_LEFT,
		Keys.KEY_DOWN,
		Keys.KEY_RIGHT
	])

	evm.setTrigButton(Pos.LEFT, Keys.BTN_RIGHT)
	evm.setTrigButton(Pos.RIGHT, Keys.BTN_LEFT)

	evm.setButtonAction(SCButtons.LB, Keys.KEY_VOLUMEDOWN)
	evm.setButtonAction(SCButtons.RB, Keys.KEY_VOLUMEUP)

	evm.setButtonAction(SCButtons.STEAM, Keys.KEY_HOMEPAGE)

	evm.setButtonAction(SCButtons.A, Keys.KEY_ENTER)
	evm.setButtonAction(SCButtons.B, Keys.KEY_BACKSPACE)
	evm.setButtonAction(SCButtons.X, Keys.KEY_ESC)
	evm.setButtonAction(SCButtons.Y, Keys.KEY_PLAYPAUSE)

	evm.setButtonAction(SCButtons.START, Keys.KEY_NEXTSONG)
	evm.setButtonAction(SCButtons.BACK, Keys.KEY_PREVIOUSSONG)

	evm.setButtonAction(SCButtons.LGRIP, Keys.KEY_BACK)
	evm.setButtonAction(SCButtons.RGRIP, Keys.KEY_FORWARD)

	evm.setButtonAction(SCButtons.LPAD, Keys.BTN_MIDDLE)
	evm.setButtonAction(SCButtons.RPAD, Keys.KEY_SPACE)

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
		parser.add_argument('-c', '--config-file', type = str, required = True)
		parser.add_argument('-i', '--index', type=int, choices=[0,1,2,3], default=None)
		args = parser.parse_args()

		config = load_vdf(args.config_file)

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
				return

	_main()
