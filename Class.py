from abc import *

class Volume():
    @property
    @abstractmethod
    def name(self) -> str:
        #Name of item
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        #Size of item
        pass
        
    @abstractmethod
    def show_attr(self, flag) -> str:
        #Show all attributes
        pass
    
    
    


class Directory(Volume):     
    def get_subentries(self, entry, n = 0):
        #build a list of item
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        #Name of item
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        #Size of item
        pass
        
    @abstractmethod
    def show_attr(self) -> str:
        #Show all attributes
        pass
    
class File(Volume):
    def dump_binary_data(self) -> bytes:
        #Data in bytes
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        #Name of item
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        #Size of item
        pass
        
    @abstractmethod
    def show_attr(self) -> str:
        #Show all attributes
        pass