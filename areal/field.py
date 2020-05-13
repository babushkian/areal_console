import random
import math
from collections import Counter

from areal import constants as cn
from areal.plant import Plant
from areal.seed import Seed
from areal.rot import Rot

class Field:  # клетка поля
    # максимальное количество растений на клетку, чтобы симуляция не тормозила
    MAX_PLANTS_IN_FIELD = cn.MAX_PLANTS_IN_FIELD
    # физическое расстояние от центра до края клетки  (половина клетки!!, т.к. PHYS_SIZE - половина игрового поля)
    FIELD_GRAPH_TO_PHYS_PROPORTION = cn.PHYS_SIZE / cn.FIELDS_NUMBER_BY_SIDE


    def __init__(self, world, row, col, soil):
        self.world = world
        self.row = row
        self.col = col
        self.id = f'{self.row:02d}x{self.col:02d}'
        self.name = 'field'
        self.starving = 0
        self.counts = Counter({'plant':0, 'seed':0, 'rot':0})
        self.plants = {} # словарь растений, размещенных на данной клетке; в качестве ключа - id графического объекта
        self.to_breed = [] # растения, готовые к размножению
        self.rot = {} # гниль на клетке
        self.seeds = {} # семена на клетке
        self.seed_mass =0
        self.plant_mass = 0
        self.rot_mass = 0
        self.plant_ration = 0 # сколько можно скормить каждому растению за ход
        self.soil = soil
        # физические координаты поля: его центра и краев
        self.center_x, self.center_y = self.graph_to_phys(row, col)
        self.lu_x = self.center_x - self.FIELD_GRAPH_TO_PHYS_PROPORTION # left-up conner
        self.lu_y = self.center_y + self.FIELD_GRAPH_TO_PHYS_PROPORTION
        self.rd_x = self.center_x + self.FIELD_GRAPH_TO_PHYS_PROPORTION # right-down corner
        self.rd_y = self.center_y - self.FIELD_GRAPH_TO_PHYS_PROPORTION
        self.area = self.spread_area()  # соседние клетки, на которые происходит  распространиение семян


    def spread_area(self):
        area = []
        r_start = self.row - 1
        c_start = self.col - 1
        for r in range(r_start, self.row +2):
            for c in range(c_start, self.col +2):
                if r in range(cn.FIELDS_NUMBER_BY_SIDE) and c in range(cn.FIELDS_NUMBER_BY_SIDE):  # проверяем, чтобы соседи не вылезали за границы игрового поля
                    area.append((r, c))
        return area


    def create_plant(self):
        """
        Вызывается из класса World при размножении расений
        Служит для инициалищзации пастений  вначале симуляции. В дальнейшем не используется,
        растения прорастают из семян
        """
        # определяем координаты новорожденного растения
        # физические координаты
        x = self.lu_x + random.randrange(int(self.rd_x - self.lu_x))
        y = self.rd_y + random.randrange(int(self.lu_y - self.rd_y))
        # экранные координаты
        sx, sy = self.phys_to_screen(x, y)

        if self.counts["plant"] < self.MAX_PLANTS_IN_FIELD:
            Plant(self, sx, sy)
        else:
            Rot(self, sx, sy, cn.TOTAL_SEED_MASS)

    def create_seed(self, seed_mass):
        # определяем координаты новорожденного растения
        # физические координаты
        x = self.lu_x + random.randrange(int(self.rd_x - self.lu_x))
        y = self.rd_y + random.randrange(int(self.lu_y - self.rd_y))
        # экранные координаты
        sx, sy = self.phys_to_screen(x, y)
        Seed(self, sx, sy, seed_mass)

    def update_rot(self):
        rot_list = list(self.rot)
        for r in rot_list:
            self.rot[r].update()

    def update_seeds(self):
        seeds_list = list(self.seeds)
        sl = len(seeds_list)
        if sl > 2:
            x = random.randrange(sl)
            y = random.randrange(sl)
            seeds_list[x], seeds_list[y] = seeds_list[y], seeds_list[x]
        for seed in seeds_list:
            self.seeds[seed].update()


    def update_plants(self):
        if self.counts['plant'] > 0:
            if self.to_breed:
                self.breed_plants()
            plants_list = list(self.plants)
            self.plant_ration = self.soil/self.counts['plant']
            for plant in plants_list:
                self.plants[plant].update()

    def breed_plants(self):
        for p in self.to_breed:
            # выбираем случайную клетку в окрестностях, чтобы засеять семя
            l = len(p.field.area)
            row, col = self.get_near_field_coords()
            seed_mass = p.split_mass()
            self.world.create_seed(row, col, seed_mass)
        self.to_breed = []

    def get_near_field_coords(self):
        l = len(self.area)
        return self.area[random.randrange(l)]


    def info(self):
        self.starving = 0
        self.plant_mass = 0
        for p in self.plants:
            self.plant_mass += self.plants[p].all_energy
            if self.plants[p].delta < 0:
                self.starving += 1
        self.rot_mass = 0
        for r in self.rot:
            self.rot_mass += self.rot[r].all_energy
        self.seed_mass =0
        for s in self.seeds:
            self.seed_mass += self.seeds[s].all_energy
        self.write_info()

    def write_info(self):
        s = []
        s.append(f'{self.world.global_time}')
        s.append(f'[{self.row:2d}][{self.col:2d}]')
        s.append(f'{self.counts["plant"]:2d}')
        s.append(f'{self.counts["rot"]:2d}')
        s.append(f'{self.counts["seed"]:2d}')
        s.append(f'{self.plant_mass:6.1f}')
        s.append(f'{self.rot_mass:6.1f}')
        s.append(f'{self.seed_mass:6.1f}')
        s.append(f'{self.soil:6.1f}')
        s.append(f'{(self.plant_mass + self.rot_mass + self.seed_mass + self.soil):7.1f}\n')
        field_string = '\t'.join(s).replace('.', ',')
        return field_string

    def create_tooltip_text(self):
        text = f'Клетка: {self.row:02d}x{self.col:02d}\n'
        text += f'Растений: {self.counts["plant"]:4d}({self.plant_mass:6.1f})\n'
        text += f'Семян: {self.counts["seed"]:4d}({self.seed_mass:6.1f})\n'
        text += f'Гнили: {self.counts["rot"]:4d}({self.rot_mass:6.1f})\n'
        text += f'Масса почвы: {self.soil:6.1f}'
        return text
    # в момент, когда графическией элемент удаляется, а подсказка была активирована, подтсказка
    # остается висеть навсегда, потому что не срабатывает обработчик выхода из поля объекта - его нет.


    @staticmethod
    def phys_to_screen(x, y):
        side = 2 * cn.PHYS_SIZE
        scr_len = cn.FIELDS_NUMBER_BY_SIDE * cn.FIELD_SIZE_PIXELS
        proportion = scr_len / side
        sx = math.floor(x * proportion + scr_len / 2)
        sy = math.floor(scr_len / 2 - y * proportion)
        return sx, sy

    @staticmethod
    def graph_to_phys(row, col):
        side = 2*cn.PHYS_SIZE
        proportion = side/cn.FIELDS_NUMBER_BY_SIDE
        x = (row + .5) *proportion - cn.PHYS_SIZE
        y = cn.PHYS_SIZE - (col + .5) *proportion
        return x, y
