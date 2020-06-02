#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.emulator import Emulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import json, shutil

from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2


def cal_qoe(x=0.82):
    block_data = []
    urgency = []
    priorities = []
    qoe = 0
    tmp = [3, 2, 1]
    with open("output/block.log", "r") as f:
        for line in f.readlines():
            block_data.append(json.loads(line.replace("'", '"')))
    for block in block_data:
        priority = float(tmp[int(block['Priority'])] / 3)
        priorities.append(priority)
        if block['Miss_ddl'] == 0:
            urgency.append(1)
        else:
            urgency.append(0)
            priorities[-1] *= 0
    for i in range(len(urgency)):
        qoe += x * priorities[i] + (1 - x) * urgency[i]
    return qoe


def cal_nums():
    block_data = []
    urgency = []
    priorities = []
    tmp = [3, 2, 1]
    with open("output/block.log", "r") as f:
        for line in f.readlines():
            block_data.append(json.loads(line.replace("'", '"')))
    for block in block_data:
        priority = float(tmp[int(block['Priority'])] / 3)
        priorities.append(priority)
        if block['Miss_ddl'] == 0:
            urgency.append(1)
        else:
            urgency.append(0)
            priorities[-1] *= 0

    return [sum(priorities), sum(urgency)]


def cal_distance(block_file, trace_file, x):
    emulator1 = Emulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s1(),
        SEED=1,
        ENABLE_LOG=False
    )
    emulator1.run_for_dur(20)
    reno_qoe = []
    for i in range(1, 100):
        reno_qoe.append(cal_qoe(i/100))
    reno_nums = cal_nums()
    shutil.copyfile("output/block.log", "qoe_test/reno/" + trace_file.split('/')[-1])

    emulator2 = Emulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s2(),
        SEED=1,
        ENABLE_LOG=False
    )
    emulator2.run_for_dur(20)
    bbr_qoe = []
    for i in range(1, 100):
        bbr_qoe.append(cal_qoe(i/100))
    bbr_nums = cal_nums()
    shutil.copyfile("output/block.log", "qoe_test/bbr/" + trace_file.split('/')[-1])

    ret = []
    for i in range(1, 100):
        ret.append(reno_qoe[i-1] - bbr_qoe[i-1])
    return ret, [reno_nums, bbr_nums]


def plot_rate(data):
    new_data = np.array(data, float)




if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"
    new_block_files = ["config/data_video-2.csv", "config/data_audio-2.csv"]
    new_block_file_1 = ["scripts/block_5-27-7.csv"]
    x = 0
    qoes = {}
    arr = []
    rate_nums = []
    for j in range(1, 121, 1):
        print("x = {0}, trace_id = {1}".format(x, j))
        trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
        qoe_distance, tmp  = cal_distance(new_block_file_1, trace_file, x)
        rate_nums.append(tmp)
        qoe_distance = np.array(qoe_distance, float)
        arr.append(qoe_distance)
    arr = np.array(arr)
    qoes = np.var(arr, axis=0)
    print(qoes)
    best_x = np.argmax(qoes)*0.01
    with open("qoemodel/qoe_model.log","w+") as f:
        f.write(str(qoes) + '\n')
        f.write(str(best_x) + " * priority + " + str(1 - best_x) + " * ddl " )

    print(rate_nums)
    plot_rate(rate_nums)





