from config.constant import *
import numpy as np
from utils import debug_print


class Solution(object):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0
        self.cwnd = 1
        self.send_rate = np.inf
        self.ssthresh = np.inf
        self.curr_state = "slow_start"
        self.states = ["slow_start", "congestion_avoidance", "fast_recovery"]
        self.drop_nums = 0
        self.ack_nums = 0

        self.cur_time = -1
        self.last_cwnd = 0
        self.instant_drop_nums = 0


    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate
        }

        return output


    def cc_trigger(self, data):

        packet_type = data["packet_type"]
        event_time = data["event_time"]

        if self.cur_time < event_time:
            self.last_cwnd = 0
            self.instant_drop_nums = 0

        if packet_type == PACKET_TYPE_DROP:
            if self.instant_drop_nums > 0:
                return
            self.instant_drop_nums += 1
            self.curr_state = self.states[2]
            self.drop_nums += 1
            self.ack_nums = 0
            # Ref 1 : For ensuring the event type, drop or ack?
            self.cur_time = event_time
            if self.last_cwnd > 0 and self.last_cwnd != self.cwnd:
                self.cwnd = self.last_cwnd
                self.last_cwnd = 0

        elif packet_type == PACKET_TYPE_FINISHED:
            # Ref 1
            if event_time <= self.cur_time:
                return
            self.cur_time = event_time
            self.last_cwnd = self.cwnd

            self.ack_nums += 1
            if self.curr_state == self.states[0]:
                if self.ack_nums == self.cwnd:
                    self.cwnd *= 2
                    self.ack_nums = 0
                if self.cwnd >= self.ssthresh:
                    self.curr_state = self.states[1]

            elif self.curr_state == self.states[1]:
                if self.ack_nums == self.cwnd:
                    self.cwnd += 1

        if self.curr_state == self.states[2]:
            self.ssthresh = self.cwnd // 2
            self.cwnd = self.ssthresh + 3
            self.curr_state = self.states[1]
        if self.drop_nums == 0:
            debug_print(self.drop_nums, self.ack_nums)


    def append_input(self, data):
        self._input_list.append(data)

        if data["packet_type"] != PACKET_TYPE_TEMP:
            self.cc_trigger(data)
            return {
                "cwnd" : self.cwnd,
                "send_rate" : self.send_rate
            }

        return None
