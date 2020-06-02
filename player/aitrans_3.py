from player.congestion_control_algorithm import Solution as CcSolution
from player.packet_selection import Solution as PacketSelection
from player.examples.simple_bbr import BBR
from player.examples.match_trace_rate import MTR


class Solution(MTR, PacketSelection):
    pass
