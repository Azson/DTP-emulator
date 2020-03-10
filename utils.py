#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : utils
# @Function : 
# @Author : azson
# @Time : 2020/1/8 15:59
'''

import time, json
from matplotlib import pyplot as plt
import numpy as np
from config.constant import *


def get_ms_time(rate=1000):

    return time.time()*rate


def analyze_pcc_emulator(log_file, trace_file=None, rows=None, time_range=None, scatter=False):

    plt_data = []

    with open(log_file, "r") as f:
        for line in f.readlines():
            plt_data.append(json.loads(line.replace("'", '"')))

    plt_data = list(filter(lambda x:x["Type"]=='A' and x["Position"] == 2, plt_data))
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # priority by packet id
    # plt_data = sorted(plt_data, key=lambda x:int(x["Packet_id"]))[:rows]
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_lantency = []
    data_finish_time = []
    data_drop = []
    data_sum_time = []
    data_miss_ddl = []
    for idx, item in enumerate(plt_data):
        if item["Type"] == 'A':
            if item["Drop"] == 1:
                data_drop.append(idx)
            else:
                data_lantency.append(item["Queue_delay"])
                data_finish_time.append(item["Time"])
                data_sum_time.append(item["Send_delay"] + item["Queue_delay"] + item["Propagation_delay"])

            if item["Deadline"] < data_sum_time[-1]:
                data_miss_ddl.append(idx)

    pic = plt.figure(figsize=(50, 30 * pic_nums))
    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 1)
    ax.set_title("Acked packet latency distribution", fontsize=font_size)
    ax.set_ylabel("Latency / s", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    if scatter:
        ax.scatter(data_finish_time, data_lantency, label="Latency", s=200)
    else:
        ax.plot(data_finish_time, data_lantency, label="Latency")

    ax.scatter([plt_data[idx]["Time"] for idx in data_drop],
               [0 for idx in data_drop], label="Drop", s=200, c='r', marker='x')

    # plot average latency
    ax.plot([0, data_finish_time[-1] ], [np.mean(data_lantency)]*2, label="Average Latency",
            c='g')
    plt.legend(fontsize=font_size)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.2)
    plt.tick_params(labelsize=tick_size)

    # # plot miss deadline rate block
    # ax = plt.subplot(pic_nums, 1, 2)
    # ax.set_title("Acked packet lost distribution", fontsize=font_size)
    # ax.set_ylabel("Latency / s", fontsize=font_size)
    # ax.set_xlabel("Time / s", fontsize=font_size)
    # ax.scatter([data_finish_time[idx] for idx in data_drop],
    #                 [data_lantency[idx] for idx in data_drop], label="Drop")
    # ax.scatter([data_finish_time[idx] for idx in data_miss_ddl],
    #                 [data_lantency[idx] for idx in data_miss_ddl], label="Miss_deadline")
    # plt.legend(fontsize=font_size)
    # ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.5)
    # plt.tick_params(labelsize=tick_size)

    # # plot latency distribution
    # ax = plt.subplot(pic_nums, 1, 3)
    # ax.set_title("Acked packet life time distribution", fontsize=font_size)
    # ax.set_ylabel("Latency / s", fontsize=font_size)
    # ax.set_xlabel("Time / s", fontsize=font_size)
    # ax.set_ylim(-np.min(data_sum_time)*2, np.max(data_sum_time)*2)
    #
    # ax.scatter(data_finish_time, data_sum_time, label="Latency")
    # # plot average latency
    # ax.plot([0, data_finish_time[-1]], [np.mean(data_sum_time)] * 2, label="Average Latency",
    #         c='r')
    # plt.legend(fontsize=font_size)
    # ax.set_xlim(data_finish_time[0]/2, data_finish_time[-1]*1.5)
    # plt.tick_params(labelsize=tick_size)

    # plot bandwith
    if trace_file:
        max_time = data_finish_time[-1]
        trace_list = []
        with open(trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))

        st = 0
        for idx in range(len(trace_list)):
            if trace_list[idx][0] > max_time:
                break
            plt.plot([st, trace_list[idx][0]], [len(plt_data) + 1] * 2, '--',
                     linewidth=5)
            st = trace_list[idx][0]

        if trace_list[-1][0] < max_time:
            plt.plot([st, max_time], [len(plt_data) + 1] * 2, '--',
                 label="Different Bandwith", linewidth=5)

    plt.tight_layout()

    plt.savefig("output/pcc_emulator-analysis.png")


def check_solution_format(input):

    if not isinstance(input, dict):
        raise TypeError("The return value should be a dict!")

    keys = ["cwnd", "send_rate"]
    for item in keys:
        if not item in input.keys():
            raise ValueError("Key %s should in the return dict!" % (item))

    return input


def get_emulator_info(sender_mi):

    event = {}
    event["Name"] = "Step"
    # event["Target Rate"] = sender_mi.target_rate
    event["Send Rate"] = sender_mi.get("send rate")
    event["Throughput"] = sender_mi.get("recv rate")
    event["Latency"] = sender_mi.get("avg latency")
    event["Loss Rate"] = sender_mi.get("loss ratio")
    event["Latency Inflation"] = sender_mi.get("sent latency inflation")
    event["Latency Ratio"] = sender_mi.get("latency ratio")
    event["Send Ratio"] = sender_mi.get("send ratio")
    # event["Cwnd"] = sender_mi.cwnd
    # event["Cwnd Used"] = sender_mi.cwnd_used

    return event


def analyze_application(acked_packets):
    pass


def get_packet_type(sender, packet):
    if packet.drop:
        return PACKET_TYPE_DROP
    if packet.packet_type == EVENT_TYPE_ACK and \
        packet.next_hop == len(sender.path):
        return PACKET_TYPE_FINISHED

    return PACKET_TYPE_TEMP


def debug_print(*args, **kwargs):
    if ENABLE_DEBUG:
        print(*args, **kwargs)


def time_filter(data, time_range):
    if time_range[0] is None:
        time_range[0] = -1
    if time_range[1] is None:
        time_range[1] = data[-1]["Time"]
    data = list(filter(lambda x: time_range[0] <= x["Time"] <= time_range[1], data))
    return data


def plot_cwnd(log_file, rows=None, trace_file=None, time_range=None, scatter=False):
    plt_data = []
    with open(log_file, "r") as f:
        for line in f.readlines():
            plt_data.append(json.loads(line.replace("'", '"')))
    # filter the packet at sender
    plt_data = list(filter(lambda x: x["Type"] == 'S' and x["Position"] == 0, plt_data))
    # plt_data = list(filter(lambda x: x["Drop"] == 0, plt_data))
    # filter by the time
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # plot "rows" counts data
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_time = []
    data_cwnd = []
    data_Ucwnd = []
    last_cwnd = -1
    for item in plt_data:
        if item["Cwnd"] == last_cwnd:
            continue
        last_cwnd = item["Cwnd"]
        data_time.append(item["Time"])
        data_cwnd.append(item["Cwnd"])
        data_Ucwnd.append(item["Waiting_for_ack_nums"])

    pic = plt.figure(figsize=(50, 30*pic_nums))
    # plot cwnd changing
    ax = plt.subplot(pic_nums, 1, 1)
    if scatter:
        ax.scatter(data_time, data_cwnd, label="cwnd", c='g', s=200)
    else:
        ax.plot(data_time, data_cwnd, label="cwnd", c='g')
    ax.set_ylabel("Packet", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)
    plt.legend(fontsize=font_size)

    # # plot used cwnd changing
    # ax = plt.subplot(pic_nums, 1, 2)
    # ax.scatter(data_time, data_Ucwnd, c='y', label="used_cwnd")
    # ax.set_ylabel("Packet", fontsize=20)
    # ax.set_xlabel("Time (s)", fontsize=20)
    # plt.tick_params(labelsize=20)
    # plt.legend(fontsize=20)

    # plot bandwith
    if trace_file:
        max_time = data_time[-1]
        trace_list = []
        with open(trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))

        st = data_time[0]
        ax = ax.twinx()
        ed = -1
        for idx in range(1, len(trace_list)):
            if trace_list[idx][0] < st:
                continue
            if trace_list[idx][0] > max_time:
                ed = idx
                break
            ax.plot([st, trace_list[idx][0]], [trace_list[idx-1][1]/BYTES_PER_PACKET ] * 2, '--',
                     linewidth=5)
            st = trace_list[idx][0]

        if ed == -1 and trace_list[-1][0] < max_time:
            ax.plot([st, max_time], [trace_list[-1][1]/BYTES_PER_PACKET ] * 2, '--',
                    label="Different Bandwith", linewidth=5)
        elif ed != -1:
            ax.plot([st, max_time], [trace_list[ed-1][1]/BYTES_PER_PACKET ] * 2, '--',
                    label="Different Bandwith", linewidth=5)

        ax.set_ylabel("Link bandwith (Packet/s)", fontsize=font_size)
        plt.tick_params(labelsize=tick_size)
        plt.legend(fontsize=font_size)
    print(data_time)
    plt.savefig("output/cwnd_changing.png")


if __name__ == '__main__':

    log_packet_file = "output/pcc_emulator_packet.log"
    trace_file = "config/trace.txt"
    # analyze_pcc_emulator(log_packet_file, time_range=[0, 0.2], scatter=True)
    plot_cwnd(log_packet_file, None, trace_file=trace_file, time_range=[7.5, 9.], scatter=False)