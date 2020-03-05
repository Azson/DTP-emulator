DELTA_SCALE = 0.9

MAX_CWND = 5000
MIN_CWND = 4

MAX_RATE = 1000
MIN_RATE = 40

REWARD_SCALE = 0.001

EVENT_TYPE_SEND = 'S'
EVENT_TYPE_ACK = 'A'

BYTES_PER_PACKET = 1500
HEAD_PER_PACKAET = 20

LATENCY_PENALTY = 1.0
LOSS_PENALTY = 1.0

USE_LATENCY_NOISE = False
MAX_LATENCY_NOISE = 1.1

USE_CWND = True
MAX_QUEUE = 5
MIN_QUEUE = 5

PACKET_TYPE_FINISHED = 'F'
PACKET_TYPE_TEMP = 'T'
PACKET_TYPE_DROP = 'D'