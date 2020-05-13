
import os
from areal import constants as cn
from areal import weather

from areal.field import Field
from areal.plant import Plant
from areal.seed import Seed
from areal.rot import Rot
from areal import base


class World:
    def __init__(self, sim_dir, metr_file, sim_number = 1):
        self.sim_dir = sim_dir
        self.metr_file = metr_file
        self.sim_number = sim_number
        self.newborn = True # смиуляция только создана и еще не запускалась
        self.game_over  = False # симуляция закончена по той или иной причине
        self.time_over = False # истек срок симуляции
        self.perish = False # все вымерли
        # создаем пустое игровое поле
        temp = [None for _ in range(cn.FIELDS_NUMBER_BY_SIDE)]
        self.fields = [temp[:] for x in range(cn.FIELDS_NUMBER_BY_SIDE)]
        self.season_time = 0
        self.global_time = 0
        self.years = 0
        self.starving = 0  # растения, не получющие необходимое количество пищи
        self.starving_percent = 0
        self.world_mass = 0
        self.seed_mass = 0
        self.plant_mass = 0
        self.rot_mass = 0
        self.soil_mass = 0 # полная масса системы: почва растения, семена и гниль
        self.sign_plant_num = 0
        self.sign_plant_mass_energy = 0
        self.sign_plant_mass_integral = 0
        self.sign_seeds_born = 0
        self.sign_seeds_grow_up = 0
        # МЕТРИКА: сколько гнили переработалось в почву за весь период симулчяции (пока есть живые сущности)
        self.soil_flow = 0
        self.living_beings = 0

        self.weather = weather.Weather()
        self.logfile_associations = {'every_plant_life': self.log_plants,
                             'fields_info': self.log_fields,
                             'world_info': self.log_world}
        self.log_functions = {} # словарь содержит функции, которые должны вызываться для логирования ключевого файла
        self.db = base.WorldBase(self, self.sim_dir)

    def init_sim(self):
        def param_tuple():
            t = [self.sim_number]
            t.append(cn.FIELDS_NUMBER_BY_SIDE)
            t.append(cn.SIMULATION_PERIOD)
            t.append(cn.MAX_PLANTS_IN_FIELD)
            t.append(cn.INIT_SOIL)
            t.append(cn.SEED_GROW_UP_CONDITION)
            t.append(cn.SEED_LIFE)
            t.append(cn.SEED_PROHIBITED_GROW_UP)
            t.append(cn.PLANT_LIFETIME_YEARS)
            t.append(cn.FRUITING_PERIOD)
            t.append(cn.PLANT_HIDDEN_MASS)
            t.append(cn.SEED_MASS)
            t.append(cn.PLANT_MAX_MASS)
            return tuple(t)

        Plant.COUNT = 0
        Seed.COUNT = 0
        Rot.COUNT = 0
        self.db.insert_params(param_tuple())
        self.db.insert_time()
        self.create_fields()
        self.plant_setup_3()
        self.newborn = False
        self.delay = cn.define_delay()
        self.logging_prepare()


    def update_a(self):
        self.years = self.global_time // cn.MONTHS
        self.global_time += 1
        self.season_time +=1
        self.db.insert_time()
        if self.season_time == cn.MONTHS:
            self.season_time = 0
        self.living_beings = Plant.COUNT + Seed.COUNT # проверяем, есть кто живой на карте
        self.update_rot()
        self.update_seeds()
        self.update_plants()
        self.statistics() # изменить двойной цикл по клеткам на одинарный
        self.write_logs()
        self.check_end_of_simulation()

        if self.global_time% (3*cn.MONTHS) == 0:
            self.db.commit()
        if self.game_over:
            self.end_of_simulation()

    def check_end_of_simulation(self):
        if not self.global_time < cn.MONTHS * cn.SIMULATION_PERIOD:
            self.time_over = True
            self.game_over = True
        if Plant.COUNT + Seed.COUNT + Rot.COUNT < 1:
            self.perish = True
            self.game_over = True

    def end_of_simulation(self):
        self.population_metric_record(self.metr_file)
        self.metr_file.flush()
        self.logging_close()
        self.db.close_connection()


    def calculate_color(self, temp):
        t = (temp + 14)* 1.6
        color = 'gray%d' % t
        return color

    def plant_setup_1(self):
        for _ in range(5):
            self.create_plant(int(cn.FIELDS_NUMBER_BY_SIDE / 2), int(cn.FIELDS_NUMBER_BY_SIDE / 2))

    def plant_setup_2(self):
        for x in range(int(cn.FIELDS_NUMBER_BY_SIDE / 2) - 2, int(cn.FIELDS_NUMBER_BY_SIDE / 2) + 3):
            for y in range(int(cn.FIELDS_NUMBER_BY_SIDE / 2) - 2, int(cn.FIELDS_NUMBER_BY_SIDE / 2) + 3):
                self.create_plant(x, y)

    def plant_setup_3(self):
        for x in range(cn.FIELDS_NUMBER_BY_SIDE):
            for y in range(cn.FIELDS_NUMBER_BY_SIDE):
                self.create_plant(x, y)


    def create_fields(self):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                self.fields[row][col] = Field(self, row, col, cn.INIT_SOIL)
                self.db.insert_field(self.fields[row][col])

    def create_plant(self, row, col):
        self.fields[row][col].create_plant()

    def create_seed(self, row, col, seed_mass):
        self.fields[row][col].create_seed(seed_mass)


    def update_plants(self):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                self.fields[row][col].update_plants()


    def update_seeds(self):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                self.fields[row][col].update_seeds()

    def update_rot(self):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                self.fields[row][col].update_rot()


    def statistics(self):
        self.soil_mass = 0
        self.seed_mass = 0
        self.plant_mass = 0
        self.rot_mass = 0
        self.starving = 0
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                # считаем статистику
                # подсчет масс растений семян, гнили и почвы на каждой клетке
                field = self.fields[row][col]
                field.info()
                self.db.update_soil(field)
                # подсчет полной массы почвы на на игровом поле
                self.soil_mass += field.soil
                self.seed_mass += field.seed_mass
                self.plant_mass += field.plant_mass
                self.rot_mass += field.rot_mass
                self.starving += field.starving
        self.sign_plant_mass_integral += self.plant_mass
        if self.starving == 0:
            self.starving_percent = 0
        else:
            self.starving_percent = self.starving / Plant.COUNT * 100
        self.world_mass = self.soil_mass + self.seed_mass + self.plant_mass + self.rot_mass

    def log_world(self, file):
        s = f'{self.years}\t{self.global_time}\t{Plant.COUNT}\t'
        s += f'{Plant.COUNT - self.starving}\t{self.starving}\t'
        s += f'{Seed.COUNT}\t'
        s += f'{Rot.COUNT}\t'
        s += f'{self.seed_mass:8.1f}\t{self.plant_mass:8.1f}\t{self.rot_mass:8.1f}\t'
        s += f'{self.soil_mass:8.1f}\t{self.world_mass:8.1f}\n'
        file.write(s.replace('.', ','))

    def log_fields(self, file):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                file.write(self.fields[row][col].write_info())

    def log_plants(self, file):
        for row in range(cn.FIELDS_NUMBER_BY_SIDE):
            for col in range(cn.FIELDS_NUMBER_BY_SIDE):
                for plant in self.fields[row][col].plants.values():
                    file.write(plant.info())

    @staticmethod
    def file_suffix():
        suffix = list()
        suffix.append(f'sgc{cn.SEED_GROW_UP_CONDITION:03}')
        suffix.append(f'sl{cn.SEED_LIFE:03}')
        suffix.append(f'spg{cn.SEED_PROHIBITED_GROW_UP:03}')
        suffix.append(f'pl{cn.PLANT_LIFETIME_YEARS:03}')
        suffix.append(f'sm{cn.SEED_MASS:03}')
        suffix.append(f'pm{cn.PLANT_MAX_MASS:03}')
        suffix.append(f'is{cn.INIT_SOIL:03}')
        suffix.append(f'fi{cn.FIELDS_NUMBER_BY_SIDE:03}')
        s = '_'.join(suffix)
        return s

    def logging_prepare(self):
        suffix = self.file_suffix()
        for action, name, header in cn.LOGGING:
            if action:
                fname = os.path.join(self.sim_dir, f'{name}_{suffix}.csv')
                f = open(fname, 'w', encoding='UTF16')
                f.write(header)
                self.log_functions[f] = self.logfile_associations[name]

    def write_logs(self):
        for file in self.log_functions:
            self.log_functions[file](file)

    def logging_close(self):
        for file in self.log_functions:
            if not file.closed:
                file.close()

    @staticmethod
    def population_metric_head(file):
        s = 'dimension\t'
        s += 'end date\t'
        s += 'soil on tile\t'
        s += 'grow up condition\t'
        s += 'prohibited grow up period\t'
        s += 'seed life\t'
        s += 'seed mass\t'
        s += 'plant life\t'
        s += 'plant mass\t'
        s += 'plants number\t'
        s += 'seeds number\t'
        s += 'grow up seeds percent\t'
        s += 'total plant enetgy\t'
        s += 'total soil flow\n'
        file.write(s)

    def population_metric_record(self, file):
        s = list()
        s.append(str(cn.FIELDS_NUMBER_BY_SIDE))
        s.append(str(self.global_time))
        s.append(str(cn.INIT_SOIL))
        s.append(str(cn.SEED_GROW_UP_CONDITION))
        s.append(str(cn.SEED_PROHIBITED_GROW_UP))
        s.append(str(cn.SEED_LIFE))
        s.append(str(cn.SEED_MASS))
        s.append(str(cn.PLANT_LIFETIME_YEARS))
        s.append(str(cn.PLANT_MAX_MASS))
        s.append(str(self.sign_plant_num))
        s.append(str(self.sign_seeds_born))
        s.append(f'{(self.sign_seeds_grow_up /self.sign_seeds_born *100):4.1f}')
        s.append(f'{self.sign_plant_mass_energy:10.0f}')
        s.append(f'{self.soil_flow:10.0f}\n')

        string = '\t'.join(s)
        string=string.replace('.', ',')
        file.write(string)
