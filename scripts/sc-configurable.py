#!/usr/bin/env python3

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

	# ID -> binding doesn't really do us any good.  Flip it.
	obj['controller_mappings']['preset']['group_source_bindings'] = {value : key for key, value in obj['controller_mappings']['preset']['group_source_bindings'].items()}

	return obj
# }}}

def get_binding(group_inputs, input_name, activator): # {{{
	try:
		binding = group_inputs[input_name]['activators'][activator]['bindings']['binding'].split()
	except KeyError:
		return None

	# TODO:  mouse_wheel, mouse_button, mode_shift ... more?
	if(binding[0] == 'key_press'):
		# Ugly
		binding[1] = binding[1].replace('_ARROW', '')
		return Keys.__getattr__('KEY_' + binding[1])

	return None
# }}}

def set_trackpad_config(evm, pos, group): # {{{
	button = SCButtons.RPAD if pos == Pos.RIGHT else SCButtons.LPAD
	if(group['mode'] == 'absolute_mouse'):
		evm.setPadMouse(pos)
		evm.setButtonAction(button, get_binding(group['inputs'], 'click', 'Full_Press'))
	elif(group['mode'] == 'scrollwheel'):
		# TODO:  Support configuration for scroll directions
		evm.setPadScroll(pos)
		evm.setButtonAction(button, get_binding(group['inputs'], 'click', 'Full_Press'))
	elif(group['mode'] == 'dpad'):
		inputs = group['inputs']
		# TODO:  Configurable whether or not click is required?
		evm.setPadButtons(pos, [
			get_binding(inputs, 'dpad_north', 'Full_Press'),
			get_binding(inputs, 'dpad_west', 'Full_Press'),
			get_binding(inputs, 'dpad_south', 'Full_Press'),
			get_binding(inputs, 'dpad_east', 'Full_Press')
		], clicked = True)
# }}}

def evminit(config_file_path):
	evm = EventMapper()
	config = load_vdf(config_file_path)

	groups = config['controller_mappings']['group']
	bindings = config['controller_mappings']['preset']['group_source_bindings']

	# TODO:  Check/respect all possible "mode" entries in each group

	if('right_trackpad active' in bindings):
		group_id = bindings['right_trackpad active']
		set_trackpad_config(evm, Pos.RIGHT, groups[group_id])

	if('left_trackpad active' in bindings):
		group_id = bindings['left_trackpad active']
		set_trackpad_config(evm, Pos.LEFT, groups[group_id])

	if('joystick active' in bindings):
		group_id = bindings['joystick active']
		group = groups[group_id]
		inputs = group['inputs']
		if(group['mode'] == 'dpad'):
			evm.setStickButtons([
				get_binding(inputs, 'dpad_north', 'Full_Press'),
				get_binding(inputs, 'dpad_west', 'Full_Press'),
				get_binding(inputs, 'dpad_south', 'Full_Press'),
				get_binding(inputs, 'dpad_east', 'Full_Press')
			])

	evm.setTrigButton(Pos.LEFT, Keys.BTN_RIGHT)
	evm.setTrigButton(Pos.RIGHT, Keys.BTN_LEFT)

	evm.setButtonAction(SCButtons.LB, Keys.KEY_VOLUMEDOWN)
	evm.setButtonAction(SCButtons.RB, Keys.KEY_VOLUMEUP)

	evm.setButtonAction(SCButtons.STEAM, Keys.KEY_HOMEPAGE)

	if('button_diamond active' in bindings):
		group_id = bindings['button_diamond active']
		inputs = groups[group_id]['inputs']
		evm.setButtonAction(SCButtons.A, get_binding(inputs, 'button_a', 'Full_Press'))
		evm.setButtonAction(SCButtons.B, get_binding(inputs, 'button_b', 'Full_Press'))
		evm.setButtonAction(SCButtons.X, get_binding(inputs, 'button_x', 'Full_Press'))
		evm.setButtonAction(SCButtons.Y, get_binding(inputs, 'button_y', 'Full_Press'))

	evm.setButtonAction(SCButtons.START, Keys.KEY_NEXTSONG)
	evm.setButtonAction(SCButtons.BACK, Keys.KEY_PREVIOUSSONG)

	evm.setButtonAction(SCButtons.LGRIP, Keys.KEY_BACK)
	evm.setButtonAction(SCButtons.RGRIP, Keys.KEY_FORWARD)

	evm.setButtonAction(SCButtons.LPAD, Keys.BTN_MIDDLE)
	evm.setButtonAction(SCButtons.RPAD, Keys.KEY_SPACE)

	return evm

class SCDaemon(Daemon):
	def __init__(self, pidfile, config_file):
		self.pidfile = pidfile
		self.config_file = config_file

	def run(self):
		evm = evminit(self.config_file)
		sc = SteamController(callback=evm.process)
		sc.run()
		del sc
		del evm
		gc.collect()

if __name__ == '__main__':
	import argparse

	def _main():
		parser = argparse.ArgumentParser(description = __doc__)
		parser.add_argument('command', type = str, choices = ['start', 'stop', 'restart', 'debug'])
		parser.add_argument('-c', '--config-file', type = str, required = True)
		parser.add_argument('-i', '--index', type = int, choices = [0,1,2,3], default = None)
		args = parser.parse_args()

		if args.index != None:
			daemon = SCDaemon('/tmp/steamcontroller{:d}.pid'.format(args.index), args.config_file)
		else:
			daemon = SCDaemon('/tmp/steamcontroller.pid', args.config_file)

		if 'start' == args.command:
			daemon.start()
		elif 'stop' == args.command:
			daemon.stop()
		elif 'restart' == args.command:
			daemon.restart()
		elif 'debug' == args.command:
			try:
				evm = evminit(args.config_file)
				sc = SteamController(callback=evm.process)
				sc.run()
			except KeyboardInterrupt:
				return

	_main()
