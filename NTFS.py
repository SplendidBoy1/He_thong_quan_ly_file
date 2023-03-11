'''
Tham khảo NTFS:
http://inform.pucp.edu.pe/~inf232/Ntfs/ntfs_doc_v0.5/index.html
https://flatcap.github.io/linux-ntfs/ntfs/index.html
'''

from BytesReader import *
#from AbstractBaseClasses import AbstractVolume, AbstractDirectory, AbstractFile
from Class import *

class NTFSVolume(Volume):
    main_directory = None 
    size = None
    file_object = None

    def __init__(self, file_object):
        self.file_object = file_object

        # Đọc VBR của đĩa
        VBR_buffer = read_sector(self.file_object, 0, 1)

        # Vùng BPB bắt đầu từ offset 0x0B đến 0x53 của VBR

        # Số byte/sector
        self.bps = read_number_from_buffer(VBR_buffer, 0x0B, 2)
        # Số sector/cluster
        self.sc = read_number_from_buffer(VBR_buffer, 0x0D, 1)
        # Số sector để dành
        self.sb = read_number_from_buffer(VBR_buffer, 0x0E, 2)
        # Tổng sector trong ổ đĩa
        self.nv = read_number_from_buffer(VBR_buffer, 0x28, 8)
        # Cluster bắt đầu của MFT
        self.mft_begin = read_number_from_buffer(VBR_buffer, 0x30, 8)
        # Từ đây, muốn truy cập tới MFT entry thứ n, thì tính sector bắt đầu của nó bằng self.sc * self.mft_begin + n * 2

        

        # Không cần đọc buffer của MFT vì kích thước của nó không được nhắc đến
        # Tuy nhiên, chú ý tới MFT entry số 5 là entry mô tả cho thư mục có tên "."
        # Thư mục này chính là thư mục gốc của ổ đĩa theo format NTFS, từ đây ta đi tìm các thư mục/tập tin con của nó để tạo ra cây thư mục
        
        # Đọc thông tin của thư mục gốc tại entry số 5
        # Đọc hai sector từ vị trí của entry số 5
        root_entry_buffer = read_sector(self.file_object, self.mft_begin * self.sc + 5 * 2, 2, self.bps)

        # Đi tìm attribute $FILE_NAME của entry này
        first_attribute = read_number_from_buffer(root_entry_buffer, 0x14, 2)
        list_attr = None
        while(True):
            # Đọc mã attribute đang xét
            type_id = read_number_from_buffer(root_entry_buffer, first_attribute, 4)
            if type_id != 0x30: # $FILE_NAME
                # Nếu khác attribute FILE_NAME thì skip attribute này
                attr_length = read_number_from_buffer(root_entry_buffer, first_attribute + 4, 4)
                first_attribute = first_attribute + attr_length
                continue
            else:
                # Đọc offset đến nội dung attribute FILE_NAME
                offset = read_number_from_buffer(root_entry_buffer, first_attribute + 0x14, 2)
                # Đọc 4 bytes từ offset 0x38 của vùng nội dung để lấy giá trị flag
                flag =  read_number_from_buffer(root_entry_buffer, first_attribute + offset + 0x38, 4)
                list_attr = NTFSDirectory.show_attr(flag)
                break

        # Tạo thư mục gốc, biết size = 0, record number luôn là 5, tên luôn là "." và có list_attr là danh sách các thuộc tính của nó
        self.main_directory = NTFSDirectory('.', 0, list_attr, self.file_object, 5, self.mft_begin, self.sc)
        # Cần sử dụng hàm build_tree() để tạo cây thư mục cho biến này
        # Sau đó dùng biến này để in cây thư mục (mẫu composite OOP)
        
    def show_infor_volume(self):
        print('Volume information:')
        print('Bytes per sector:', self.bps)
        print('Sectors per cluster (Sc):', self.sc)
        print('Reserved sectors (Sb):', self.sb)
        print('Total sectors of logical drive (nv):', self.nv)
        print('MFT begin sector:', self.mft_begin * self.sc)
        print('\n')

class NTFSDirectory(Directory):
    name = None
    size = None
    attr = None
    file_object = None
    record_number = None
    subentries = None
    sectors = None
    mft_begin = None
    sc = None

    def __init__(self, name, size, attr, file_oject, record_number, mft_begin, sc):
        self.name = name
        self.size = size
        self.attr = attr
        self.file_object = file_oject
        self.record_number = record_number
        self.mft_begin = mft_begin
        self.sc = sc

        # Tính sector mà entry của directory này chiếm
        self.sectors = [self.mft_begin * self.sc + self.record_number * 2, self.mft_begin * self.sc + self.record_number * 2 + 1]

    def get_subentries(self):
        '''
        Hàm dò attribute $INDEX_ROOT và $INDEX_ALLOCATION (nếu có) của một directory entry
        Đọc các index entry mô tả trong attribute và thêm các item vào biến subentries
        Trong trường hợp số index entry đủ để chứa trong MFT entry thì MFT entry này sẽ chỉ có $INDEX_ROOT
        Ngược lại, các index entry sẽ được lưu ở vùng nhớ non-resident, được mô tả trong $INDEX_ALLOCATION được thêm ngay sau $INDEX_ROOT
        '''
        # Đi tìm attribute $INDEX_ROOT của entry mô tả thư mục này
        if self.subentries != None:
            return
        
        self.subentries = []
        entry_buffer = read_sector(self.file_object, self.mft_begin * self.sc + self.record_number * 2, 2, 512)
        first_attribute = read_number_from_buffer(entry_buffer, 0x14, 2)
        while(True):
            # Đọc mã attribute đang xét
            type_id = read_number_from_buffer(entry_buffer, first_attribute, 4)
            attr_length = read_number_from_buffer(entry_buffer, first_attribute + 4, 4)
            if type_id != 0x90:
                # Nếu khác attribute INDEX_ROOT thì skip attribute này
                first_attribute = first_attribute + attr_length
                continue
            else:
                # Đọc offset đến nội dung attribute INDEX_ROOT
                offset = read_number_from_buffer(entry_buffer, first_attribute + 0x14, 2)

                # Hai phần đầu của nội dung INDEX_ROOT là Index Root (16 bytes) và Index Header (16 bytes)
                # Ta chỉ quan tâm giá trị flags trong Index Header (offset 0x0C tính từ đầu Index Header)
                # Nếu flag là 0x00, các index là resident và nằm ngay sau Index Header
                # Nếu flag là 0x01, các index là non-resident và nằm ở cluster được quy định bởi attribute kế tiếp là $INDEX_ALLOCATION
                flag = read_number_from_buffer(entry_buffer, first_attribute + offset + 16 + 0x0C, 1)
                if flag == 0x00:
                    # Bảng index entry phía sau Index Header bao gồm nhiều entry, mỗi index entry cho thông tin về:
                    #   Mã record number của file đang xét
                    #   Mã record number của thư mục cha
                    #   Kích thước file
                    #   Flag của file
                    #   Tên của file
                    # Do đó, chỉ cần đọc index entry là đã có đầy đủ những thông tin cơ bản của file

                    # Đọc kích thước của bảng index entry
                    size = read_number_from_buffer(entry_buffer, first_attribute + offset + 16 + 0x04, 4)
                    cur_pos = 32
                    while(True):
                        # 8 byte đầu là mã record number (6 byte) và sequence (2 byte) của file đang xét
                        record_number = read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos, 6)
                        # 2 byte kế là kích thước entry này
                        entry_size = read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x08, 2)
                        # Từ offset 0x10 lấy 8 byte là mã record number (6 byte) và sequence (2 byte) của thư mục cha
                        parrent_record_number = read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x10, 6)
                        
                        if (parrent_record_number == self.record_number):
                            # Đọc kích thước file
                            file_size = read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x40, 8)
                            # Đọc flag và dịch thành list các attribute
                            list_attr = NTFSDirectory.show_attr(read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x48, 8))
                            # Đọc độ dài tên file
                            name_size = read_number_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x50, 1) * 2
                            # Đọc tên file
                            name = read_string_from_buffer(entry_buffer, first_attribute + offset + cur_pos + 0x52, name_size).replace('\x00', '')

                            # Xác định item cần thêm vào subitem là directory hay file, với điều kiện không phải file hệ thống
                            if 'S' not in list_attr:
                                if 'D' in list_attr:
                                    self.subentries.append(NTFSDirectory(name, file_size, list_attr, self.file_object, record_number, self.mft_begin, self.sc))
                                elif 'A' in list_attr:
                                    self.subentries.append(NTFSFile(name, file_size, list_attr, self.file_object, record_number, self.mft_begin, self.sc))

                        cur_pos = cur_pos + entry_size
                        if(size - cur_pos < 88):
                            break
                elif flag == 0x01:
                    # Các index entry giờ được lưu ở vùng nhớ cho non-resident
                    # Để xác định nó, ta tìm attribute FILE_ALLOCATION, nằm ngay sau FILE_ROOT
                    first_attribute = first_attribute + attr_length
                    # Đọc offset đến phần data runs của INDEX_ALLOCATION
                    offset = read_number_from_buffer(entry_buffer, first_attribute + 0x20, 2)
                    # Phần data runs gồm 3 - 8 bytes, trong đó cần chú ý đến cluster count (byte thứ 2) và first cluster (byte thứ 3 - 8)
                    cluster_count = read_number_from_buffer(entry_buffer, first_attribute + offset + 0x01, 1)
                    first_cluster = read_number_from_buffer(entry_buffer, first_attribute + offset + 0x02, 6)
                    # Lập list các sector cần đọc
                    sector_list = []
                    for i in range (first_cluster * self.sc, (first_cluster + cluster_count) * self.sc):
                        sector_list.append(i)
                    entry_buffer = read_list_of_sector(self.file_object, sector_list, 512)

                    # Tại offset 0x18 lấy 4 byte là offset đến entry đầu tiên
                    # Tại offset 0x1C lấy 4 byte là kích thước của bảng index entry
                    first_entry_offset = read_number_from_buffer(entry_buffer, 0x18, 4)
                    size = read_number_from_buffer(entry_buffer, 0x1C, 4)
                    cur_pos = 24 + first_entry_offset
                    while(True):
                        # 8 byte đầu là mã record number (6 byte) và sequence (2 byte) của file đang xét
                        record_number = read_number_from_buffer(entry_buffer, cur_pos, 6)
                        # 2 byte kế là kích thước entry này
                        entry_size = read_number_from_buffer(entry_buffer, cur_pos + 0x08, 2)
                        # Từ offset 0x10 lấy 8 byte là mã record number (6 byte) và sequence (2 byte) của thư mục cha
                        parrent_record_number = read_number_from_buffer(entry_buffer, cur_pos + 0x10, 6)
                        
                        if (parrent_record_number == self.record_number):
                            # Đọc kích thước file
                            file_size = read_number_from_buffer(entry_buffer, cur_pos + 0x40, 8)
                            # Đọc flag và dịch thành list các attribute
                            list_attr = NTFSDirectory.show_attr(read_number_from_buffer(entry_buffer, cur_pos + 0x48, 8))
                            # Đọc độ dài tên file
                            name_size = read_number_from_buffer(entry_buffer, cur_pos + 0x50, 1) * 2
                            # Đọc tên file
                            name = read_string_from_buffer(entry_buffer, cur_pos + 0x52, name_size).replace('\x00', '')

                            # Xác định item cần thêm vào subitem là directory hay file, với điều kiện không phải file hệ thống
                            if 'S' not in list_attr:
                                if 'D' in list_attr:
                                    self.subentries.append(NTFSDirectory(name, file_size, list_attr, self.file_object, record_number, self.mft_begin, self.sc))
                                elif 'A' in list_attr:
                                    self.subentries.append(NTFSFile(name, file_size, list_attr, self.file_object, record_number, self.mft_begin, self.sc))

                        cur_pos = cur_pos + entry_size
                        if(size - cur_pos < 88):
                            break
            break         

    # def get_subentries(self):
    #     '''
    #     Hàm tạo cây thư mục, bắt đầu từ thư mục gốc "."
    #     Sử dụng hàm check_index_entry để thêm vô biến subentries danh sách các thư mục/tập tin con
    #     Sau đó duyệt qua danh sách thư mục/tập tin con, nếu phần tử đó là thư mục, đệ quy hàm này cho thư mục đó
    #     '''
    #     self.check_index_entry()
    #     for item in self.subitem:
    #         if 'Directory' in item.attr:
    #             item.get_subentries()
    #         elif 'Archive' in item.attr and item.name.endswith('.txt'):
    #             print(item.name)
    #             item.get_data()     

    @staticmethod
    def show_attr(flag) -> str:
        flags = {
            0x0001 : 'R',
            0x0002 : 'H',
            0x0004 : 'S',
            0x0020 : 'A',
            0x10000000 : 'D'
        }
        list_attr = ''
        for item in flags:
            if flag & item == item:
                list_attr += flags[item]
        return list_attr

class NTFSFile(File):
    name = None
    size = None
    attr = None
    file_object = None
    record_number = None
    sectors = None
    mft_begin = None
    sc = None
    data = None

    def __init__(self, name, size, attr: list, file_oject, record_number, mft_begin, sc):
        self.name = name
        self.size = size
        self.attr = attr
        self.file_object = file_oject
        self.record_number = record_number
        self.mft_begin = mft_begin
        self.sc = sc

        # Tính sector mà entry của file này chiếm
        self.sectors = [self.mft_begin * self.sc + self.record_number * 2, self.mft_begin * self.sc + self.record_number * 2 + 1]

    def show_attr(flag) -> str:
        return NTFSDirectory.show_attr(flag)

    def dump_binary_data(self):
        '''
        Hàm đọc dữ liệu cho file có định dạng txt
        Để xài hàm này cần 2 điều kiện: trong biến attr có chứa 'Archive' và tên file kết thúc bằng '.txt'
        Hàm bao gồm việc xử lý khi data thuộc vùng non-resident
        '''
        # Đi tìm attribute $DATA của MFT entry này
        entry_buffer = read_sector(self.file_object, self.mft_begin * self.sc + self.record_number * 2, 2, 512)
        first_attribute = read_number_from_buffer(entry_buffer, 0x14, 2)
        while(True):
            # Đọc mã attribute đang xét
            type_id = read_number_from_buffer(entry_buffer, first_attribute, 4)
            attr_length = read_number_from_buffer(entry_buffer, first_attribute + 4, 4)
            if type_id != 0x80:
                # Nếu khác attribute DATA thì skip attribute này
                first_attribute = first_attribute + attr_length
                continue
            else:
                # Đọc cờ non-resident của attribute header
                non_resident = read_number_from_buffer(entry_buffer, first_attribute + 0x08, 1)
                # Check cờ non-resident, nếu = 0 thì dữ liệu nằm ngày sau phần attribute header, độ dài bằng size của file
                if(non_resident == 0x00):
                    # Đọc offset đến nội dung attribute DATA
                    offset = read_number_from_buffer(entry_buffer, first_attribute + 0x14, 2)
                    self.data = read_bytes_from_buffer(entry_buffer, first_attribute + offset, self.size).decode('utf-8','ignore')
                # Nếu = 1, dữ liệu file nằm ở vùng nhớ non-resident, sau phần attribute header sẽ là data run, 
                elif(non_resident == 0x01):
                    # Đọc offset đến phần data run của attribute DATA
                    offset = read_number_from_buffer(entry_buffer, first_attribute + 0x20, 2)
                    # Phần data runs gồm 3 - 8 bytes, trong đó cần chú ý đến cluster count (byte thứ 2) và first cluster (byte thứ 3 - 8)
                    cluster_count = read_number_from_buffer(entry_buffer, first_attribute + offset + 0x01, 1)
                    first_cluster = read_number_from_buffer(entry_buffer, first_attribute + offset + 0x02, 6)
                    # Lập list các sector cần đọc
                    sector_list = []
                    for i in range (first_cluster * self.sc, (first_cluster + cluster_count) * self.sc):
                        sector_list.append(i)
                    entry_buffer = read_list_of_sector(self.file_object, sector_list, 512)
                    # Đọc data file
                    self.data = read_bytes_from_buffer(entry_buffer, 0, self.size).decode('utf-8','ignore')
                    return self.data
            break