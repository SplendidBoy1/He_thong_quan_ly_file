from BytesReader import *
from FAT import *
from NTFS_ import *


"""luckytea"""

class menu():
    object = None
    """
    Constructor create menu for 2 options:
    Show information in volumn such as sc, sb, nf, sf, ...
    Show information of directory 
    Show tree directory
    """
    
    def __init__(self, object):
        self.object = object
    
    def show(self):
        while(True):
            
            print('MENU')
            print('1. Show information of volume')
            print('2. Show a information of directory')
            print('3. Exit program')
            n = input('Input the a number to use option respectively: ')
            match n:
                case '1':
                    self.show_infor()
                case '2':
                    self.show_directory()
                case '3':
                    return
            print('\n')
    
    def show_infor(self):
        self.object.volume.show_infor_volume()
        
    def show_directory(self):
        self.object.current_dir.build_dir_tree()
        self.object.volume.create_table_directory(self.object.current_dir)
        
        
        

