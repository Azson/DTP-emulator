## INDRODUCTION

```
       * The core algorithm does not react directly to packet losses or delays,
       * although BBR may adjust the size of next send per ACK when loss is
       * observed, or adjust the sending rate if it estimates there is a
       * traffic policer, in order to keep the drop rate reasonable.
       *
       * Here is a state transition diagram for BBR:
       *
       *             |
       *             V
       *    +---> STARTUP  ----+
       *    |        |         |
       *    |        V         |
       *    |      DRAIN   ----+
       *    |        |         |
       *    |        V         |
       *    +---> PROBE_BW ----+
       *    |      ^    |      |
       *    |      |    |      |
       *    |      +----+      |
       *    |                  |
       *    +---- PROBE_RTT <--+
```
## PROCESSION

### TARGET: pacing-rate and cwnd

```
 * BBR congestion control computes the sending rate based on the delivery
   rate (throughput) estimated from ACKs. In a nutshell:
 *
 *   On each ACK, update our model of the network path:
 *      bottleneck_bandwidth = windowed_max(delivered / elapsed, 10 round trips)
 *      min_rtt = windowed_min(rtt, 10 seconds)
 *   pacing_rate = pacing_gain * bottleneck_bandwidth
 *   cwnd = max(cwnd_gain * bottleneck_bandwidth * min_rtt, 4)
```
- In our **simple_bbr.py**, we use `bw_windows` to keep the latest 10 bandwidth;

- we also use `ten_sec_wnd` to store the latest rtt in 10 seconds and we 
use function `update_min_rtt` to update it. 
However, to fit for our system, we change 10s to 5s.

- we use function `cal_gain` to calculate pacing_gain and cwnd_gain in different modes.

### STARTUP
> A BBR flow starts in STARTUP, and ramps up its sending rate quickly.
When it estimates the pipe is full, it enters DRAIN to drain the queue.

- In our **simple_bbr.py**, we use `four_bws` to restore the recent four bandwidth and 
`stop_increasing` to check when entering **DRAIN**.

### DRAIN

- In our **simple_bbr.py**, we compare the size of BDP and inflight to estimate entering **PROBE_BW**;

### PROBE_BW
> In steady state a BBR flow only uses PROBE_BW and PROBE_RTT.
  A long-lived BBR flow spends the vast majority of its time remaining
  (repeatedly) in PROBE_BW, fully probing and utilizing the pipe's bandwidth
  in a fair manner, with a small, bounded queue. 

### COMMON OPERATION
> If a flow has beencontinuously sending for the entire min_rtt window, and hasn't seen an RTT
  sample that matches or decreases its min_rtt estimate for 10 seconds, 
  then it briefly enters PROBE_RTT to cut inflight to a minimum value to re-probe
  the path's two-way propagation delay (min_rtt). 

- so we also use function `update_min_rtt` to find out when entering **PROBE_RTT**.

### PROBE_RTT
> When exiting PROBE_RTT, if we estimated that we reached the full bw of the pipe then we enter PROBE_BW;
  otherwise we enter STARTUP to try to fill the pipe.

- In our **simple_bbr.py**, we only have **200ms** to stay in PROBE_RTT, then we will entering **PROBE_BW** or **START_UP**.

## FLOW DIAGRAM
 ![avatar](http://assets.processon.com/chart_image/5e732bf3e4b01518202c832a.png)