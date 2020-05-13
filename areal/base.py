import sqlite3
import os

class WorldBase:

    def __init__(self, world, dir):
        self.world = world
        base = os.path.join(dir, 'world.db')
        self.conn = sqlite3.connect(base)
        self.c = self.conn.cursor()
        '''
        self.c.execute('DROP TABLE IF EXISTS parameters')
        self.c.execute('DROP TABLE IF EXISTS time')
        self.c.execute('DROP TABLE IF EXISTS fields')
        self.c.execute('DROP TABLE IF EXISTS soil')
        self.c.execute('DROP TABLE IF EXISTS plants')
        self.c.execute('DROP TABLE IF EXISTS plant_mass')
        '''
        self.c.execute('PRAGMA foreign_keys=on')

        self.c.execute("""CREATE TABLE IF NOT EXISTS parameters (
            sim_id INTEGER PRIMARY KEY, 
            dimension INTEGER NOT NULL,
            sim_period INTEGER NOT NULL, 
            max_plants_on_field INTEGER NOT NULL, 
            init_soil INTEGER,
            grow_up_condition REAL, 
            seed_life REAL NOT NULL, 
            seed_prohibit_period REAL, 
            plant_life REAL NOT NULL, 
            fruiting_period REAL NOT NULL, 
            hidden_mass REAL, 
            seed_mass REAL NOT NULL, 
            max_plant_mass REAL NOT NULL)""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS time (
            tick_id INTEGER PRIMARY KEY, 
            tick INTEGER, 
            sim_id INTEGER NOT NULL,
            FOREIGN KEY (sim_id) REFERENCES parameters (sim_id)
            )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS fields (
            field_id TEXT PRIMARY KEY,
            row INTEGER NOT NULL, 
            col INTEGER NOT NULL)""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS plants (
            plant_id INTEGER PRIMARY KEY,
            field_id TEXT NOT NULL, 
            birth INTEGER, 
            death INTEGER DEFAULT NULL,
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (birth) REFERENCES time (tick_id)
            FOREIGN KEY (death) REFERENCES time (tick_id)
            )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS seeds (
            seed_id INTEGER PRIMARY KEY,
            field_id TEXT NOT NULL, 
            birth INTEGER, 
            death INTEGER DEFAULT NULL,
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (birth) REFERENCES time (tick_id)
            FOREIGN KEY (death) REFERENCES time (tick_id)
            )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS rot (
            rot_id INTEGER PRIMARY KEY,
            field_id TEXT NOT NULL, 
            birth INTEGER, 
            death INTEGER DEFAULT NULL,
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (birth) REFERENCES time (tick_id)
            FOREIGN KEY (death) REFERENCES time (tick_id)
            )""")


        self.c.execute("""CREATE TABLE IF NOT EXISTS soil (
            id INTEGER PRIMARY KEY,
            field_id TEXT NOT NULL,
            tick_id INTEGER NOT NULL,
            soil REAL, 
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (tick_id) REFERENCES time (tick_id)
            )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS plant_mass (
            id INTEGER PRIMARY KEY,
            plant_id INTEGER NOT NULL,
            tick_id INTEGER NOT NULL,
            mass REAL, 
            all_energy REAL, 
            FOREIGN KEY (plant_id) REFERENCES plants (plant_id),
            FOREIGN KEY (tick_id) REFERENCES time (tick_id) 
            )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS rot_mass (
            id INTEGER PRIMARY KEY,
            rot_id INTEGER NOT NULL,
            tick_id INTEGER NOT NULL,
            mass REAL,  
            FOREIGN KEY (rot_id) REFERENCES rot (rot_id),
            FOREIGN KEY (tick_id) REFERENCES time (tick_id) 
            )""")

        self.conn.commit()

    def close_connection(self):
        self.conn.commit()
        self.c.close()
        self.conn.close()


    def insert_params(self, params):
        self.c.execute("""INSERT INTO parameters (sim_id,
                                            dimension, 
                                            sim_period, 
                                            max_plants_on_field, 
                                            init_soil, 
                                            grow_up_condition, 
                                            seed_life, 
                                            seed_prohibit_period, 
                                            plant_life, 
                                            fruiting_period, 
                                            hidden_mass, 
                                            seed_mass, 
                                            max_plant_mass) 
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (params))


    def insert_time(self):
        self.tick_id = self.world.global_time + 1_000_000 * self.world.sim_number
        self.c.execute('INSERT INTO time (tick_id, tick, sim_id) VALUES (?, ?, ?)',
                       (self.tick_id, self.world.global_time, self.world.sim_number))

    def insert_field(self, field):
        self.c.execute('INSERT OR REPLACE INTO fields (field_id, row, col) VALUES (?, ?, ?)', (field.id, field.row, field.col))

    def insert_plant(self, plant):
        self.c.execute('INSERT INTO plants (plant_id, field_id, birth) VALUES (?, ?, ?)',
                       (plant.id, plant.field.id, self.tick_id))

    def update_plant_mass(self, plant):
        self.c.execute("""INSERT INTO  plant_mass (plant_id, tick_id, mass, all_energy) VALUES (?, ?, ?, ?)""",
                       (plant.id, self.tick_id, plant.mass, plant.all_energy))

    def plant_death(self, plant):
        self.c.execute('UPDATE plants SET death = (?) WHERE plant_id = (?)', (self.tick_id, plant.id))


    def insert_seed(self, seed):
        self.c.execute('INSERT INTO seeds (seed_id, field_id, birth) VALUES (?, ?, ?)', (seed.id, seed.field.id, self.tick_id))

    def seed_death(self, seed):
        self.c.execute('UPDATE seeds SET death = (?) WHERE seed_id = (?)', (self.tick_id, seed.id))


    def insert_rot(self, rot):
        self.c.execute('INSERT INTO rot (rot_id, field_id, birth) VALUES (?, ?, ?)',
                       (rot.id, rot.field.id, self.tick_id))

    def update_rot_mass(self, rot):
        self.c.execute("""INSERT INTO  rot_mass (rot_id, tick_id, mass) VALUES (?, ?, ?)""",
                       (rot.id, self.tick_id, rot.all_energy))

    def rot_to_soil(self, rot):
        self.c.execute('UPDATE rot SET death = (?) WHERE rot_id = (?)', (self.tick_id, rot.id))


    def update_soil(self, field):
        self.c.execute('INSERT INTO  soil (field_id, tick_id, soil) VALUES (?, ?, ?)', (field.id, self.tick_id, field.soil))


    def commit(self):
        self.conn.commit()
