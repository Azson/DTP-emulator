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


def analyze_pcc_emulator(log_file, trace_file=None, rows=1000):

    plt_data = []

    with open(log_file, "r") as f:
        for line in f.readlines():
            plt_data.append(json.loads(line.replace("'", '"')))

    plt_data = filter(lambda x:x["Type"]=='A' and x["Position"] == 2, plt_data)
    # priority by packet id
    plt_data = sorted(plt_data, key=lambda x:int(x["Packet_id"]))[:rows]

    pic_nums = 3
    data_lantency = []
    data_finish_time = []
    data_drop = []
    data_sum_time = []
    data_miss_ddl = []
    for idx, item in enumerate(plt_data):
        if item["Type"] == 'A':
            data_lantency.append(item["Queue_delay"])
            data_finish_time.append(item["Time"])
            data_sum_time.append(item["Send_delay"] + item["Queue_delay"] + item["Propagation_delay"])
            if item["Drop"] == 1:
                data_drop.append(len(data_finish_time)-1)
            if item["Deadline"] < data_sum_time[-1]:
                data_miss_ddl.append(len(data_finish_time)-1)

    plt.figure(figsize=(20, 5*pic_nums))
    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 1)
    ax.set_title("Acked packet latency distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.scatter(data_finish_time, data_lantency, label="Latency")
    # plot average latency
    ax.plot([0, data_finish_time[-1] ], [np.mean(data_lantency)]*2, label="Average Latency",
            c='r')
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.5)

    # plot miss deadline rate block
    ax = plt.subplot(pic_nums, 1, 2)
    ax.set_title("Acked packet lost distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.scatter([data_finish_time[idx] for idx in data_drop],
                    [data_lantency[idx] for idx in data_drop], label="Drop")
    ax.scatter([data_finish_time[idx] for idx in data_miss_ddl],
                    [data_lantency[idx] for idx in data_miss_ddl], label="Miss_deadline")
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.5)

    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 3)
    ax.set_title("Acked packet life time distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.set_ylim(-np.min(data_sum_time)*2, np.max(data_sum_time)*2)

    ax.scatter(data_finish_time, data_sum_time, label="Latency")
    # plot average latency
    ax.plot([0, data_finish_time[-1]], [np.mean(data_sum_time)] * 2, label="Average Latency",
            c='r')
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0]/2, data_finish_time[-1]*1.5)

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

    plt.savefig("output/pcc_emulator-analysis.jpg")


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


if __name__ == '__main__':

    log_packet_file = "output/pcc_emulator_packet.log"
    analyze_pcc_emulator(log_packet_file)