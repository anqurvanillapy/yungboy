#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse, os, subprocess
from PIL import Image

def parse_argument():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'filename',
        metavar='filename',
        action='store',
        )

    return parser.parse_args()

def convert_to_gba(filename):

    img = Image.open(filename)
    width, height = img.size

    if width > 240 or height > 160:
        print 'error: resolution of image is higher than 240x120'
        return

    pix = img.load()
    data = []

    c_head = '''int main(){const unsigned int targetbmp[%d]={\n''' % (width * height)
    c_eof = '''
};*(unsigned int*)0x04000000=0x0403;int x,y;for(y=0;y<%d;y++){for(x=0;x<=%d;x++){
((unsigned short*)0x06000000)[240*y+x]=targetbmp[%d*y+x];}}while(1);return 0;}
''' % (height, width, width)

    for y in range(height):
        for x in range(width):
            r, g, b = pix[x, y]
            hexstr = convert_to_16color(r, g, b)
            data.append(hexstr)

    ofilename = os.path.splitext(filename)[0] + '.c'

    with open(ofilename, 'w') as filehandle:

        filehandle.write(c_head)
        for item in data:
            filehandle.write(item)
        filehandle.write(c_eof)

    with open('makefile', 'w') as filehandle:

        makefile = '''
PATH := $(DEVKITARM)/bin:$(PATH)

PROJ    := {0}
TARGET  := $(PROJ)

OBJS    := $(PROJ).o

PREFIX  := arm-none-eabi-
CC      := $(PREFIX)gcc
LD      := $(PREFIX)gcc
OBJCOPY := $(PREFIX)objcopy

ARCH    := -mthumb-interwork -mthumb
SPECS   := -specs=gba.specs

CFLAGS  := $(ARCH) -O2 -Wall -fno-strict-aliasing
LDFLAGS := $(ARCH) $(SPECS)


.PHONY : build clean

build: $(TARGET).gba

$(TARGET).gba : $(TARGET).elf
\t$(OBJCOPY) -v -O binary $< $@
\t-@gbafix $@

$(TARGET).elf : $(OBJS)
\t$(LD) $^ $(LDFLAGS) -o $@

$(OBJS) : %.o : %.c
\t$(CC) -c $< $(CFLAGS) -o $@


clean : 
\t@rm -fv *.gba
\t@rm -fv *.elf
\t@rm -fv *.o
'''.format(os.path.splitext(filename)[0])

        filehandle.write(makefile)

    subp = subprocess.Popen(
        ['make'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )

    out, err = subp.communicate()
    if err:
        print err
    else:
        print out

def convert_to_16color(r, g, b):

    # converts to 16-bit RGB values
    r, g, b = int(r / 256.0 * 32), int(g / 256.0 * 32), int(b / 256.0 * 32)
    color = r | (g << 5) | (b << 10)

    return "0x{:04x},".format(color)

if __name__ == '__main__':
    args = parse_argument()
    gbaimg = convert_to_gba(args.filename)