from areal import constants as cn
from areal.proto import Plant_proto

class Rot(Plant_proto):
    COUNT = 0
    # скорость гнеиния
    DECAY_SPEED = cn.PLANT_MAX_MASS / cn.MONTHS * cn.DECAY_MULTIPLIER
    def __init__(self, field, sx ,sy, all_energy):
        self.name = 'rot'
        super().__init__(field, sx, sy)
        self.world = field.world
        self.field = field
        self.all_energy = all_energy
        self.state = 0
        self.field.rot[self.id] = self
        self.world.db.insert_rot(self)


    # гниль медленно превращается в землю - на каждом ходу образуется немного земли
    def update(self):
        super().update()
        decrement = min(self.all_energy, self.DECAY_SPEED)
        self.all_energy -= decrement
        self.field.soil += decrement

        if self.world.living_beings > 0:
            self.world.soil_flow += decrement
        if self.all_energy == 0:
            self.become_soil()
        else:
            self.world.db.update_rot_mass(self)

    def become_soil(self):
        self.count_down()
        self.world.db.rot_to_soil(self)
        self.field.soil += self.all_energy  # растение превращается в почву
        del self.field.rot[self.id]

