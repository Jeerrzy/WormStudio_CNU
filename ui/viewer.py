# date: 2023/3/19
# author: Jin Zhiyu


"""
viewer: 查看器
"""


import cv2
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class MainViewer(QWidget):
    """主显示区"""
    def __init__(self, database, logger, parent=None):
        super(MainViewer, self).__init__(parent)
        self.database = database
        self.logger = logger
        # 布局
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # 显示容器
        self.graphic_obj = MyGraphicItem(database=database)
        self.scene = MyGraphicScene()
        self.scene.addItem(self.graphic_obj)
        self.viewer = MyGraphicView()
        self.viewer.setScene(self.scene)
        self.layout.addWidget(self.viewer, 0, 0, 9, 11)
        self.cuda_btn = MyQPushButton(
            icon1="QPushButton{border-image: url(./database/icon/CPU.png)}",
            icon2="QPushButton{border-image: url(./database/icon/GPU.png)}",
            size=35
        )
        self.layout.addWidget(self.cuda_btn, 10, 0, 1, 1)
        self.start_btn = IconButton(icon="QPushButton{border-image: url(./database/icon/start.png)}", size=40)
        self.layout.addWidget(self.start_btn, 10, 5, 1, 1)
        self.colors_btn = IconButton(icon="QPushButton{border-image: url(./database/icon/colors.png)}", size=35)
        self.layout.addWidget(self.colors_btn, 10, 9, 1, 1)
        self.download_btn = IconButton(icon="QPushButton{border-image: url(./database/icon/download.png)}", size=35)
        self.layout.addWidget(self.download_btn, 10, 10, 1, 1)

    def change_current_file(self):
        """切换当前文件"""
        # try:
        self.set_fixed_size()
        self.graphic_obj.file_obj = self.database.current_file_obj()
        self.graphic_obj.update_pix_map(update_parameter=True)
        # except:
        #     self.logger.info('System Error: Fail to Change Current File!')

    def set_fixed_size(self):
        """设置固定大小"""
        try:
            w, h = self.viewer.width(), self.viewer.height()
            self.graphic_obj.set_fixed_size(w, h)
            self.scene.set_fixed_size(w, h)
        except:
            self.logger.info('System Error: Fail to Set Fixed Size!')

    def mousePressEvent(self, event):
        """右键重置"""
        if event.buttons() == Qt.RightButton:
            self.graphic_obj.refresh_parameter()


"""
MyGraphicView: 自定义显示器元素
"""


class MyGraphicView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置渲染属性
        self.setRenderHints(QPainter.Antialiasing |                  # 抗锯齿
                            QPainter.HighQualityAntialiasing |       # 高品质抗锯齿
                            QPainter.TextAntialiasing |              # 文字抗锯齿
                            QPainter.SmoothPixmapTransform |         # 平滑图元变化
                            QPainter.LosslessImageRendering)         # 不失真的图片渲染
        # 视窗更新
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 不显示滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        # 设置拖拽模式
        self.setDragMode(self.RubberBandDrag)


"""
MyGraphicScene: 自定义场景元素
"""


class MyGraphicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置画笔
        self._color_light = QColor('#2f2f2f')
        self._color_dark = QColor('#292929')
        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

    def set_fixed_size(self, w, h):
        self.setSceneRect(-w / 2, -h / 2, w, h)


"""
MyGraphicItem: 自定义图片元素
"""


class MyGraphicItem(QGraphicsPixmapItem):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.file_obj = None
        self.pix_map = None
        # 缩放以及位移参数
        self.iw, self.ih = 0, 0
        self.vw, self.vh = 0, 0
        self.ori_w, self.ori_h = 0, 0
        self.ori_scale = 0
        self.scale = 1.0
        self.offset_x, self.offset_y = 0, 0

    """设置固定大小"""
    def set_fixed_size(self, w, h):
        # 更新参数
        self.vw, self.vh = w, h

    """设定图像内容"""
    def update_pix_map(self, update_parameter=False):
        if self.file_obj is not None and self.file_obj['flag']:
            opencv_array = cv2.imread(os.path.join(self.file_obj['cache'], 'visual', 'cache_all.png'))
        else:
            opencv_array = cv2.imread(os.path.join(self.file_obj['cache'], 'cover.png'))
        rgb_array = cv2.cvtColor(opencv_array, cv2.COLOR_BGR2RGB)
        self.pix_map = QPixmap(QImage(rgb_array, rgb_array.shape[1], rgb_array.shape[0], QImage.Format_RGB888))
        if update_parameter is True:
            self.refresh_parameter()
        self.setPixmap(self.pix_map)
        self.setScale(self.scale)

    """重置参数"""
    def refresh_parameter(self):
        self.iw, self.ih = self.pix_map.width(), self.pix_map.height()
        self.ori_scale = min(self.vw / self.iw, self.vh / self.ih)
        self.ori_w, self.ori_h = self.iw * self.ori_scale, self.ih * self.ori_scale
        self.scale = self.ori_scale
        self.setScale(self.scale)
        self.setPos(-self.ori_w / 2, -self.ori_h / 2)

    """鼠标单击事件"""
    def mousePressEvent(self, event):
        if event.buttons() == Qt.RightButton:
            self.refresh_parameter()

    """滚轮事件"""
    def wheelEvent(self, event: 'QGraphicsSceneWheelEvent'):
        # 只能放大5倍
        if event.delta() > 0 and self.scale >= 15:
            return
        if event.delta() < 0 and self.scale <= 0.01:
            return
        else:
            if event.delta() > 0:
                # 每次放大10%
                self.scale *= 1.1
            else:
                # 每次缩小10%
                self.scale *= 0.9
            self.setScale(self.scale)
            if event.delta() > 0:
                # moveBy指的是item左上角移动的相对距离，相对原始左上角，原始值为(0, 0)向上向右为负数
                self.moveBy(-event.pos().x() * self.scale * 0.1, -event.pos().y() * self.scale * 0.1)
            else:
                self.moveBy(event.pos().x() * self.scale * 0.1, event.pos().y() * self.scale * 0.1)


"""
IconButton: 自定义图标按钮
"""


class IconButton(QPushButton):
    def __init__(self, icon: str, size: int, parent=None):
        super(IconButton, self).__init__(parent)
        self.setStyleSheet(icon)
        self.setMaximumSize(size, size)
        self.setMinimumSize(size, size)


"""
MyPushButton: 自定义的可点击切换状态按钮
"""


class MyQPushButton(QPushButton):
    def __init__(self, icon1=None, icon2=None, size=None, parent=None, default_state=False):
        super(QPushButton, self).__init__(parent)
        self.state = default_state
        self.icon1 = icon1
        self.icon2 = icon2
        self.update_icon()
        self.set_size(size)

    def set_size(self, size):
        if size is not None:
            self.setMaximumSize(size, size)
            self.setMinimumSize(size, size)

    def click(self):
        self.state = not self.state
        self.update_icon()

    def reset(self):
        self.state = False
        self.update_icon()

    def update_icon(self):
        if self.state:
            if self.icon2 is not None:
                self.setStyleSheet(self.icon2)
        else:
            if self.icon1 is not None:
                self.setStyleSheet(self.icon1)