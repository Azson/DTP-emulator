class Packet(object):
    _packet_id = 1

    def __init__(self,
                 create_time,
                 next_hop,
                 block_id,
                 offset,
                 payload,
                 packet_id=None,
                 packet_size=1500,
                 deadline=0.2,
                 packet_type="S",
                 drop = False,
                 send_delay=.0,
                 queue_delay=.0
                 ):
        self.packet_type = packet_type
        self.create_time = create_time
        self.next_hop = next_hop
        self.block_id = block_id
        self.offset = offset
        self.packet_id = packet_id
        self.payload=payload
        self.packet_size=packet_size
        self.deadline = deadline
        self.drop = drop

        self.send_delay = send_delay
        self.queue_delay = queue_delay
        self.propagation_delay = 0.0002

        if packet_id is None:
            self.packet_id = Packet._get_next_packet()


    @classmethod
    def _get_next_packet(cls):
        result = cls._packet_id
        cls._packet_id += 1
        return result


    def parse(self):

        return [self.packet_type,
                self.next_hop,
                self.queue_delay,
                self.drop,
                self.queue_delay,
                self.packet_id]


    def trans2dict(self):
        print_data = {
            "Type": self.packet_type,
            "Position": self.next_hop,
            "Send_delay": self.send_delay,
            "Queue_delay": self.queue_delay,
            "Propagation_delay": self.propagation_delay,
            "Drop": 1 if self.drop else 0,
            "Packet_id": self.packet_id,
            "Block_id": self.block_id,
            "Create_time": self.create_time,
            "Deadline": self.deadline,
            "Offset" : self.offset,
            "Payload" : self.payload,
            "Packet_size" : self.packet_size
        }
        return print_data


    def __lt__(self, other):
        return self.create_time < other.create_time


    def __str__(self):
        print_data = self.trans2dict()
        return str(print_data)