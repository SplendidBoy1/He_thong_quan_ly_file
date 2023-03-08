from abc import *
import os

class Tool():
    
    @staticmethod
    def input_directory():
        """
        Function will input a directory and return a path

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
    
    @staticmethod
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