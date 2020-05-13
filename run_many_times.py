import os
import time

from areal import constants as cn
from areal import world


for roll in range(25):

    soil = [220, 250, 290, 350]
    condit = [0, 15, 30, 45, 60, 80, 110, 140]
    progib = [0, 0.5, 1.5, 3]
    life = [1, 3, 5, 8, 12]
    cur_date = time.time()
    sim_dir = 'sim_' + time.strftime("%d.%m.%Y_%H.%M.%S", time.localtime(cur_date))
    os.mkdir(sim_dir)
    metr = os.path.join(sim_dir, 'metric.csv')
    metr_file = open(metr, 'w', encoding='UTF16')
    count = 0
    for v in soil:
        cn.INIT_SOIL = v
        for x in condit:
            cn.SEED_GROW_UP_CONDITION = x
            for y in progib:
                cn.SEED_PROHIBITED_GROW_UP = y
                for z in life:
                    cn.SEED_LIFE = z
                    count +=1
                    print(f' ROLL: {roll}\tNUM: {count:4}\tsoil: {v:4}\tcondition: \t{x:4} prohibit: {y:4}\tlife: {z:4}')
                    w = world.World(sim_dir, metr_file, count)
                    if os.path.getsize(metr_file.name) == 0:
                        w.population_metric_head(metr_file)
                    w.init_sim()
                    while not w.game_over:
                        w.update_a()

