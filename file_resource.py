from sys import byteorder
from PIL import Image,ImageDraw
import os
import numpy as np
import copy


def ReadString(file):
    read_string = ""
    initial_pos = file.tell()

    while True:
        byte = file.read(1)
        if int.from_bytes(byte, "little") == 0:
            file.seek(initial_pos)
            return read_string
        else:
            read_string += byte.decode()

#Reads little endian int from file and advances cursor
def readInt(file):
    integer = int.from_bytes(file.read(4), byteorder='little')
    return integer

#Reads little endian short from file and advances cursor
def readShort(file):
    readShort = int.from_bytes(file.read(2), byteorder='little')
    return readShort

#Reads little endian byte from file and advances cursor
def readByte(file):
    readByte = int.from_bytes(file.read(1), byteorder='little')
    return readByte
