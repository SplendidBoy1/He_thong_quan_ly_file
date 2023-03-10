from BytesReader import *
from menu import *
from Object import *

def main():
    object_instance = Object()
    menu_instance = menu(object_instance)
    menu_instance.show()
    
    
if __name__ == '__main__':
    main()