from utils import get_ms_time


class Block(object):
    _block_id = 1

    def __init__(self,
                 priority=0,
                 block_id=-1,
                 bytes_size=200000,
                 deadline=0.2,
                 timestamp=None):

        self.priority = priority
        self.block_id = block_id if block_id != -1 else Block.get_next_block_id()
        self.size = bytes_size
        self.deadline = deadline
        self.timestamp = timestamp if not timestamp is None else get_ms_time(1)
        # emulator params
        self.send_delay = 0
        self.latency = 0

        # log params
        self.finish_timestamp = -1
        self.miss_ddl = 0
        self.split_nums = -1
        self.finished_bytes = 0

    @classmethod
    def get_next_block_id(cls):
        ret = cls._block_id
        cls._block_id += 1
        return ret

    def get_cost_time(self):

        return self.send_delay + self.latency

    def get_block_info(self):
        return {
            "Block_id" : self.block_id,
            "Priority" : self.priority,
            "Deadline" : self.deadline,
            "Create_time" : self.timestamp,
            "Size" : self.size
        }

    def __str__(self):

        return str(self.__dict__)