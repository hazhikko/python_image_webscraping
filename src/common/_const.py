# coding: utf-8
class _const:
    """PythonでConstを実現するためのクラス
    """
    class ConstEroor(TypeError):
        pass
    
    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstEroor('const (%s) は再定義できません' % name)
        self.__dict__[name] = value

import sys
sys.modules[__name__] = _const()