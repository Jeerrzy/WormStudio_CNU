#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @folder: tracker
# @author: jerrzzy
# @date: 2023/8/26


__all__ = ['mot_track']


import numpy as np
from .sort import Sort


def mot_track(dets_seq_path, trk_result_path, max_age, min_hints, iou_threshold):
    """
    Params:
    dets_seq_path - MOT格式的检测结果文件路径
    trk_result_path - MOT格式的追踪结果文件路径
    """
    sort_tracker = Sort(
        max_age=max_age,
        min_hits=min_hints,
        iou_threshold=iou_threshold
    )
    det_data = np.loadtxt(dets_seq_path, delimiter=',')
    det_data[:, 4:6] += det_data[:, 2:4]  # convert [x,y,w,h] to [x1,y1,x2,y2]
    with open(trk_result_path, 'w') as f:
        for frame_id in range(1, int(det_data[:, 0].max())+1):
            frame_data = det_data[det_data[:, 0] == frame_id, 2:7]
            trackers = sort_tracker.update(frame_data)
            for d in trackers:
                """
                MOT: <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <conf>, <x>, <y>, <z>
                """
                f.write(f'%d,%d,%.2f,%.2f,%.2f,%.2f,1,-1,-1,-1' % (frame_id, d[4], d[0], d[1], d[2]-d[0], d[3]-d[1]) + '\n')
    f.close()
