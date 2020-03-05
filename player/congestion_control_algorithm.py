from config.constant import *


class Solution(object):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0
        self.cwnd = 1
        self.send_rate = 700
        self.ssthresh = 16
        self.curr_state = "slow_start"
        self.states = ["slow_start", "congestion_avoidance", "fast_recovery"]

    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate
        }

        return output


    def cc_trigger(self, data):
        print(self.cwnd)
        packet_type = data["packet_type"]

        while True:
            if self.curr_state == self.states[0]:
                if packet_type != 'D':
                    self.cwnd *= 2
                    if self.cwnd >= self.ssthresh:
                        self.curr_state = self.states[1]
                break

            if self.curr_state == self.states[1]:
                if packet_type != 'D':
                    self.cwnd += 1
                else:
                    self.curr_state = self.states[2]
                break

            if self.curr_state == self.states[2]:
                self.ssthresh = self.cwnd // 2 + 3
                self.cwnd = self.ssthresh
                self.curr_state = self.states[1]
                break





    def append_input(self, data):
        self._input_list.append(data)

        if data["packet_type"] not in PACKET_TYPE_TEMP:
            self.cc_trigger(data)
            return {
                "cwnd" : self.cwnd,
                "send_rate" : self.send_rate
            }

        return None
