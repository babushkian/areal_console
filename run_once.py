import os
import time
from areal import constants as cn
from areal import world


cur_date = time.time()
sim_dir = 'sim_' + time.strftime("%d.%m.%Y_%H.%M.%S", time.localtime(cur_date))
os.mkdir(sim_dir)
metr = os.path.join(sim_dir, 'metric.csv')
metr_file = open(metr, 'w', encoding='UTF16')
del metr
cn.INIT_SOIL = 200
cn.SEED_GROW_UP_CONDITION = 45
cn.SEED_PROHIBITED_GROW_UP = 0.5
cn.SEED_LIFE = 4
w = world.World(sim_dir , metr_file)
w.population_metric_head(metr_file)
w.init_sim()
while not w.game_over:
    w.update_a()

