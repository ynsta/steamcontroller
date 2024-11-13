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

"""Event mapper class and enums used to map steamcontroller inputs to uinput events"""

import math
from time import time
from enum import IntEnum
from collections import deque

import steamcontroller.uinput as sui
from steamcontroller import SCStatus, SCButtons, SCI_NULL


EXIT_PRESS_DURATION = 2.0


class Pos(IntEnum):
    """Specify which pad or trig is used"""
    RIGHT = 0
    LEFT = 1


class PadModes(IntEnum):
    """Possible pads modes"""
    NOACTION = 0
    AXIS = 1
    MOUSE = 2
    MOUSESCROLL = 3
    BUTTONTOUCH = 4
    BUTTONCLICK = 5


class TrigModes(IntEnum):
    """Possible trig modes"""
    NOACTION = 0
    AXIS = 1
    BUTTON = 2


class StickModes(IntEnum):
    """Possible stick modes"""
    NOACTION = 0
    AXIS = 1
    BUTTON = 2


class EventMapper(object):
    """
    Event mapper class permit to configure events and provide the process event
    callback to be registered to a SteamController instance

    @param uinput_devices: Optional. Input devices to register. Defaults to
                           `(sui.Gamepad(), sui.Keyboard(), sui.Mouse())`
                            where `sui` is `steamcontroller.uinput`
    @type uinput_devices: Tuple or List of steamcontroller.uinput.UInput instances`
    """

    def __init__(self, uinput_devices=None):
        if uinput_devices is None:
            self._uips = (sui.Gamepad(), sui.Keyboard(), sui.Mouse())
        else:
            self._uips = uinput_devices

        assert all(isinstance(uip, sui.UInput) for uip in self._uips)

        self._btn_map = {x: (None, 0) for x in list(SCButtons)}

        self._pad_modes = [PadModes.NOACTION, PadModes.NOACTION]
        self._pad_dzones = [0, 0]
        self._pad_evts = [[(None, 0)] * 4] * 2
        self._pad_revs = [False, False]

        self._trig_modes = [TrigModes.NOACTION, TrigModes.NOACTION]
        self._trig_evts = [(None, 0)] * 2

        self._stick_mode = StickModes.NOACTION
        self._stick_evts = [(None, 0)] * 2
        self._stick_rev = False

        self._sci_prev = SCI_NULL

        self._xdq = [deque(maxlen=8), deque(maxlen=8)]
        self._ydq = [deque(maxlen=8), deque(maxlen=8)]

        self._onkeys = set()
        self._onabs = {}

        self._stick_tys = None
        self._stick_lxs = None
        self._stick_bys = None
        self._stick_rxs = None
        self._stick_axes_callback = None
        self._stick_pressed_callback = None

        self._trig_s = [None, None]
        self._trig_axes_callbacks = [None, None]

        self._moved = [0, 0]
        self._steam_pressed_time = 0.0

    def __del__(self):
        if hasattr(self, '_uip') and self._uips:
            for u in self._uips:
                del u
            self._uips = []

    def _get_uip_idx_by_keyManaged(self, key, fail=True):
        for idx, uip in enumerate(self._uips):
            if uip.keyManaged(key):
                return idx
        if fail:
            raise RuntimeError('no uinput_device given to handle key %s' % key)

    def _get_uip_idx_by_axisManaged(self, axis, fail=True):
        for idx, uip in enumerate(self._uips):
            if uip.axisManaged(axis):
                return idx
        if fail:
            raise RuntimeError('no uinput_device given to handle axis %s' % axis)

    def _get_uip_idx_by_relManaged(self, rel, fail=True):
        for idx, uip in enumerate(self._uips):
            if uip.relManaged(rel):
                return idx
        if fail:
            raise RuntimeError('no uinput_device given to handle rel %s' % rel)

    def _get_uip_idx_by_attr_exists(self, attr, fail=True):
        for idx, uip in enumerate(self._uips):
            if hasattr(uip, attr):
                return idx
        if fail:
            raise RuntimeError('no uinput_device has attribute %s' % attr)

    def _get_uip_idx_by_instance(self, cls, fail=True):
        for idx, uip in enumerate(self._uips):
            if isinstance(uip, cls):
                return idx
        if fail:
            raise RuntimeError('no uinput_device of class %s' % cls)

    def process(self, sc, sci):
        """
        Process SteamController inputs to generate events

        @param SteamController sc       steamcontroller class used to get input
        @param SteamControllerInput sci inputs from the steam controller
        """
        if sci.status != SCStatus.INPUT:
            return

        sci_p = self._sci_prev
        self._sci_prev = sci

        _xor = sci_p.buttons ^ sci.buttons
        btn_rem = _xor & sci_p.buttons
        btn_add = _xor & sci.buttons

        uip_mouse = self._get_uip_idx_by_instance(sui.Mouse, fail=False)

        syn = set()

        def _abspressed(uip_idx, ev, val):
            if ev not in self._onabs or self._onabs[ev] != val:
                self._uips[uip_idx].axisEvent(ev, val)
                syn.add(uip_idx)
                self._onabs[ev] = val
                return True
            else:
                return False

        def _absreleased(uip_idx, ev):
            if ev not in self._onabs or self._onabs[ev] == 0:
                return False
            else:
                self._uips[uip_idx].axisEvent(ev, 0)
                syn.add(uip_idx)
                self._onabs[ev] = 0
                return True

        def _keypressed(uip_idx, ev):
            """Private function used to generate different kind of key press"""
            if ev not in self._onkeys:
                self._uips[uip_idx].keyEvent(ev, 1)
                syn.add(uip_idx)
            if ev in self._onkeys:
                return False
            else:
                self._onkeys.add(ev)
                return True

        def _keyreleased(uip_idx, ev):
            """Private function used to generate different kind of key release"""
            if ev in self._onkeys:
                self._onkeys.remove(ev)
                self._uips[uip_idx].keyEvent(ev, 0)
                syn.add(uip_idx)
                return True
            else:
                return False

        # Manage long Steam press to exit
        if btn_add & SCButtons.STEAM == SCButtons.STEAM:
            self._steam_pressed_time = time()
        if (sci.buttons & SCButtons.STEAM == SCButtons.STEAM and
                time() - self._steam_pressed_time > EXIT_PRESS_DURATION):
            for uip in self._uips:
                uip.destroyDevice()
            sc.addExit()

        # Manage buttons
        for btn, (uip_idx, ev) in self._btn_map.items():
            if uip_idx is None:
                continue

            if btn & btn_add:
                if uip_idx is None:
                    ev(self, btn, True)
                else:
                    _keypressed(uip_idx, ev)
            elif btn & btn_rem:
                if uip_idx is None:
                    ev(self, btn, False)
                else:
                    _keyreleased(uip_idx, ev)

        # Manage pads
        for pos in [Pos.LEFT, Pos.RIGHT]:
            if pos == Pos.LEFT:
                x, y = sci.lpad_x, sci.lpad_y
                x_p, y_p = sci_p.lpad_x, sci_p.lpad_y
                touch = SCButtons.LPADTOUCH
                click = SCButtons.LPAD
            else:
                x, y = sci.rpad_x, sci.rpad_y
                x_p, y_p = sci_p.rpad_x, sci_p.rpad_y
                touch = SCButtons.RPADTOUCH
                click = SCButtons.RPAD

            if sci.buttons & touch == touch:
                # Compute mean pos
                try:
                    xm_p = int(sum(self._xdq[pos]) / len(self._xdq[pos]))
                except ZeroDivisionError:
                    xm_p = 0

                try:
                    ym_p = int(sum(self._ydq[pos]) / len(self._ydq[pos]))
                except ZeroDivisionError:
                    ym_p = 0

                self._xdq[pos].append(x)
                self._ydq[pos].append(y)
                try:
                    xm = int(sum(self._xdq[pos]) / len(self._xdq[pos]))
                except ZeroDivisionError:
                    xm = 0

                try:
                    ym = int(sum(self._ydq[pos]) / len(self._ydq[pos]))
                except ZeroDivisionError:
                    ym = 0

                if not sci_p.buttons & touch == touch:
                    xm_p, ym_p = xm, ym

            # Mouse and mouse scroll modes
            if (self._pad_modes[pos] in (PadModes.MOUSE, PadModes.MOUSESCROLL)
                    and uip_mouse is not None):
                _free = True
                _dx = 0
                _dy = 0

                if sci.buttons & touch == touch:
                    _free = False
                    if sci_p.buttons & touch == touch:
                        _dx = xm - xm_p
                        _dy = ym - ym_p

                if self._pad_modes[pos] == PadModes.MOUSE:
                    self._moved[pos] += int(self._uips[uip_mouse].moveEvent(_dx, -_dy, _free))
                    # FIXME: make haptic configurable
                    if self._moved[pos] >= 4000:
                        if not _free:
                            sc.addFeedback(pos, amplitude=100)
                        self._moved[pos] %= 4000
                else:
                    if self._uips[uip_mouse].scrollEvent(_dx, _dy, _free):
                        # FIXME: make haptic configurable
                        if not _free:
                            sc.addFeedback(pos, amplitude=256)

            # Axis mode
            elif self._pad_modes[pos] == PadModes.AXIS:
                revert = self._pad_revs[pos]
                (x_uip_idx, xev), (y_uip_idx, yev) = self._pad_evts[pos]
                if x_uip_idx is not None:
                    # FIXME: make haptic configurable
                    if sci.buttons & touch == touch:
                        self._moved[pos] += math.sqrt((xm - xm_p) ** 2 + (ym - ym_p) ** 2)
                        if self._moved[pos] >= 4000:
                            sc.addFeedback(pos, amplitude=100)
                            self._moved[pos] %= 4000

                    if x != x_p:
                        self._uips[x_uip_idx].axisEvent(xev, x)
                        syn.add(x_uip_idx)
                    if y != y_p:
                        self._uips[y_uip_idx].axisEvent(yev, y if not revert else -y)
                        syn.add(y_uip_idx)

            # Button touch mode
            elif (self._pad_modes[pos] == PadModes.BUTTONTOUCH
                  or self._pad_modes[pos] == PadModes.BUTTONCLICK):
                if self._pad_modes[pos] == PadModes.BUTTONTOUCH:
                    on_test = touch
                    off_test = touch
                else:
                    on_test = click | touch
                    off_test = click

                haptic = False

                if sci.buttons & on_test == on_test:
                    # Get callback events
                    callbacks = []
                    for evt in self._pad_evts[pos]:
                        if evt[0] is None:
                            callbacks.append(evt)
                    for callback_evt in callbacks:
                        callback_evt[1](self, pos, xm, ym)

                    dzone = self._pad_dzones[pos]
                    if len(self._pad_evts[pos]) == 4:
                        # Key or buttons
                        t_uip_idx, tev = self._pad_evts[pos][0]
                        l_uip_idx, lev = self._pad_evts[pos][1]
                        b_uip_idx, bev = self._pad_evts[pos][2]
                        r_uip_idx, rev = self._pad_evts[pos][3]

                        # Correct weird rotational offset of d-touch-pad
                        angle = -0.35877  # Roughly 20.556 degrees
                        cos = math.cos(angle)
                        sin = math.sin(angle)
                        xm_cor = cos * x - sin * y
                        ym_cor = sin * x + cos * y

                        # Top
                        if ym_cor >= dzone:
                            haptic |= _keypressed(t_uip_idx, tev)
                        else:
                            haptic |= _keyreleased(t_uip_idx, tev)

                        # Left
                        if xm_cor <= -dzone:
                            haptic |= _keypressed(l_uip_idx, lev)
                        else:
                            haptic |= _keyreleased(l_uip_idx, lev)

                        # Bottom
                        if ym_cor <= -dzone:
                            haptic |= _keypressed(b_uip_idx, bev)
                        else:
                            haptic |= _keyreleased(b_uip_idx, bev)

                        # Right
                        if xm_cor >= dzone:
                            haptic |= _keypressed(r_uip_idx, rev)
                        else:
                            haptic |= _keyreleased(r_uip_idx, rev)

                    elif len(self._pad_evts[pos]) == 2:
                        x_uip_idx, xev = self._pad_evts[pos][0]
                        y_uip_idx, yev = self._pad_evts[pos][1]
                        rev = self._pad_revs[pos]

                        # Correct weird rotational offset of d-touch-pad
                        angle = -0.35877  # Roughly 20.556 degrees
                        cos = math.cos(angle)
                        sin = math.sin(angle)
                        xm_cor = cos * x - sin * y
                        ym_cor = sin * x + cos * y

                        if ym_cor > dzone:  # Top
                            haptic |= _abspressed(y_uip_idx, yev,
                                                  -1 if rev else 1)
                        elif ym_cor < -dzone:  # Bottom
                            haptic |= _abspressed(y_uip_idx, yev,
                                                  1 if rev else -1)
                        else:
                            haptic |= _absreleased(y_uip_idx, yev)

                        if xm_cor < -dzone:  # Left
                            haptic |= _abspressed(x_uip_idx, xev, -1)
                        elif xm_cor > dzone:  # Right
                            haptic |= _abspressed(x_uip_idx, xev, 1)
                        else:
                            haptic |= _absreleased(x_uip_idx, xev)

                if sci.buttons & off_test != off_test and sci_p.buttons & on_test == on_test:
                    if len(self._pad_evts[pos]) == 4:
                        for uip_idx, ev in self._pad_evts[pos]:
                            haptic |= _keyreleased(uip_idx, ev)
                    elif len(self._pad_evts[pos]) == 2:
                        for uip_idx, ev in self._pad_evts[pos]:
                            haptic |= _absreleased(uip_idx, ev)

                if haptic and self._pad_modes[pos] == PadModes.BUTTONTOUCH:
                    sc.addFeedback(pos, amplitude=300)

            if sci.buttons & touch != touch:
                xm_p, ym_p, xm, ym = 0, 0, 0, 0
                self._xdq[pos].clear()
                self._ydq[pos].clear()

        # Manage Trig
        for pos in [Pos.LEFT, Pos.RIGHT]:
            trigval = sci.ltrig if pos == Pos.LEFT else sci.rtrig
            trigval_prev = sci_p.ltrig if pos == Pos.LEFT else sci_p.rtrig
            uip_idx, ev = self._trig_evts[pos]

            if trigval != trigval_prev:
                if self._trig_axes_callbacks[pos]:
                    self._trig_axes_callbacks[pos](self, pos, trigval)
                elif self._trig_modes[pos] == TrigModes.AXIS:
                    syn.add(uip_idx)
                    self._uips[uip_idx].axisEvent(ev, trigval)

            elif self._trig_modes[pos] == TrigModes.BUTTON:
                if self._trig_s[pos] is None and trigval > min(trigval_prev + 10, 200):
                    self._trig_s[pos] = max(0, min(trigval - 10, 180))
                    _keypressed(uip_idx, ev)
                elif self._trig_s[pos] is not None and trigval <= self._trig_s[pos]:
                    self._trig_s[pos] = None
                    _keyreleased(uip_idx, ev)

        # Manage Stick
        if sci.buttons & SCButtons.LPADTOUCH != SCButtons.LPADTOUCH:
            x, y = sci.lpad_x, sci.lpad_y
            x_p, y_p = sci_p.lpad_x, sci_p.lpad_y

            if self._stick_axes_callback is not None and (x != x_p or y != y_p):
                self._stick_axes_callback(self, x, y)

            if self._stick_mode == StickModes.AXIS:
                revert = self._stick_rev
                (x_uip_idx, xev), (y_uip_idx, yev) = self._stick_evts
                if x != x_p:
                    syn.add(x_uip_idx)
                    self._uips[x_uip_idx].axisEvent(xev, x)
                if y != y_p:
                    syn.add(y_uip_idx)
                    self._uips[y_uip_idx].axisEvent(yev, y if not revert else -y)

            elif self._stick_mode == StickModes.BUTTON:
                t_uip_idx, tev = self._stick_evts[0]
                l_uip_idx, lev = self._stick_evts[1]
                b_uip_idx, bev = self._stick_evts[2]
                r_uip_idx, rev = self._stick_evts[3]

                # Top
                if self._stick_tys is None and y > 0 and y > min(y_p + 2000, 32000):
                    self._stick_tys = max(0, min(y - 2000, 31000))
                    _keypressed(t_uip_idx, tev)
                elif self._stick_tys is not None and y <= self._stick_tys:
                    self._stick_tys = None
                    _keyreleased(t_uip_idx, tev)

                # Left
                if self._stick_lxs is None and x < 0 and x < max(x_p - 2000, -32000):
                    self._stick_lxs = min(0, max(x + 2000, -31000))
                    _keypressed(l_uip_idx, lev)
                elif self._stick_lxs is not None and x >= self._stick_lxs:
                    self._stick_lxs = None
                    _keyreleased(l_uip_idx, lev)

                # Bottom
                if self._stick_bys is None and y < 0 and y < max(y_p - 2000, -32000):
                    self._stick_bys = min(0, max(y + 2000, -31000))
                    _keypressed(b_uip_idx, bev)
                elif self._stick_bys is not None and y >= self._stick_bys:
                    self._stick_bys = None
                    _keyreleased(b_uip_idx, bev)

                # Right
                if self._stick_rxs is None and x > 0 and x > min(x_p + 2000, 32000):
                    self._stick_rxs = max(0, min(x - 2000, 31000))
                    _keypressed(r_uip_idx, rev)
                elif self._stick_rxs is not None and x <= self._stick_rxs:
                    self._stick_rxs = None
                    _keyreleased(r_uip_idx, rev)

            if sci.buttons & SCButtons.LPAD == SCButtons.LPAD:
                if self._stick_pressed_callback is not None:
                    self._stick_pressed_callback(self)

        for i in list(syn):
            self._uips[i].synEvent()

    def setButtonAction(self, btn, key_event):
        uip_idx = self._get_uip_idx_by_keyManaged(key_event)
        self._btn_map[btn] = (uip_idx, key_event)

    def setButtonCallback(self, btn, callback):
        """
        Set callback function to be executed when button is clicked
        Callback is called with parameters self(EventMapper), btn
        and pushed (boollean True -> Button pressed, False -> Button released)

        @param btn                      Button
        @param function callback        Callback function
        """
        self._btn_map[btn] = (None, callback)

    def setPadButtons(self, pos, key_events, deadzone=0.6, clicked=False):
        """
        Set pad as buttons

        @param Pos pos          designate left or right pad
        @param list key_events  list of key events for the pad buttons (top, left, bottom, right)
        @param float deadzone   portion of the pad in the center dead zone from 0.0 to 1.0
        @param bool clicked     action on touch or on click event
        """
        assert len(key_events) == 4
        assert 0.0 <= deadzone < 1.0

        self._pad_modes[pos] = PadModes.BUTTONCLICK if clicked else PadModes.BUTTONTOUCH

        self._pad_evts[pos] = []
        for ev in key_events:
            uip_idx = self._get_uip_idx_by_keyManaged(ev)
            self._pad_evts[pos].append((uip_idx, ev))

        self._pad_dzones[pos] = 32768 * deadzone

        if clicked:
            if pos == Pos.LEFT:
                self._btn_map[SCButtons.LPAD] = (None, 0)
            else:
                self._btn_map[SCButtons.RPAD] = (None, 0)

    def setPadButtonCallback(self, pos, callback, clicked=False):
        """
        Set callback function to be executed when Pad clicked or touched
        If clicked is False callback will be called with pad, xpos and ypos
        else with pad and boolean is_pressed

        @param Pos pos          designate left or right pad
        @param callback         Callback function
        @param bool clicked     callback on touch or on click event
        """
        if not clicked:
            self._pad_modes[pos] = PadModes.BUTTONTOUCH
            self._pad_evts[pos].append((None, callback))
        else:
            self._pad_modes[pos] = PadModes.BUTTONCLICK
            if pos == Pos.LEFT:
                self._btn_map[SCButtons.LPAD] = (None, callback)
            else:
                self._btn_map[SCButtons.RPAD] = (None, callback)

    def setPadAxesAsButtons(self, pos, abs_events, deadzone=0.6, clicked=False, revert=True):
        """
        Set pad as buttons

        @param Pos pos          designate left or right pad
        @param list key_events  list of axes events for the pad buttons (X, Y)
        @param float deadzone   portion of the pad in the center dead zone from 0.0 to 1.0
        @param bool clicked     action on touch or on click event
        @param bool revert      revert axes
        """
        assert len(abs_events) == 2
        assert 0.0 <= deadzone < 1.0

        self._pad_modes[pos] = PadModes.BUTTONCLICK if clicked else PadModes.BUTTONTOUCH

        self._pad_evts[pos] = []
        for ev in abs_events:
            uip_idx = self._get_uip_idx_by_axisManaged(ev)
            self._pad_evts[pos].append((uip_idx, ev))

        self._pad_revs[pos] = revert
        self._pad_dzones[pos] = 32768 * deadzone

        if clicked:
            if pos == Pos.LEFT:
                self._btn_map[SCButtons.LPAD] = (None, 0)
            else:
                self._btn_map[SCButtons.RPAD] = (None, 0)

    def setPadMouse(self, pos,
                    trackball=True,
                    friction=sui.Mouse.DEFAULT_FRICTION,
                    xscale=sui.Mouse.DEFAULT_XSCALE,
                    yscale=sui.Mouse.DEFAULT_XSCALE):
        if not trackball:
            friction = 100.0
        uip_idx = self._get_uip_idx_by_instance(sui.Mouse)
        self._uips[uip_idx].updateParams(friction=friction, xscale=xscale, yscale=yscale)
        self._pad_modes[pos] = PadModes.MOUSE

    def setPadScroll(self, pos,
                     trackball=True,
                     friction=sui.Mouse.DEFAULT_SCR_FRICTION,
                     xscale=sui.Mouse.DEFAULT_SCR_XSCALE,
                     yscale=sui.Mouse.DEFAULT_SCR_XSCALE):
        if not trackball:
            friction = 100.0
        uip_idx = self._get_uip_idx_by_instance(sui.Mouse)
        self._uips[uip_idx].updateScrollParams(friction=friction, xscale=xscale, yscale=yscale)
        self._pad_modes[pos] = PadModes.MOUSESCROLL

    def setPadAxes(self, pos, abs_x_event, abs_y_event, revert=True):
        uip_idx_x = self._get_uip_idx_by_axisManaged(abs_x_event)
        uip_idx_y = self._get_uip_idx_by_axisManaged(abs_y_event)
        self._pad_modes[pos] = PadModes.AXIS
        self._pad_evts[pos] = [(uip_idx_x, abs_x_event), (uip_idx_y, abs_y_event)]
        self._pad_revs[pos] = revert

    def setTrigButton(self, pos, key_event):
        self._trig_modes[pos] = TrigModes.BUTTON
        uip_idx = self._get_uip_idx_by_keyManaged(key_event)
        self._trig_evts[pos] = (uip_idx, key_event)

    def setTrigAxis(self, pos, abs_event):
        uip_idx = self._get_uip_idx_by_axisManaged(abs_event)
        self._trig_modes[pos] = TrigModes.AXIS
        self._trig_evts[pos] = (uip_idx, abs_event)

    def setTrigAxesCallback(self, pos, callback):
        self._trig_modes[pos] = StickModes.AXIS
        self._trig_axes_callbacks[pos] = callback

    def setStickAxes(self, abs_x_event, abs_y_event, revert=True):
        uip_idx_x = self._get_uip_idx_by_axisManaged(abs_x_event)
        uip_idx_y = self._get_uip_idx_by_axisManaged(abs_y_event)
        self._stick_mode = StickModes.AXIS
        self._stick_evts = [(uip_idx_x, abs_x_event), (uip_idx_y, abs_y_event)]
        self._stick_rev = revert

    def setStickAxesCallback(self, callback):
        """
        Set Callback on StickAxes Movement
        The function will be called with EventMapper, pos_x, pos_y

        @param function callback       the callback function
        """
        self._stick_axes_callback = callback

    def setStickButtons(self, key_events):
        """
        Set stick as buttons

        @param list key_events  list of key events for the pad buttons (top, left, bottom, right)
        """
        assert len(key_events) == 4

        self._stick_mode = StickModes.BUTTON

        self._stick_evts = []
        for ev in key_events:
            uip_idx = self._get_uip_idx_by_keyManaged(ev)
            self._stick_evts.append((uip_idx, ev))

    def setStickPressedCallback(self, callback):
        """
        Set callback on StickPressed event
        The function will be called with EventMapper as first (and only) argument

        @param function Callback function      function that is called on button press.
        """
        self._stick_pressed_callback = callback
