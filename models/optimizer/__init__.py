#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @folder: optimizer
# @author: jerrzzy
# @date: 2023/8/26


__all__ = ['mot_optimize']


from .optimizer import TrajectoryOptimizer


def mot_optimize(trk_seq_path, opt_result_path, optimize_rate, st_ratio):
    """
    Params:
    trk_seq_path - MOT格式的追踪结果文件路径
    opt_result_path - MOT格式的优化结果文件路径
    """
    to = TrajectoryOptimizer(optimize_rate=optimize_rate, st_ratio=st_ratio)
    to.global_optimization(trk_seq_path=trk_seq_path, opt_result_path=opt_result_path)

