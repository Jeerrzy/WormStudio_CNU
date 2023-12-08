#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: baseclass.py
# @author: jerrzzy
# @date: 2023/7/17


import json
import os
import zipfile
import shutil
import cv2
import numpy as np
import xlsxwriter as xw
import logging


# 允许的文件拓展名
FILE_EXTENSION = ('.mp4', '.avi')


class Database(object):
    """数据系统"""
    def __init__(self):
        self.cache_dir = './models/cache'
        self.config_path = './database/config/config.json'
        self.ad_path = './database/icon/contact_us.jpg'
        self.zip_file_path = None
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        else:
            shutil.rmtree(self.cache_dir)
            os.mkdir(self.cache_dir)
        shutil.copyfile(self.ad_path, os.path.join(self.cache_dir, 'README.jpg'))
        self.file_obj_list = []
        self.file_name_list = []
        self.current_obj_id = None
        with open(self.config_path, 'r') as f:
            self.cfg = json.load(f)
        self.running = False

    def append_new_file(self, new_file_path):
        """
        :param new_file_path: 输入的新文件地址
        :return: None
        """
        basename = os.path.basename(new_file_path)
        if basename not in self.file_name_list:
            name, ext = os.path.splitext(basename)
            cache_dir = os.path.join(self.cache_dir, name)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            src = cv2.VideoCapture(new_file_path)
            height, width = src.get(cv2.CAP_PROP_FRAME_HEIGHT), src.get(cv2.CAP_PROP_FRAME_WIDTH)
            fps, frames = src.get(cv2.CAP_PROP_FPS), src.get(cv2.CAP_PROP_FRAME_COUNT)
            ret, frame = src.read()
            if ret:
                cv2.imwrite(os.path.join(cache_dir, 'cover.png'), frame)
            _dict = {
                'src': new_file_path,
                'name': basename,
                'height': int(height),
                'width': int(width),
                'fps': int(fps),
                'frames': int(frames),
                'cache': cache_dir,
                'flag': False
            }
            self.file_obj_list.append(_dict)
            self.file_name_list.append(basename)

    def delete_file(self, _id):
        """
        :param _id: 要删除的文件索引
        :return: None
        """
        self.file_obj_list.pop(_id)
        self.file_name_list.pop(_id)

    def current_file_obj(self):
        """
        :return: 当前指向的文件信息字典对象
        """
        if self.current_obj_id is not None and 0 <= self.current_obj_id < len(self.file_obj_list):
            return self.file_obj_list[self.current_obj_id]
        else:
            return None

    def get_length(self):
        """
        :return: 数据长度
        """
        return len(self.file_obj_list)

    def compress_cache_to_zip(self):
        """
        :param zip_file_path: 压缩文件路径
        :return: None
        """
        with zipfile.ZipFile(self.zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(self.cache_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_file.write(file_path, os.path.relpath(file_path, self.cache_dir))

    def save_config(self):
        """保存配置"""
        with open(self.config_path, 'w') as f:
            json.dump(self.cfg, f, indent=2)

    def export_excel(self):
        """导出所有结果为excel"""
        workbook = xw.Workbook(os.path.join(self.cache_dir, 'summary_results.xlsx'))
        worksheet = workbook.add_worksheet('summary')
        worksheet.activate()
        header_names = ['VideoName', 'TotalFrames', 'FPS', 'Resolution', 'AverageSpeed', 'AverageSwing']
        worksheet.set_column('A:B', 25)
        worksheet.set_column('B:C', 20)
        worksheet.set_column('C:D', 10)
        worksheet.set_column('D:E', 20)
        worksheet.set_column('E:F', 30)
        worksheet.set_column('F:G', 30)
        for row in range(1, len(self.file_obj_list) + 1):
            worksheet.set_row(row, 25)
        head_format = {
            'font_size': 15,  # 字体大小
            'bold': True,  # 是否粗体
            'font_color': '#9400D3',  # 字体颜色
            'align': 'center',  # 水平居中对齐
            'valign': 'vcenter',  # 垂直居中对齐
            'border': 1,  # 边框宽度
            'top': 1,  # 上边框
            'left': 1,  # 左边框
            'right': 1,  # 右边框
            'bottom': 1  # 底边框
        }
        head_style = workbook.add_format(head_format)
        worksheet.write_row('A1', header_names, head_style)
        content_format = {
            'font_size': 10,  # 字体大小
            'align': 'center',  # 水平居中对齐
            'valign': 'vcenter'  # 垂直居中对齐
        }
        content_style = workbook.add_format(content_format)
        for i, file_obj in enumerate(self.file_obj_list):
            with open(os.path.join(file_obj['cache'], 'math', 'result.json'), 'r') as f:
                result = json.load(f)
            worksheet.write(i + 1, 0, file_obj['name'], content_style)
            worksheet.write(i + 1, 1, str(file_obj['frames']), content_style)
            worksheet.write(i + 1, 2, str(file_obj['fps']), content_style)
            worksheet.write(i + 1, 3, str(file_obj['width']) + ',' + str(file_obj['height']), content_style)
            worksheet.write(i + 1, 4, str(result['aver_speed']), content_style)
            worksheet.write(i + 1, 5, str(result['aver_swing']), content_style)
        workbook.close()


def get_logger():
    logger = logging.getLogger('test')  # 构建一个日志对象，'test'为logger对象名
    logger.setLevel(level=logging.INFO)  # 设置这个日志对象的可以产生的日志等级
    # 此Handler用于将日志信息输出到屏幕
    display_hand = logging.StreamHandler()
    # 日志输出格式
    currency_format = logging.Formatter('%(asctime)s: %(filename)s %(levelname)s %(message)s')
    currency_format.datefmt = '%Y-%m-%d %H:%M:%S'  # 日志输出时间格式
    # 将日志输出格式添加到创建的Handler里用于输出
    display_hand.setFormatter(currency_format)
    # 将Handler添加到logger里
    logger.addHandler(display_hand)
    return logger