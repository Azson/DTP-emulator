from config.constant import *


class Solution(object):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0
        self.cwnd = 10
        self.send_rate = 700


    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate
        }

        return output


    def cc_trigger(self, data):
        pass


    def append_input(self, data):
        self._input_list.append(data)

        if data["packet_type"] != PACKET_TYPE_TEMP:
            self.cc_trigger(data)
            return {
                "cwnd" : self.cwnd,
                "send_rate" : self.send_rate
            }

        return None
