import os
import math
import sys

DATA_START = 24
DATA_SECTOR_SIZE = 0x800
SECTOR_SIZE = 2352

   
   
def replaceFile(filePath, targetBin, startSector, startOffset=0):
    injectFile = open(filePath,  'rb')
    targetFile = open(targetBin, 'r+b')

    fileSize = os.path.getsize(filePath)
    bytesRemaining = fileSize
    for x in range(math.ceil(fileSize/DATA_SECTOR_SIZE)):

        targetFile.seek((startSector + x)*SECTOR_SIZE + DATA_START)
        if bytesRemaining <= DATA_SECTOR_SIZE:
            targetFile.write(injectFile.read(bytesRemaining))
            break
        else:
            targetFile.write(injectFile.read(DATA_SECTOR_SIZE))
            bytesRemaining -= DATA_SECTOR_SIZE
    
    injectFile.close()
    targetFile.close()
    

def extractFile(targetBinPath, out_path, startSector, size_in_bytes):
    targetBin = open(targetBinPath,  'rb')
    outFile = open(out_path, 'wb')
    bytesRemaining = size_in_bytes
    
    for x in range(math.ceil(bytesRemaining/DATA_SECTOR_SIZE)):

        targetBin.seek((startSector + x)*SECTOR_SIZE + DATA_START)
        if bytesRemaining <= DATA_SECTOR_SIZE:
            outFile.write(targetBin.read(bytesRemaining))
            break
        else:
            outFile.write(targetBin.read(DATA_SECTOR_SIZE))
            bytesRemaining -= DATA_SECTOR_SIZE
    
    outFile.close()
    targetBin.close()
    
    return


#extractFile("bin\\Vagrant Story (USA).bin", "System_dat_test_out.bin", 1387, 0x2e000)
