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

"""Steam Controller gyro data plot"""

from steamcontroller import SteamController
from PySide import QtGui
import pyqtgraph as pg
import time
import struct

run = True
times = []

def _main():
    app = QtGui.QApplication([])

    win = pg.GraphicsWindow(title="Steam Controller")
    win.resize(1000, 600)
    win.nextRow()

    p1 = win.addPlot(name="plot1", title='Pitch')
    win.nextColumn()

    p2 = win.addPlot(name="plot2", title='Roll')
    p2.setYLink("plot1")
    win.nextColumn()

    p3 = win.addPlot(name="plot3", title='Yaw')
    p3.setYLink("plot1")
    win.nextRow()

    p4 = win.addPlot(name="plot4", title='Others', colspan=5)
    win.nextRow()


    p1.addLegend()
    p1.showGrid(x=True, y=True, alpha=0.5)
    p1.setYRange(-8000, 8000)

    p2.addLegend()
    p2.showGrid(x=True, y=True, alpha=0.5)
    p2.setYRange(-8000, 8000)

    p3.addLegend()
    p3.showGrid(x=True, y=True, alpha=0.5)
    p3.setYRange(-8000, 8000)

    p4.addLegend()
    p4.showGrid(x=True, y=True, alpha=0.5)
    p4.setYRange(-32767, 32767)


    imu = {
        'gpitch' : [],
        'groll'  : [],
        'gyaw'   : [],
        'q1'     : [],
        'q2'     : [],
        'q3'     : [],
        'q4'     : [],
    }

    curves = {
        'gpitch' : p1.plot(times, [], pen=(0, 2), name='vel'),
        'groll'  : p2.plot(times, [], pen=(0, 2), name='vel'),
        'gyaw'   : p3.plot(times, [], pen=(0, 2), name='vel'),
        'q1'     : p4.plot(times, [], pen=(0, 4), name='1'),
        'q2'     : p4.plot(times, [], pen=(1, 4), name='2'),
        'q3'     : p4.plot(times, [], pen=(2, 4), name='3'),
        'q4'     : p4.plot(times, [], pen=(3, 4), name='4'),
    }

    def update(sc, sci):
        global times
        if sci.status != 15361:
            return
        cur = time.time()
        times.append(cur)
        times = [x for x in times if cur - x <= 10.0]

        for name in imu.keys():
            imu[name].append(sci._asdict()[name])
            nt = len(times)
            ni = len(imu[name])
            if nt < ni:
                imu[name] = imu[name][-nt:]
            elif nt > ni:
                times = times[nt-ni:]
            curves[name].setData(times, imu[name])

    app.processEvents()
    sc = SteamController(callback=update)
    sc.handleEvents()
    sc._sendControl(struct.pack('>' + 'I' * 6,
                                0x87153284,
                                0x03180000,
                                0x31020008,
                                0x07000707,
                                0x00301400,
                                0x2f010000))
    def closeEvent(event):
        global run
        run = False
        event.accept()

    win.closeEvent = closeEvent
    app.processEvents()

    try:
        i = 0
        while run:
            i = i + 1
            sc.handleEvents()
            app.processEvents()
    except KeyboardInterrupt:
        print("Bye")


if __name__ == '__main__':
    _main()
