import heapq, random
from config.constant import *
from utils import get_packet_type


class Engine():

    def __init__(self, senders, links):
        self.q = []
        self.cur_time = 0.0
        self.senders = senders
        self.links = links
        self.queue_initial_packets()

        self.fir_log = True
        self.log_packet_file = "output/pcc_emulator_packet.log"


    def queue_initial_packets(self):
        for sender in self.senders:
            sender.register_network(self)
            sender.reset_obs()
            packet = sender.new_packet(1.0 / sender.rate)
            if packet:
                heapq.heappush(self.q, (1.0 / sender.rate, sender, packet))


    def reset(self):
        self.cur_time = 0.0
        self.q = []
        [link.reset() for link in self.links]
        [sender.reset() for sender in self.senders]
        self.queue_initial_packets()


    def get_cur_time(self):
        return self.cur_time


    def run_for_dur(self, dur):
        end_time = self.cur_time + dur
        for sender in self.senders:
            sender.reset_obs()

        while self.cur_time < end_time:
            if len(self.q) == 0:
                print("There is no packet from application~")
                return

            event_time, sender, packet = heapq.heappop(self.q)
            self.log_packet(event_time, sender, packet)

            event_type, next_hop, cur_latency, dropped, life, packet_id = packet.parse()
            # print("Got event %s, to link %d, latency %f at time %f" % (event_type, next_hop, cur_latency, event_time))
            self.cur_time = event_time
            new_event_time = event_time
            new_event_type = event_type
            new_next_hop = next_hop
            new_latency = cur_latency
            new_dropped = dropped
            push_new_event = False

            if event_type == EVENT_TYPE_ACK:
                # got ack in source or destination
                if next_hop == len(sender.path):
                    self.append_cc_input(event_time, sender, packet)
                    if dropped:
                        sender.on_packet_lost()
                        # print("Packet lost at time %f" % self.cur_time)
                    else:
                        sender.on_packet_acked(cur_latency, packet)
                        # print("Packet acked at time %f" % self.cur_time)
                    # for reno
                    while _packet in sender.slide_windows(self.cur_time):
                        heapq.heappush(self.q, (self.cur_time, sender, _packet))

                # ack back to source
                else:
                    new_next_hop = next_hop + 1
                    # bug : not update last enter link time. How treat drop packet from last link
                    link_latency = sender.path[next_hop].get_cur_latency(self.cur_time)
                    if USE_LATENCY_NOISE:
                        link_latency *= random.uniform(1.0, MAX_LATENCY_NOISE)
                    new_latency += link_latency
                    new_event_time += link_latency
                    push_new_event = True
            if event_type == EVENT_TYPE_SEND:
                if next_hop == 0:
                    # print("Packet sent at time %f" % self.cur_time)
                    if sender.can_send_packet():
                        sender.on_packet_sent()
                        push_new_event = True
                    _packet = sender.new_packet(self.cur_time + (1.0 / sender.rate))
                    if _packet:
                        if sender.cwnd > 1 + len(self.q) + len(sender.wait_for_push_packets):
                            heapq.heappush(self.q, (self.cur_time + (1.0 / sender.rate), sender, _packet))
                        else:
                            sender.wait_for_push_packets.append([event_time, sender, _packet])

                else:
                    push_new_event = True

                if next_hop == sender.dest:
                    new_event_type = EVENT_TYPE_ACK
                new_next_hop = next_hop + 1
                link_latency = sender.path[next_hop].get_cur_latency(self.cur_time)
                if USE_LATENCY_NOISE:
                    link_latency *= random.uniform(1.0, MAX_LATENCY_NOISE)
                new_latency += link_latency
                new_event_time += link_latency
                new_dropped = not sender.path[next_hop].packet_enters_link(self.cur_time)
                life += link_latency + sender.path[next_hop].extra_delay

            if push_new_event:
                packet.next_hop = new_next_hop
                packet.packet_type = new_event_type
                packet.queue_delay = new_latency
                packet.drop = new_dropped
                heapq.heappush(self.q, (new_event_time, sender, packet))

        sender_mi = self.senders[0].get_run_data()
        throughput = sender_mi.get("recv rate")
        latency = sender_mi.get("avg latency")
        loss = sender_mi.get("loss ratio")
        # bw_cutoff = self.links[0].bw * 0.8
        # lat_cutoff = 2.0 * self.links[0].dl * 1.5
        # loss_cutoff = 2.0 * self.links[0].lr * 1.5
        # print("thpt %f, bw %f" % (throughput, bw_cutoff))
        # reward = 0 if (loss > 0.1 or throughput < bw_cutoff or latency > lat_cutoff or loss > loss_cutoff) else 1 #

        # Super high throughput
        # reward = REWARD_SCALE * (20.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)

        # Very high thpt
        reward = (10.0 * throughput / (8 * BYTES_PER_PACKET) - 1e3 * latency - 2e3 * loss)

        # High thpt
        # reward = REWARD_SCALE * (5.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)

        # Low latency
        # reward = REWARD_SCALE * (2.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)
        # if reward > 857:
        # print("Reward = %f, thpt = %f, lat = %f, loss = %f" % (reward, throughput, latency, loss))

        # reward = (throughput / RATE_OBS_SCALE) * np.exp(-1 * (LATENCY_PENALTY * latency / LAT_OBS_SCALE + LOSS_PENALTY * loss))
        return reward * REWARD_SCALE


    def log_packet(self, event_time, sender, packet):
        '''
        packet is tuple of (event_time, sender, event_type, next_hop, cur_latency, dropped, packet_id, life)
        :param packet: tuple
        :return: Packet
        '''

        if self.fir_log:
            self.fir_log = False
            with open(self.log_packet_file, "w") as f:
                pass

        log_data = {
            "Time" : event_time,
            "Cwnd" : sender.cwnd,
            # "Send_rate" : sender.rate,
            "Waiting_for_ack_nums" : sender.get_waiting_ack_nums()
        }
        log_data.update(packet.trans2dict())

        with open(self.log_packet_file, "a") as f:
            f.write(str(log_data)+"\n")

        return packet


    def append_cc_input(self, event_time, sender, packet, event_type="packet"):

        if event_type == "packet":
            data = {
                "event_time" : event_time,
                "link_rate" : -1 if packet.next_hop == 0 else sender.path[packet.next_hop-1].bandwith,
                "send_rate" : sender.rate,
                "packet_type" : get_packet_type(sender, packet),
                "packet" : packet.trans2dict()
            }
        # todo : how to design system information
        elif event_type == "system":
            data = {

            }

        feed_back = sender.solution.append_input(data)
        if feed_back:
            sender.cwnd = feed_back["cwnd"]
            sender.rate = feed_back["send_rate"]