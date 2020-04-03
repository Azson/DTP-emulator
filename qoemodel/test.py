
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


# x = np.linspace(0, 50, 50)
# y1 = list(range(50))
# fig, ax = plt.subplots()
# ax.plot(x, y1, color="blue", label="y(x)") # 定义x, y, 颜色，图例上显示的东西
# # ax.plot(x, y2, color="red", label="y'(x)")
# # ax.plot(x, y3, color="green", label="y''(x)")
# ax.set_xlabel("x") # x标签
# ax.set_ylabel("y") # y标签
# ax.legend()# 显示图例
# plt.savefig("test.png")
def plt_qoe(reno_arr, bbr_arr):
    x = np.linspace(0, 50, 50)
    fig, ax = plt.subplots()
    ax.plot(x,reno_arr, color="blue", label="reno_qoe")
    ax.plot(x, bbr_arr, color="red", label="bbr_qoe")
    ax.set_xlabel("trace_index")  # x标签
    ax.set_ylabel("qoe")  # y标签
    ax.legend()  # 显示图例
    plt.savefig("test.png")

if __name__ == '__main__':
    with open("bbr_reno_qoes.log","w+") as f:
        strs = ["trace numbers : 50\n", "buffer: MAX_QUEUE = 10, MIN_QUEUE = 50\n",
                "bw : 0.1 ~ 2 MB \n",
                str(list(range(40))) + "\n",
                str(list(range(30)))]
        f.writelines(strs)