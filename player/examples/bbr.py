from config.constant import *
from objects.cc_base import CongestionControl
from player.examples.reno import Reno
import random


class BBR(Reno):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0

        self.cwnd = 10
        # Initialize pacing rate to: high_gain * init_cwnd
        self.pacing_rate = 10 * self.bbr_high_gain

        self.maxbw = None
        self.minrtt = None

        self.bbr_mode = ["BBR_STARTUP", "BBR_DRAIN", "BBR_PROBE_BW", "BBR_PROBE_RTT"]
        self.mode = "BBR_STARTUP"

        # Window length of bw filter (in rounds)
        self.bbr_bw_rtts = 10

        # Window length of min_rtt filter (in sec)
        self.bbr_min_rtt_win_sec = 10
        # Minimum time (in ms) spent at bbr_cwnd_min_target in BBR_PROBE_RTT mode
        self.bbr_probe_rtt_mode_ms = 200

        self.bbr_high_gain = 2885 / 1000 + 1
        self.bbr_drain_gain = 1000 / 2885
        # probe_bw
        self.bbr_cwnd_gain = 2
        self.probe_bw_gain = [5 / 4, 4 / 3, 1]
        self.probe_rtt_gain = 1
        self.bbr_min_cwnd = 4

        self.pacing_gain = self.bbr_high_gain
        self.cwnd_gain = self.bbr_high_gain

        self.delivered_nums = 0
        self.ack_pairs = {}
        self.send_pairs = {}

        # to check when the mode come to drain
        self.three_bws = [0] * 4

        self.drain_start_time = 0

        self.delivered = 0

    # calculate rtt and bw on ack
    def cal_rtt_bw(self, packet_id):
        delivered = self.ack_pairs[packet_id][0] - self.send_pairs[packet_id][0]
        rtt = self.ack_pairs[packet_id][1] - self.send_pairs[packet_id][1]
        return rtt, delivered / rtt


    def stop_increasing(self, bws):
        scale1 = (bws[1] - bws[0]) / bws[0]
        scale2 = (bws[2] - bws[1]) / bws[1]
        scale3 = (bws[3] - bws[2]) / bws[2]
        return len(bws) == 4 and bws[0] and bws[1] and bws[2] \
               and scale1 < 0.25 and scale2 < 0.25 and scale3 < 0.25

    def change_probe_rtt(self):
        pass

    def update_bw_rtt(self, maxbw, minrtt):
        self.maxbw = maxbw
        self.minrtt = minrtt

    def set_output(self, mode):
        pacing_gain, cwnd_gain = self.cal_gain(mode)
        self.pacing_rate = max(10 * self.bbr_high_gain, pacing_gain * self.maxbw)
        self.cwnd = max(self.maxbw * self.minrtt * cwnd_gain, 10)

    def cal_gain(self, mode):
        pacing_gain, cwnd_gain = 0, 0
        if mode == self.bbr_mode[0]:
            pacing_gain = self.bbr_high_gain
            cwnd_gain = self.bbr_high_gain
        elif mode == self.bbr_mode[1]:
            pacing_gain = self.bbr_drain_gain
            cwnd_gain = self.bbr_high_gain
        elif mode == self.bbr_mode[2]:
            pacing_gain = self.probe_bw_gain[random.randint(0, 3)]
            cwnd_gain = pacing_gain
        elif mode == self.bbr_mode[3]:
            pacing_gain = 1
            cwnd_gain = 1
        return pacing_gain, cwnd_gain

    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd": self.cwnd,
            "send_rate": float("inf"),
            "pacing_rate": 100.
        }

        return output

    def cc_trigger(self, data):
        packet_type = data["Type"]
        packet_id = data["Packet_id"]
        event_time = data["event_time"]
        lantency = data["Lantency"]
        maxbw, minrtt = float("-inf"), float("inf")
        if packet_type == EVENT_TYPE_ACK:
            self.delivered_nums += 1
            self.ack_pairs[packet_id] = [self.delivered_nums, event_time]
            rtt, bw = self.cal_rtt_bw(packet_id)

            maxbw = max(maxbw, bw)
            minrtt = min(minrtt, rtt)

            if self.ack_pairs[packet_id][0] > self.delivered:
                self.delivered = self.ack_pairs[packet_id][0]

                self.three_bws[:] = self.three_bws[-3:] + [maxbw]
                if self.stop_increasing(self.three_bws) and self.mode == self.bbr_mode[0]:
                    self.mode = self.bbr_mode[1]
                    self.drain_start_time = event_time

                self.bbr_bw_rtts -= 1
                if self.bbr_bw_rtts == 0:
                    self.update_bw_rtt(maxbw, minrtt)
                    self.bbr_bw_rtts = 10
                    self.set_output(self.mode)

        if self.mode == self.bbr_mode[1]:
            inflight = data['Waiting_for_ack_nums']
            BDP = self.maxbw * self.minrtt
            if BDP < inflight:
                self.mode = self.bbr_mode[2]

            # how to check staying 10s and the rtt all greater than min_rtt
            if self.change_probe_rtt():
                self.mode = self.bbr_mode[3]

        elif self.mode == self.bbr_mode[2]:
            if self.change_probe_rtt():
                self.mode = self.bbr_mode[3]
        elif self.mode == self.bbr_mode[3]:
            self.cwnd = self.bbr_min_cwnd
            # after lasting 200ms,
            # if self.stop_increasing(self.three_bws):
            #     self.mode = self.bbr_mode[2]
            # else:
            #     self.mode = self.bbr_mode[0]


        elif packet_type == EVENT_TYPE_SEND:
            self.send_pairs[packet_id] = [self.delivered_nums, event_time - lantency]

