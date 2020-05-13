
from areal import constants as cn
from areal.proto import Plant_proto
from areal.rot import Rot

class Plant(Plant_proto):
    COUNT = 0
    LIFETIME = int(cn.PLANT_LIFETIME_YEARS * cn.MONTHS)
    BREED_TIME = int(cn.FRUITING_PERIOD * cn.MONTHS)
    TIME_COEF = 4 / cn.MONTHS  # коэффициент влияющий на скорость роста и питания
    # чем больше скважность, тем более мелкими порциями растение питается
    GROW_UP_PER_TIC = 15 / cn.MONTHS
    ALPHA = 0.1 * GROW_UP_PER_TIC
    BETA = 0.3 * GROW_UP_PER_TIC
    GAMA = 0.5 * GROW_UP_PER_TIC
    EPSILON = 0.3


    def __init__(self,  field, sx, sy):
        self.name = 'plant'
        super().__init__(field, sx, sy)
        self.world.sign_plant_num += 1
        self.mass = cn.SEED_MASS
        self.all_energy = cn.TOTAL_SEED_MASS  # еда, потребленная за всю жизнь
        self.field.plants[self.id] = self
        self.world.db.insert_plant(self)


    def count_needs(self):
        self.res_to_live = self.ALPHA * self.mass  # сколько ресурсов нужно просто на поддержание жизни
        self.res_to_grow = self.BETA * (cn.PLANT_MAX_MASS - self.mass)
        self.res_ability = self.GAMA * (1 + self.EPSILON * self.mass)  # возможность добыть еды за ход
        return self.res_to_live, self.res_to_grow, self.res_ability

    def feed(self):
        res_to_live, res_to_grow, res_ability = self.count_needs()
        want =  min(res_to_live + res_to_grow, res_ability)
        self.get = min(want, self.field.plant_ration)
        self.field.soil -= self.get
        self.all_energy += self.get
        self.delta = self.get - res_to_live  # растение может получать меньше, чем тратит на жизнь
        self.mass += self.delta
        if self.mass < 0.5:  # как только масса понижается до минимума, растение гибнет от голода
            self.die()


    def update(self):
        super().update()
        if self.age == self.LIFETIME:
            self.die()
        else:
            if self.world.global_time % self.BREED_TIME == 0 and self.mass > 0.95 * cn.PLANT_MAX_MASS:
                self.field.to_breed.append(self)  # встает в очередь на размножение
            self.feed()
            self.info()
            self.world.db.update_plant_mass(self)

    def split_mass(self):
        """
        Вызывается при размножении. Уменьшает массу растения нм амссу семечка.
        Возвращает массу семечка
        :return: seed_mass
        """
        self.mass -= cn.TOTAL_SEED_MASS
        self.all_energy -= cn.TOTAL_SEED_MASS
        return cn.TOTAL_SEED_MASS

    def die(self):
        self.count_down()
        self.world.sign_plant_mass_energy += self.all_energy
        self.world.db.plant_death(self)
        Rot(self.field, self.sx, self.sy, self.all_energy)
        del self.field.plants[self.id]


    def info(self):
        out_string = []
        out_string.append(str(self.world.global_time))
        out_string.append(str(self.id))
        out_string.append(f'[{self.field.row:2d}][{self.field.col:2d}]')
        out_string.append(str(self.age))
        out_string.append(f'{self.mass:4.1f}')
        out_string.append(f'{self.all_energy:5.1f}')
        out_string.append(f'{self.res_to_live:4.1f}')
        out_string.append(f'{self.res_to_grow:4.1f}')
        out_string.append(f'{self.res_ability:4.1f}')
        out_string.append(f'{self.get:4.1f}')
        out_string.append(f'{self.delta:4.1f}')
        out_string.append(f'{self.field.soil:7.1f}\n')
        plant_string = '\t'.join(out_string).replace('.', ',')
        return plant_string



