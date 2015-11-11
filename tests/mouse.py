#!/usr/bin/env python

import time
from steamcontroller.uinput import Mouse

m = Mouse()

# move 65536 in 1/4 sec
for i in range(250):
    d = m.moveEvent(65536.0/250.0, 0)
    time.sleep(0.001)

# let the ball roll
t0 = time.time()
dtotal = 0
while d != 0.0:
    d = m.moveEvent(0,0,True)
    dtotal += d
dt = time.time()-t0
print('Intertia time = {:f}, total mvmt = {:d}'.format(dt, int(dtotal)))


print('Set friction to 4.0')
m.updateParams(friction=4.0)

# move 65536 in 1/4 sec
for i in range(250):
    d = m.moveEvent(-65536.0/250.0, 0)
    time.sleep(0.001)

# let the ball roll
t0 = time.time()
dtotal = 0
while d != 0.0:
    d = m.moveEvent(0,0,True)
    dtotal += d
dt = time.time()-t0
print('Intertia time = {:f}, total mvmt = {:d}'.format(dt, int(dtotal)))


print('Set friction to 10.0')
m.updateParams(friction=10.0)

# move 65536 in 1/4 sec
for i in range(250):
    d = m.moveEvent(65536.0/250.0, 0)
    time.sleep(0.001)

# let the ball roll
t0 = time.time()
dtotal = 0
while d != 0.0:
    d = m.moveEvent(0,0,True)
    dtotal += d
dt = time.time()-t0
print('Intertia time = {:f}, total mvmt = {:d}'.format(dt, int(dtotal)))
