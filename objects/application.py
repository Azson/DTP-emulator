from objects.block import Block
from objects.packet import Packet
import numpy as np
import pandas as pd
from utils import debug_print
import json


class Appication_Layer(object):

    def __init__(self,
                 block_file,
                 create_det=1,
                 bytes_per_packet=1500,
                 RS_N = 10,
                 RS_M = 2
                 ):
        self.block_file = block_file
        self.block_queue = []
        self.bytes_per_packet = bytes_per_packet

        self.block_nums = None
        self.init_time = .0
        self.pass_time = .0
        self.fir_log = True

        self.now_block = None
        self.now_block_offset = 0
        self.head_per_packet = 20

        self.create_det = create_det
        self.handle_block(block_file)
        self.ack_blocks = dict()
        self.blocks_status = dict()

        self.rs_n = RS_N
        self.rs_m = RS_M

        self.now_block_rs_group_counter = 0
        self.now_group_rs_length_needed = RS_N
        self.now_group_rs_data_counter = RS_N
        self.now_group_rs_repair_counter = RS_M
        self.now_group_rs_start = 0

        self.rs_checker = dict()

    def update_rs_parameter(self,n,m):
        self.rs_n = n
        self.rs_m = m

    def handle_block(self, block_file):
        """
        creating block queue by "block_file".
        :param block_file: str
        :return:
        """
        if isinstance(block_file, str):
            block_file = [block_file]
        for single_file in block_file:
            if single_file[-4:] == ".csv":
                self.create_blok_by_csv(single_file)
            else:
                self.create_block_by_file(single_file, self.create_det)

    def create_blok_by_csv(self, csv_file):
        df_data = pd.read_csv(csv_file, header=None)
        shape = df_data.shape
        assert len(shape) >= 2
        if shape[1] == 2:
            df_data.columns = ["time", "size"]
        elif shape[1]== 3:
            df_data.columns = ["time", "size", "key_frame"]

        for idx in range(shape[0]):
            block = Block(bytes_size=float(df_data["size"][idx]),
                          deadline=0.2,
                          timestamp=float(df_data["time"][idx]))
            self.block_queue.append(block)

    def create_block_by_file(self, block_file, det=0.1):
        with open(block_file, "r") as f:
            self.block_nums = int(f.readline())

            pattern_cols = ["type", "size", "ddl"]
            pattern=[]
            for line in f.readlines():
                pattern.append(
                    { pattern_cols[idx]:item.strip() for idx, item in enumerate(line.split(',')) }
                )

            peroid = len(pattern)
            for idx in range(self.block_nums):
                ch = idx % peroid
                block = Block(bytes_size=float(pattern[ch]["size"]),
                              deadline=float(pattern[ch]["ddl"]),
                              timestamp=self.init_time+self.pass_time+idx*det,
                              priority=pattern[ch]["type"])
                self.block_queue.append(block)

    def select_algorithm(self, cur_time, block_queue):
        '''
        The alogrithm to select the block which will be sended in next.
        The following example is selecting block by the radio of rest life time to deadline.
        :param cur_time: float
        :param block_queue: the list of Block.You can get more detail about Block in objects/blocks.py
        :return: int
        '''
        def is_better(block):
            return (cur_time - block.timestamp) * best_block.deadline > \
                    (cur_time - best_block.timestamp) * block.deadline

        best_block_idx = -1
        best_block = None
        for idx, item in enumerate(block_queue):
            if best_block is None or is_better(item) :
                best_block_idx = idx
                best_block = item

        return best_block_idx

    def select_block(self):
        """select the block that not sent and return it  """
        cur_time = self.init_time + self.pass_time
        # call player's code
        best_block_idx = self.select_algorithm(cur_time, self.block_queue)
        if best_block_idx == -1:
            return None
        best_block = self.block_queue.pop(best_block_idx)
        # Is it necessary ? filter block with missing ddl
        for idx in range(len(self.block_queue)-1, -1, -1):
            item = self.block_queue[idx]
            # if miss ddl in queue, clean and log
            if cur_time > item.timestamp + item.deadline:
                self.block_queue[idx].miss_ddl = 1
                self.log_block(self.block_queue[idx])
                self.block_queue.pop(idx)

        return best_block

    def get_next_packet(self, cur_time, mode=None):
        """
        get the packet that can be sent at "cur_time" and return it to sender.
        :param cur_time: float, current time.
        :param mode: if mode is "force", it will return the packet after cur_time in case of lacking of packet.
        :return: Packet.
        """
        self.pass_time = cur_time
        if self.now_block is None or (self.now_block_offset == self.now_block.split_nums and self.now_group_rs_repair_counter == 0):
            self.now_block = self.select_block()
            if self.now_block is None:
                return None
            self.now_block_offset = 0
            self.now_block_rs_group_counter = 0
            self.now_block.split_nums = int(np.ceil(self.now_block.size /
                                            (self.bytes_per_packet - self.head_per_packet)))

            self.blocks_status[self.now_block.block_id] = self.now_block

        # It will only send the packet that already created if mode is None;
        # else will update system time
        if mode != "force" and cur_time < self.now_block.timestamp:
            return None
        payload = self.bytes_per_packet - self.head_per_packet
        if self.now_block.size % (self.bytes_per_packet - self.head_per_packet) and \
                self.now_block_offset == self.now_block.split_nums - 1:
            payload = self.now_block.size % (self.bytes_per_packet - self.head_per_packet)

        if self.now_group_rs_data_counter == 0 and self.now_group_rs_repair_counter == 0:
            
            self.now_block_rs_group_counter += 1
            
            self.now_group_rs_data_counter = self.rs_n
            self.now_group_rs_repair_counter = self.rs_m
            self.now_group_rs_length_needed = self.rs_n
            self.now_group_rs_start = self.now_block_offset

            if (self.now_block.split_nums - self.now_block_offset) < self.now_group_rs_data_counter:
                self.now_group_rs_length_needed = self.now_block.split_nums - self.now_block_offset
                self.now_group_rs_data_counter = self.now_block.split_nums - self.now_block_offset

        if self.now_group_rs_data_counter == 0:
            packet = Packet(create_time=max(cur_time, self.now_block.timestamp),
                            next_hop=0,
                            offset=-1,
                            packet_size=self.bytes_per_packet,
                            payload=payload,
                            block_info=self.now_block.get_block_info(),
                            rs_group = self.now_block_rs_group_counter,
                            rs_length = self.now_group_rs_length_needed,
                            rs_start = self.now_group_rs_start
                            )
            self.now_group_rs_repair_counter -= 1
        else:
            packet = Packet(create_time=max(cur_time, self.now_block.timestamp),
                            next_hop=0,
                            offset=self.now_block_offset,
                            packet_size=self.bytes_per_packet,
                            payload=payload,
                            block_info=self.now_block.get_block_info(),
                            rs_group = self.now_block_rs_group_counter,
                            rs_length = self.now_group_rs_length_needed,
                            rs_start = self.now_group_rs_start
                            )
            self.now_block_offset += 1
            self.now_group_rs_data_counter -= 1

        #print(packet.offset,packet.rs_group,packet.rs_length,packet.rs_start)

        return packet

    def update_block_status(self, packet):
        """update the block finishing status according to the acknowledge packets pushed from sender."""
        block_id = packet.block_info["Block_id"]
        rs_group = packet.rs_group
        rs_group_length_needed = packet.rs_length
        rs_group_start = packet.rs_start

        # filter repeating acked packet
        if block_id in self.ack_blocks and   \
                packet.offset in self.ack_blocks[block_id]:
            return

        if block_id not in self.rs_checker:
            self.rs_checker[block_id] = dict()
        
        if rs_group not in self.rs_checker[block_id]:
            self.rs_checker[block_id][rs_group] = 1
        else:
            self.rs_checker[block_id][rs_group] += 1
            if packet.offset == -1 and self.rs_checker[block_id][rs_group] == rs_group_length_needed:
                for i in range(rs_group_length_needed):
                    if rs_group_start + i not in self.ack_blocks[block_id]:
                        self.ack_blocks[block_id].append(rs_group_start + i)
                        
                        print("repair",rs_group_start + i,block_id)

                        self.blocks_status[block_id].send_delay += packet.send_delay
                        self.blocks_status[block_id].latency += packet.latency
                        #self.blocks_status[block_id].finished_bytes += packet.payload
                        self.blocks_status[block_id].finished_nums += 1

        if packet.offset == -1:
            return

        # update block information.
        # Which is better? Save packet individual value or sum value
        self.blocks_status[block_id].send_delay += packet.send_delay
        # whether or not take pacing delay into consideration?
        self.blocks_status[block_id].latency += packet.latency
        self.blocks_status[block_id].finished_bytes += packet.payload

        self.blocks_status[block_id].finished_nums += 1

        if block_id not in self.ack_blocks:
            self.ack_blocks[block_id] = [packet.offset]
        # retransmission packet may be sended many times
        else:
            self.ack_blocks[block_id].append(packet.offset)

        if self.is_sent_block(block_id):
            self.blocks_status[block_id].finish_timestamp = packet.finish_time
            self.log_block(self.blocks_status[block_id])

    def log_block(self, block):
        """logging the finished blocks or the blocks with missing deadline"""
        if self.fir_log:
            self.fir_log = False
            with open("output/block.log", "w") as f:
                pass

        if not self.is_sent_block(block.block_id):
            block.finish_timestamp = self.init_time + self.pass_time
        if block.is_miss_ddl():
            block.miss_ddl = 1

        with open("output/block.log", "a") as f:
            f.write(json.dumps(block.trans2dict())+'\n')

    def is_sent_block(self, block_id):
        """check whether or not the block with the id of "block_id" is finished."""
        if block_id in self.ack_blocks and \
                len(self.ack_blocks[block_id]) == self.blocks_status[block_id].split_nums:
            return True
        return False

    def close(self):
        """do some operations when system is closing, like logging the blocks with the packets that have not been acked or sent."""
        for block_id, packet_list in self.ack_blocks.items():
            if self.is_sent_block(block_id):
                continue
            debug_print("block {} not finished!".format(block_id))
            self.log_block(self.blocks_status[block_id])
        return None
