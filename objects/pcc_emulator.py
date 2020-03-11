import json, random
import numpy as np

from utils import (
    get_emulator_info
)
from objects.sender import Sender
from objects.windows_based_sender import Sender as W_sender
from objects.link import Link
from objects.engine import Engine

from player import congestion_control_algorithm


class PccEmulator(object):

    def __init__(self,
                 block_file=None,
                 trace_file=None,
                 queue_range=None):

        self.trace_cols = ("time", "bandwith", "loss_rate", "delay")
        self.queue_range = queue_range if queue_range else (10, 20)
        self.trace_file = trace_file
        self.block_file = block_file
        self.event_record = { "Events" : [] }

        # unkown params
        self.features = [] # ["send rate", "recv rate"]
        self.history_len = 1
        self.steps_taken = 0

        self.links = None
        self.senders = None
        self.create_new_links_and_senders()
        self.net = Engine(self.senders, self.links)


    def get_trace(self):

        trace_list = []
        with open(self.trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))
                if len(trace_list[-1]) != len(self.trace_cols):
                    raise ValueError("Trace file error!\nPlease check its format like : {0}".format(self.trace_cols))

        if len(trace_list) == 0:
            raise ValueError("Trace file error!\nThere is no data in the file!")

        return trace_list


    def create_new_links_and_senders(self):

        self.trace_list = self.get_trace()
        # queue = 1 + int(np.exp(random.uniform(*self.queue_range)))
        # print("queue size : %d" % queue)
        # bw = self.trace_list[0][1]

        queue = int(random.uniform(*self.queue_range))
        self.links = [Link(self.trace_list, queue) , Link([], queue)]
        #self.senders = [Sender(0.3 * bw, [self.links[0], self.links[1]], 0, self.history_len)]
        #self.senders = [Sender(random.uniform(0.2, 0.7) * bw, [self.links[0], self.links[1]], 0, self.history_len)]
        self.senders = [W_sender(self.links, 0, self.features,
                               history_len=self.history_len, solution=congestion_control_algorithm.Solution())]
        for item in self.senders:
            item.init_application(self.block_file)


    def run_for_dur(self, during_time):

        # action = [0.9, 0.9]
        # for i in range(len(self.senders)):
        #     self.senders[i].apply_rate_delta(action[0])
        #     if USE_CWND:
        #         self.senders[i].apply_cwnd_delta(action[1])

        reward = self.net.run_for_dur(during_time)
        for sender in self.senders:
            sender.record_run()

        sender_obs = self._get_all_sender_obs()
        sender_mi = self.senders[0].get_run_data()
        event = get_emulator_info(sender_mi)
        event["reward"] = reward
        self.event_record["Events"].append(event)
        if event["Latency"] > 0.0:
            self.run_dur = 0.5 * sender_mi.get("avg latency")

        return event, sender_obs


    def print_debug(self):
        print("---Link Debug---")
        for link in self.links:
            link.print_debug()
        print("---Sender Debug---")
        for sender in self.senders:
            sender.print_debug()


    def reset(self):
        self.steps_taken = 0
        self.net.reset()
        self.create_new_links_and_senders()
        self.net = Engine(self.senders, self.links)
        self.episodes_run += 1
        if self.episodes_run > 0 and self.episodes_run % 100 == 0:
            self.dump_events_to_file("pcc_env_log_run_%d.json" % self.episodes_run)
        self.event_record = {"Events": []}
        self.net.run_for_dur(self.run_dur)
        self.net.run_for_dur(self.run_dur)
        self.reward_ewma *= 0.99
        self.reward_ewma += 0.01 * self.reward_sum
        print("Reward: %0.2f, Ewma Reward: %0.2f" % (self.reward_sum, self.reward_ewma))
        self.reward_sum = 0.0
        return self._get_all_sender_obs()


    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None


    def dump_events_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.event_record, f, indent=4)


    def _get_all_sender_obs(self):
        sender_obs = self.senders[0].get_obs()
        sender_obs = np.array(sender_obs).reshape(-1, )
        # print(sender_obs)
        return sender_obs