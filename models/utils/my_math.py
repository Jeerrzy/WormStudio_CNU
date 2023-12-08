#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: my_math.py
# @author: jerrzzy
# @date: 2023/7/13


import os
import json
import math
import numpy as np


def get_individual_math_results(result_dir, trk_seq_path):
    """
    从MOT追踪文件格式中计算目标个体关键参数指标并保存为字典格式
    :param result_dir: 保存结果路径
    :param trk_seq_path: MOT格式追踪序列数据
    :param food_mask_path: 食物分割图
    :return: None 结果以json文件保存
    """
    result_dict = dict()
    trk_data = np.loadtxt(trk_seq_path, dtype=int, delimiter=',')
    if not len(trk_data) > 0:
        return None
    # 计算每个ID号码的指标
    trajectory_num = int(trk_data[:, 1].max())
    result_dict['number'] = trajectory_num
    for worm_id in range(1, trajectory_num + 1):
        id_dict = dict()
        speed, swing = [], []
        id_data = trk_data[trk_data[:, 1] == worm_id]
        _, _, x0, y0, w0, h0, _, _, _, _ = id_data[0]
        cx0, cy0 = int(x0 + w0 / 2), int(y0 + h0 / 2)
        for f, _, x, y, w, h, _, _, _, _ in id_data:
            cx, cy = int(x + w / 2), int(y + h / 2)
            speed.append(math.sqrt((cx-cx0)**2+(cy-cy0)**2))
            swing.append(abs(w/h-w0/h0))
            cx0, cy0, w0, h0 = cx, cy, w, h
        id_dict['frame'] = len(id_data)
        id_dict['speed'] = np.mean(np.array(speed))
        id_dict['swing'] = np.mean(np.array(swing))
        result_dict[str(worm_id)] = id_dict
    # 整理平均指标
    aver_speed, aver_swing = [], []
    for i in range(1, trajectory_num+1):
        id_dict = result_dict[str(i)]
        aver_speed.append(id_dict['speed'])
        aver_swing.append(id_dict['swing'])
    result_dict['aver_speed'] = np.mean(np.array(aver_speed))
    result_dict['aver_swing'] = np.mean(np.array(aver_swing))
    with open(os.path.join(result_dir, 'result.json'), 'w') as f:
        json.dump(result_dict, f, indent=2, cls=NumpyArrayEncoder)


class NumpyArrayEncoder(json.JSONEncoder):
    """重写JSONEncoder中的default方法"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
