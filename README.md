# Quickly Start

For players, you need to finish the code both of  "congestion_control_algorithm.py" 
and "block_selection.py" files in path of "/player".

Here we provide you some congestion control algorithm.
By default the congestion control is "reno" and block selection algorithm is selecting block which is closest to it's deadline.

Then, just run the order "python3 main.py".

You will get some output in the path "/output/" and should fix your code according to the output.

# For Detail

## player

Here are the 2 modules that players need to finished.

### block_selection.py

In this module, you have to implement the function "select_block" with the parameters "cur_time, block_queue" and return an integer value which means the block index in block queue, which will be sent at the time "cur_time".

#### select_block

For every block in block queue, it's implement in "objects/block.py". But we recommend you to get more information at  [Block](#block-log) .

### congestion_control_algorithm.py

In this module, you have to implement a class with member function "make_decision" and "append_input". So we recommend you to accomplish this by inheriting from the object of "CongestionControl" implemented in "cc_base.py" in case you forget these. 

#### make_decision

For the member function "make_decision", we will call it every time I want to send a packet. And it should return a dictionary with window size and send rate according to the information from "_input_list", just like below.

```json
{
    "cwnd" : 10,
    "send_rate" : 10
}
```

#### append_input

For item information in "_input_list",  it is a triad of **(event_time, packet_type, and packet)**. 

- event_time

  > The time when the packet arrived.

- packet_type

  > We divide the packet into three categories : PACKET_TYPE_FINISHED, PACKET_TYPE_TEMP, PACKET_TYPE_DROP.
  >
  > PACKET_TYPE_FINISHED : The acknowledge packet that successfully reached the source point;
  >
  > PACKET_TYPE_TEMP : The packet that have not yet reached the source point;
  >
  > PACKET_TYPE_DROP : The packet used to inform the source point of packet loss.

- packet

  > The packet it the object implemented in "objects/packet.py". But we recommend you to get more information at [Packet](#packet-log) .

Why we design a individual function to add element to "_input_list"?

It's because there are some congestion control algorithm that need to update window size and send rate immediately. So you need to return a dictionary with window size and send rate if you want to do some changes as soon as the data is received , like [here](#make_decision).

## config

### Block data

We create the block by using the file "data_audio.csv" and "data_video.csv" which are record from WebRTC.

For "data_audio.csv", the first columns is the created time of block and the second columns is the block size. 

| 时间 (s) | 数据大小 (B) |
| -------- | ------------ |
| 0.0      | 514          |
| 0.06     | 305          |
| ...      | ...          |

For "data_video.csv", it has the same columns like "data_audio.csv" except the third columns, which means P frame or I frame.

| 时间 (s) | 数据大小 (B) | 关键帧 |
| -------- | ------------ | ------ |
| 0.0      | 9584         | P      |
| 0.033    | 8069         | P      |
| ...      | ...          | ...    |

### Trace data

We use the generated trace data by using the Hidden Markov algorithm to simulate the bandwidth changing of the network, which is implemented in "scripts/network.py". 

For the trace file, the first columns is the changed time of bandwidth. The second columns is the bandwidth whose unit is megabytes. And the third columns is the link random loss rate. Finally, the last columns is the fixed propagation delay of link whose unit is seconds.

| 时间 (s) | 带宽 (MB)          | 丢包率 | 传播时延 (s) |
| -------- | ------------------ | ------ | ------------ |
| 0        | 19.38592070201254  | 0      | 0.001        |
| 1        | 24.832955411664393 | 0      | 0.001        |
| ...      | ...                | ...    | ...          |

## objects

Here are all the objects that our system uses. You can get more details from our powerpoint presentation.

What I want to emphasize here is that, your congestion control module, which implemented in "player/congestion_control_algorithm.py", should inherit from the object of "CongestionControl" implemented in "cc_base.py". 

We've provided some examples of classic congestion control algorithms in path "player/examples", like [Reno](https://en.wikipedia.org/wiki/TCP_congestion_control), [BBR](https://en.wikipedia.org/wiki/BBR) .

## output

### packet log

We will output all the packet log into the directory. Here you can get one packet all life time.

Because of there may be so many packet information that logging file is big. So we split all information into different files if its rows exceed **MAX_PACKET_LOG_ROWS** which you can reset in "config/constant.py".

For every row,  it's form like below：

```json
{
    "Time": 0.001,
    "Cwnd": 1, 
    "Waiting_for_ack_nums": 1, 
    "Type": "A", 
    "Position": 1, 
    "Send_delay": 0.0, 
    "Lantency": 0.001, 
    "Drop": 0, 
    "Packet_id": 1, 
    "Block_id": 1, 
    "Create_time": 0.0, 
    "Deadline": 0.2, 
    "Offset": 0, 
    "Payload": 1480, 
    "Packet_size": 1500
}
```

Here is every key's explanation：

- Time : The time handle this event;
- Cwnd : The size of crowded window at sender.Its unit is packet; 
- Waiting_for_ack_nums : The numbers of packets that sended but not acknowledged by source.
- Type : To distinguish sending or acknowledge packet;
- Send_delay : The time that packet sent into window;
- Lantency : The time that packet spending on links including queue delay and propagation delay;
- Drop : Label whether the packet is dropped;
- Packet_id : The Identity of packet;
- Block_id : The identity of the block to which the packet belongs;
- Create_time : The time when the packet is created;
- Deadline : The deadline of the block to which the packet belongs;
- Offset : The offset of the packet in its block;
- Payload : The size of valid data in packet whose unit is bytes;
- Packet_size : The size of the packet whose unit is bytes;

### block log

Here is all of the blocks that the system sent.

For every row, it's form like below：

``` json
{
    "priority": 0, 
    "block_id": 1, 
    "size": 9584, 
    "deadline": 0.2, 
    "timestamp": 0.0, 
    "send_delay": 0.0, 
    "latency": 0.014309502968274143, 
    "finish_timestamp": 0.014309502968274143, 
    "miss_ddl": 0, 
    "split_nums": 7, 
    "finished_bytes": 9584
}
```

Here is every key's explanation：

- priority : The degree of emergency of block;
- block_id : The identity of block;
- size : The size of block whose unit is bytes;
- deadline : The block's failure time size;
- timestamp : The time when block is created;
- send_delay : The sum of all packets's "send_delay" which belong to the block;
- latency : The sum of all packets's "latency" which belong to the block;
- finish_timestamp :  The time when block is finished if it don't miss deadine; Otherwise, it's the time when the block was detected failure;
- miss_ddl : Whether the block is miss deadline;
- split_nums : The count of packets that the block is divided;
- finished_bytes : The number of bytes received by the receiver.

### cwnd_changing.png

Here we provided a simple schematic diagram of window change process according to partial packet log.

The horizontal axis is the time(seconds), the left vertical axis is the number of packets, and the right vertical axis is the bandwidth (unit is packet).So solid lines represent window changes and dashed lines represent bandwidth changes.

We put the draw function in the "plot_cwnd" of "utils.py". You can specify the value of "raws" to set the amount of data to be processed, specify the value of "time_range" to set the the time interval you want see, and  specify the value of "scatter" to use a line chart or scatter chart.

![cwnd_changing](output/cwnd_changing.png)

### pcc_emulator-analysis.png

Here we provided a simple schematic diagram of latency of packets change process according to partial packet log.

The horizontal axis is the time(seconds), the left vertical axis is the latency of packets. So solid lines represent latency changes. And the cross indicates that the packet was lost at this time.

We put the draw function in the "analyze_pcc_emulator" of "utils.py". You also can describe these parameters mentioned above and do some customization, like "rows", "time_range" and "scatter".

![emulator-analysis](output/pcc_emulator-analysis.png)



# Todo list

- [ ] Add BBR congestion control module.
- [ ] Add AI congestion control module.
- [ ] Add QOE mudule.
- [ ] Add system presentation PPT.