from config.constant import *
from objects.cc_base import CongestionControl
from player.examples.reno import Reno

class BBR(Reno):

    def make_decision(self):

        output = {
            "cwnd": self.cwnd,
            "send_rate": float("inf"),
            "pacing_rate" : 100.
        }
        return output