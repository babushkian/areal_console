from abc import ABC, abstractmethod
from areal import constants as cn



class Plant_proto(ABC):
    def __init__(self, field, sx, sy):
        self.field = field
        self.world = field.world
        self.all_energy = 0
        # координаты экранного пространства,  а не физические
        self.sx = sx
        self.sy = sy
        self.age = 0
        type(self).COUNT += 1 # глобальный счетчик сущностей
        self.field.counts[self.name] += 1 # счетчик сущностей на клетке
        # в наследуемом классе определяется параметр name, который служит ключом для словарей насроек
        # и тегом для объектов на холсте
        self.id = cn.global_counter()


    @abstractmethod
    def update(self):
        self.age += 1

    def count_down(self):
        type(self).COUNT -= 1
        self.field.counts[self.name] -= 1 # убавляе количество сущностей на клетке
