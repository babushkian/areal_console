import sqlite3
import time

conn = sqlite3.connect('world.db')
c = conn.cursor()

t1 = time.time()
c.execute('''SELECT  pm.plant_id, pm.tick_id, pm.mass 
		FROM plant_mass pm INNER JOIN plants p
		ON pm.plant_id = p.plant_id
		WHERE p.field_id = '05x05' AND p.sim_id = 1
		ORDER BY pm.plant_id''')
p = c.fetchall()
t2 = time.time()
c.execute('CREATE INDEX IF NOT EXISTS plant_mass_idx  ON plant_mass (plant_id)')
t3 = time.time()
c.execute('''SELECT  pm.plant_id, pm.tick_id, pm.mass 
		FROM plant_mass pm INNER JOIN plants p
		ON pm.plant_id = p.plant_id
		WHERE p.field_id = '06x06' AND p.sim_id = 1
		ORDER BY pm.plant_id''')

p = c.fetchall()
t4 = time.time()
conn.close()
for x in p:
	print(x)


print('find records: ', len(p))
print('query time: ', t2 - t1)
print('create index time: ', t3 - t2)
print('indexed query time: ', t4 - t3)
	


