#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : block_trace_generator
# @Function : 
# @Author : azson
# @Time : 2020/4/23 9:18
'''
import random, os
import pandas as pd
import numpy as np
import time
from matplotlib import pyplot as plt

from player.aitrans_3 import Solution as s3
from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2
from objects.emulator import Emulator
from qoe_model import cal_qoe


def ffmpeg(block_src, output, tool_path="D:/迅雷下载/ffmpeg-20200422-2e38c63-win64-static/bin"):
    order = 'ffprobe -show_frames '+ block_src +' | grep -E \"media_type|pkt_duration_time|pkt_size|key_frame\"  > temp.data'
    os.system(tool_path + '/' + order)

    stra = 'media_type=video'
    strb = 'media_type=audio'
    data_audio = open("data_audio.csv", 'w+')
    data_video = open("data_video.csv", 'w+')
    time_video = 0.0
    time_audio = 0.0

    f = open('temp.data')
    list_str = f.readlines()

    for i in range(len(list_str)):
        if i + 3 >= len(list_str):
            break
        if list_str[i][0:16] == stra:
            b = list_str[i + 1]
            c = list_str[i + 2]
            d = list_str[i + 3]
            # print("check1",b[:-1],c[:-1],d[:-1])
            try:
                c = float(c[18:-1])
            except ValueError:
                print('error', c[18:-1])
                continue
            # print('video',b[10:-1],c,d[9:-1])
            print(time_video, ',', d[9:-1], ',', b[10:-1], file=data_video)
            time_video += c
        elif list_str[i][0:16] == strb:
            b = list_str[i + 2]
            d = list_str[i + 3]
            # print("check2",b[:-1],d[:-1])
            # print('audio',b[18:-1],d[9:-1])
            b = float(b[18:-1])
            print(time_audio, ',', d[9:-1], file=data_audio)
            time_audio += b


def modify_block_trace(block_file, change_seqs=None, delta=10, output=None, need_range=None):
    df_block = pd.read_csv(block_file, header=None)
    df_block.columns = ["time", "size", 'p'] if "video" in block_file else ["time", "size"]
    print(df_block.describe())
    if need_range:
        df_block = df_block[(df_block["time"] < need_range[1]) & (need_range[0] <= df_block["time"])]
        df_block[["time"]] = df_block[["time"]].apply(lambda x:x-need_range[0])
    if change_seqs:
        for seq in change_seqs:
            left, right, seq_delta = seq
            df_block.loc[(df_block["time"] < right) & (left <= df_block["time"]), "size"] *= seq_delta
    else:
        df_block["size"] *= delta
    if output:
        df_block.to_csv(output, header=None, index=None)
    return df_block


def plot_block(block_file, left=-1, right=float("inf")):
    df_block = pd.read_csv(block_file, header=None)
    df_block.columns = ["time", "size", 'p'] if len(df_block.columns) == 3 else ["time", "size"]
    df_block = df_block[(df_block["time"] < right) & (left <= df_block["time"])]
    plt.scatter(df_block["time"], df_block["size"], s=5)
    plt.xlabel("Time (s)")
    plt.ylabel("Block Size (B)")
    plt.show()


def cal_rate(block_files, trace_file):
    data = []
    for block in block_files:
        df_block = pd.read_csv(block, header=None)
        # print(df_block.info())
        data.append(df_block)
    data = pd.concat(data, ignore_index=True)
    data.sort_values(0, inplace=True)
    data.reset_index(inplace=True)
    if 2 in data.columns:
        data.drop(2, axis=1, inplace=True)

    time_seq = []
    size_seq = []
    rate_seq = []
    rate_time_seq = []
    for i in range(len(data[0])):
        time_seq.append(data[0][i])
        size_seq.append(data[1][i])
        while time_seq[-1] - time_seq[0] > 1.0:
            time_seq.pop(0)
            size_seq.pop(0)
        if time_seq[-1] - time_seq[0] > 0:
            rate_seq.append(sum(size_seq) / (time_seq[-1] - time_seq[0]) / (1500))
            rate_time_seq.append(data[0][i])

    ax = plt.subplot(1, 1, 1)
    font_size = 10
    tick_size = 10
    print("block_nums = {0}".format(len(data[0])))
    print("avg_rate = {0}".format(np.mean(rate_seq)))
    print(rate_seq)
    print(data.head(3))
    ax.plot(rate_time_seq, rate_seq, c='r')

    if trace_file:
        # plot trace
        BYTES_PER_PACKET = 1500
        max_time = rate_time_seq[-1]
        trace_list = []
        with open(trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))

        st = rate_time_seq[0]
        # ax = ax.twinx()
        ed = -1
        for idx in range(1, len(trace_list)):
            if trace_list[idx][0] < st:
                continue
            if trace_list[idx][0] > max_time:
                ed = idx
                break
            ax.plot([st, trace_list[idx][0]], [trace_list[idx - 1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                    c='b')
            st = trace_list[idx][0]

        if ed == -1 and trace_list[-1][0] < max_time:
            ax.plot([st, max_time], [trace_list[-1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                    label="Different Bandwith", c='b')
        elif ed != -1:
            ax.plot([st, max_time], [trace_list[ed - 1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                    label="Different Bandwith", c='b')

        ax.set_ylabel("Packet/s", fontsize=font_size)
        plt.tick_params(labelsize=tick_size)
    plt.show()


def perfect_qoe(block_files, x=0.82):
    ret = 0
    for block in block_files:
        df_block = pd.read_csv(block, header=None)
        sz = len(df_block[0])
        priority = 1
        if "video" in block:
            priority = 1/3
        elif "audio" in block:
            priority = 2/3
        ret += sz * (x*priority + (1-x)*1)
    return ret


def test_score(block_files, trace_file, solution=None):
    if solution is None:
        solution = s3()
        solution.init_trace(trace_file)
    emulator3 = Emulator(
        block_file=block_files,
        trace_file=trace_file,
        solution=solution,
        USE_CWND=False,
        SEED=1,
        ENABLE_LOG=False,
        RUN_DIR="E:/Azson/bupt/AITrans/simple_emulator/scripts"
    )
    st = time.time()
    emulator3.run_for_dur()
    ed = time.time()
    print("use time {0}s".format(ed-st))
    mtr_qoe = cal_qoe()

    full_qoe = perfect_qoe(block_files)
    print("mtr_qoe = {}, full_qoe = {}".format(mtr_qoe, full_qoe))


def generate_block_trace(network_trace, avg_block_size=200000, dur_sec=15, use_noisy=False, output_file="data_block.csv"):
    trace_list = []
    block_list = []
    with open(network_trace, "r") as f:
        for line in f.readlines():
            trace_list.append(list(
                map(lambda x: float(x), line.split(","))
            ))
    cur_time = 0
    for idx, item in enumerate(trace_list):
        time, bw, loss_rate, p_time = item
        if idx == 0:
            continue
        bw = trace_list[idx-1][1] * 10 ** 6
        end_time = trace_list[-1][0]+5 if idx == len(trace_list)-1 else trace_list[idx][0]
        end_time = min(end_time, dur_sec)
        while cur_time < end_time:
            new_block_create_time = cur_time
            new_block_size = avg_block_size
            if use_noisy:
                new_block_size = new_block_size * (0.9+0.2*random.random())

            block_list.append([new_block_create_time, new_block_size])
            # cur_time += new_block_size / bw
            cur_time += (new_block_size + 20*(new_block_size//1480 + 1)) / bw
            print(cur_time, new_block_size, bw)
        if cur_time >= dur_sec:
            break
    if output_file:
        with open(output_file, 'w') as f:
            for line in block_list:
                f.write(','.join(list(map(lambda x:str(x), line))))
                f.write('\n')

    return block_list



if __name__ == '__main__':
    # network_trace = "first_group/traces_1.txt"
    # network_trace = "../config/trace.txt"
    trace_file = "first_group/traces_100.txt"
    output_file = "block_5-27-7.csv"
    # block_trace = generate_block_trace(trace_file, use_noisy=True, output_file=output_file, dur_sec=50)
    # print(block_trace)
    # print(len(block_trace))

    # block_files = ["data_video.csv", "data_audio.csv"]
    # block_files_1 = ["../config/data_video-2.csv", "../config/data_audio-2.csv"]
    # block_files_2 = ["block_5-27-5.csv", "block_5-27-6.csv"]
    # trace_file = "first_group/traces_59.txt"
    # output_file = "block_5-27-6.csv"
    #
    # # modify_block_trace(block_files[1], output=output_file, delta=10, need_range=[6563, 6613])
    #
    # plot_block(output_file)

    cal_rate([output_file], trace_file)

    # last do
    # test_score(block_files_2, trace_file, None)