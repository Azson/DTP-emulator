#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.pcc_emulator import PccEmulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import matplotlib.pyplot as plt
import numpy as np
import json

from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2

def cal_qoe(x):
    block_data = []
    urgency = []
    priorities = []
    qoe = 0
    with open("output/block.log", "r") as f:
        for line in f.readlines():
            block_data.append(json.loads(line.replace("'", '"')))
    for block in block_data:
        priority = float((int(block['Priority']) + 1) / 3)
        priorities.append(priority)
        if block['Miss_ddl'] == 0:
            urgency.append(1)
        else:
            urgency.append(0)
    for i in range(len(urgency)):
        qoe += x * priorities[i] + (1 - x) * urgency[i]
    return qoe

def cal_distance(block_file, trace_file, x):
    emulator1 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s1()
    )
    emulator1.run_for_dur(float("inf"))
    reno_qoe = cal_qoe(x)

    emulator2 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s2()
    )
    emulator2.run_for_dur(float("inf"))
    bbr_qoe = cal_qoe(x)
    return [reno_qoe, bbr_qoe]

def plt_qoe(reno_arr, bbr_arr):
    x = np.linspace(1, 50, 50)
    fig, ax = plt.subplots()
    ax.plot(x,reno_arr, color="blue", label="reno_qoe")
    ax.plot(x, bbr_arr, color="red", label="bbr_qoe")
    ax.set_xlabel("trace_index")
    ax.set_ylabel("qoe")
    ax.legend()
    plt.savefig("qoemodel/qoes.png")


if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"
    x = 0.1
    reno_arr = []
    bbr_arr = []
    for j in range(1, 51):
        trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
        qoe_difference = cal_distance(block_file, trace_file, x)
        reno_arr.append(qoe_difference[0])
        bbr_arr.append(qoe_difference[1])

    plt_qoe(reno_arr, bbr_arr)

    with open("qoemodel/bbr_reno_qoes.log","w+") as f:
        strs = ["trace numbers : 50\n", "buffer: MAX_QUEUE = 10, MIN_QUEUE = 50\n",
                "bw : 0.1 ~ 2 MB \n",
                "qoe = 0.1 * priority + 0.9 * deadline\n",
                str(reno_arr) + "\n",
                str(bbr_arr)]
        f.writelines(strs)







