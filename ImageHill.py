import sys    
import os
import math
from pathlib import Path
from PIL import Image
import numpy as np
import TIMresource

#CLUT MODES
NO_CLUT = -1
RGB_555 = 0
RGBA_32_PS2 = 1  #0-128 alpha
RGBA_32 = 2      #0-255 alpha
RGBA_5551_PS1 = 3

    #PXL MODES
#Indexed
ONE_BIT = 0
TWO_BIT = 1
FOUR_BIT = 2
EIGHT_BIT = 3
#Direct color
FIFTEEN_BIT_DIRECT = 4
TWENTY_FOUR_BIT_DIRECT = 5
THIRTY_TWO_BIT_DIRECT = 6
SIXTEEN_BIT_PS1_DIRECT = 7
THIRTY_TWO_BIT_PS2_DIRECT = 8


def readPXL(file, offset, width, height, mode, inset=-1):
    file.seek(offset)
    buffer = []
    if mode == EIGHT_BIT:
        #buffer = list(file.read(width*height))
        for y in range(height):
            buffer += list(file.read(width))
            
            if inset != -1:
                file.read(inset) #Skip inset bytes if horizontally stacked image
                
    elif mode == FOUR_BIT:
        for y in range(height):
            for x in range(width//2):
                next_byte = int.from_bytes(file.read(1), "little")
                buffer.append(next_byte&0b1111)
                buffer.append((next_byte&0b11110000)>>4)
            if inset != -1:
                file.read(inset) #Skip inset bytes if horizontally stacked image
    elif mode == SIXTEEN_BIT_PS1_DIRECT or mode == FIFTEEN_BIT_DIRECT:
        for y in range(height):
            for x in range(width):
                buffer.append(int.from_bytes(file.read(2), "little"))
            if inset != -1:
                file.read(inset) #Skip inset bytes if horizontally stacked image
    return buffer

def getColorCount(mode):
    
    if mode == 0:
        count = 2
    elif mode == 1:
        count = 4
    elif mode == 2:
        count = 16
    elif mode == 3:
        count = 256
    else:
        count = 0
        '''
    match mode:
        case 0:#one bit
            count = 2
        case 1:#two bit
            count = 4
        case 2:#four bit
            count = 16
        case 3:#eight bit
            count = 256
        case _:#no clut or unidentified
            count = 0'''

    return count

def changeBase(num, old_base, new_base):
    fraction = num/old_base
    value = math.floor(fraction*new_base)
    return value

def readCLUT(file, offset, n_entries, mode):
    
    buffer = []
    if mode == RGBA_5551_PS1:
        file.seek(offset)
        for x in range(n_entries):
            entry_value = int.from_bytes(file.read(2), "little")
            red   = (entry_value & 0b11111)
            red = changeBase(red, 31, 255)
            green = (entry_value & 0b1111100000) >> 5
            green = changeBase(green, 31, 255)
            blue  = (entry_value & 0b111110000000000) >> 10
            blue = changeBase(blue, 31, 255)
            STP =   (entry_value & 0b1000000000000000) >> 15
            if red == green == blue == STP == 0:
                alpha = 0
            else:
                alpha = 255
            
            buffer.append((red,green,blue,alpha))
    elif mode == RGBA_32_PS2:
        file.seek(offset)
        if n_entries > 16:
            for x in range(n_entries//8):
                #Swizzle
                block_number = x % 4
                if block_number == 0:
                    pass
                elif block_number == 1:
                    file.seek(file.tell() + 4*8)
                elif block_number == 2:
                    file.seek(file.tell() - 4*8*2)
                elif block_number == 3:
                    file.seek(file.tell() + 4*8)
                    
                for y in range(8):
                    entry_value = int.from_bytes(file.read(4), "little")
                    red =    entry_value & 0xFF
                    green = (entry_value & 0xFF00)>>8
                    blue =  (entry_value & 0xFF0000)>>16
                    alpha = (entry_value & 0xFF000000)>>24
                    buffer.append((red, green, blue, min(255, alpha*2)))
        else:
            for x in range(n_entries):
                entry_value = int.from_bytes(file.read(4), "little")
                red =    entry_value & 0xFF
                green = (entry_value & 0xFF00)>>8
                blue =  (entry_value & 0xFF0000)>>16
                alpha = (entry_value & 0xFF000000)>>24
                buffer.append((red, green, blue, min(255, alpha*2)))
    elif mode == NO_CLUT:
        buffer = []
    return buffer


def convertDirectColor(pxl, width, height, color_mode, semitransparency_mode = -1):
    
    if color_mode == SIXTEEN_BIT_PS1_DIRECT:
        im = Image.new("RGBA", (width,height), (0, 0, 0, 0))
        for y in range(height):
            for x in range(width):
                val = pxl[width*y + x]
                red = val & 0b11111
                green = (val & 0b1111100000) >> 5
                blue = (val & 0b111110000000000) >> 10
                semitransparency_flag = (val & 0x8000)
                
                if red == green == blue == semitransparency_flag == 0:
                    pixel =  (red<<3, green<<3, blue<<3, 0)
                else:
                    pixel =  (red<<3, green<<3, blue<<3, 255)
                im.putpixel((x,y), pixel)
    elif color_mode == THIRTY_TWO_BIT_PS2_DIRECT or color_mode == THIRTY_TWO_BIT_DIRECT:
        im = Image.new("RGBA", (width,height), (0, 0, 0, 0))
        for y in range(height):
            for x in range(width):
                val = pxl[width*y + x]
                red    = val & 0xFF
                green = (val & 0xFF00) >> 8
                blue =  (val & 0xFF0000) >> 16
                alpha = (val & 0xFF000000) >> 24
                
                if color_mode == THIRTY_TWO_BIT_DIRECT:
                    pixel = (red, green, blue, alpha)
                else:
                    pixel = (red, green, blue, min(alpha*2, 255))
                im.putpixel((x,y), pixel)
    return im

def getTIM(path, offset, STP_mode=TIMresource.STP_FIFTY_FIFTY):
    file = open(path, 'rb')
    file.read(offset)
    timObj = TIMresource.TIM(file)
    
    if timObj.CF==1:
        cluts = []
        total_colors = (timObj.CLUT.bnum - 0xC)//2
        if timObj.PMD == TIMresource.FOUR_BIT_CLUT:
            palette_colors =  16
        elif timObj.PMD == TIMresource.EIGHT_BIT_CLUT:
            palette_colors =  256
        
        n_cluts = total_colors//palette_colors
        
        for n in range(n_cluts):
            clut = {}
            clut["CLUT_OFFSET"] = timObj.CLUT_offset
            clut["CLUT_FILE"] = path
            clut["CLUT_MODE"] = RGBA_5551_PS1
            if timObj.PMD == TIMresource.FOUR_BIT_CLUT:
                clut["N_COLORS"] = 16
            elif timObj.PMD == TIMresource.EIGHT_BIT_CLUT:
                clut["N_COLORS"] = 256
            else:
                assert False, "Bad PMD mode: " + path
                
            cluts.append(clut)
    
    pxl = {}
    
    pxl["PXL_FILE"] = path
    pxl["PXL_OFFSET"] = timObj.PXL_offset
    
    pxl["HEIGHT"] = timObj.H
    if timObj.PMD == TIMresource.FOUR_BIT_CLUT:
        pxl["WIDTH"] = timObj.W*4
        pxl["PXL_MODE"] = FOUR_BIT
        
    elif  timObj.PMD == TIMresource.EIGHT_BIT_CLUT:
        pxl["WIDTH"] = timObj.W*2
        pxl["PXL_MODE"] = EIGHT_BIT
    elif timObj.PMD == TIMresource.SIXTEEN_BIT_CLUT:
        pxl["WIDTH"] = timObj.W
        pxl["PXL_MODE"] = SIXTEEN_BIT_PS1_DIRECT
        clut = {"CLUT_MODE":NO_CLUT}
        return pxl, [clut]
    
    return pxl, cluts

def extractTIM(path, offset, outfolder, STP_mode=TIMresource.STP_FIFTY_FIFTY):
    pxl, cluts = getTIM(path, offset)
    
    file_stem = Path(path).stem
    
    for clut_number in range(len(cluts)):
        out_path = os.path.join(outfolder, file_stem + "-offset-" + hex(offset) + "-CLUT-" + hex(clut_number) + ".PNG")
        convertImage(pxl, cluts[clut_number], out_path)
        
    return

def injectTIM(path, offset, PNG_path, clut_number = 0):
    pxl, cluts =  getTIM(path, offset)
    injectImage(pxl, cluts[clut_number], PNG_path)
    return

def generateGrayscaleCLUT(clut_mode, n_colors, file_path):

    out_file = open(file_path, "wb")
    buffer = b''
    if clut_mode == RGBA_5551_PS1:
        max_tone = 0b11111
    elif clut_mode == RGBA_32_PS2:
        max_tone = 0xFF
    
    for x in range(n_colors):
        val = (x/(n_colors-1)) * max_tone
        
        if clut_mode == RGBA_5551_PS1:
            byte_1 = max_tone | ((max_tone & 0b111) << 5)
            
            alpha = min(val, 1)
            byte_2 = ((max_tone & 0b11000)) >>3 | (val << 2)
            byte_2 |= alpha << 7
            
            out_file.write(byte_1)
            out_file.write(byte_2)
        elif clut_mode == RGBA_32_PS2:
            out_file.write()
        

    return
    

def convertImage(image_definition, clut_definition, output_path, show_output=False, STP_MODE=TIMresource.STP_OFF):
    image_file = open(image_definition["PXL_FILE"], "rb")
    
    if "PXL_INSET" in image_definition:
        inset = image_definition["PXL_INSET"]
    else:
        inset = -1
    pxl = readPXL(image_file, image_definition["PXL_OFFSET"], image_definition["WIDTH"],image_definition["HEIGHT"], image_definition["PXL_MODE"], inset)
    
    
    if clut_definition["CLUT_MODE"] != NO_CLUT:
        #indexed color
        clut_file = open(clut_definition["CLUT_FILE"], "rb")
        n_clut_entries = getColorCount(image_definition["PXL_MODE"])
        clut = readCLUT(clut_file,clut_definition["CLUT_OFFSET"], n_clut_entries, clut_definition["CLUT_MODE"])
        
        
        im = Image.new("RGBA", (image_definition["WIDTH"],image_definition["HEIGHT"]), (0, 0, 0, 0))

        for y in range(image_definition["HEIGHT"]):
            for x in range(image_definition["WIDTH"]):
                pixel =  clut[pxl[y*image_definition["WIDTH"] + x]]
                im.putpixel((x,y), pixel)
        
        if show_output:
            im.show()
        im.save(output_path)
    else:
        #direct color
        im = convertDirectColor(pxl, image_definition["WIDTH"],image_definition["HEIGHT"], image_definition["PXL_MODE"], semitransparency_mode = -1)
        if show_output:
            im.show()
        im.save(output_path)
    

    return im

def closest(color,colors):
    if color[3] == 0:
        return getAlpha(colors)
    #colors = np.array(colors)
    color = np.array(color)
    
    distances = np.sqrt(np.sum((colors-color)**2,axis=1))
    index_of_smallest = int(np.where(distances==np.amin(distances))[0][0])
    smallest_distance = colors[index_of_smallest]
    return index_of_smallest

def getAlpha(palette):
    for color_num in range(len(palette)):
        if palette[color_num][3] == 0:
            return color_num

    #print("ERROR: ALPHA NOT FOUND!!!!")
    return 0

def injectImage(imagedef, clutdef, png_path, STP_mode=TIMresource.STP_OFF):
    print("Injecting PXL:", imagedef, "\nCLUT:", clutdef, "\nPNG:", png_path,"\n")
    #Open and read clut
    if clutdef["CLUT_MODE"] != NO_CLUT:
        clut_parent_path = clutdef["CLUT_FILE"]
        clut_parent_file = open(clut_parent_path, "rb")
        clut = readCLUT(clut_parent_file, clutdef["CLUT_OFFSET"], clutdef["N_COLORS"], clutdef["CLUT_MODE"])
        clut = np.array(clut)
        pass
    
    #Open pxl
    pxl_parent_path = imagedef["PXL_FILE"]
    pxl_parent_file = open(pxl_parent_path, "r+b")
    pxl_parent_file.seek(imagedef["PXL_OFFSET"])
    
    edited_im = Image.open(png_path).convert("RGBA")
    
    pxl_mode = imagedef["PXL_MODE"]
    if pxl_mode == ONE_BIT:
        #TODO
        pass
    elif pxl_mode == TWO_BIT:
        for y in range(imagedef["HEIGHT"]):
            for x in range(imagedef["WIDTH"]//4):
                x1 = x*4
                y1 = y
                edit_color1 = edited_im.getpixel((x1, y1))
                val1 = closest(edit_color1, clut)
                
                x2 = x*4 + 1
                y2 = y
                edit_color2 = edited_im.getpixel((x2, y2))
                val2 = closest(edit_color2, clut)
                
                x3 = x*4 + 2
                y3 = y
                edit_color3 = edited_im.getpixel((x3, y3))
                val3 = closest(edit_color3, clut)
                
                x4 = x*4 + 3
                y4 = y
                edit_color4 = edited_im.getpixel((x4, y4))
                val4 = closest(edit_color4, clut)
                
                new_byte = val1 | (val2 << 2) | (val3 << 4) | (val4 << 6)
                pxl_parent_file.write(new_byte.to_bytes(1, "little"))
            
            if "PXL_INSET" in imagedef:
                pxl_parent_file.read(imagedef["PXL_INSET"])
    elif pxl_mode == FOUR_BIT:
        for y in range(imagedef["HEIGHT"]):
            for x in range(imagedef["WIDTH"]//2):
                x1 = x*2
                y1 = y
                edit_color1 = edited_im.getpixel((x1, y1))
                val1 = closest(edit_color1, clut)
                
                x2 = x*2 + 1
                y2 = y
                edit_color2 = edited_im.getpixel((x2, y2))
                val2 = closest(edit_color2, clut)
                new_byte = val1 | (val2 << 4)
                pxl_parent_file.write(new_byte.to_bytes(1, "little"))
            
            if "PXL_INSET" in imagedef:
                pxl_parent_file.read(imagedef["PXL_INSET"])
    elif pxl_mode == EIGHT_BIT:
        for y in range(imagedef["HEIGHT"]):
            for x in range(imagedef["WIDTH"]):
                edit_color = edited_im.getpixel((x, y))
                val = closest(edit_color, clut)
                pxl_parent_file.write(val.to_bytes(1, "little"))
                
            if "PXL_INSET" in imagedef:
                pxl_parent_file.read(imagedef["PXL_INSET"])
    elif pxl_mode == SIXTEEN_BIT_PS1_DIRECT:
        for y in range(imagedef["HEIGHT"]):
            for x in range(imagedef["WIDTH"]):
                color = edited_im.getpixel((x, y))
                red = color[0]>>3
                green = color[1] >> 3
                blue = color[2] >> 3
                alpha = color[3]
                if alpha == red == green == blue == 0:
                    stp = 0
                else:
                    stp = 1
                    
                val = red | (green <<5) | (blue << 10) | (stp << 15) #R,G,B
                pxl_parent_file.write(val.to_bytes(2, "little"))
                
            if "PXL_INSET" in imagedef:
                pxl_parent_file.read(imagedef["PXL_INSET"])
    elif pxl_mode == THIRTY_TWO_BIT_PS2_DIRECT:
        for y in range(imagedef["HEIGHT"]):
            for x in range(imagedef["WIDTH"]):
                color = edited_im.getpixel((x, y))
                red = color[0]
                green = color[1]
                blue = color[2]
                alpha = (color[3] + 1) //2
                
                pxl_parent_file.write(red.to_bytes(1, "little"))
                pxl_parent_file.write(green.to_bytes(1, "little"))
                pxl_parent_file.write(blue.to_bytes(1, "little"))
                pxl_parent_file.write(alpha.to_bytes(1, "little"))
                
            if "PXL_INSET" in imagedef:
                pxl_parent_file.read(imagedef["PXL_INSET"])
            
    return