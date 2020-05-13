import sqlite3
import time

conn = sqlite3.connect('world.db')
c = conn.cursor()

t1 = time.time()

c.execute('CREATE INDEX IF NOT EXISTS plant_mass_idx  ON plant_mass (plant_id)')
c.execute('CREATE INDEX IF NOT EXISTS plant_tick_idx  ON plant_mass (tick_id)')
c.execute('CREATE INDEX IF NOT EXISTS soil_tick_idx  ON soil (tick_id)')
t2 = time.time()
c.execute('''SELECT tick_id
		FROM time
		WHERE sim_id = 1
		ORDER BY tick_id''')		
x = c.fetchall()
#print(x)

t3 = time.time()
for i in x:
	#print(i)
	c.execute('''SELECT  field_id, soil
		FROM soil
		WHERE tick_id = (?)
		ORDER BY field_id''', i)
	field_soil = c.fetchall()
	# без нужного индекса очень медленно работает
	c.execute('''SELECT plant_mass.plant_id, plants.field_id,plant_mass.mass 
			FROM plant_mass INNER JOIN plants
			ON plant_mass.plant_id = plants.plant_id
			WHERE tick_id = (?)''', i)
	plants = c.fetchall()
	#print(plants)

t4 = time.time()

conn.close()	
print('index time: ', t2 - t1)
print('query time: ', t3 - t2)
print('cycle time: ', t4 - t3)
