#!/usr/bin/env python

"""Steam Controller USB Dumper"""

import usb1
from collections import namedtuple
import struct

VENDOR_ID  = 0x28de
PRODUCT_ID = 0x1142
ENDPOINT   = 2

STEAM_CONTROLER_FORMAT = [
    ('B',   'ukn_00'),
    ('B',   'ukn_01'),
    ('H',   'status'),
    ('H',   'seq'),
    ('B',   'ukn_02'),
    ('B',   'ukn_03'),
    ('B',   'buttons_00'),
    ('B',   'buttons_01'),
    ('B',   'buttons_02'),
    ('B',   'ltrig'),
    ('B',   'rtrig'),
    ('B',   'ukn_04'),
    ('B',   'ukn_05'),
    ('B',   'ukn_06'),
    ('H',   'lpad_x'),
    ('H',   'lpad_y'),
    ('H',   'rpad_x'),
    ('H',   'rpad_y'),
    ('40p', 'ukn_07'),
]

context = usb1.USBContext()
handle = context.openByVendorIDAndProductID(
    VENDOR_ID, PRODUCT_ID,
    skip_on_error=True,
)

if handle is None:
    raise ValueError('Device not found')

dev = handle.getDevice()
cfg = dev[0]

for inter in cfg:
    for setting in inter:
        number = setting.getNumber()
        if handle.kernelDriverActive(number):
            handle.detachKernelDriver(number)
        if (setting.getClass() == 3 and
            setting.getSubClass() == 0 and
            setting.getProtocol() == 0):
            handle.claimInterface(number)

formats, names = zip(*STEAM_CONTROLER_FORMAT)

SteamController = namedtuple('SteamController', ' '.join(names))

def processReceivedData(transfer):
    if transfer.getStatus() != usb1.TRANSFER_COMPLETED or transfer.getActualLength() != 64:
        return

    data = transfer.getBuffer()
    tup = SteamController._make(struct.unpack('<' + ''.join(formats), data))
    print(tup)
    transfer.submit()

transfer_list = []
transfer = handle.getTransfer()
transfer.setInterrupt(
    usb1.ENDPOINT_IN | ENDPOINT,
    64,
    callback=processReceivedData,
)
transfer.submit()
transfer_list.append(transfer)

try:
    while any(x.isSubmitted() for x in transfer_list):
        try:
            context.handleEvents()
        except usb1.USBErrorInterrupted:
            pass
except KeyboardInterrupt:
    handle.close()
