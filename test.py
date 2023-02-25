import os

class READ:
    def read_root(self):
        self.volumne_path = '\\\\.\\D:'
        self.fd = os.open(self.volumne_path, os.O_RDONLY | os.O_BINARY)
        return os.fdopen(self.fd, 'rb')


def main():
    read_file = READ()
    read_file.read_root()
    print(read_file)
    
if __name__ == '__main__':
    main()
        