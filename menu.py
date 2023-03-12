from BytesReader import *
from FAT import *
from NTFS import *
import os

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
            print('2. Show a directory tree with file\'s information')
            print('3. Exit program')
            n = input('Input a number to use the respective option: ')
            os.system('cls')
            match n:
                case '1':
                    self.show_infor()
                case '2':
                    self.show_directory(self.object.volume.main_directory)
                case '3':
                    return
            os.system('cls')
    
    
    def show_infor(self):
        self.object.volume.show_infor_volume()
        os.system('pause')
    
    def show_directory(self, entry, n = 0, isrdet = True):
        format_str = '{0: <30} {1: <8} {2: <8} {3: <8}\n'
        if isrdet:
            print_str = format_str.format('NAME', 'SIZE', 'ATTR', 'SECTOR')
            print(print_str)

        if entry.name == 'System Volume Information':
            return
        else:
            entry.get_subentries()

        for subentry in entry.subentries:
            if subentry.name == '.' or subentry.name == '..':
                continue

            subentry_info = {
                'name': ' ' * n + ('- ' if n != 0 else '') + subentry.name, 
                'size': '' if isinstance(subentry, Directory) else subentry.size, 
                'attr': subentry.show_attr() if isinstance(subentry, FATVolume) else subentry.attr,
                'sector': '' if len(subentry.sectors) == 0 else subentry.sectors[0]
            }

            print_str = format_str.format(subentry_info['name'], subentry_info['size'], subentry_info['attr'], subentry_info['sector'])
            print(print_str)

            if isinstance(subentry, (FATFile, NTFSFile)):
                continue    
            self.show_directory(subentry, n+1, False)
        if isrdet:
            self.file_interact(entry)

    def file_interact(self, entry):
        print('1. Go into a directory')
        print('2. View data of an archive')

        choice = input('Enter choice (1, 2 or others to go back): ')

        if choice == '1':
            check = 0
            dirName = input('Input directory name: ')
            os.system('cls')
            for directory in entry.subentries:
                if directory.name == dirName and isinstance(directory, Directory):
                    check = 1
                    self.show_directory(directory)
                    self.show_directory(entry)
                    break
            if not check: 
                print('Incorrect name or subject is not a directory!')
                self.show_directory(entry)
        elif choice == '2':
            check = 0
            fileName = input('Input file\'s name (including extension, eg: text.txt): ')
            os.system('cls')
            for file in entry.subentries:
                if file.name == fileName and '.txt' in fileName:
                    check = 1
                    data = file.dump_binary_data()
                    print('\nText file data:\n' + data + '\n')
                    os.system('pause')
                    self.show_directory(entry)
                    break
            if not check:
                print('Incorrect name or subject is not a text file!')
                self.show_directory(entry)