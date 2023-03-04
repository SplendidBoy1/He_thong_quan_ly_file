from LowLevel_ import *
from datetime import datetime, timedelta

ATTR_NAME = 48
EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time


class NTFSVolume():
    # Override các abstract attribute
    # Trong python để "khai báo" là mình sẽ override các abstract attribute của class cha thì mình khởi tạo giá trị đầu cho nó (ở đây khởi tạo là None [giống null của C++])
    root_directory = None
    size = None
    volume_label = None
    file_object = None

    def __init__(self, file_object):
        """
        Constructor nhận vào 1 tham số là `file_object`, là một Python file object.
        """
        self.file_object = file_object

        # Đọc partition boot sector
        PBS_buffer = read_sectors(self.file_object, 0, 1)  # đọc sector thứ 0 (sector đầu tiên) và đọc 1 sector

        # Đọc số byte/sector
        self.sector_size = read_number_buffer(PBS_buffer, 0x0B, 2)

        # Đọc số sector/cluster
        self.sc = read_number_buffer(PBS_buffer, 0x0D, 1)

        # Đọc số sector để dành
        self.sb = read_number_buffer(PBS_buffer, 0x0E, 2)

        # Đọc tổng sector trong Volume
        self.nv = read_number_buffer(PBS_buffer, 0x28, 8)

        # Vị trí bắt đầu của MFT
        self.mft_begin = self.sc * read_number_buffer(PBS_buffer, 0x30, 8)
        
        #Vị trí bắt đầu của MFT dự phòng
        self.mft_mir = self.sc * read_number_buffer(PBS_buffer, 0x38, 8)
        
        # Đọc Bảng MFT
        self.mft_table = read_sectors(self.file_object, self.mft_begin, 1)

        print('Volume information:')
        print('Bytes per sector:', self.sector_size)
        print('Sectors per cluster (Sc):', self.sc)
        print('Reserved sectors (Sb):', self.sb)
        print('Sector number of logical drive (nv):', self.nv)
        print('MFT begin sector:', self.mft_begin)
        print('MFT Mirror begin sector:', self.mft_mir)
        print('\n')

    def clusterChainToSectors(self, clusterChain):
        # Hàm đổi danh sách các cluster thành danh sách các sector
        sectors = []
        for cluster in clusterChain:
            for i in range(self.sc):
                sectors.append(cluster * self.sc + i)
        return sectors

    def readInfoEntry(self):
        sectorsIndex = 0
        skipped_entry = 0

        while (sectorsIndex < self.nv):
            skipped = False
            attrTypeID = 99
            attribOffset = 20   # 0x14

            # mỗi lần duyệt 2 sector <=> 1024 bytes
            buffer = read_sectors(self.file_object, self.mft_begin + sectorsIndex, 2)

            # Đọc chữ ký entry 
            signature = read_bytes_buffer(buffer, 0, 4)
            if signature != b'FILE':
                sectorsIndex += 2
                skipped_entry += 1

                if skipped_entry > 100:
                    break

                continue

            # Tổng số byte đã đọc của MFT entry
            totalBytesRead = 0
            # Đọc nơi bắt đầu (offset) của phần nội dung (attr đầu đọc tại byte thứ 20-21)
            attribOffset = read_number_buffer(buffer, attribOffset, 2)

            while True:
                # Đọc mã loại attribute byte thứ 0-3
                attrTypeID = read_number_buffer(buffer, attribOffset, 4)
                # Mã loại: 0xFFFFFF: kết thúc MFT entry (hoặc đã đọc sang mft entry khác)
                if attrTypeID in (0xFFFFFFFF, 0x0) or totalBytesRead >= 1024:
                    break

                # Đọc kích thước attribute byte thứ 4-7
                attrLength = read_number_buffer(buffer, attribOffset + 4, 4)
                totalBytesRead += attrLength

                # Đọc kiểu attribite (resident non-resident)
                resident = read_number_buffer(buffer, attribOffset + 8, 1)

                if (resident > 1):
                    break

                # Đọc kích thước của phần nội dung attribute, đọc byte thứ 16-19
                contentSize = read_number_buffer(buffer, attribOffset + 16, 4)
                # Đọc nơi bắt đầu (offset) của phần nội dung attribute, đọc tại byte thứ 20-21)
                contentOffset = read_number_buffer(buffer, attribOffset + 20, 2)

                if (attrTypeID == ATTR_NAME):  # Attribute loại $FILE_NAME
                    # Đọc chiều dài tên tại byte thứ 64 (từ phần nội dung attr)
                    nameLength = read_number_buffer(buffer, attribOffset + contentOffset + 64, 1)
                    # Đọc tên tại byte thứ 66 (từ phần nội dung attr)
                    name = read_bytes_buffer(buffer, attribOffset + contentOffset + 66, nameLength * 2)
                    name = name.decode('utf-16le')

                    if name.startswith('$'):
                        skipped = True
                        break

                    # thời gian tạo tập tin, đọc byte thứ 8-15
                    timeCreate = self.filetime_to_dt(read_number_buffer(buffer, attribOffset + contentOffset + 8, 8))
                    # thời gian tập tin có sự thay đổi, đọc byte thứ 16-23
                    timeModified = self.filetime_to_dt(read_number_buffer(buffer, attribOffset + contentOffset + 16, 8))
                    # thời gian truy cập tập tin mới nhất, đọc byte thứ 32-39
                    timeAccessed = self.filetime_to_dt(read_number_buffer(buffer, attribOffset + contentOffset + 32, 8))

                fileRealSize = 0
                if (attrTypeID == 0x80):  # Attribute loại $DATA
                    # Nếu data là resident
                    if resident == 0:
                        # Nếu $DATA là resident thì kích thước file chính là kích thước của attribute trong MFT entry
                        fileRealSize = contentSize
                        # Đọc phần nội dung
                        fileContent = read_bytes_buffer(buffer, attribOffset + contentOffset, contentSize)
                        # Sector bắt đầu cũng chính là số sector của attribute
                        fileSector = sectorsIndex
                    # Nếu data là non-resident
                    elif resident == 1:
                        fileRunsOffset = read_number_buffer(buffer, attribOffset + 0x20, 2)
                        # Nếu attribute là nonresident thì nó có chứa thêm size thực của attribute
                        fileRealSize = read_number_buffer(buffer, attribOffset + 0x30, 7)
                        
                        if name.lower().endswith('.txt'):
                            # 1 byte tại offset 1 của data của $DATA: số lượng cluster
                            fileClusterNumber = read_number_buffer(buffer, attribOffset + fileRunsOffset + 1, 1)
                            # 2 byte tại offset 2 của data của $DATA: chỉ số cluster đầu của vùng chứa data thực
                            fileClusterBegin = read_number_buffer(buffer, attribOffset + fileRunsOffset + 2, 2)
                            # Lập danh sách các cluster chứa data thực
                            fileClusterList = [c for c in range(fileClusterBegin, fileClusterBegin + fileClusterNumber)]
                            # Lập danh sách các sector chứa data thực 
                            fileSectorList = self.clusterChainToSectors(fileClusterList)
                            # Đọc nội dung thực 
                            fileContent = read_sector_chain(self.file_object, fileSectorList, self.sector_size)
                    
                attribOffset = (attribOffset + attrLength)

            if not skipped and not name.startswith('$'):
                print('\nTên: {}\n'
                        'Size: {}\n'
                        'Sector begin: {}\n'
                        'Create: {}\n'
                        'Modified: {}\n'
                        'Accessed: {}\n'.format(name, fileRealSize, sectorsIndex, timeCreate, timeModified, timeAccessed))
                if name.lower().endswith('.txt'):
                    print(fileContent.decode('utf-8'))
                print('--------------------------------------------------------------')

            # Tăng vị trí sector lên 2 <=> 1024 bytes
            sectorsIndex += 2

    @staticmethod
    def filetime_to_dt(ft):
        '''
            Đổi số nano giây ra ngày giờ
        '''
        us = (ft - EPOCH_AS_FILETIME) // 10
        return datetime(1970, 1, 1) + timedelta(microseconds=us)


