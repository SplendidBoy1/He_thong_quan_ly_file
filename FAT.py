from BytesReader import *
from Class import *
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
    fat_table = None
    """
    FAT table
    """
    rdet_data = None
    
    def __init__(self, file_object):
        self.file_object = file_object
        #read boot sector
        bootsec_buffer = read_sector(self.file_object, 0, 1)
        
        #read end number (0xAA55 = 43605)
        #read 2 byte at offset 0x1FA
        self.end_number = read_number_from_buffer(bootsec_buffer, 0x1FE, 2)
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
        #
        self.fat_table = read_sector(file_object, self.sb, self.sf, self.bps)
        #RDET data
        rdet_clusters_chain = self.read_cluster_from_fat(self.root_cluster)
        rdet_sector_chain = self.change_cluster_chain_to_sector_chain(rdet_clusters_chain)
        self.rdet_data = read_list_of_sector(self.file_object, rdet_sector_chain, self.bps)
    
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
    
    def read_cluster_from_fat(self, n) -> list:
        """Function check from FAT table to find a cluster in one exactly entry, begining which a the n-th cluster that given

        Args:
            n (integer): 

        Returns:
            list: _a cluster (which combine a lot of sectors_
        """
        #Sign of end in cluster
        end_sign = [0xFFFFFFF, 0xFFFFFF7, 0xFFFFFF8]
        if n in end_sign:
            return []
        next_cluster = n
        chain = [next_cluster]
        
        while True:
            next_cluster = read_number_from_buffer(self.fat_table, next_cluster * 4, 4)
            if next_cluster in end_sign:
                break
            else:
                chain.append(next_cluster)
        return chain
        
    def change_cluster_chain_to_sector_chain(self, cluster_chain):
        """Fucntion change a cluster chain to sector chain

        Args:
            cluster_chain (_list_): all cluster which store as a list 
        """
        
        sector_chain = []
        for each_cluster in cluster_chain:
            begin_sector = self.data_begin_cluster + (each_cluster - 2)*self.sc
            for sector in range(begin_sector, begin_sector + self.sc):
                sector_chain.append(sector)
        return sector_chain
            
    @staticmethod
    def read_subentry_to_name(subentries: list):
        """Function  that combine subentries to give information of file or folder

        Args:
            subentries (list): _list of subentries_
        """
        name = b''
        for subentry in subentries:
            name += read_bytes_from_buffer(subentry, 0x1, 10)
            name += read_bytes_from_buffer(subentry, 0xE, 12)
            name += read_bytes_from_buffer(subentry, 0x1C, 4)
        name = name.decode('utf-8')
        if name.find('NULL') > 0:
            name = name[:name.find('NULL')]
        return name
            
            
class FATDirectory(Directory):
    """
    Object that illustrate folder in FAT system
    """
    #Define some attributes
    main_entry_of_rdet = None
    volume = None
    subentries = None
    name = None
    attr = None
    sectors = None
    path_address = None
    cluster_begin = None
    
    def __init__(self, rdet_data, parrent_path, volume, isrdet = False, list_entries = []):
        #rdet_data: main entry
        self.main_entry_of_rdet = rdet_data
        self.volume = volume
        #list of subentries
        self.subentries = None
        
        if not isrdet:
            if len(list_entries) > 0:
                list_entries.reverse()
                self.name = FATVolume.read_subentry_to_name(list_entries)
                list_entries.clear()
            else:
                self.name = read_bytes_from_buffer(self.main_entry_of_rdet, 0, 8)
                self.name += read_bytes_from_buffer(self.main_entry_of_rdet, 8, 3)
                self.name = self.name.decode('utf-8')
            
            self.attr = read_number_from_buffer(self.main_entry_of_rdet, 0xB, 1)
            highbyte = read_number_from_buffer(self.main_entry_of_rdet, 0x1B, 2)
            lowbyte = read_number_from_buffer(self.main_entry_of_rdet, 0x1A, 2)
            self.cluster_begin = highbyte * 0x100 + lowbyte
            self.path_address = parrent_path + '/' + self.name
        else:
            self.name = read_bytes_from_buffer(self.main_entry_of_rdet, 0, 8)
            self.name += read_bytes_from_buffer(self.main_entry_of_rdet, 8, 3)
            self.name = self.name.decode('utf-8')
            self.cluster_begin = self.volume.root_cluster
            self.path = ''
            
        chain_cluster = self.volume.read_cluster_from_fat(self.cluster_begin)
        self.sectors = self.volume.change_cluster_chain_to_sector_chain(self, chain_cluster)
        
    def build_tree(self):
        pass
        
    def show_attr(self):
        check = {
            16: 'D',
            32: 'A',
            1: 'R',
            2: 'H',
            4: 'S',
            8: 'V'
        }
        list_attr = []
        for attr in check:
            if self.attr & attr == attr:
                list_attr.append(check[attr])
        return list_attr
        
class FATFile(File):
    pass