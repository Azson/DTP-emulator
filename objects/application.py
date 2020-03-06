from objects.block import Block
from objects.packet import Packet
import numpy as np
from player import block_selection


class Appication_Layer(object):


    def __init__(self,
                 block_file,
                 create_det=0.1,
                 bytes_per_packet=1500):
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

        self.create_block_by_file(create_det)
        self.ack_blocks = dict()
        self.blocks_status = dict()
        self.block_selection = block_selection.Solution()


    def create_block_by_file(self, det=0.1):
        with open(self.block_file, "r") as f:
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


    def select_block(self):

        cur_time = self.init_time + self.pass_time
        # call player's code
        best_block_idx = self.block_selection.select_block(cur_time, self.block_queue)
        if best_block_idx == -1:
            return None
        best_block = self.block_queue[best_block_idx]

        self.block_queue.pop(best_block_idx)
        # filter block with missing ddl
        for idx in range(len(self.block_queue)-1, -1, -1):
            item = self.block_queue[idx]
            # if miss ddl in queue, clean and log
            if cur_time > item.timestamp + item.deadline:
                self.block_queue[idx].miss_ddl = 1
                self.log_block(self.block_queue[idx])
                self.block_queue.pop(idx)

        return best_block


    def get_retrans_packet(self):
        for block_id, packet_list in self.ack_blocks.items():
            if self.is_sended_block(block_id):
                continue
            for i in range(self.blocks_status[block_id].split_nums):
                if i not in packet_list:
                    return i
        return None


    def get_next_packet(self, cur_time):
        self.pass_time = cur_time
        retrans_packet = None
        if self.now_block is None or self.now_block_offset == self.now_block.split_nums:
            # 1. the retransmisson time is bad, which may cause consistently loss packet
            # 2. the packet will be retransmission many times for a while
            retrans_packet = self.get_retrans_packet()
            if retrans_packet:
                self.now_block_offset = retrans_packet
            else:
                self.now_block = self.select_block()
                if self.now_block is None:
                    return None

                self.now_block_offset = 0
                self.now_block.split_nums = int(np.ceil(self.now_block.size /
                                                (self.bytes_per_packet - self.head_per_packet)))
                self.blocks_status[self.now_block.block_id] = self.now_block

        if self.now_block is None:
            return None
        payload = self.bytes_per_packet - self.head_per_packet
        if self.now_block.size % (self.bytes_per_packet - self.head_per_packet) and \
                self.now_block_offset == self.now_block.split_nums - 1:
            payload = self.now_block.size % (self.bytes_per_packet - self.head_per_packet)

        packet = Packet(create_time=cur_time,
                          next_hop=0,
                          block_id=self.now_block.block_id,
                          offset=self.now_block_offset,
                          packet_size=self.bytes_per_packet,
                          payload=payload
                          )
        if retrans_packet is None:
            self.now_block_offset += 1
        else:
            self.now_block_offset = self.now_block.split_nums

        return packet


    def update_block_status(self, packet):
        # filter repeating acked packet
        if packet.block_id in self.ack_blocks and   \
            packet.offset in self.ack_blocks[packet.block_id]:
            return

        # update block information.
        # Which is better? Save packet individual value or sum value
        self.blocks_status[packet.block_id].send_delay += packet.send_delay
        self.blocks_status[packet.block_id].queue_delay += packet.queue_delay
        self.blocks_status[packet.block_id].propagation_delay += packet.propagation_delay
        self.blocks_status[packet.block_id].finished_bytes += packet.payload

        if packet.block_id not in self.ack_blocks:
            self.ack_blocks[packet.block_id] = [packet.offset]
        # retransmission packet may be sended many times
        else:
            self.ack_blocks[packet.block_id].append(packet.offset)
            # Assuming every block can be split into more than 1 packet.
            if self.is_sended_block(packet.block_id):
                self.log_block(self.blocks_status[packet.block_id])


    def log_block(self, block):

        if self.fir_log:
            self.fir_log = False
            with open("output/block.log", "w") as f:
                pass

        block.finish_timestamp = self.init_time + self.pass_time
        if block.get_cost_time() > block.deadline:
            block.miss_ddl = 1

        with open("output/block.log", "a") as f:
            f.write(str(block)+'\n')


    def is_sended_block(self, block_id):
        if len(self.ack_blocks[block_id]) == self.blocks_status[block_id].split_nums:
            return True
        return False


    def analyze_application(self):
        pass