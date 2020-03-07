from emulator import Emulator
import random
import numpy as np
import matplotlib.pyplot as plt
def creat_network(row, max_bw, idx):
    trace_list = []
    for i in range(row):
        tmp = []
        tmp.append(i * 10)
        tmp.append(random.uniform(0, max_bw))
        tmp.append(random.random())
        trace_list.append(tmp)

    with open("scripts/second_group/traces_"+ str(idx) + ".txt", "w+") as f:
        for i in range(len(trace_list)):
            for j in range(2):
                f.write(str(trace_list[i][j]))
                f.write(',')
            f.write(str(trace_list[i][2]))
            f.write('\n')


def main(times, row, max_bw, flag=0):
    first_qoe = []
    second_qoe = []
    for idx in range(times):
        creat_network(row=row, max_bw=max_bw, idx=idx + 1)
        block_file = "config/block.txt"
        trace_file = "scripts/second_group/traces_"+ str(idx + 1) + ".txt"

        emulator0 = Emulator(block_file=block_file,
                            trace_file=trace_file,
                            det=1,
                            tag=0)
        emulator0.run(times=1)
        qoe0 = emulator0.cal_QOE(flag=flag)
        first_qoe.append(qoe0)

        emulator1 = Emulator(block_file=block_file,
                            trace_file=trace_file,
                            det=1,
                            tag=1)
        emulator1.run(times=1)
        qoe1 = emulator1.cal_QOE(flag=flag)
        second_qoe.append(qoe1)

    data = np.array([first_qoe, second_qoe])
    data = data.T
    np.savetxt("scripts/second_group/network.log", data,fmt="%.8f", delimiter=',')
    return first_qoe,second_qoe


def drawing(times, first_qoe, second_qoe):
    X = np.linspace(1, times, times)
    Y1 = np.array(first_qoe)
    Y2 = np.array(second_qoe)
    fig, ax = plt.subplots()
    ax.plot(X, Y1, color='blue', label="base_priority")
    ax.plot(X, Y2, color='red',label="base_ddl")
    ax.set_xlabel("times")
    ax.set_ylabel("qoe")
    ax.legend()
    plt.savefig("scripts/second_group/network-drawing.png")


if __name__ == '__main__':
    times = 100
    #row and max_bw are used to create network
    row = 10
    max_bw = 100

    # flag used to cal QOE in different ways
    flag = 0
    first_qoe, second_qoe = main(times, row, max_bw, flag)
    drawing(times, first_qoe, second_qoe)



