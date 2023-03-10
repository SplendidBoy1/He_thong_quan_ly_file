from abc import ABCMeta, abstractmethod
"""
File định nghĩa các Abstract Base Classes (ABC)
"""

class AbstractVolume(metaclass=ABCMeta):
    pass

class AbstractEntry(metaclass=ABCMeta):
    pass

class AbstractDirectory(AbstractEntry):
    pass


class AbstractFile(AbstractEntry):
    pass