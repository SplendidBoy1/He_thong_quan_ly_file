from BytesReader import *
from NTFS_ import *
import os

def print_tree(d, tab_level):
        for i in range (tab_level):
                print('\t', end = '')
        print(d.name, end = ' / ')
        print(str(d.size) + ' bytes')
        if 'Directory' in d.attr:
                for i in d.subitem:
                        print_tree(i, tab_level + 1)
        elif 'Archive' in d.attr and d.name.endswith('.txt'):
                for i in range (tab_level):
                        print('\t', end = '')
                print('Content: ', end = ' ')
                print(d.data)

fd = os.open('\\\\.\\E:', os.O_RDONLY | os.O_BINARY)
with os.fdopen(fd, 'rb') as file_object:
        volume = NTFSVolume(file_object)
        volume.root_directory.build_tree()
        print_tree(volume.root_directory, 0)