from config.constant import *
from objects.cc_base import CongestionControl
from player.examples.reno import Reno
import random


class BBR(Reno):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0

        self.maxbw = None
        self.minrtt = None

        self.bbr_mode = ["BBR_STARTUP", "BBR_DRAIN", "BBR_PROBE_BW", "BBR_PROBE_RTT"]
        self.mode = "BBR_STARTUP"

        # Window length of bw filter (in rounds)
        self.bbr_bw_rtts = 10

        # Window length of min_rtt filter (in sec)
        self.bbr_min_rtt_win_sec = 10

        # Minimum time (in s) spent at bbr_cwnd_min_target in BBR_PROBE_RTT mode
        self.bbr_probe_rtt_mode_ms = 0.2

        self.bbr_high_gain = 2885 / 1000 + 1
        self.bbr_drain_gain = 1000 / 2885

        # probe_bw
        self.bbr_cwnd_gain = 2
        self.probe_bw_gain = [5 / 4, 4 / 3, 1]

        self.probe_rtt_gain = 1

        self.bbr_min_cwnd = 4

        self.pacing_gain = self.bbr_high_gain
        self.cwnd_gain = self.bbr_high_gain

        # to check when the mode come to drain
        self.four_bws = [0] * 4

        # the start time of probe rtt
        self.probe_rtt_time = 0

        self.delivered = 0
        self.delivered_nums = 0

        # used to check when come to PROBE_RTT mode
        self.ten_sec_wnd = []

        self.send_rate = float("inf")
        self.cwnd = 10
        # Initialize pacing rate to: high_gain * init_cwnd
        self.pacing_rate = 10 * self.bbr_high_gain

    # calculate rtt and bw on ack
    def cal_bw(self, send_delivered, rtt):
        delivered = self.delivered_nums - send_delivered
        return delivered / rtt


    def stop_increasing(self, bws):
        scale1 = (bws[1] - bws[0]) / bws[0]
        scale2 = (bws[2] - bws[1]) / bws[1]
        scale3 = (bws[3] - bws[2]) / bws[2]
        return len(bws) == 4 and bws[0] and bws[1] and bws[2] \
               and scale1 < 0.25 and scale2 < 0.25 and scale3 < 0.25

    #
    def swto_probe_rtt(self):
        time_distance = self.ten_sec_wnd[-1][0] -  self.ten_sec_wnd[0][0]
        if  self.bbr_min_rtt_win_sec <=  time_distance <= self.bbr_min_rtt_win_sec + 0.01:
            for time_bw in self.ten_sec_wnd:
                if time_bw[1] <= self.minrtt:
                    return False
        return True

    def update_sec_wnd(self, time_bw):
        if len(self.ten_sec_wnd) <= 1:
            self.ten_sec_wnd.append(time_bw)
        if time_bw[0] - self.ten_sec_wnd[0][0] <= self.bbr_min_rtt_win_sec + 0.01:
            self.ten_sec_wnd.append(time_bw)
        else:
            self.ten_sec_wnd.pop(0)
            self.ten_sec_wnd.append(time_bw)


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
            "pacing_rate": 100.,
            "extra": {
                "delivered": self.delivered_nums
            }
        }

        return output

    def cc_trigger(self, data):

        packet_type = data["packet_type"]
        event_time = data["event_time"]
        packet = data["packet"]
        rtt = packet["Lantency"]


        maxbw, minrtt = float("-inf"), float("inf")
        if packet_type == PACKET_TYPE_FINISHED:
            self.delivered_nums += 1

            send_delivered = packet["Extra"]["delivered"]
            bw = self.cal_bw(send_delivered, rtt)
            time_bw = [event_time, bw]
            self.update_sec_wnd(time_bw)

            maxbw = max(maxbw, bw)
            minrtt = min(minrtt, rtt)

            # todo : feel like delivered_nums is always greater than self.delivered
            # todo : the meaning of sack, the round of rtt
            # todo : the 768 line of bbr source coder

            if self.delivered_nums > self.delivered:
                self.delivered = self.delivered_nums
                self.four_bws[:] = self.four_bws[-3:] + [maxbw]
                self.bbr_bw_rtts -= 1

                if self.bbr_bw_rtts == 0:
                    self.update_bw_rtt(maxbw, minrtt)
                    self.bbr_bw_rtts = 10
                    self.set_output(self.mode)



            if self.swto_probe_rtt():
                self.mode = self.bbr_mode[3]
                self.probe_rtt_time = event_time


        if self.mode == self.bbr_mode[0]:
            if self.stop_increasing(self.four_bws):
                self.mode = self.bbr_mode[1]

        elif self.mode == self.bbr_mode[1]:

            inflight = data['Waiting_for_ack_nums']
            BDP = self.maxbw * self.minrtt
            if BDP < inflight:
                self.mode = self.bbr_mode[2]

        elif self.mode == self.bbr_mode[3]:
            self.cwnd = self.bbr_min_cwnd
            if event_time - self.probe_rtt_time > self.bbr_probe_rtt_mode_ms:
                if self.stop_increasing(self.four_bws):
                    self.mode = self.bbr_mode[2]
                else:
                    self.mode = self.bbr_mode[0]



