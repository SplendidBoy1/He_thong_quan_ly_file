from BytesReader import *
import os

fd = os.open('\\\\.\\D:', os.O_RDONLY | os.O_BINARY)
with os.fdopen(fd, 'rb') as f:
    bootsec_buffer = read_sector(f, 0, 1)
    magic_number = hex(read_number_from_buffer(bootsec_buffer, 0x1FE, 2))
    print(magic_number)
