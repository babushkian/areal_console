import math
from areal import constants as cn

class Weather:  # климатические условия
    AVERAGE_TEMP = 15
    TEMP_COEF_GRADIENT = AVERAGE_TEMP / cn.PHYS_SIZE

    def __init__(self):
        pass

    def harshness(self, x, y):
        return self.AVERAGE_TEMP * math.hypot(x, y)

    def temp_in_field(self, x, y, time):
        t_coord = self.AVERAGE_TEMP - self.TEMP_COEF_GRADIENT * y  # средняя температурв в зависимости от широты
        t_harsh = self.harshness(x, y) / cn.PHYS_HYPOT * math.sin(cn.MONTS_ANGLE * time)
        return int(t_coord + t_harsh)
