#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @folder: models
# @author: jerrzzy
# @date: 2023/7/13


from PyQt5.QtCore import *
from models.detector import mot_detect
from models.tracker import mot_track
from models.optimizer import mot_optimize
from models.utils.draw import *
from models.utils.my_math import *
from models.utils.excel import *


class DownloadResultFileThread(QThread):
    """下载结果文件线程"""
    def __init__(self, database):
        super(DownloadResultFileThread, self).__init__(parent=None)
        self.database = database

    def run(self):
        try:
            self.database.compress_cache_to_zip()
        except:
            print('Fail to download result file.')


class ProcessingCurrentFileThread(QThread):
    """处理当前文件的线程"""
    def __init__(self, database):
        super(ProcessingCurrentFileThread, self).__init__(parent=None)
        self.database = database

    def run(self):
        self.database.running = True
        cfg = self.database.cfg
        length = self.database.get_length()
        for i, file_obj in enumerate(self.database.file_obj_list):
            try:
                if not file_obj['flag']:
                    print(f'Processing {file_obj["name"]}, {i+1}/{length}')
                    if not os.path.exists(file_obj['cache']):
                        os.makedirs(file_obj['cache'])
                    total_frames = mot_processing(
                        src_video_path=file_obj['src'],
                        result_dir=file_obj['cache'],
                        input_shape=cfg['input_shape'],
                        cuda=cfg['cuda'],
                        confidence=cfg['confidence'],
                        nms_iou=cfg['nms_iou'],
                        max_age=cfg['max_age'],
                        min_hints=cfg['min_hints'],
                        iou_threshold=cfg['iou_threshold'],
                        optimize_rate=cfg['optimize_rate'],
                        st_ratio=cfg['st_ratio'],
                        colors=cfg['colors'],
                        w=file_obj['width'],
                        h=file_obj['height'],
                        total_frames=file_obj['frames'],
                        fps=30,
                    )
                    file_obj['frames'] = total_frames
                    file_obj['flag'] = True
                    print(f'Process {file_obj["name"]} down, {i+1}/{length}')
            except:
                print(f'Fail to process {file_obj["name"]}')
        try:
            self.database.export_excel()
        except:
            print('Fail to export excel.')
        self.database.running = False


def mot_processing(src_video_path, result_dir, input_shape, cuda, confidence, nms_iou, max_age, min_hints, iou_threshold,
                   optimize_rate, st_ratio, colors, w, h, total_frames, fps):
    """
    :param src_video_path: 输入视频对象
    :param result_dir: 结果路径
    :param cfg: 字典格式的配置文件
    :return: None
    """
    # MOT追踪
    mot_cache_path = os.path.join(result_dir, 'cache.txt')
    # 检测
    total_frames = mot_detect(
        input_video_path=src_video_path,
        txt_result_path=mot_cache_path,
        input_shape=input_shape,
        total_frames=total_frames,
        cuda=cuda,
        confidence=confidence,
        nms_iou=nms_iou
    )
    # 追踪
    mot_track(
        dets_seq_path=mot_cache_path,
        trk_result_path=mot_cache_path,
        max_age=max_age,
        min_hints=min_hints,
        iou_threshold=iou_threshold
    )
    # 优化
    mot_optimize(
        trk_seq_path=mot_cache_path,
        opt_result_path=mot_cache_path,
        optimize_rate=optimize_rate,
        st_ratio=st_ratio
    )
    # 数学计算
    math_result_dir = os.path.join(result_dir, 'math')
    if not os.path.exists(math_result_dir):
        os.makedirs(math_result_dir)
    get_individual_math_results(
        result_dir=math_result_dir,
        trk_seq_path=mot_cache_path,
    )
    # 计算绘图
    draw_math_results(
        json_path=os.path.join(math_result_dir, 'result.json'),
        out_image_dir=math_result_dir,
        colors=colors
    )
    # 生成excel
    get_excel_results(
        json_path=os.path.join(math_result_dir, 'result.json'),
        result_dir=result_dir,
        colors=colors
    )
    # 可视化
    visual_result_dir = os.path.join(result_dir, 'visual')
    if not os.path.exists(visual_result_dir):
        os.makedirs(visual_result_dir)
    # 绘制视频
    mot_visualize_video(
        src_video_path=src_video_path,
        out_video_path=os.path.join(visual_result_dir, 'visualization.mp4'),
        trk_seq_path=mot_cache_path,
        colors=colors,
        width=w,
        height=h,
        fps=fps,
    )
    # 绘图
    mot_visualize_image(
        out_image_dir=visual_result_dir,
        trk_seq_path=mot_cache_path,
        colors=colors,
        width=w,
        height=h,
    )
    # 总帧数，用于检查
    return total_frames
