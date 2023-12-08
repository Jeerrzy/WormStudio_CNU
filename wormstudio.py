#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: wormstudio.py
# @author: jerrzzy
# @date: 2023/7/17


import sys
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from qt_material import apply_stylesheet
from database import *
from models import *
from ui import *
import warnings
from multiprocessing import freeze_support


warnings.filterwarnings("ignore")
freeze_support()


class WormStudioMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(WormStudioMainWindow, self).__init__(parent)
        # 数据库
        self.database = Database()
        # 日志记录
        self.logger = get_logger()
        # 设置标题和图标
        self.setWindowTitle('WormStudio V5.0.0')
        self.setWindowIcon(QIcon("./database/icon/worm.png"))
        # 布局
        self.layout = QGridLayout()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)
        # 设置窗口分辨率
        self.desktop = QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.screenheight = self.screenRect.height()
        self.screenwidth = self.screenRect.width()
        self.height = int(self.screenheight * 0.6)
        self.width = int(self.screenwidth * 0.6)
        self.resize(self.width, self.height)
        # 文件管理器
        self.file_manager = FileManager(database=self.database, logger=self.logger)
        self.file_manager.file_name_line.currentIndexChanged.connect(self.change_current_file)
        self.layout.addWidget(self.file_manager, 0, 0, 10, 2)
        # 查看器
        self.main_viewer = MainViewer(database=self.database, logger=self.logger)
        self.main_viewer.start_btn.clicked.connect(self.pcf_start)
        self.main_viewer.download_btn.clicked.connect(self.download_result)
        self.main_viewer.cuda_btn.clicked.connect(self.set_cuda)
        self.main_viewer.colors_btn.clicked.connect(self.set_colors)
        self.layout.addWidget(self.main_viewer, 0, 2, 10, 7)
        # 线程
        self.pcf_thread = ProcessingCurrentFileThread(database=self.database)
        self.pcf_thread.finished.connect(self.pcf_down)
        self.drf_thread = DownloadResultFileThread(database=self.database)
        # 更新GPU状态
        self.main_viewer.cuda_btn.state = self.database.cfg['cuda']
        self.main_viewer.cuda_btn.update_icon()

    def change_current_file(self, _id):
        """切换当前数据"""
        self.database.current_obj_id = _id
        self.main_viewer.change_current_file()
        file_obj = self.database.current_file_obj()
        self.logger.info(f'User: Change Current File: {file_obj["name"]}')

    def pcf_start(self):
        """PCF线程开始执行"""
        if self.database.get_length() > 0:
            self.pcf_thread.start()
            self.file_manager.set_progressbar(state=True)
            self.logger.info(f'User: Start Processing Thread')
        else:
            QMessageBox.warning(self, 'WARNING', 'Please input file!', QMessageBox.Close)

    def pcf_down(self):
        """PCF线程结束"""
        self.file_manager.set_progressbar(state=False)
        self.change_current_file(self.database.current_obj_id)
        self.logger.info('System: Processing Thread Down')

    def download_result(self):
        """下载结果"""
        if self.database.get_length() > 0:
            if not self.database.running:
                now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
                fileName_choose, filetype = QFileDialog.getSaveFileName(self, "Save Result to zip", f'C:/wormstudio_{now_time}.zip', "ZIP Files (*.zip)")
                self.database.zip_file_path = fileName_choose
                if fileName_choose == "":
                    return
                else:
                    self.drf_thread.start()
                    self.logger.info(f'User: Save Result to {fileName_choose}')
            else:
                QMessageBox.warning(self, 'WARNING', 'Please wait for processing down!', QMessageBox.Close)
        else:
            QMessageBox.warning(self, 'WARNING', 'Unable to Download Result!', QMessageBox.Close)

    def set_cuda(self):
        """设置GPU"""
        self.main_viewer.cuda_btn.click()
        if self.main_viewer.cuda_btn.state:
            self.database.cfg['cuda'] = True
            self.logger.info(f'User: Activate GPU')
        else:
            self.database.cfg['cuda'] = False
            self.logger.info(f'User: Shut Down GPU')
        self.database.save_config()

    def set_colors(self):
        c = QColorDialog.getColor()
        colors = []
        for i in range(QColorDialog.customCount()):
            qcolor = QColorDialog.customColor(i)
            opencv_bgr = (qcolor.blue(), qcolor.green(), qcolor.red())
            colors.append(opencv_bgr)
        self.database.cfg['colors'] = colors
        self.database.save_config()
        self.logger.info(f'User: Save config down.')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    win = WormStudioMainWindow()
    win.show()
    sys.exit(app.exec_())