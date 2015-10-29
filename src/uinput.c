/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2015 Stany MARCEL <stanypub@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */


#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/uinput.h>
#include <string.h>
#include <unistd.h>

int uinput_init(
    int key_len, int * key,
    int abs_len, int * abs,
    int vendor, int product,
    char * name)
{
    struct uinput_user_dev uidev;
    int fd;
    int i;

    memset(&uidev, 0, sizeof(uidev));

    fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0)
        return -1;

    strncpy(uidev.name, name, UINPUT_MAX_NAME_SIZE);
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x045e;
    uidev.id.product = 0x028e;
    uidev.id.version = 1;

    if (key_len > 0 && ioctl(fd, UI_SET_EVBIT, EV_KEY) < 0) {
        close(fd);
        return -2;
    }

    for (i = 0; i < key_len; i++) {
        if (ioctl(fd, UI_SET_KEYBIT, key[i]) < 0) {
            close(fd);
            return -4;
        }
    }


    if (abs_len > 0 && ioctl(fd, UI_SET_EVBIT, EV_ABS) < 0) {
        close(fd);
        return -3;;
    }

    for (i = 0; i < abs_len; i++) {

        if (ioctl(fd, UI_SET_ABSBIT, abs[i]) < 0) {
            close(fd);
            return -5;
        }
        uidev.absmin[abs[i]] = -32767;
        uidev.absmax[abs[i]] = 32767;
        uidev.absfuzz[abs[i]] = 0;
    }

    if (write(fd, &uidev, sizeof(uidev)) < 0) {
        close(fd);
        return -6;
    }

    if (ioctl(fd, UI_DEV_CREATE) < 0) {
        close(fd);
        return -7;
    }
    return fd;
}


void uinput_key(int fd, int key, int val)
{
    struct input_event ev;

    memset(&ev, 0, sizeof(ev));
    ev.type = EV_KEY;
    ev.code = key;
    ev.value = val;
    write(fd, &ev, sizeof(ev));
}

void uinput_abs(int fd, int abs, int val)
{
    struct input_event ev;

    memset(&ev, 0, sizeof(ev));
    ev.type = EV_ABS;
    ev.code = abs;
    ev.value = val;
    write(fd, &ev, sizeof(ev));
}

void uinput_syn(int fd)
{
    struct input_event ev;

    memset(&ev, 0, sizeof(ev));
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;
    write(fd, &ev, sizeof(ev));
}

void uinput_destroy(int fd)
{
    ioctl(fd, UI_DEV_DESTROY);
    close(fd);
}
