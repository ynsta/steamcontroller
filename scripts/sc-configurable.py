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
from steamcontroller.events import EventMapper, Modes, PadModes, Pos, TrigModes
from steamcontroller.uinput import Axes, Keys, Scans

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
		activator = group_inputs[input_name]['activators'][activator]
		if(type(activator) == list):
			# TODO:  Support multiples
			activator = activator[0]
		binding = activator['bindings']['binding'].split()
	except KeyError:
		return None

	# TODO:  mode_shift ... maybe more?
	if(binding[0] == 'key_press'):
		# Ugly
		binding[1] = binding[1].replace('_ARROW', '')
		binding[1] = binding[1].replace('_', '')
		binding[1] = binding[1].replace(',', '') # Items such as "key_press W, w"; everything after the comma is already trimmed by split() above, ignore trailing items for now'

		if(binding[1] == 'PERIOD'):
			binding[1] = 'DOT'

		return Keys.__getattr__('KEY_' + binding[1])
	elif(binding[0] == 'mouse_wheel'):
		# TODO:  Figure out if we actually need this; if so, add support
		return None
	elif(binding[0] == 'mouse_button'):
		return Keys.__getattr__('BTN_' + binding[1])

	return None
# }}}

def parse_analog_config(group): # {{{
	config = {}
	if(group['mode'] == 'absolute_mouse'):
		config['mode'] = PadModes.MOUSE
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
	elif(group['mode'] == 'scrollwheel'):
		config['mode'] = PadModes.MOUSESCROLL
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
	elif(group['mode'] == 'dpad'):
		config['mode'] = PadModes.BUTTONCLICK
		config['buttons'] = {
			'north' : get_binding(group['inputs'], 'dpad_north', 'Full_Press'),
			'west' : get_binding(group['inputs'], 'dpad_west', 'Full_Press'),
			'south' : get_binding(group['inputs'], 'dpad_south', 'Full_Press'),
			'east' : get_binding(group['inputs'], 'dpad_east', 'Full_Press')
		}
	return config
# }}}

def parse_trigger_config(group): # {{{
	config = {}
	if(group['mode'] == 'trigger'):
		config['mode'] = TrigModes.BUTTON
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
	return config
# }}}

def parse_config(config): # {{{
	groups = config['controller_mappings']['group']
	bindings = config['controller_mappings']['preset']['group_source_bindings']

	# TODO:  Check/respect all possible "mode" entries in each group

	output_config = {
		'left_trackpad' : {},
		'right_trackpad' : {},
		'joystick' : {},
		'button_diamond' : {},
		'switch' : {},
		'left_trigger' : {},
		'right_trigger' : {}
	}

	if('left_trackpad active' in bindings):
		output_config['left_trackpad']['active'] = parse_analog_config(groups[bindings['left_trackpad active']])
		print('--- Left trackpad (active) loaded')

	if('right_trackpad active' in bindings):
		output_config['right_trackpad']['active'] = parse_analog_config(groups[bindings['right_trackpad active']])
		print('--- Right trackpad (active) loaded')

	if('joystick active' in bindings):
		group = groups[bindings['joystick active']]
		output_config['joystick']['active'] = parse_analog_config(group)
		output_config['joystick']['active']['buttons']['click'] = get_binding(group['inputs'], 'click', 'Full_Press')
		print('--- Joystick (active) loaded')

	if('button_diamond active' in bindings):
		inputs = groups[bindings['button_diamond active']]['inputs']
		output_config['button_diamond']['active'] = {'buttons' : {
			'a' : get_binding(inputs, 'button_a', 'Full_Press'),
			'b' : get_binding(inputs, 'button_b', 'Full_Press'),
			'x' : get_binding(inputs, 'button_x', 'Full_Press'),
			'y' : get_binding(inputs, 'button_y', 'Full_Press')
		}}
		print('--- Button diamond (active) loaded')

	if('switch active' in bindings):
		inputs = groups[bindings['switch active']]['inputs']
		output_config['switch']['active'] = {'buttons' : {
			'left_bumper' : get_binding(inputs, 'left_bumper', 'Full_Press'),
			'right_bumper' : get_binding(inputs, 'right_bumper', 'Full_Press'),
			'start' : get_binding(inputs, 'button_escape', 'Full_Press'),
			'back' : get_binding(inputs, 'button_menu', 'Full_Press'),
			'left_grip' : get_binding(inputs, 'button_back_left', 'Full_Press'),
			'right_grip' : get_binding(inputs, 'button_back_right', 'Full_Press')
		}}
		print('--- Switches (active) loaded')
	
	if('left_trigger active' in bindings):
		group_id = bindings['left_trigger active']
		output_config['left_trigger']['active'] = parse_trigger_config(groups[bindings['left_trigger active']])
		print('--- Left trigger (active) loaded')

	if('right_trigger active' in bindings):
		group_id = bindings['right_trigger active']
		output_config['right_trigger']['active'] = parse_trigger_config(groups[bindings['right_trigger active']])
		print('--- Right trigger (active) loaded')

	return output_config
# }}}

def set_trackpad_config(evm, pos, config): # {{{
	button = SCButtons.RPAD if pos == Pos.RIGHT else SCButtons.LPAD
	if(config['mode'] == PadModes.MOUSE):
		evm.setPadMouse(pos)
		evm.setButtonAction(button, config['buttons']['click'], Modes.GAMEPAD)
	elif(config['mode'] == PadModes.MOUSESCROLL):
		# TODO:  Support configuration for scroll directions
		evm.setPadScroll(pos)
		evm.setButtonAction(button, config['buttons']['click'], Modes.GAMEPAD)
	elif(config['mode'] == PadModes.BUTTONCLICK):
		# TODO:  Configurable whether or not click is required?
		buttons = config['buttons']
		evm.setPadButtons(pos, [buttons['north'], buttons['west'], buttons['south'], buttons['east']], clicked = True)
# }}}

def set_trigger_config(evm, pos, config): # {{{
	if(config['mode'] == TrigModes.BUTTON):
		evm.setTrigButton(pos, config['buttons']['click'], Modes.GAMEPAD)
# }}}

def get_keys_from_config(config): # {{{
	buttons = []
	for group in config.values():
		for mode in group.values():
			if('buttons' in mode):
				for button in mode['buttons'].values():
					if(button != None):
						buttons.append(button)
	buttons = list(set(buttons))
	return buttons
# }}}

def evminit(config_file_path):
	vdf = load_vdf(config_file_path)
	config = parse_config(vdf)

	keys = get_keys_from_config(config)

	# TODO:  Dynamic gamepad definition for axes based on config
	evm = EventMapper(gamepad_definition = {
		'vendor' : 0x28de,
		'product' : 0x1142,
		'version' : 0x1,
		'name' : b"Steam Controller",
		'keys' : keys,
		'axes' : [
			(Axes.ABS_X, -32768, 32767, 16, 128),
			(Axes.ABS_Y, -32768, 32767, 16, 128),
			(Axes.ABS_Z, 0, 255, 0, 0),
			(Axes.ABS_RZ, 0, 255, 0, 0),
			(Axes.ABS_HAT0X, -1, 1, 0, 0),
			(Axes.ABS_HAT0Y, -1, 1, 0, 0),
			(Axes.ABS_HAT1X, -1, 1, 0, 0),
			(Axes.ABS_HAT1Y, -1, 1, 0, 0)
		],
		'rels' : []
	})

	if('active' in config['left_trackpad']):
		set_trackpad_config(evm, Pos.LEFT, config['left_trackpad']['active'])
		print('--- Left trackpad configured')

	if('active' in config['right_trackpad']):
		set_trackpad_config(evm, Pos.RIGHT, config['right_trackpad']['active'])
		print('--- Right trackpad configured')

	if('active' in config['joystick']):
		group = config['joystick']['active']
		if(group['mode'] == PadModes.BUTTONCLICK):
			evm.setStickButtons([group['buttons']['north'], group['buttons']['west'], group['buttons']['south'], group['buttons']['east']], Modes.GAMEPAD)
			if('click' in group['buttons'] and group['buttons']['click'] != None):
				evm.setButtonAction(SCButtons.LPAD, group['buttons']['click'], Modes.GAMEPAD)
		print('--- Joystick configured')

	if('active' in config['button_diamond']):
		group = config['button_diamond']['active']
		evm.setButtonAction(SCButtons.A, group['buttons']['a'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.B, group['buttons']['b'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.X, group['buttons']['x'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.Y, group['buttons']['y'], Modes.GAMEPAD)
		print('--- Button diamond configured')

	if('active' in config['switch']):
		group = config['switch']['active']
		evm.setButtonAction(SCButtons.LB, group['buttons']['left_bumper'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.RB, group['buttons']['right_bumper'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.START, group['buttons']['start'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.BACK, group['buttons']['back'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.LGRIP, group['buttons']['left_grip'], Modes.GAMEPAD)
		evm.setButtonAction(SCButtons.RGRIP, group['buttons']['right_grip'], Modes.GAMEPAD)
		print('--- Switches configured')

	if('active' in config['left_trigger']):
		set_trigger_config(evm, Pos.LEFT, config['left_trigger']['active'])
		print('--- Left trigger configured')

	if('active' in config['right_trigger']):
		set_trigger_config(evm, Pos.RIGHT, config['right_trigger']['active'])
		print('--- Right trigger configured')

	# This cannot be configured from the Steam UI.  Should we extend that file
	#    to support configuring it?
	evm.setButtonAction(SCButtons.STEAM, Keys.KEY_HOMEPAGE, Modes.GAMEPAD)

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
