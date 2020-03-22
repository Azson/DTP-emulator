from config.constant import *
from objects.cc_base import CongestionControl
from player.examples.reno import Reno
import random


class BBR(Reno):

    def __init__(self):
        self._input_list = []
        self.call_nums = 0

        self.maxbw = float("-inf")
        self.minrtt = float("inf")

        self.bbr_mode = ["BBR_STARTUP", "BBR_DRAIN", "BBR_PROBE_BW", "BBR_PROBE_RTT"]
        self.mode = "BBR_STARTUP"

        # Window length of bw filter (in rounds)
        self.bbr_bw_rtts = 10

        # Window length of min_rtt filter (in sec)
        self.bbr_min_rtt_win_sec = 5

        # Minimum time (in s) spent at bbr_cwnd_min_target in BBR_PROBE_RTT mode
        self.bbr_probe_rtt_mode_s = 0.2

        self.bbr_high_gain = 2885 / 1000 + 1
        self.bbr_drain_gain = 1000 / 2885

        # probe_bw
        self.bbr_cwnd_gain = 2
        self.probe_bw_gain = [5 / 4, 4 / 3, 1, 1, 1, 1, 1, 1]
        self.cycle_index = 0

        self.probe_rtt_gain = 1

        self.bbr_min_cwnd = 4

        self.pacing_gain = self.bbr_high_gain
        self.cwnd_gain = self.bbr_high_gain

        # to check when the mode come to drain
        self.four_bws = [0] * 4

        # the start time of probe rtt
        self.probe_rtt_time = 0
        self.delivered_nums = 0

        # used to check when come to PROBE_RTT mode
        self.ten_sec_wnd = []

        self.send_rate = float("inf")
        self.cwnd = 10
        #  high_gain * init_cwnd / RTT
        self.pacing_rate = self.bbr_high_gain * self.cwnd / 0.002
        # for sampling
        self.bw_windows = []

    def get_max_bw(self):
        return max(self.bw_windows)

    def append_bw(self, now_bw):
        self.bw_windows.append(now_bw)
        # keep the latest 10 bbr_bw_rtts bw
        if len(self.bw_windows) > self.bbr_bw_rtts:
            self.bw_windows.pop(0)

    # calculate rtt and bw on ack
    def cal_bw(self, send_delivered, rtt):
        delivered = self.delivered_nums - send_delivered
        return delivered / rtt

    def stop_increasing(self, bws):
        if len(bws) < 4:
            return False
        thresh = 0.1
        scale1 = (bws[1] - bws[0]) / bws[0]
        scale2 = (bws[2] - bws[1]) / bws[1]
        scale3 = (bws[3] - bws[2]) / bws[2]
        return scale1 < thresh and scale2 < thresh and scale3 < thresh

    # def swto_probe_rtt(self):
    #     for time_rtt in self.ten_sec_wnd:
    #         if time_rtt[1] <= self.minrtt:
    #             return False
    #     return True

    def update_min_rtt(self, event_time):
        # making sure the rtt data is in 10s
        # the last item is from now packet, so their difference=0
        while event_time - self.ten_sec_wnd[0][0] >= self.bbr_min_rtt_win_sec :
            self.ten_sec_wnd.pop(0)
        idx = -1
        for i, time_rtt in enumerate(self.ten_sec_wnd):
            if idx == -1 or time_rtt[1] < self.ten_sec_wnd[idx][1]:
                idx = i
        # now rtt is not the minist
        if idx == -1 or idx != len(self.ten_sec_wnd)-1:
            return False
        # update min rtt in new round
        self.minrtt = self.ten_sec_wnd[idx][1]
        # begin with the time with min rtt
        self.ten_sec_wnd = self.ten_sec_wnd[idx:]
        return  True

    def set_output(self, mode):
        # pacing_gain, cwnd_gain = self.cal_gain(mode)
        # it seems that there is a minest pacing rate
        # ref : https://code.woboq.org/linux/linux/net/ipv4/tcp_bbr.c.html#259
        # print(self.maxbw, self.minrtt)
        self.pacing_rate = max(self.pacing_gain * self.maxbw, 1000.)
        self.cwnd = max(self.maxbw * self.minrtt * self.cwnd_gain, 4)

    def cal_gain(self, mode):
        pacing_gain, cwnd_gain = 0, 0
        if mode == self.bbr_mode[0]:
            pacing_gain = self.bbr_high_gain
            cwnd_gain = self.bbr_high_gain

        elif mode == self.bbr_mode[1]:
            pacing_gain = self.bbr_drain_gain
            cwnd_gain = self.bbr_high_gain

        elif mode == self.bbr_mode[2]:
            pacing_gain = 1 if self.stop_increasing(self.four_bws) else self.probe_bw_gain[self.cycle_index]
            cwnd_gain = self.bbr_cwnd_gain
            self.cycle_index += 1
            if self.cycle_index == len(self.probe_bw_gain):
                self.cycle_index = 1

        elif mode == self.bbr_mode[3]:
            pacing_gain = 1
            cwnd_gain = 1
        return pacing_gain, cwnd_gain

    def make_decision(self):
        self.call_nums += 1

        output = {
            "cwnd": self.cwnd,
            "send_rate": float("inf"),
            "pacing_rate": self.pacing_rate,
            "extra": {
                "delivered": self.delivered_nums,
                "pcing_rate" : self.pacing_rate,
                "pacing_gain" : self.pacing_gain,
                "cwnd_gain" : self.cwnd_gain,
                "max_bw" : self.maxbw,
                "min_rtt" : self.minrtt,
                "mode" : self.mode
            }
        }

        return output

    def cc_trigger(self, data):

        packet_type = data["packet_type"]
        event_time = data["event_time"]
        packet = data["packet"]
        rtt = packet["Lantency"] + packet["Pacing_delay"]

        if packet_type == PACKET_TYPE_FINISHED:
            self.delivered_nums += 1

            send_delivered = packet["Extra"]["delivered"]
            # update bandwidth
            bw = self.cal_bw(send_delivered, rtt)
            self.append_bw(bw)
            self.four_bws = self.bw_windows[-4:]
            self.bbr_bw_rtts -= 1
            if self.bbr_bw_rtts == 0:
                self.maxbw = self.get_max_bw()
                self.bbr_bw_rtts = 10
            # if is the first
            if self.maxbw == float("-inf"):
                self.maxbw = bw
                self.minrtt = rtt

            if self.mode == self.bbr_mode[0]:
                if self.stop_increasing(self.four_bws):
                    self.mode = self.bbr_mode[1]

            if self.mode == self.bbr_mode[1]:
                inflight = packet["Extra"]["inflight"]
                BDP = self.maxbw * self.minrtt
                if BDP >= inflight:
                    self.mode = self.bbr_mode[2]
                    self.cycle_index = 0

            if self.mode == self.bbr_mode[3]:
                if event_time - self.probe_rtt_time >= self.bbr_probe_rtt_mode_s:
                    if self.stop_increasing(self.four_bws):
                        self.mode = self.bbr_mode[2]
                        self.cycle_index = 1
                    else:
                        self.mode = self.bbr_mode[0]
            # update RTT
            # value of ten_sec_wnd
            time_rtt = [event_time, rtt]
            self.ten_sec_wnd.append(time_rtt)
            # rtt window exceed
            if event_time - self.ten_sec_wnd[0][0] >= self.bbr_min_rtt_win_sec:
                flag = self.update_min_rtt(event_time)
                # now rtt is not the minest, so enter prob_rtt
                if not flag:
                    self.mode = self.bbr_mode[3]
                    self.cwnd = self.bbr_min_cwnd
                    self.probe_rtt_time = event_time
            # find new min rtt in bbr_min_rtt_win_sec
            elif rtt < self.ten_sec_wnd[0][1]:
                self.minrtt = rtt
                self.ten_sec_wnd = self.ten_sec_wnd[-1:]
            # update gains
            self.pacing_rate, self.cwnd_gain = self.cal_gain(self.mode)
            # when we should calculate pacing and cwnd ?
            self.set_output(self.mode)
            # print(self.cwnd, self.cwnd_gain, self.pacing_rate, self.pacing_gain)