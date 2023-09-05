from PIL import Image,ImageDraw
import os
import numpy
import copy
import shutil
import numpy as np
from pathlib import Path
import file_resource
import ImageHill
import fill


font_1 = [
                        {
                            "PXL_FILE":"src\\BATTLE\\SYSTEM.DAT",
                            "PXL_OFFSET":0x1aa70,
                            "WIDTH":256,
                            "HEIGHT":220,
                            "PXL_MODE":ImageHill.FOUR_BIT
                        },
                        
                        {
                            "CLUT_FILE":"src\\BATTLE\\SYSTEM.DAT",
                            "N_COLORS":16,
                            "CLUT_OFFSET":0x21970,
                            "CLUT_MODE":ImageHill.RGBA_5551_PS1
                        }
        ]

font_2 = [
                        {
                            "PXL_FILE":"src\\TITLE\\TITLE.PRG",
                            "PXL_OFFSET":0x46b68,
                            "WIDTH":256,
                            "HEIGHT":220,
                            "PXL_MODE":ImageHill.FOUR_BIT
                        },
                        
                        {
                            "CLUT_FILE":"src\\BATTLE\\SYSTEM.DAT",
                            "N_COLORS":16,
                            "CLUT_OFFSET":0x21970,
                            "CLUT_MODE":ImageHill.RGBA_5551_PS1
                        }
        ]


def extractFont():
    ImageHill.convertImage(font_1[0], font_1[1], "font_1.png")
    ImageHill.convertImage(font_2[0], font_2[1], "font_2.png")

def injectFont():
    
    fill.extractFile("bin\\Vagrant Story (USA).bin", "SYSTEM.DAT",   1387, 0x2e000)
    fill.extractFile("bin\\Vagrant Story (USA).bin", "TITLE.PRG",  256000, 0x87800)
    
    ImageHill.injectImage(font_1[0], font_1[1], "font_edit.png")
    ImageHill.injectImage(font_2[0], font_2[1], "font_edit.png")
    
    fill.replaceFile("SYSTEM.DAT", "bin\\Vagrant Story (USA).bin", 1387)
    fill.replaceFile("TITLE.PRG", "bin\\Vagrant Story (USA).bin", 256000)



injectFont()