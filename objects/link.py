import random
from config.constant import BYTES_PER_PACKET
import numpy as np


class Link():

    def __init__(self, trace_list, queue_size):
        '''
        :param trace_list: [[time, bandwith, loss_rate, delay] ...]
        :param queue_size:
        '''
        self.trace_list = trace_list
        if len(trace_list) == 0:
            self.bandwith = np.inf
            self.loss_rate = .0
            self.delay = .001
        else:
            self.bandwith = trace_list[0][1] * 10**6 / BYTES_PER_PACKET
            self.loss_rate = trace_list[0][2]
            self.delay = trace_list[0][3]

        self.queue_delay = 0.0
        self.queue_delay_update_time = 0.0
        self.max_queue_delay = queue_size / self.bandwith

        self.extra_delay = 0
        self.queue_size = queue_size
        self.trace_start_id = 0


    def get_cur_queue_delay(self, event_time):
        return max(0.0, self.queue_delay - (event_time - self.queue_delay_update_time))


    def get_cur_latency(self, event_time):
        return self.delay + self.get_cur_queue_delay(event_time)


    def packet_enters_link(self, event_time):
        if (random.random() < self.loss_rate):
            return False
        self.queue_delay = self.get_cur_queue_delay(event_time)
        self.queue_delay_update_time = event_time
        self.extra_delay = self.send_delay(event_time) # 1.0 / self.bandwith
        # print("Extra delay: %f, Current delay: %f, Max delay: %f" % (extra_delay, self.queue_delay, self.max_queue_delay))
        if self.extra_delay + self.queue_delay > self.max_queue_delay:
            # print("\tDrop!")
            return False
        self.queue_delay += self.extra_delay
        # print("\tNew delay = %f" % self.queue_delay)
        return True


    def send_delay(self, event_time):

        rest_block_size = 1
        transmition_time = 0
        # different bandwith
        for i in range(self.trace_start_id, len(self.trace_list)):
            if rest_block_size <= 0:
                break
            if event_time + transmition_time > self.trace_list[i][0]:
                continue

            used_time = rest_block_size / self.bandwith
            tmp = self.trace_list[i][0] - (event_time + transmition_time)
            if used_time > tmp:
                used_time = tmp
                rest_block_size -= used_time * self.bandwith
                self.bandwith = self.trace_list[i][1] * 10 ** 6 / BYTES_PER_PACKET
            else:
                rest_block_size = 0
            transmition_time += used_time
            self.trace_start_id = i

        if rest_block_size > 0:
            transmition_time += rest_block_size / self.bandwith

        self.max_queue_delay = self.queue_size / self.bandwith

        return transmition_time


    def print_debug(self):
        print("Link:")
        print("Bandwidth: %f" % self.bandwith)
        print("Delay: %f" % self.delay)
        print("Queue Delay: %f" % self.queue_delay)
        print("Max Queue Delay: %f" % self.max_queue_delay)
        print("One Packet Queue Delay: %f" % (1.0 / self.bandwith))


    def reset(self):
        self.queue_delay = 0.0
        self.queue_delay_update_time = 0.0