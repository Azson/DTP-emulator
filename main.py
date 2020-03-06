#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : main
# @Function : 
# @Author : azson
# @Time : 2020/3/2 20:02
'''

from objects.pcc_emulator import PccEmulator
from utils import analyze_pcc_emulator, plot_cwnd
import os, sys, inspect
from config.constant import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


if __name__ == '__main__':

    block_file = "config/block.txt"
    trace_file = "config/trace.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/pcc_emulator_packet.log"

    emulator = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE)
    )

    print(emulator.run_for_dur(10))
    emulator.dump_events_to_file(log_file)
    emulator.print_debug()
    print(emulator.senders[0].rtt_samples)
    print(emulator.senders[0].application.ack_blocks)
    analyze_pcc_emulator(log_packet_file, trace_file)
    plot_cwnd(log_packet_file, trace_file=trace_file)