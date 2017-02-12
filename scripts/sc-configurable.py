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
from steamcontroller.events import EventMapper, Modes, StickModes, PadModes, Pos, TrigModes
from steamcontroller.uinput import Axes, Keys, Scans

from steamcontroller.daemon import Daemon

import gc
import json
import os

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
		# TODO:  Proper support for multiples
		if(type(activator) != list):
			activator = [activator]
		binding = activator[0]['bindings']['binding'].split()
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

		# Holy crap, the hacks don't get much uglier than this.  Add 0x100 to
		#    all KEY_ constants, because the keyboard ends at 0xff and that
		#    seems to make the uinput subsystem happy about considering this
		#    to be a gamepad/joystick.
		return Keys.__getattr__('KEY_' + binding[1]) + 0x100
	elif(binding[0] == 'mouse_wheel'):
		# TODO:  Figure out if we actually need this; if so, add support
		return None
	elif(binding[0] == 'mouse_button'):
		return Keys.__getattr__('BTN_' + binding[1])
	elif(binding[0] == 'mode_shift'):
		return [a['bindings']['binding'].split()[1] for a in activator]

	return None
# }}}

def get_dpad_inputs(group): # {{{
	return {
		'north' : get_binding(group, 'dpad_north', 'Full_Press'),
		'west' : get_binding(group, 'dpad_west', 'Full_Press'),
		'south' : get_binding(group, 'dpad_south', 'Full_Press'),
		'east' : get_binding(group, 'dpad_east', 'Full_Press')
	}
# }}}

def get_diamond_inputs(group): # {{{
	return {
		'north' : get_binding(group, 'button_y', 'Full_Press'),
		'west' : get_binding(group, 'button_x', 'Full_Press'),
		'south' : get_binding(group, 'button_b', 'Full_Press'),
		'east' : get_binding(group, 'button_a', 'Full_Press')
	}
# }}}

def parse_trackpad_config(group, pos): # {{{
	config = {}
	if(group['mode'] == 'absolute_mouse'):
		config['mode'] = PadModes.MOUSE
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
	elif(group['mode'] == 'mouse_region'):
		# TODO:  Implement
		config['mode'] = PadModes.NOACTION
		pass
	elif(group['mode'] == 'scrollwheel'):
		config['mode'] = PadModes.MOUSESCROLL
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
	elif(group['mode'] == 'dpad'):
		config['mode'] = PadModes.BUTTONCLICK
		config['buttons'] = get_dpad_inputs(group['inputs'])
	elif(group['mode'] == 'buttons'):
		config['mode'] = PadModes.BUTTONCLICK
		config['buttons'] = get_diamond_inputs(group['inputs'])
	elif(group['mode'] == 'mouse_joystick'):
		config['mode'] = PadModes.AXIS
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
		axes = [Axes.ABS_HAT0X, Axes.ABS_HAT0Y] if pos == Pos.LEFT else [Axes.ABS_HAT1X, Axes.ABS_HAT1Y]
		config['axes'] = [(axis, -1, 1, 0, 0) for axis in axes]
	return config
# }}}

def parse_joystick_config(group): # {{{
	config = {}
	if(group['mode'] == 'joystick_mouse'):
		config['mode'] = StickModes.AXIS
		config['buttons'] = {'click' : get_binding(group['inputs'], 'click', 'Full_Press')}
		config['axes'] = [(axis, -32768, 32767, 16, 128) for axis in [Axes.ABS_X, Axes.ABS_Y]]
	elif(group['mode'] == 'scrollwheel'):
		# TODO:  Implement
		config['mode'] = StickModes.NOACTION
		pass
	elif(group['mode'] == 'dpad'):
		config['mode'] = StickModes.BUTTON
		config['buttons'] = get_dpad_inputs(group['inputs'])
	elif(group['mode'] == 'buttons'):
		config['mode'] = StickModes.BUTTON
		config['buttons'] = get_diamond_inputs(group['inputs'])
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
		output_config['left_trackpad']['active'] = parse_trackpad_config(groups[bindings['left_trackpad active']], Pos.LEFT)
		if('left_trackpad active modeshift' in bindings):
			output_config['left_trackpad']['modeshift'] = parse_trackpad_config(groups[bindings['left_trackpad active modeshift']], Pos.LEFT)
		print('--- Left trackpad (active) loaded')

	if('right_trackpad active' in bindings):
		output_config['right_trackpad']['active'] = parse_trackpad_config(groups[bindings['right_trackpad active']], Pos.RIGHT)
		if('right_trackpad active modeshift' in bindings):
			output_config['right_trackpad']['modeshift'] = parse_trackpad_config(groups[bindings['right_trackpad active modeshift']], Pos.RIGHT)
		print('--- Right trackpad (active) loaded')

	if('joystick active' in bindings):
		group = groups[bindings['joystick active']]
		output_config['joystick']['active'] = parse_joystick_config(group)
		output_config['joystick']['active']['buttons']['click'] = get_binding(group['inputs'], 'click', 'Full_Press')
		if('joystick active modeshift' in bindings):
			group = groups[bindings['joystick active modeshift']]
			output_config['joystick']['modeshift'] = parse_joystick_config(group)
			output_config['joystick']['modeshift']['buttons']['click'] = get_binding(group['inputs'], 'click', 'Full_Press')
		print('--- Joystick (active) loaded')

	if('button_diamond active' in bindings):
		inputs = groups[bindings['button_diamond active']]['inputs']
		output_config['button_diamond']['active'] = {'buttons' : {
			'a' : get_binding(inputs, 'button_a', 'Full_Press'),
			'b' : get_binding(inputs, 'button_b', 'Full_Press'),
			'x' : get_binding(inputs, 'button_x', 'Full_Press'),
			'y' : get_binding(inputs, 'button_y', 'Full_Press')
		}}
		if('button_diamond active modeshift' in bindings):
			inputs = groups[bindings['button_diamond active modeshift']]['inputs']
			output_config['button_diamond']['modeshift'] = {'buttons' : {
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
		if('switch active modeshift' in bindings):
			inputs = groups[bindings['switch active modeshift']]['inputs']
			output_config['switch']['modeshift'] = {'buttons' : {
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
		if('left_trigger active modeshift' in bindings):
			group_id = bindings['left_trigger active modeshift']
			output_config['left_trigger']['modeshift'] = parse_trigger_config(groups[bindings['left_trigger active modeshift']])
		print('--- Left trigger (active) loaded')

	if('right_trigger active' in bindings):
		group_id = bindings['right_trigger active']
		output_config['right_trigger']['active'] = parse_trigger_config(groups[bindings['right_trigger active']])
		if('right_trigger active modeshift' in bindings):
			group_id = bindings['right_trigger active modeshift']
			output_config['right_trigger']['modeshift'] = parse_trigger_config(groups[bindings['right_trigger active modeshift']])
		print('--- Right trigger (active) loaded')

	return output_config
# }}}

def get_keys_from_config(config): # {{{
	buttons = []
	for group in config.values():
		for mode in group.values():
			if('buttons' in mode):
				for button in mode['buttons'].values():
					if(button != None and type(button) != list):
						buttons.append(button)
	buttons = list(set(buttons))
	return buttons
# }}}

def get_axes_from_config(config): # {{{
	axes = []
	for group in config.values():
		for mode in group.values():
			if('axes' in mode):
				for axis in mode['axes']:
					if(axis != None):
						axes.append(axis)
	axes = list(set(axes))
	return axes
# }}}

def get_modes_from_config(config): # {{{
	modes = set()
	for group in config.values():
		for mode in group.values():
			if('buttons' in mode):
				modes.add(Modes.GAMEPAD)
				break
		if(Modes.GAMEPAD in modes):
			break
	for group in ['left_trackpad', 'right_trackpad']:
		for mode in config[group].values():
			if(mode['mode'] == PadModes.MOUSE):
				modes.add(Modes.MOUSE)
				break
		if(Modes.MOUSE in modes):
			break
	return list(modes)
# }}}

def modeshift(evm, sections, pressed, config): # {{{
	group = 'modeshift' if pressed else 'active'
	if('left_trackpad' in sections and group in config['left_trackpad']):
		set_trackpad_config(evm, Pos.LEFT, config['left_trackpad'][group])
	if('right_trackpad' in sections and group in config['right_trackpad']):
		set_trackpad_config(evm, Pos.RIGHT, config['right_trackpad'][group])
	if('joystick' in sections and group in config['joystick']):
		set_joystick_config(evm, config['joystick'][group])
	if('button_diamond' in sections and group in config['button_diamond']):
		set_diamond_config(evm, config['button_diamond'][group])
	if('switch' in sections and group in config['switch']):
		set_switches_config(evm, config['switch'][group], config, False)
	if('left_trigger' in sections and group in config['left_trigger']):
		set_trigger_config(evm, Pos.LEFT, config['left_trigger'][group])
	if('right_trigger' in sections and group in config['right_trigger']):
		set_trigger_config(evm, Pos.RIGHT, config['right_trigger'][group])
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
		evm.setPadButtons(pos, [buttons['north'], buttons['west'], buttons['south'], buttons['east']], clicked = True, mode = Modes.GAMEPAD)
	elif(config['mode'] == PadModes.AXIS):
		evm.setPadAxes(pos, *[axis[0] for axis in config['axes']])
		evm.setButtonAction(button, config['buttons']['click'], Modes.GAMEPAD)
# }}}

def set_joystick_config(evm, config): # {{{
	if(config['mode'] == StickModes.BUTTON):
		evm.setStickButtons([config['buttons']['north'], config['buttons']['west'], config['buttons']['south'], config['buttons']['east']], Modes.GAMEPAD)
		if('click' in config['buttons'] and config['buttons']['click'] != None):
			evm.setButtonAction(SCButtons.LPAD, config['buttons']['click'], Modes.GAMEPAD)
	elif(config['mode'] == StickModes.AXIS):
		evm.setStickAxes(*[axis[0] for axis in config['axes']])
# }}}

def set_diamond_config(evm, config): # {{{
	evm.setButtonAction(SCButtons.A, config['buttons']['a'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.B, config['buttons']['b'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.X, config['buttons']['x'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.Y, config['buttons']['y'], Modes.GAMEPAD)
# }}}

def set_switches_config(evm, group, config, do_modeshifts): # {{{
	evm.setButtonAction(SCButtons.LB, group['buttons']['left_bumper'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.RB, group['buttons']['right_bumper'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.START, group['buttons']['start'], Modes.GAMEPAD)
	evm.setButtonAction(SCButtons.BACK, group['buttons']['back'], Modes.GAMEPAD)
	if(type(group['buttons']['left_grip']) == list):
		if(do_modeshifts):
			evm.setButtonCallback(SCButtons.LGRIP, lambda evm, btn, pressed: modeshift(evm, group['buttons']['left_grip'], pressed, config))
	else:
		evm.setButtonAction(SCButtons.LGRIP, group['buttons']['left_grip'], Modes.GAMEPAD)
	if(type(group['buttons']['right_grip']) == list):
		if(do_modeshifts):
			evm.setButtonCallback(SCButtons.RGRIP, lambda evm, btn, pressed: modeshift(evm, group['buttons']['right_grip'], pressed, config))
	else:
		evm.setButtonAction(SCButtons.RGRIP, group['buttons']['right_grip'], Modes.GAMEPAD)
# }}}

def set_trigger_config(evm, pos, config): # {{{
	if(config['mode'] == TrigModes.BUTTON):
		evm.setTrigButton(pos, config['buttons']['click'], Modes.GAMEPAD)
# }}}

def evminit(config_file_path):
	vdf = load_vdf(config_file_path)
	config = parse_config(vdf)

	keys = get_keys_from_config(config)
	axes = get_axes_from_config(config)
	modes = get_modes_from_config(config)

	evm = EventMapper(gamepad_definition = {
		'vendor' : 0x28de,
		'product' : 0x1142,
		'version' : 0x1,
		'name' : b"Steam Controller [" + bytes(os.path.basename(config_file_path), 'utf-8') + b']',
		'keys' : keys,
		'axes' : axes,
		'rels' : []
	}, modes = modes)

	if('active' in config['left_trackpad']):
		set_trackpad_config(evm, Pos.LEFT, config['left_trackpad']['active'])
		print('--- Left trackpad configured')

	if('active' in config['right_trackpad']):
		set_trackpad_config(evm, Pos.RIGHT, config['right_trackpad']['active'])
		print('--- Right trackpad configured')

	if('active' in config['joystick']):
		set_joystick_config(evm, config['joystick']['active'])
		print('--- Joystick configured')

	if('active' in config['button_diamond']):
		set_diamond_config(evm, config['button_diamond']['active'])
		print('--- Button diamond configured')

	if('active' in config['switch']):
		set_switches_config(evm, config['switch']['active'], config, True)
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
