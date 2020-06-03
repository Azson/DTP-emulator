from player.packet_selection import Solution as PacketSelection
from player.examples.simple_bbr import BBR

class Solution(BBR, PacketSelection):
    pass
