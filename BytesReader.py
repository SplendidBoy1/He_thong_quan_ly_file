'''
Module hỗ trợ đọc dữ liệu dưới dạng binary
Yêu cầu mở volume ở chế độ đọc binary và có file object để sử dụng module này
'''

def read_sector(file_object, starting_sector, no_sector = 1, bytes_per_sector = 512) -> bytes:
    '''
    Hàm đọc dữ liệu trong 1 hoặc nhiều sector
        file_object: file object có được từ hàm open() hoặc os.fdopen()
        starting_sector: sector bắt đầu đọc
        no_sector: số lượng sector cần đọc
        bytes_per_sector: số bytes/sector
    '''
    file_object.seek(bytes_per_sector * starting_sector)
    result = file_object.read(bytes_per_sector * no_sector)
    return result

def read_list_of_sector(file_object, sector_list: list, bytes_per_sector = 512) -> bytes:
    '''
    Hàm đọc một danh sách các sector, sử dụng khi biết tập tin chiếm những sector nào
        file_object: file object có được từ hàm open() hoặc os.fdopen()
        sector_list: danh sách những sector cần đọc
        bytes_per_sector: số bytes/sector
    '''
    result = b''
    for sector in sector_list:
        result += read_sector(file_object, sector, 1, bytes_per_sector)
    return result

def read_bytes_from_buffer(buffer, offset, size) -> bytes:
    '''
    Hàm slice một chuỗi bytes thành một chuỗi bytes con
        buffer: chuỗi bytes cần slice
        offset: vị trí bắt đầu slice
        size: số bytes cần lấy từ vị trí offset
    '''
    result = buffer[offset:offset+size]
    return result

def read_number_from_buffer(buffer, offset, size) -> int:
    '''
    Hàm đọc một phần chuỗi bytes và chuyển sang số dạng int
        buffer: chuỗi bytes cần lấy số ra
        offset: vị trí bắt đầu của chuỗi bytes thể hiện số
        size: độ dài của chuỗi bytes thể hiện số
    '''
    buffer = read_bytes_from_buffer(buffer,offset,size)
    result = int.from_bytes(buffer, "little")
    return result

def read_string_from_buffer(buffer,offset,size) -> str:
    '''
    Hàm đọc một phần chuỗi bytes và dịch thành chuỗi chữ
        buffer: chuỗi bytes cần lấy số ra
        offset: vị trí bắt đầu của chuỗi bytes thể hiện chuỗi chữ
        size: độ dài của chuỗi bytes thể hiện chuỗi chữ
    '''
    buffer = read_bytes_from_buffer(buffer,offset,size)
    result = buffer.decode('utf-8','ignore')
    return result