from config.constant import *
import numpy as np

class Solution(object):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0
        self.cwnd = 1
        self.send_rate = np.inf
        self.ssthresh = np.inf
        self.curr_state = "slow_start"
        self.states = ["slow_start", "congestion_avoidance", "fast_recovery", "stay_fast_recovery"]
        self.drop_nums = 0
        self.ack_nums = 0
        self.pre_data = None

    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate
        }

        return output


    def cc_trigger(self, data):

        packet_type = data["packet_type"]

        if packet_type == PACKET_TYPE_DROP:
            self.curr_state = self.states[2]
            self.drop_nums += 1
        elif packet_type == PACKET_TYPE_FINISHED:
            self.ack_nums += 1
            if self.curr_state == self.states[0]:
                self.cwnd += 1
                if self.cwnd >= self.ssthresh:
                    self.curr_state = self.states[1]

            elif self.curr_state == self.states[1]:
                self.cwnd += 1 / self.cwnd

        if self.curr_state == self.states[2]:
            self.ssthresh = self.cwnd // 2
            self.cwnd = self.ssthresh + 3
            self.curr_state = self.states[3]

        if self.curr_state == self.states[3]:
            if packet_type == PACKET_TYPE_DROP:
                self.curr_state = self.states[2]
                self.drop_nums += 1
            elif packet_type == PACKET_TYPE_FINISHED:
                # if receive duplicated ack
                if self.pre_data["packet_type"] == PACKET_TYPE_DROP and \
                        (data["packet"]["Block_id"] == self.pre_data["packet"]["Block_id"] and
                         data["packet"]["Offset"] == self.pre_data["packet"]["Offset"]):
                    self.cwnd += 1
                else:
                    self.cwnd = self.ssthresh
                    self.curr_state = self.states[1]


        if self.drop_nums == 0:
            print(self.drop_nums, self.ack_nums)


    def append_input(self, data):
        self._input_list.append(data)

        if data["packet_type"] != PACKET_TYPE_TEMP:
            self.cc_trigger(data)
            self.pre_data = data
            return {
                "cwnd" : self.cwnd,
                "send_rate" : self.send_rate
            }

        return None
