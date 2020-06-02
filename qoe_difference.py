#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.emulator import Emulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import matplotlib.pyplot as plt
import numpy as np
import json, time

from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2
from player.aitrans_3 import Solution as s3

from qoe_model import cal_qoe
from double_flow import create_2flow_emulator


def cal_distance_double(block_file, trace_file, x):

    emulator1 = create_2flow_emulator(s1(), block_file, trace_file)
    emulator1.run_for_dur(21)
    reno_qoe = cal_qoe(x)

    emulator2 = create_2flow_emulator(s2(), block_file, trace_file)
    emulator2.run_for_dur(21)
    bbr_qoe = cal_qoe(x)

    tmp = s3()
    tmp.init_trace(trace_file)
    emulator3 = create_2flow_emulator(tmp, block_file, trace_file)
    emulator3.run_for_dur(21)
    mtr_qoe = cal_qoe(x)

    return [reno_qoe, bbr_qoe, mtr_qoe]


def cal_distance_single(block_file, trace_file, x):
    emulator1 = Emulator(
        block_file=block_file,
        trace_file=trace_file,
        solution=s1(),
        USE_CWND=True,
        SEED=1,
        ENABLE_LOG=False
    )
    emulator1.run_for_dur(51)
    reno_qoe = cal_qoe(x)

    emulator2 = Emulator(
        block_file=block_file,
        trace_file=trace_file,
        solution=s2(),
        USE_CWND=True,
        SEED=1,
        ENABLE_LOG=False
    )
    emulator2.run_for_dur(51)
    bbr_qoe = cal_qoe(x)

    tmp = s3()
    tmp.init_trace(trace_file)
    emulator3 = Emulator(
        block_file=block_file,
        trace_file=trace_file,
        solution=tmp,
        USE_CWND=False,
        SEED=1,
        ENABLE_LOG=False
    )
    emulator3.run_for_dur(51)
    mtr_qoe = cal_qoe(x)
    return [reno_qoe, bbr_qoe, mtr_qoe]


def plt_qoe(reno_arr, bbr_arr, pic, xidx, size, mtr_arr=None):
    x = np.linspace(1, 100, size)
    fig, ax = plt.subplots()
    ax.plot(x,reno_arr, color="blue", label="reno_qoe")
    ax.plot(x, bbr_arr, color="red", label="bbr_qoe")
    if mtr_arr:
        ax.plot(x, mtr_arr, color="green", label="mtr_qoe")
    ax.set_xlabel(xidx)
    ax.set_ylabel("qoe")
    ax.legend()
    plt.savefig(pic)


if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"
    pic = "qoemodel/qoe_difference.png"
    idx,size = "trace_index",12
    x = 0.82
    reno_arr = []
    bbr_arr = []
    mtr_arr = []
    new_blocks = ["config/block_2/data_video.csv", "config/block_2/data_audio.csv"]
    new_blocks_1 = ["config/block_1/block/1/data_video.csv", "config/block_1/block/1/data_audio.csv"]
    new_blocks_2 = ["scripts/block_5-26-1.csv"]
    for j in range(120, 1, -10):
        trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
        st = time.time()
        print("traces {0}, start_time {1}".format(j, st))
        qoe_difference = cal_distance_single(new_blocks_2, trace_file, x)
        ed = time.time()
        print("end_time {0}, cost {1}".format(ed, ed-st))
        reno_arr.append(qoe_difference[0])
        bbr_arr.append(qoe_difference[1])
        mtr_arr.append(qoe_difference[2])

    plt_qoe(reno_arr, bbr_arr, pic, idx, size, mtr_arr)
    MIN_QUEUE = MAX_QUEUE = queue_size = 55
    with open("qoemodel/qoe_difference.log","w+") as f:
        strs = ["trace numbers : 50\n", "buffer: MAX_QUEUE = MIN_QUEUE = "+
                str(queue_size) + "\n",
                "bw : 0.1 ~ 2 MB \n",
                "qoe = " + str(x) + " * priority + "+ str(1 - x) + " * deadline\n",
                str(reno_arr) + "\n",
                str(bbr_arr) + "\n",
                str(mtr_arr)]
        f.writelines(strs)







