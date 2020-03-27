#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.pcc_emulator import PccEmulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)



from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2

ccs1 = s1()
ccs2 = s2()

def cal_distance(block_file, trace_file, x):
    emulator1 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=ccs1
    )
    emulator1.run_for_dur(float("inf"))
    reno_qoe = emulator1.cal_qoe(x)

    emulator2 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=ccs2
    )
    emulator2.run_for_dur(float("inf"))
    bbr_qoe = emulator2.cal_qoe(x)
    return abs(reno_qoe - bbr_qoe)



if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"

    x = 0
    qoes = {}
    for i in range(1, 100):
        x = i / 100
        arr = []
        for j in range(1, 51):
            trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
            qoe_distance = cal_distance(block_file, trace_file, x)
            arr.append(qoe_distance)
        arr = np.array(arr, float)
        qoes[x] = np.var(arr)
    best_x = max(qoes, key=qoes.get)
    with open("qoemodel/qoe_model.log","w+") as f:
        f.write(str(qoes) + '\n')
        f.write("best_x: " + str(best_x))





