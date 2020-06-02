from player.congestion_control_algorithm import Solution as CcSolution
from player.packet_selection import Solution as PacketSelection
from player.examples.reno import Reno


class Solution(Reno, PacketSelection):
    pass
