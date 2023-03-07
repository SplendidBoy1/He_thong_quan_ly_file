from BytesReader import *
from FAT import *
from NTFS import *
import sys
import os


"""luckytea"""

class menu():
    file_object = None
    volume = None
    """
    Constructor create menu for 2 options:
    Show information in volumn such as sc, sb, nf, sf, ...
    Show tree of directory and information of their file like .txt, .bin, ...
    """
    
    def __init__(self):
        address_name = input_directory()
        self.file_object = fileobject_to_read(address_name)
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
    
    def show(self):
        print('MENU')
        print('1. Show information of volume')
        print('2. Show a tree of directory')
        print('3. Exit program')
        n = input('Input the a number to use option respectively: ')
        match n:
            case '1':
                self.show_infor()
            case '2':
                self.show_tree()
            case '3':
                return
    
    def show_infor(self):
        self.volume.show_infor_volume()
    
    def show_tree(self):
        self.volume.main_directory.get_subentries()
        for subentry in self.volume.main_directory.subentries:
            print(subentry.name)

        

def input_directory():
    """Function will input a directory and return a path

    Returns:
        String: volumn path
    """
    os_name = os.name
    if os_name not in ['nt', 'posix']:
        print('Detect a unsupported platform of operating system, just support of WINDOW NT and POSIX')
        return None
    else:
        print('PLEASE SELECT YOUR VOLUME')
        if os_name == 'nt':
            print('Detected Windows NT platform')
            print('Enter one CAPITAL LETTER of Volume')
            while True:
                name_volume = input('=> Enter your address path:')
                if name_volume.isupper():
                    break
                else:
                    continue
            address_path = '\\\\.\\' + name_volume + ':'
        else:
            print('Enter the path of the volume. Exp: /dev/disk1, ...')
            address_path = input('=> Enter your address path')
        print(address_path)
        print('\n')
        return address_path
            
def fileobject_to_read(address_path):
    """Function create a fileobject to read a data like bootsector, FAT, ...

    Args:
        address_path (String): _a address of drive path_

    Returns:
        _Object_: 
    """
    os_name = os.name
    if os_name == 'nt':
        fd = os.open(address_path, os.O_RDONLY | os.O_BINARY)
    else:
        fd = os.open(address_path, os.O_RANDOM)
    return os.fdopen(fd, 'rb')

