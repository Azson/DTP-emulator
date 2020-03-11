from objects.sender import Sender as Super_sender

class Sender(Super_sender):


    def slide_windows(self, cur_time):
        ret = []
        for i in range(int(self.cwnd) - self.get_waiting_ack_nums()):
            if len(self.wait_for_push_packets) == 0:
                _packet = self.new_packet(cur_time + (1.0 / self.rate))
                if _packet is None:
                    return ret
            else:
                _packet = self.wait_for_push_packets.pop(0)[2]
            ret.append(_packet)

        return ret
