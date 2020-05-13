from areal import field as fd # класс загружается только при таком импорте, не знаю почему
from areal import constants as cn
from areal.proto import Plant_proto
from areal.plant import Plant
from areal.rot import Rot


class Seed(Plant_proto):
    COUNT = 0
    def __init__(self, field,  sx, sy, seed_mass): # добавлю параметры позже
        # в будущем у зерна надо сделать регулируемый запас питательных веществ, чтобы его жизнь
        # зависела от этого запаса. А сам запас определялся геномом растений
        self.name = 'seed'
        super().__init__(field, sx, sy)
        self.world.sign_seeds_born += 1
        self.all_energy = seed_mass
        self.grow_up_age = cn.SEED_PROHIBITED_GROW_UP * cn.MONTHS
        self.field.seeds[self.id] = self
        self.world.db.insert_seed(self)

    def update(self):
        super().update()
        if self.age > cn.SEED_LIFE * cn.MONTHS:
            self.become_rot()
        else:
            self.age += 1
            if self.field.soil >= cn.SEED_GROW_UP_CONDITION and self.age >= self.grow_up_age:
                self.grow_up()

    def grow_up(self):
        if len(self.field.plants) < fd.Field.MAX_PLANTS_IN_FIELD:
            self.world.sign_seeds_grow_up += 1
            Plant(self.field,  self.sx, self.sy)
            self.destroy_seed()
        else:
            self.become_rot()

    def become_rot(self):
        self.world.db.seed_death(self)
        Rot(self.field, self.sx, self.sy, self.all_energy)
        self.destroy_seed()

    def destroy_seed(self):
        self.world.db.seed_death(self)
        self.count_down()
        del self.field.seeds[self.id]

