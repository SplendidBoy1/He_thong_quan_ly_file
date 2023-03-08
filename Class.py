from abc import *

class Item():
    @abstractmethod
    def path_address(seld) -> str:
        #Path of item
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        #Name of item
        pass
    
    @property
    @abstractmethod
    def attr(self) -> list:
        #All attributes of item
        pass
        
    @abstractmethod
    def show_attr(self) -> list:
        #Show all attributes
        pass
    
    
    


class Directory(Item):
    
    @abstractmethod
    def subentries(self) -> list:
        #List of all subentries
        pass
        
    def get_subentries(self, entry, n = 0):
        #build a list of item
        pass
    
class File(Item):
    @abstractmethod
    def size(self) -> int:
        #Size of file
        pass
    
    def data(self) -> bytes:
        #Data in bytes
        pass