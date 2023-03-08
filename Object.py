from Tool import *
from BytesReader import *
from FAT import *
from NTFS_ import *
import sys

class Object():
    file_object = None
    volume = None
    
    def __init__(self):
        address_name = Tool.input_directory()
        self.file_object = Tool.fileobject_to_read(address_name)
        bootsec_read = read_sector(self.file_object, 0, 1)
        fat32_test = read_bytes_from_buffer(bootsec_read, 0x52, 8)
        ntfs_test = read_bytes_from_buffer(bootsec_read, 3, 4)
        if b'FAT32' in fat32_test:
            self.volume = FATVolume(self.file_object)
            print('FAT32 was detected as a type of format volume')
            
        elif b'NTFS' in ntfs_test:
            self.volume = NTFSVolume(self.file_object)
            print('NTFS was detected as a type of format volume')
            """ Add statement in there to detect NTFS"""
            sys.exit(0)
        print('\n')