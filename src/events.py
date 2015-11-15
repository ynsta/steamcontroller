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

from enum import IntEnum

from steamcontroller import \
    SteamController, \
    SCStatus, \
    SCButtons, \
    SCI_NULL

import steamcontroller.uinput as sui
from steamcontroller.uinput import Keys, Axes, Rels

from collections import deque

class Pos(IntEnum):
    Left = 0
    Right = 1

class Modes(IntEnum):
    Gamepad = 0
    Keyboard = 1
    Mouse = 2

class PadModes(IntEnum):
    NoAction = 0
    Axis = 1
    Mouse = 2
    MouseScroll = 3
    ButtonTouch = 4
    ButtonClick = 5

class TrigModes(IntEnum):
    NoAction = 0
    Axis = 1
    Button = 2

class StickModes(IntEnum):
    NoAction = 0
    Axis = 1
    Button = 2

class EventMapper(object):

    def __init__(self):

        self._uip = (sui.Gamepad(),
                     sui.Keyboard(),
                     sui.Mouse())

        self._btn_map = {x : (None, 0) for x in list(SCButtons)}

        self._pad_modes = [PadModes.NoAction, PadModes.NoAction]
        self._pad_dzones = [0, 0]
        self._pad_evts = [[(None, 0)]*4]*2
        self._pad_revs = [False, False]

        self._trig_modes = [TrigModes.NoAction, TrigModes.NoAction]
        self._trig_evts = [(None, 0)]*2

        self._stick_mode = StickModes.NoAction
        self._stick_evts = [(None, 0)]*2
        self._stick_rev = False

        self._sci_prev = SCI_NULL

        self._xdq = [deque(maxlen=6), deque(maxlen=6)]
        self._ydq = [deque(maxlen=6), deque(maxlen=6)]

        self._onkeys = set()

        self._stick_tys = None
        self._stick_lxs = None
        self._stick_bys = None
        self._stick_rxs = None


        self._trig_s = [None, None]

    def process(self, sc, sci):

        if sci.status != SCStatus.Input:
            return

        sci_p = self._sci_prev
        self._sci_prev = sci

        _xor = sci_p.buttons ^ sci.buttons
        btn_rem = _xor & sci_p.buttons
        btn_add = _xor & sci.buttons

        _pressed = []
        _released = []

        syn = set()

        def _keypressed(mode, ev):
            if mode == Modes.Gamepad or mode == Modes.Mouse:
                if ev not in self._onkeys:
                    self._uip[mode].keyEvent(ev, 1)
                    syn.add(mode)
            elif mode == Modes.Keyboard:
                _pressed.append(ev)
            self._onkeys.add(ev)


        def _keyreleased(mode, ev):
            if ev in self._onkeys:
                self._onkeys.remove(ev)
                if mode == Modes.Gamepad or mode == Modes.Mouse:
                    self._uip[mode].keyEvent(ev, 0)
                    syn.add(mode)
                elif mode == Modes.Keyboard:
                    _released.append(ev)

        # Manage buttons
        for btn, (mode, ev) in self._btn_map.items():

            if mode is None:
                continue

            _uip = self._uip[mode]

            if btn & btn_add:
                _keypressed(mode, ev)
            elif btn & btn_rem:
                _keyreleased(mode, ev)


        # Manage pads
        for pos in [Pos.Left, Pos.Right]:

            if pos == Pos.Left:
                x, y = sci.lpad_x, sci.lpad_y
                xp, yp = sci_p.lpad_x, sci_p.lpad_y
                touch  = SCButtons.LPadTouch
                click  = SCButtons.LPad
            else:
                x, y =  sci.rpad_x, sci.rpad_y
                xp, yp = sci_p.rpad_x, sci_p.rpad_y
                touch  = SCButtons.RPadTouch
                click  = SCButtons.LPad

            if sci.buttons & touch == touch:
                # Compute mean pos
                try:
                    xmp = int(sum(self._xdq[pos]) / len(self._xdq[pos]))
                    ymp = int(sum(self._ydq[pos]) / len(self._ydq[pos]))
                except ZeroDivisionError:
                    xmp, ymp = 0, 0
                self._xdq[pos].append(x)
                self._ydq[pos].append(y)
                try:
                    xm = int(sum(self._xdq[pos]) / len(self._xdq[pos]))
                    ym = int(sum(self._ydq[pos]) / len(self._ydq[pos]))
                except ZeroDivisionError:
                    xm, ym = 0, 0
                if not sci_p.buttons & touch == touch:
                    xmp, ymp = xm, ym


            # Mouse and mouse scroll modes
            if self._pad_modes[pos] in (PadModes.Mouse, PadModes.MouseScroll):
                _free = True
                _dx = 0
                _dy = 0

                if sci.buttons & touch == touch:
                    _free = False
                    if sci_p.buttons & touch == touch:
                        _dx = xm - xmp
                        _dy = ym - ymp


                if self._pad_modes[pos] == PadModes.Mouse:
                    self._uip[Modes.Mouse].moveEvent(_dx, -_dy, _free)
                else:
                    self._uip[Modes.Mouse].scrollEvent(_dx, _dy, _free)

            # Axis mode
            elif self._pad_modes[pos] == PadModes.Axis:
                revert = self._pad_revs[pos]
                (xmod, xev), (ymod, yev) = self._pad_evts[pos]
                if xmod is not None:
                    if x != xp:
                        self._uip[xmod].axisEvent(xev, x)
                        syn.add(xmode)
                    if y != yp:
                        self._uip[ymod].axisEvent(yev, y if not revert else -y)
                        syn.add(ymode)

            # Button touch mode
            elif (self._pad_modes[pos] == PadModes.ButtonTouch or
                  self._pad_modes[pos] == PadModes.ButtonClick):

                if self._pad_modes[pos] == PadModes.ButtonTouch:
                    on_test = touch
                    off_test = touch
                else:
                    on_test = click | touch
                    off_test = click

                if sci.buttons & on_test == on_test:
                    dzone = self._pad_dzones[pos]

                    tmode, tev = self._pad_evts[pos][0]
                    lmode, lev = self._pad_evts[pos][1]
                    bmode, bev = self._pad_evts[pos][2]
                    rmode, rev = self._pad_evts[pos][3]

                    if ym > dzone: # TOP
                        _keypressed(tmode, tev)
                    else:
                        _keyreleased(tmode, tev)

                    if xm < -dzone: # LEFT
                        _keypressed(lmode, lev)
                    else:
                        _keyreleased(lmode, lev)

                    if ym < -dzone: # BOTTOM
                        _keypressed(bmode, bev)
                    else:
                        _keyreleased(bmode, bev)

                    if xm > dzone: # RIGHT
                        _keypressed(rmode, rev)
                    else:
                        _keyreleased(rmode, rev)

                if (sci.buttons & off_test != off_test and
                    sci_p.buttons & on_test == on_test):
                    for mode, ev in self._pad_evts[pos]:
                        _keyreleased(mode, ev)

            if sci.buttons & touch != touch:
                xmp, ymp, xm, xmp = 0, 0, 0, 0
                self._xdq[pos].clear()
                self._ydq[pos].clear()


        # Manage Trig
        for pos in [Pos.Left, Pos.Right]:
            trigval = sci.ltrig if pos == Pos.Left else sci.rtrig
            trigval_prev = sci_p.ltrig if pos == Pos.Left else sci_p.rtrig
            mode, ev = self._trig_evts[pos]
            if self._trig_modes[pos] == TrigModes.Axis:
                if trigval != trigval_prev:
                    syn.add(mode)
                    self._uip[mode].axisEvent(ev, trigval)
            elif self._trig_modes[pos] == TrigModes.Button:
                if self._trig_s[pos] is None and trigval > min(trigval_prev + 10, 200):
                    self._trig_s[pos] = max(0, min(trigval - 10, 180))
                    _keypressed(mode, ev)
                elif self._trig_s[pos] is not None and trigval <= self._trig_s[pos]:
                    self._trig_s[pos] = None
                    _keyreleased(mode, ev)


        # Manage Stick
        if sci.buttons & SCButtons.LPadTouch != SCButtons.LPadTouch:
            x, y = sci.lpad_x, sci.lpad_y
            xp, yp = sci_p.lpad_x, sci_p.lpad_y

            if self._stick_mode == StickModes.Axis:
                revert = self._stick_rev
                (xmod, xev), (ymod, yev) = self._stick_evts
                if x != xp:
                    syn.add(xmod)
                    self._uip[xmod].axisEvent(xev, x)
                if y != yp:
                    syn.add(ymod)
                    self._uip[ymod].axisEvent(yev, y if not revert else -y)
            elif self._stick_mode == StickModes.Button:

                tmode, tev = self._stick_evts[0]
                lmode, lev = self._stick_evts[1]
                bmode, bev = self._stick_evts[2]
                rmode, rev = self._stick_evts[3]

                # top
                if self._stick_tys is None and y > 0 and y > min(yp + 600, 32200):
                    self._stick_tys = max(0, min(y - 600, 32000))
                    _keypressed(tmode, tev)
                elif self._stick_tys is not None and y <= self._stick_tys:
                    self._stick_tys = None
                    _keyreleased(tmode, tev)

                # left
                if self._stick_lxs is None and x < 0 and x < max(xp - 600, -32200):
                    self._stick_lxs = min(0, max(x + 600, -32000))
                    _keypressed(lmode, lev)
                elif self._stick_lxs is not None and x >= self._stick_lxs:
                    self._stick_lxs = None
                    _keyreleased(lmode, lev)

                # bottom
                if self._stick_bys is None and y < 0 and y < max(yp - 600, -32200):
                    self._stick_bys = min(0, max(y + 600, -32000))
                    _keypressed(bmode, bev)
                elif self._stick_bys is not None and y >= self._stick_bys:
                    self._stick_bys = None
                    _keyreleased(bmode, bev)

                # right
                if self._stick_rxs is None and x > 0 and x > min(xp + 600, 32200):
                    self._stick_rxs = max(0, min(x - 600, 32000))
                    _keypressed(rmode, rev)
                elif self._stick_rxs is not None and x <= self._stick_rxs:
                    self._stick_rxs = None
                    _keyreleased(rmode, rev)


        if len(_pressed):
            self._uip[Modes.Keyboard].pressEvent(_pressed)

        if len(_released):
            self._uip[Modes.Keyboard].releaseEvent(_released)

        for i in list(syn):
            self._uip[i].synEvent()


    def setButtonAction(self, btn, key_event):
        for mode in Modes:
            if self._uip[mode].keyManaged(key_event):
                self._btn_map[btn] = (mode, key_event)
                return

    def setPadButtons(self, pos, key_events, deadzone=0.6, clicked=False):
        """
        Set pad as buttons

        @param Pos pos          designate Left or Right pad
        @param list key_events  list of key events for the pad buttons (top,left,bottom,right)
        @param fload deadzone   portion of the pad in the center dead zone from 0.0 to 1.0
        @param bool clicked     action on touch or on click event
        """

        assert(len(key_events) == 4)
        assert(deadzone >= 0.0 and deadzone < 1.0)

        self._pad_modes[pos] = PadModes.ButtonClick if clicked else PadModes.ButtonTouch

        self._pad_evts[pos] = []
        for ev in key_events:
            for mode in Modes:
                if self._uip[mode].keyManaged(ev):
                    self._pad_evts[pos].append((mode, ev))
                    break

        self._pad_dzones[pos] = 32768 * deadzone

        if clicked:
            if pos == Pos.Left:
                self._btn_map[SCButtons.LPad] = (None, 0)
            else:
                self._btn_map[SCButtons.RPad] = (None, 0)

    def setPadMouse(self, pos,
                    trackball=True,
                    friction=sui.Mouse.DEFAULT_FRICTION,
                    xscale=sui.Mouse.DEFAULT_XSCALE,
                    yscale=sui.Mouse.DEFAULT_XSCALE):
        if not trackball:
            friction = 100.0
        self._uip[Modes.Mouse].updateParams(friction=friction, xscale=xscale, yscale=yscale)
        self._pad_modes[pos] = PadModes.Mouse


    def setPadScroll(self, pos,
                    trackball=True,
                    friction=sui.Mouse.DEFAULT_SCR_FRICTION,
                    xscale=sui.Mouse.DEFAULT_SCR_XSCALE,
                    yscale=sui.Mouse.DEFAULT_SCR_XSCALE):
        if not trackball:
            friction = 100.0
        self._uip[Modes.Mouse].updateScrollParams(friction=friction, xscale=xscale, yscale=yscale)
        self._pad_modes[pos] = PadModes.MouseScroll

    def setPadAxes(self, pos, abs_x_event, abs_y_event, revert):
        self._pad_modes[pos] = PadModes.Axis
        self._pad_evts[pos] = [(Modes.Gamepad, abs_x_event),
                               (Modes.Gamepad, abs_y_event)]
        self._pad_revs[pos] = revert

    def setTrigButton(self, pos, key_event):
        self._trig_modes[pos] = TrigModes.Button
        for mode in Modes:
            if self._uip[mode].keyManaged(key_event):
                self._trig_evts[pos] = (mode, key_event)
                return

    def setTrigAxis(self, pos, abs_event):
        self._trig_modes[pos] = TrigModes.Axis
        self._trig_evts[pos]  = (mode, abs_event)

    def setStickAxes(self, abs_x_event, abs_y_event, revert):
        self._stick_mode = StickModes.Axis
        self._stick_evts = [(Modes.Gamepad, abs_x_event),
                            (Modes.Gamepad, abs_y_event)]
        self._stick_rev  = revert

    def setStickButtons(self, key_events):
        """
        Set stick as buttons

        @param list key_events  list of key events for the pad buttons (top,left,bottom,right)
        """

        assert(len(key_events) == 4)

        self._stick_mode = StickModes.Button

        self._stick_evts = []
        for ev in key_events:
            for mode in Modes:
                if self._uip[mode].keyManaged(ev):
                    self._stick_evts.append((mode, ev))
                    break
