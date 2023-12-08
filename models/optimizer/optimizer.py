#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: optimizer.py
# @author: jerrzzy
# @date: 2023/7/13


import numpy as np
from tqdm import tqdm


class TrajectoryOptimizer(object):
    """轨迹优化器"""
    def __init__(self, optimize_rate=0.1, st_ratio=1.0):
        self.optimize_rate = optimize_rate
        self.st_ratio = st_ratio
        self.frame_count = 0
        self.ids = None
        self.trajectories = None

    def init_trajectories(self, trk_seq_path):
        """初始化轨迹"""
        trk_data = np.loadtxt(trk_seq_path, delimiter=',')
        trk_data[:, 4:6] += trk_data[:, 2:4]  # convert [x,y,w,h] to [x1,y1,x2,y2]
        frame_count = int(trk_data[:, 0].max())
        ids = []
        trajectories = []
        for frame_id in range(1, frame_count+1):
            frame_data = trk_data[trk_data[:, 0] == frame_id, 1:6]
            """
            MOT: <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <conf>, <x>, <y>, <z>
            """
            for (_id, x1, y1, x2, y2) in frame_data:
                if _id not in ids:
                    ids.append(_id)
                    trajectories.append(
                        TrajectoryObject(_id=_id, init_frame_id=frame_id, init_bbox=[x1, y1, x2, y2])
                    )
                else:
                    trajectory = trajectories[ids.index(_id)]  # 通过id寻找
                    trajectory.update(frame_id=frame_id, bbox=[x1, y1, x2, y2])
        return frame_count, ids, trajectories

    def one_post_process(self, frame_margin, pos_margin):
        """
        一次后处理连接碎片：id大小和出现顺序有相关性，ID越小，起始点越靠前，ID越大，起始点越靠后
        """
        # 搜寻每条id的轨迹：[id, 开始帧，结束帧，开始点，结束点]
        pre_match = []
        for i in range(len(self.ids)):
            trajectory1 = self.trajectories[i]
            if trajectory1.length >= 0.99 * self.frame_count:
                # 轨迹完整，跳过
                continue
            # 结束点
            break_id = trajectory1.id
            break_frame = trajectory1.frame_list[-1]
            break_bbox = trajectory1.bbox_list[-1]
            for j in range(i+1, len(self.ids)):
                trajectory2 = self.trajectories[j]
                if trajectory2.length >= 0.99 * self.frame_count:
                    # 轨迹完整，跳过
                    continue
                connect_id = trajectory2.id
                connect_frame = trajectory2.frame_list[0]
                connect_bbox = trajectory2.bbox_list[0]
                if connect_frame <= break_frame:
                    # 时间帧无法对应，跳过
                    continue
                # 贪心思想: 先完成匹配的先连接
                if len(pre_match) > 0 and connect_id in np.array(pre_match)[:, 1]:
                    continue
                # 计算距离
                frame_dis = connect_frame - break_frame
                pos_dis = np.linalg.norm(np.array(break_bbox) - np.array(connect_bbox))
                if frame_dis <= frame_margin and pos_dis <= pos_margin:
                    pre_match.append([break_id, connect_id])
                    # 贪心思想: 先完成匹配的先连接，后续满足条件的不管
                    break
        match = np.array(pre_match)
        # match按照最后一列的降序排列，保证后面的id都被正确链接到前面的id上
        # 按照分配id的原则，后出现的大id一定被连接到先出现小的id上
        if len(match) > 0:
            match = match[np.argsort(-match[:, 1])]
            for (x, y) in match:
                # 更新轨迹和id
                tra1 = self.trajectories[self.ids.index(x)]
                tra2 = self.trajectories[self.ids.index(y)]
                tra1.connect(tra2)
                # 删除旧数据
                del_index = self.ids.index(y)
                self.trajectories.pop(del_index)
                self.ids.pop(del_index)
        return match

    def trajectories_repair(self):
        """轨迹完整和平滑插值算法"""
        for i in range(len(self.ids)):
            trajectory = self.trajectories[i]
            _id = self.ids[i]
            # 插值补全
            interval_list = []
            for j in range(0, trajectory.length-1):
                # 检查帧是否是严格递增的，如果不是，则进行插值
                if trajectory.frame_list[j+1] - trajectory.frame_list[j] > 1:
                    interval_list.append(j)
            for k in reversed(interval_list):
                # 逆向插值，防止列表乱序
                interval_frame_seq = list(range(trajectory.frame_list[k]+1, trajectory.frame_list[k+1]))
                for fm in reversed(interval_frame_seq):
                    # 逆向插值，同上
                    trajectory.frame_list.insert(k+1, fm)
                    trajectory.length += 1
                coords = np.array([trajectory.bbox_list[k], trajectory.bbox_list[k+1]])
                N = len(interval_frame_seq)
                step = np.diff(coords, axis=0) / (N + 1)
                for m in reversed(list(range(1, N + 1))):
                    # 逆向插值，同上
                    trajectory.bbox_list.insert(k + 1, coords[0]+step[0]*m)

    def re_id(self):
        """重新整理ID号"""
        for i in reversed(range(len(self.ids))):
            trajectory = self.trajectories[i]
            _id = self.ids[i]
            if trajectory.length < self.frame_count * 0.1:
                # 删除过短的轨迹
                self.trajectories.pop(i)
                self.ids.pop(i)
        for i in range(len(self.ids)):
            # 重新分配id，控制在总数内，从1开始
            self.ids[i] = i+1
            self.trajectories[i].id = i+1

    def re_file(self, opt_result_path):
        """根据优化结果重新生成记录文件"""
        with open(opt_result_path, 'w') as f:
            for trajectory in self.trajectories:
                _id = trajectory.id
                for i in range(trajectory.length):
                    frame_id = trajectory.frame_list[i]
                    (x1, y1, x2, y2) = trajectory.bbox_list[i]
                    """
                    MOT: <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <conf>, <x>, <y>, <z>
                    """
                    f.write(f'%d,%d,%.2f,%.2f,%.2f,%.2f,1,-1,-1,-1' % (frame_id, _id, x1, y1, x2-x1, y2-y1)+'\n')
        f.close()

    def global_optimization(self, trk_seq_path='', opt_result_path=''):
        """迭代执行全局优化"""
        print('start global optimize...')
        self.frame_count, self.ids, self.trajectories = self.init_trajectories(trk_seq_path=trk_seq_path)
        pbar = tqdm(total=int(self.optimize_rate*self.frame_count))
        for i in range(1, int(self.optimize_rate*self.frame_count)+1):
            self.one_post_process(frame_margin=i, pos_margin=self.st_ratio*i)
            pbar.update(1)
        self.re_id()
        self.trajectories_repair()
        self.re_file(opt_result_path=opt_result_path)
        print('global optimize down. Wait for math and draw.')


class TrajectoryObject(object):
    """轨迹结构体"""
    def __init__(self, _id, init_frame_id, init_bbox):
        self.id = _id
        self.frame_list = [init_frame_id]
        self.bbox_list = [init_bbox]
        self.length = 1

    def update(self, frame_id, bbox):
        """添加新节点"""
        self.frame_list.append(frame_id)
        self.bbox_list.append(bbox)
        self.length += 1

    def connect(self, trajectory):
        """连接新轨迹"""
        self.frame_list += trajectory.frame_list
        self.bbox_list  += trajectory.bbox_list
        self.length     += trajectory.length

