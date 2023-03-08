from BytesReader import *
from Class import *

class FATVolume():
    main_directory = None
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
        #FAT table
        self.fat_table = read_sector(file_object, self.sb, self.sf, self.bps)
        #Main directory
        rdet_clusters_chain = self.read_cluster_from_fat(self.root_cluster)
        rdet_sector_chain = self.change_cluster_chain_to_sector_chain(rdet_clusters_chain)
        self.rdet_data = read_list_of_sector(self.file_object, rdet_sector_chain, self.bps)
        self.main_directory = FATDirectory(self.rdet_data, '', self, isrdet=True)

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
            n : integer 

        Returns:
            list: a cluster (which combine a lot of sectors)
        """
        #Sign of end in cluster
        end_sign = [0xFFFFFFF, 0xFFFFFF7, 0xFFFFFF8]
        if n in end_sign or n < 2:
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
        name = name.decode('utf-16le')
        
        if name.find('\x00') > 0:
            name = name[:name.find('\x00')]
        return name
            
            
class FATDirectory(Directory):
    """
    Object that illustrate folder in FAT system
    """
    #Define some attributes
    volume = None
    subentries = None
    name = None
    attr = None
    sectors = None
    path_address = None
    cluster_begin = None
    
    def __init__(self, data_buffer, parent_path, volume , isrdet = False, lfn_entries = []):
        #data_buffer: data_buffer that contains information of Directory
        self.volume = volume
        #list of subentries
        self.subentries = None
        
        self.attr = read_number_from_buffer(data_buffer, 0xB, 1)
        if not isrdet:
            if len(lfn_entries) > 0:
                lfn_entries.reverse()
                self.name = FATVolume.read_subentry_to_name(lfn_entries)
                lfn_entries.clear()
            else:
                self.name = read_bytes_from_buffer(data_buffer, 0, 11).decode('utf-8', errors='ignore').strip()
            
            highbyte = read_number_from_buffer(data_buffer, 0x1B, 2)
            lowbyte = read_number_from_buffer(data_buffer, 0x1A, 2)
            self.cluster_begin = highbyte * 0x100 + lowbyte
            self.path_address = parent_path + '/' + self.name
        else:
            self.name = read_bytes_from_buffer(data_buffer, 0, 8)
            self.name += read_bytes_from_buffer(data_buffer, 8, 3)
            self.name = self.name.decode('utf-8')
            self.cluster_begin = self.volume.root_cluster
            self.path_address = ''
            
        chain_cluster = self.volume.read_cluster_from_fat(self.cluster_begin)
        self.sectors = self.volume.change_cluster_chain_to_sector_chain(chain_cluster)
        
    def get_subentries(self):
        """
        Get all the subentries from data part
        """
        if self.subentries != None: 
            return 
        self.subentries = []
        subentry_index = 0

        # Read SDET
        sdet_buffer = read_list_of_sector(self.volume.file_object, self.sectors, self.volume.bps)
        lfn_entries_queue = []

        while True:
            subentry_buffer = read_bytes_from_buffer(sdet_buffer, subentry_index, 32)
            # Read type
            entry_type = read_number_from_buffer(subentry_buffer, 0xB, 1)
            if entry_type & 0x10 == 0x10:
                # Is subdirectory
                isDeleted = read_number_from_buffer(sdet_buffer, subentry_index, 1)
                if isDeleted & 0xE5 == 0xE5:
                    subentry_index += 32
                    lfn_entries_queue.clear()
                    continue
                self.subentries.append(FATDirectory(subentry_buffer, self.path_address, self.volume, lfn_entries=lfn_entries_queue))
            elif entry_type & 0x20 == 0x20:
                # Is archive
                isDeleted = read_number_from_buffer(sdet_buffer, subentry_index, 1)
                if isDeleted & 0xE5 == 0xE5:
                    subentry_index += 32
                    lfn_entries_queue.clear()
                    continue
                self.subentries.append(FATFile(subentry_buffer, self.path_address, self.volume, lfn_entries=lfn_entries_queue))
            elif entry_type & 0x0F == 0x0F:
                # Is support entry
                lfn_entries_queue.append(subentry_buffer)
            if entry_type == 0:
                # EOF
                break
            subentry_index += 32
        
    def show_attr(self):
        check = {
            16: 'D',
            32: 'A',
            1: 'R',
            2: 'H',
            4: 'S',
            8: 'V'
        }

        list_attr = ''
        for attr in check:
            if self.attr & attr == attr:
                list_attr += check[attr]
        return list_attr
        
class FATFile(File):
    volume = None
    name = None
    attr = None
    sectors = None
    path_address = None
    cluster_begin = None
    size = None

    def __init__(self, data_buffer, parent_path, volume = FATVolume, lfn_entries = []):
        
        self.volume = volume

        # Thuộc tính trạng thái
        self.attr = read_number_from_buffer(data_buffer, 0xB, 1)

        # Tên entry 
        if len(lfn_entries) > 0:
            lfn_entries.reverse()
            self.name = FATVolume.read_subentry_to_name(lfn_entries)
            lfn_entries.clear()
        else:
            name_base = read_bytes_from_buffer(data_buffer, 0, 8).decode('utf-8')
            name_ext = read_bytes_from_buffer(data_buffer, 8, 3).decode('utf-8')
            self.name = name_base + '.' + name_ext

        # Phần Word(2 byte) cao
        highbytes = read_number_from_buffer(data_buffer, 0x14, 2)
        # Phần Word (2 byte) thấp
        lowbytes = read_number_from_buffer(data_buffer, 0x1A, 2)

        # Cluster bắt đầu
        self.cluster_begin = highbytes * 0x100 + lowbytes

        # Đường dẫn tập tin
        self.path_address = parent_path + '/' + self.name

        cluster_chain = self.volume.read_cluster_from_fat(self.cluster_begin)
        self.sectors = self.volume.change_cluster_chain_to_sector_chain(cluster_chain)

        # Kích thước tập tin
        self.size = read_number_from_buffer(data_buffer,0x1C,4)
    
    def dump_binary_data(self):
        """
        Trả về mảng các byte của tập tin
        """
        binary_data = read_list_of_sector(self.volume.file_object, self.sectors, self.volume.bps)
        # "trim" bớt cho về đúng kích thước
        return binary_data[:self.size]

    def show_attr(self):
        check = {
            16: 'D',
            32: 'A',
            1: 'R',
            2: 'H',
            4: 'S',
            8: 'V'
        }
        
        list_attr = ''
        for attr in check:
            if self.attr & attr == attr:
                list_attr += check[attr]
        return list_attr