from BytesReader import *
import os

class FATVolume():
    name_directory = None
    size = None
    volume_label = None
    file_object = None
    bps = None
    """byte per sector at 0XB, 2 bytes"""
    sc = None
    """sector in cluster at 0XD, 1 byte"""
    sb = None
    """sector in bootsector at 0XE, 2 bytes"""
    nf = None
    """ the amount of FAT table at 0X10, 1 byte"""
    sf = None
    """size of each FAT table at 0X24, 4 bytes"""
    root_cluster = None
    """Cluster beginer of RDET at 0x2C, 4 bytes"""
    data_begin_cluster = None
    """First sector of data, which calculate by sum sb + nf*sf"""
    end_number = None
    """End number to detect a error"""
    size_volume = None
    """
    size of volume is sv = 0 (sv > 65535) at 0x20, 4 bytes
    """
    
    def __init__(self, file_object):
        self.file_object = file_object
        #read boot sector
        bootsec_buffer = read_sector(self.file_object, 0, 1)
        
        #read end number (0xAA55 = 43605)
        #read 2 byte at offset 0x1FA
        self.end_number = read_number_from_buffer(bootsec_buffer, 0x1FE, 2)
        print(self.end_number)
        if self.end_number != 43605:
            print('Invalid boot sector (error because end number not found ar 0x1FE)')
        
        self.bps = read_number_from_buffer(bootsec_buffer, 0xB, 2)
        self.sc = read_number_from_buffer(bootsec_buffer, 0xD, 1)
        self.sb = read_number_from_buffer(bootsec_buffer, 0xE, 2)
        self.nf = read_number_from_buffer(bootsec_buffer, 0x10, 1)
        self.sf = read_number_from_buffer(bootsec_buffer, 0x24, 4)
        self.root_cluster = read_number_from_buffer(bootsec_buffer, 0x2C, 4)
        self.size_volume = read_number_from_buffer(bootsec_buffer, 0x20, 4)
        self.data_begin_cluster = self.sb + self.nf * self.sf
    
    def show_infor_volume(self):
        print('\n')
        print('Information of Volume:')
        print('Bytes per sector (bps): ', self.bps)
        print('Sector per cluster (sc): ', self.sc)
        print('Sector in bootsector (sb): ', self.sb)
        print('Amount of FAT tables (nf): ', self.nf)
        print('Size of each FAT table (sf): ', self.sf)
        print('RDET cluster: ', self.root_cluster)
        print('The first sector in data: ', self.data_begin_cluster)
        print('Size of volume: ', self.size_volume)
        return

        
        
        