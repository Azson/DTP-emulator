import os, sys, inspect, platform

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, parentdir+"/simple_emulator")
# print(sys.path)

from objects.pcc_emulator import PccEmulator
from objects.cc_base import CongestionControl
from player.packet_selection import Solution as Packet_selection
from utils import *
from config.constant import *

from player.examples.reno import Reno
from player.examples.simple_bbr import BBR
# from player.examples.RL import RL


__all__ = ["PccEmulator", "CongestionControl", "Packet_selection", "emulator",  \
           "analyze_pcc_emulator", "plot_cwnd", "plot_throughput", \
           "Reno", "BBR", "RL"]

block_file = parentdir+"/simple_emulator"+"/config/block.txt"
trace_file = parentdir+"/simple_emulator"+"/config/trace.txt"
log_file = "output/pcc_emulator.log"
log_packet_file = "output/packet_log/packet-0.log"

new_trace_file = parentdir+"/simple_emulator"+"scripts/first_group/traces_1.txt"
new_block_files = [parentdir+"/simple_emulator"+"config/data_video.csv", parentdir+"/simple_emulator"+"config/data_audio.csv"]

if platform.system() == "Windows":
    # for windows
    os.system("rmdir /Q /S output")
else:
    # for linux
    os.system("rm -rf output")

os.system("mkdir output\packet_log")

emulator = PccEmulator(
    block_file=block_file,
    trace_file=trace_file,
    queue_range=(MIN_QUEUE, MAX_QUEUE)
)
