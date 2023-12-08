#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: draw.py
# @author: jerrzzy
# @date: 2023/8/26


import os
import json
import numpy as np
import cv2
from matplotlib import pyplot as plt


def mot_visualize_video(src_video_path, trk_seq_path, out_video_path, colors, width, height, fps):
    """
    :param src_video_path: 输入视频路径
    :param trk_seq_path: MOT追踪序列文件
    :param out_video_path: 输出视频路径
    :param colors: 绘制轨迹的颜色列表
    :param w: 输出视频的宽
    :param h: 输出视频的长
    :param fps: 输出视频的帧率
    :return: None
    """
    trk_data = np.loadtxt(trk_seq_path, dtype=int, delimiter=',')
    frame_id = 1
    src = cv2.VideoCapture(src_video_path)
    out = cv2.VideoWriter(out_video_path, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))
    bg = np.zeros((height, width, 3), np.uint8)
    trajectory_num = int(trk_data[:, 1].max())
    trajectory_temp = np.zeros((trajectory_num, 2))  # 点的缓存值，用来绘制曲线
    is_trajectory_find = [False] * trajectory_num  # 是否已经找到了第一个点
    while src.isOpened():
        ret, frame = src.read()
        if not ret:
            break
        cv2.putText(frame, str(frame_id), (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 0, 0), 3)  # 左上角写明帧数
        frame_data = trk_data[trk_data[:, 0] == frame_id]
        for _, worm_id, x, y, w, h, _, _, _, _ in frame_data:
            cv2.rectangle(frame, (y, x), (y + h, x + w), colors[(worm_id-1) % len(colors)], 4)  # 方框
            cv2.putText(frame, str(worm_id), (y, x), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colors[(worm_id-1) % len(colors)], 4)  # ID号
            cx, cy = int(x+w/2), int(y+h/2)
            if is_trajectory_find[worm_id-1]:
                (cx0, cy0) = trajectory_temp[worm_id-1]
                cv2.line(bg, (int(cy0), int(cx0)), (int(cy), int(cx)), colors[(worm_id-1) % len(colors)], 3)
            else:
                is_trajectory_find[worm_id - 1] = True
            trajectory_temp[worm_id-1] = np.array([cx, cy])
        frame = cv2.addWeighted(frame, 0.8, bg, 0.2, 0)
        out.write(frame)
        frame_id += 1
    src.release()
    out.release()
    cv2.destroyAllWindows()


def mot_visualize_image(out_image_dir, trk_seq_path, colors, width, height):
    """
    :param out_image_dir: 输出图片目录
    :param trk_seq_path: MOT追踪序列文件
    :param colors: 绘制轨迹的颜色列表
    :param w: 输出视频的宽
    :param h: 输出视频的长
    :return: None
    """
    trk_data = np.loadtxt(trk_seq_path, dtype=int, delimiter=',')
    if not len(trk_data) > 0:
        return None
    trajectory_num = int(trk_data[:, 1].max())
    trajectory_image_list = [255 * np.ones((height, width, 3), np.uint8) for t in range(trajectory_num+1)]
    for worm_id in range(1, trajectory_num+1):
        id_data = trk_data[trk_data[:, 1] == worm_id]
        _, _, x0, y0, w0, h0, _, _, _, _ = id_data[0]
        cx0, cy0 = int(x0+w0/2), int(y0+h0/2)
        for _, _, x, y, w, h, _, _, _, _ in id_data:
            cx, cy = int(x+w/2), int(y+h/2)
            cv2.line(trajectory_image_list[0], (cy0, cx0), (cy, cx), colors[(worm_id - 1) % len(colors)], 3)
            cv2.line(trajectory_image_list[worm_id], (cy0, cx0), (cy, cx), colors[(worm_id - 1) % len(colors)], 3)
            cx0 = cx
            cy0 = cy
    for i, trajectory_image in enumerate(trajectory_image_list):
        if i == 0:
            cv2.imwrite(os.path.join(out_image_dir, f'cache_all.png'), trajectory_image)
        else:
            cv2.imwrite(os.path.join(out_image_dir, f'cache_worm_id_{str(i).zfill(3)}.png'), trajectory_image)


def draw_math_results(json_path, out_image_dir, colors):
    """
    :param json_path: 数学结果的json缓存路径
    :param out_image_dir: 输出图像路径
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    worm_ids, draw_colors = [], []
    speeds, swings = [], []
    for i in range(1, data['number']+1):
        id_dict = data[str(i)]
        worm_ids.append(str(i))
        color = colors[(i - 1) % len(colors)]
        c_color = [c/255 for c in color]
        draw_colors.append(c_color)
        speeds.append(id_dict['speed'])
        swings.append(id_dict['swing'])
    _dict = {
        'Speed': speeds,
        'Swing': swings,
    }
    # 保存图片
    for name in _dict.keys():
        fig = plt.figure()
        fig.tight_layout()
        ax = fig.add_subplot(111)
        ax.set_xlabel('WormID')
        ax.set_ylabel(name)
        ax.bar(range(1, data['number']+1), _dict[name], width=0.5, color=draw_colors, edgecolor='black')
        plt.savefig(os.path.join(out_image_dir, f'video_math_result_{name}.png'))

        