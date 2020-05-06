#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : analyze_block
# @Function : 
# @Author : azson
# @Time : 2020/4/24 9:38
'''

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


if __name__ == '__main__':
    block_trace = "../config/data_block.csv"
    new_block_files = ["../config/data_video.csv", "../config/data_audio.csv"]
    df_block = pd.read_csv(new_block_files[0], header=None)
    df_block.columns = ["time", "size",'p']
    df_block = df_block[df_block["time"] <= 20]
    plt.scatter(df_block["time"], df_block["size"], s=5)
    plt.xlabel("Time (s)")
    plt.ylabel("Block Size (B)")
    plt.show()

    df_video = pd.read_csv(new_block_files[0], header=None)
    df_video.columns = ["time", "size", "pp"]
    df_video.loc[df_video["time"] < 2, "size"] *= 90.
    df_video.loc[(df_video["time"] < 10.) & (2. <= df_video["time"]), "size"] *= 3.
    df_video.loc[(df_video["time"] < 15.) & (10. <= df_video["time"]), "size"] *= 20.
    df_video = df_video[df_video["time"] < 15]

    df_video.to_csv("../config/data_video-2.csv", header=None, index=None)

    df_video = pd.read_csv(new_block_files[1], header=None)
    df_video.columns = ["time", "size"]
    df_video.loc[df_video["time"] < 2, "size"] *= 90.
    df_video.loc[(df_video["time"] < 10.) & (2. <= df_video["time"]), "size"] *= 3.
    df_video.loc[(df_video["time"] < 15.) & (10. <= df_video["time"]), "size"] *= 20.
    df_video = df_video[df_video["time"] < 15]

    df_video.to_csv("../config/data_audio-2.csv", header=None, index=None)