from BytesReader import *
from Class import *
import os

class FATVolume():
    name_directory = None
    size = None
    volume_label = None
    file_object = None
    root_directory = None
    bps = None
    """byte per sector at 0XB, 2 bytes"""
    sc = None
    """sector in cluster at 0XD, 1 byte"""
    sb = None
    """The amount of sectors after bootsector at 0XE, 2 bytes"""
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
    size of volume at 0x20, 4 bytes
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
        self.root_directory = FATDirectory(self.rdet_data, '', self, isrdet=True)
        print(self.root_directory.sectors)
    
    def show_infor_volume(self):
        print('\n')
        print('Information of Volume:')
        print('Bytes per sector (bps): ', self.bps)
        print('Sector per cluster (sc): ', self.sc)
        print('Amount of sectors in bootsector (sb): ', self.sb)
        print('Amount of FAT tables (nf): ', self.nf)
        print('Size of each FAT table (sf): ', self.sf)
        print('RDET cluster: ', self.root_cluster)
        print('The first sector in data: ', self.data_begin_cluster)
        print('Size of volume: ', self.size_volume)
        return
    
    def create_table_directory(self, current_dir):
        entry_list = []
        
        map_infor = dict()
        #Define a map to store each information of each cluster
        
        for entry in current_dir.subentries:
            if len(entry.sectors) == 0:
                Sector = ''
            else:
                Sector = entry.sectors[0]
            if hasattr(entry, 'size'):
                Size = entry.size
            else:
                Size = 0
            entry_info = {
                'name' : entry.name,
                'size': Size,
                'attr': entry.show_attr(),
                'sector': Sector
            }
            if entry_info['name'] in ('.', '..'):
                continue
        entry_list.append(entry_info)
        
        for entry in entry_list:
            print('name: ', entry['name'])
        
    
    def show_directory():
        
        pass
    
    def show_tree(self):
        
        pass
    
    def read_cluster_from_fat(self, n) -> list:
        """Function check from FAT table to find a cluster in one exactly entry, begining which a the n-th cluster that given

        Args:
            n (integer): 

        Returns:
            list: _a cluster (which combine a lot of sectors_
        """
        #Sign of end in cluster
        end_sign = [0xFFFFFFF, 0xFFFFFF7, 0xFFFFFF8, 0x00000000]
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
            
        name = name.decode('utf-8', errors='ignore')
        if name.find('\x00') > 0:
            name = name[:name.find('\x00')]
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
    
    
    def __init__(self, main_entry, parrent_path, volume, isrdet = False, list_entries = []):
        self.main_entry_of_rdet = main_entry
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
            self.attr = read_number_from_buffer(self.main_entry_of_rdet, 0xB, 1)
            self.cluster_begin = self.volume.root_cluster
            self.path = ''
            
        cluster_chain = self.volume.read_cluster_from_fat(self.cluster_begin)
        self.sectors = self.volume.change_cluster_chain_to_sector_chain(cluster_chain)
        
    def build_dir_tree(self):
        if self.subentries != None:
            return
        self.subentries = list()
        count_subentry = 0
        
        #Read SDET (a cluster data of folder or file)
        sdet_data = read_list_of_sector(self.volume.file_object, self.sectors, self.volume.bps)
        entries_queue = []
        
        while True:
            subentry_data = read_bytes_from_buffer(sdet_data, count_subentry, 32)
            entry_type = read_number_from_buffer(subentry_data, 0xB, 1)
            if entry_type & 16 == 16:
                # Folder
                self.subentries.append(FATDirectory(subentry_data, self.path, self.volume, entries_queue))
            elif entry_type & 32 == 32:
                # File
                self.subentries.append(FATFile(subentry_data, self.path, self.volume, entries_queue))
            elif entry_type & 0x0F == 0x0F:
                entries_queue.append(subentry_data)
            if entry_type == 0:
                break
            count_subentry += 32
        
        
    def show_attr(self):
        check = {
            0x10: 'D',
            0x20: 'A',
            0x01: 'R',
            0x02: 'H',
            0x04: 'S',
            0x08: 'V'
        }
        list_attr = ''
        for attr in check:
            if self.attr & attr == attr:
                list_attr += check[attr]
        return list_attr
        
class FATFile(File):
    main_entry_of_rdet = None
    volume = None
    subentries = None
    name = None
    attr = None
    sectors = None
    path_address = None
    size = None
    
    def __init__(self, main_entry, parrent_path, volume, isrdet = False, list_entries = []):
        self.main_entry_of_rdet = main_entry
        self.volume = volume
        
        #attributes
        self.attr = read_number_from_buffer(self.main_entry_of_rdet, 0xB, 1)
        
        #name
        if len(list_entries) > 0:
            list_entries.reverse()
            self.name = FATVolume.read_subentry_to_name(list_entries)
            list_entries.clear()
        else:
            self.name = read_bytes_from_buffer(self.main_entry_of_rdet, 0, 8).decode('utf-8', errors='ignore').strip()
            self.name += '.'
            self.name += read_bytes_from_buffer(self.main_entry_of_rdet, 8, 3).decode('utf-8', errors='ignore').strip()
            
        self.attr = read_number_from_buffer(self.main_entry_of_rdet, 0xB, 1)
        highbyte = read_number_from_buffer(self.main_entry_of_rdet, 0x1B, 2)
        lowbyte = read_number_from_buffer(self.main_entry_of_rdet, 0x1A, 2)
        self.cluster_begin = highbyte * 0x100 + lowbyte
        self.path_address = parrent_path + '/' + self.name
        chain_cluster = self.volume.read_cluster_from_fat(self.cluster_begin)
        self.sectors = self.volume.change_cluster_chain_to_sector_chain(chain_cluster)
        
        #Size of file
        self.size = read_number_from_buffer(self.main_entry_of_rdet, 0x1C, 4)
        
        
    
    def show_attr(self):
        check = {
            0x10: 'D',
            0x20: 'A',
            0x01: 'R',
            0x02: 'H',
            0x04: 'S',
            0x08: 'V'
        }
        list_attr = ''
        for attr in check:
            if self.attr & attr == attr:
                list_attr += check[attr]
        return list_attr
        
    
        