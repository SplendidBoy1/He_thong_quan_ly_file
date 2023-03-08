from BytesReader import *
from FAT import *
from NTFS_ import *
import sys
import os


"""luckytea"""

class menu():
    object = None
    """
    Constructor create menu for 2 options:
    Show information in volumn such as sc, sb, nf, sf, ...
    Show tree of directory and information of their file like .txt, .bin, ...
    """
    
    def __init__(self, object):
        self.object = object
    
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
        self.object.volume.show_infor_volume()
        


