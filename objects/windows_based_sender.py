from objects.sender import Sender as Super_sender
import heapq


class Sender(Super_sender):

    def slide_windows(self, cur_time):
        ret = []
        for i in range(int(self.cwnd) - self.get_waiting_ack_nums()):
            if len(self.wait_for_push_packets) == 0:
                _packet = self.new_packet(cur_time + (1.0 / self.rate))
                if _packet is None:
                    return ret
            else:
                _packet = heapq.heappop(self.wait_for_push_packets)[2]
            ret.append(_packet)

        return ret
