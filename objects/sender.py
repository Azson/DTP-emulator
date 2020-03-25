from config.constant import *
from common import sender_obs
from utils import check_solution_format
from objects.application import Appication_Layer


class Sender():

    def __init__(self, path, dest, features, history_len=10, solution=None):
        self.id = Sender._get_next_id()
        self.sent = 0
        self.acked = 0
        self.lost = 0
        self.bytes_in_flight = 0
        self.min_latency = None
        self.rtt_samples = []
        self.sample_time = []
        self.net = None
        self.path = path
        self.dest = dest
        self.history_len = history_len
        self.features = features
        self.history = sender_obs.SenderHistory(self.history_len,
                                                self.features, self.id)

        self.solution = solution
        ret = check_solution_format(self.solution.make_decision())
        self.rate = ret["send_rate"] if "send_rate" in ret else float("inf")
        # Not use this if USE_CWND=FALSE
        self.cwnd = ret["cwnd"] if "cwnd" in ret else 25
        self.starting_rate = self.rate
        self.pacing_rate = ret["pacing_rate"] if "pacing_rate" in ret else float("inf")
        self.cur_time = 0

        self.application = None
        # for cut the packet numbers that can't be sended due to cwnd in log
        self.wait_for_push_packets = []
        self.extra = {}
        # for player
        self.wait_for_select_packets = []

    _next_id = 1

    @classmethod
    def _get_next_id(cls):
        result = Sender._next_id
        Sender._next_id += 1
        return result

    def init_application(self, block_file):
        self.application = Appication_Layer(block_file, bytes_per_packet=BYTES_PER_PACKET)

    def new_packet(self, cur_time, mode):
        packet = self.application.get_next_packet(cur_time, mode)
        if packet:
            packet.send_delay = 1 / self.rate

        return packet

    def clear_miss_ddl(self, cur_time):

        for idx in range(len(self.wait_for_select_packets)-1, -1, -1):
            item = self.wait_for_select_packets[idx]
            if item.is_miss_ddl(cur_time):
                self.wait_for_select_packets.pop(idx)

    def select_packet(self, cur_time):
        while True:
            # if there is no packet can be sended, we need to send packet that created after cur_time
            packet = self.new_packet(cur_time, "force" if len(self.wait_for_select_packets) == 0 else None)
            if not packet:
                break
            self.wait_for_select_packets.append(packet)
        # Is it necessary ? Reduce system burden by delete the packets missing ddl in time
        # self.clear_miss_ddl(cur_time)
        last_hash_vals = [item.get_hash_val() for item in self.wait_for_select_packets]
        # print("wait for select %d, already send %d" % (len(self.wait_for_select_packets), self.sent))
        packet_idx = self.solution.select_packet(cur_time, self.wait_for_select_packets)
        # use hash for safety
        now_hash_vals = [item.get_hash_val() for item in self.wait_for_select_packets]
        if last_hash_vals != now_hash_vals:
            raise ValueError("You shouldn't change the packet information in system!")
        if isinstance(packet_idx, int) and packet_idx >= 0:
            return self.wait_for_select_packets.pop(packet_idx)
        return None

    def apply_rate_delta(self, delta):
        delta *= DELTA_SCALE
        # print("Applying delta %f" % delta)
        if delta >= 0.0:
            self.set_rate(self.rate * (1.0 + delta))
        else:
            self.set_rate(self.rate / (1.0 - delta))

    def apply_cwnd_delta(self, delta):
        delta *= DELTA_SCALE
        # print("Applying delta %f" % delta)
        if delta >= 0.0:
            self.set_cwnd(self.cwnd * (1.0 + delta))
        else:
            self.set_cwnd(self.cwnd / (1.0 - delta))

    def can_send_packet(self):
        ret = self.solution.make_decision()
        self.rate = ret["send_rate"] if "send_rate" in ret else self.rate
        self.cwnd = ret["cwnd"] if "cwnd" in ret else self.cwnd
        self.extra = ret["extra"] if "extra" in ret else self.extra
        if USE_CWND:
            return int(self.bytes_in_flight) / BYTES_PER_PACKET < self.cwnd
        else:
            return True

    def register_network(self, net):
        self.net = net

    def on_packet_sent(self, cur_time):
        self.sent += 1
        self.bytes_in_flight += BYTES_PER_PACKET

        # the old time will <= cur_time if there is no pacing due to the sequential processing
        old_time = self.cur_time
        self.cur_time = max(cur_time, self.cur_time) + 1 / self.pacing_rate
        return max(old_time-cur_time, .0), self.extra

    def on_packet_acked(self, rtt, packet):
        self.acked += 1
        self.rtt_samples.append(rtt)
        if (self.min_latency is None) or (rtt < self.min_latency):
            self.min_latency = rtt
        self.bytes_in_flight -= BYTES_PER_PACKET
        self.application.update_block_status(packet)

    def on_packet_lost(self, event_time, packet):
        self.lost += 1
        self.bytes_in_flight -= BYTES_PER_PACKET
        # do retrans if lost
        retrans_packet = packet.create_retrans_packet(event_time)
        self.wait_for_push_packets.append([event_time, self, retrans_packet])

    def set_rate(self, new_rate):
        self.rate = new_rate
        # print("Attempt to set new rate to %f (min %f, max %f)" % (new_rate, MIN_RATE, MAX_RATE))
        if self.rate > MAX_RATE:
            self.rate = MAX_RATE
        if self.rate < MIN_RATE:
            self.rate = MIN_RATE

    def set_cwnd(self, new_cwnd):
        self.cwnd = int(new_cwnd)
        # print("Attempt to set new rate to %f (min %f, max %f)" % (new_rate, MIN_RATE, MAX_RATE))
        if self.cwnd > MAX_CWND:
            self.cwnd = MAX_CWND
        if self.cwnd < MIN_CWND:
            self.cwnd = MIN_CWND

    def get_waiting_ack_nums(self):
        return int(self.bytes_in_flight) // BYTES_PER_PACKET

    def record_run(self):
        smi = self.get_run_data()
        self.history.step(smi)

    def get_obs(self):
        return self.history.as_array()

    def get_run_data(self):
        obs_end_time = self.net.get_cur_time()

        # obs_dur = obs_end_time - self.obs_start_time
        # print("Got %d acks in %f seconds" % (self.acked, obs_dur))
        # print("Sent %d packets in %f seconds" % (self.sent, obs_dur))
        # print("self.rate = %f" % self.rate)
        # print(self.rtt_samples)
        return sender_obs.SenderMonitorInterval(
            self.id,
            bytes_sent=self.sent * BYTES_PER_PACKET,
            bytes_acked=self.acked * BYTES_PER_PACKET,
            bytes_lost=self.lost * BYTES_PER_PACKET,
            send_start=self.obs_start_time,
            send_end=obs_end_time,
            recv_start=self.obs_start_time,
            recv_end=obs_end_time,
            rtt_samples=self.rtt_samples,
            packet_size=BYTES_PER_PACKET
        )

    def reset_obs(self):
        self.sent = 0
        self.acked = 0
        self.lost = 0
        self.rtt_samples = []
        self.obs_start_time = self.net.get_cur_time()

    def print_debug(self):
        print("Sender:")
        print("Obs: %s" % str(self.get_obs()))
        print("Rate: %f" % self.rate)
        print("Sent: %d" % self.sent)
        print("Acked: %d" % self.acked)
        print("Lost: %d" % self.lost)
        print("Min Latency: %s" % str(self.min_latency))

    def reset(self):
        # print("Resetting sender!")
        self.rate = self.starting_rate
        self.bytes_in_flight = 0
        self.min_latency = None
        self.reset_obs()
        self.history = sender_obs.SenderHistory(self.history_len,
                                                self.features, self.id)

    def __lt__(self, other):
        return False