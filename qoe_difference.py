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

from qoe_model import cal_qoe

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

def plt_qoe(reno_arr, bbr_arr, pic, xidx, size):
    x = np.linspace(1, 100, size)
    fig, ax = plt.subplots()
    ax.plot(x,reno_arr, color="blue", label="reno_qoe")
    ax.plot(x, bbr_arr, color="red", label="bbr_qoe")
    ax.set_xlabel(xidx)
    ax.set_ylabel("qoe")
    ax.legend()
    plt.savefig(pic)


if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"
    pic = "qoemodel/qoe_difference.png"
    idx,size = "trace_index",100
    x = 0.9
    reno_arr = []
    bbr_arr = []
    for j in range(1, 101):
        trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
        qoe_difference = cal_distance(block_file, trace_file, x)
        reno_arr.append(qoe_difference[0])
        bbr_arr.append(qoe_difference[1])

    plt_qoe(reno_arr, bbr_arr, pic, idx, size)

    with open("qoemodel/qoe_difference.log","w+") as f:
        strs = ["trace numbers : 50\n", "buffer: MAX_QUEUE = 50, MIN_QUEUE = 50\n",
                "bw : 0.1 ~ 2 MB \n",
                "qoe = " + str(x) + " * priority + "+ str(1 - x) + " * deadline\n",
                str(reno_arr) + "\n",
                str(bbr_arr)]
        f.writelines(strs)







