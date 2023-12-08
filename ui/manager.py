#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @file: manager.py
# @author: jerrzzy
# @date: 2023/7/17


"""
manager.py: 文件管理器
"""


import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from database import FILE_EXTENSION


class FileManager(QWidget):
    """文件管理器"""
    def __init__(self, database, logger, parent=None):
        super(FileManager, self).__init__(parent)
        self.database = database
        self.logger = logger
        # 设置背景颜色
        self.setStyleSheet('''QWidget{background-color:#404040;}''')
        # 网格式布局
        self.layout = QGridLayout()
        # 文件路径搜索
        self.file_name_line = SearchComboBox()
        self.layout.addWidget(self.file_name_line, 0, 0, 1, 8)
        # 搜索按钮
        self.searchAction = QAction(self.file_name_line)
        self.searchAction.setIcon(QIcon('./source/search.png'))
        self.file_name_line.lineEdit().addAction(self.searchAction, QLineEdit.LeadingPosition)
        # 添加文件按钮
        self.openfile_btn = IconButton(icon="QPushButton{border-image: url(./database/icon/add.png)}", size=25)
        self.openfile_btn.clicked.connect(self.append_new_file)
        self.layout.addWidget(self.openfile_btn, 0, 8, 1, 1)
        # 添加路径按钮
        self.openfolder_btn = IconButton(icon="QPushButton{border-image: url(./database/icon/add_folder.png)}", size=25)
        self.openfolder_btn.clicked.connect(self.open_new_folder)
        self.layout.addWidget(self.openfolder_btn, 0, 9, 1, 1)
        # 文件名
        self.file_names = QListView()
        self.file_names.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_names.contextMenuPolicy()
        self.file_names.customContextMenuRequested[QPoint].connect(self.show_menu)
        self.file_names.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_name_model = QStringListModel()
        self.file_names.setModel(self.file_name_model)
        self.file_names.clicked.connect(self.select_current_file)
        self.layout.addWidget(self.file_names, 1, 0, 8, 10)
        # 进度条
        self.progressbar = QProgressBar()
        self.progressbar.setStyleSheet("QProgressBar {border: 2px solid grey; border-radius: 5px; "
                                       "background-color: #CCFFFF; text-align:center; font-size:5px}")
        self.set_progressbar(False)
        self.layout.addWidget(self.progressbar, 9, 0, 1, 10)
        # 设置布局
        self.setLayout(self.layout)

    def append_new_file(self):
        """添加新文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Choose file", "C:/", "*.mp4; *.avi")
            if file_path:
                self.database.append_new_file(file_path)
                self.reset_model()
                self.logger.info('User: Open New File')
        except:
            self.logger.info('System Error: Fail to Open New File!')

    def open_new_folder(self):
        """打开新文件夹"""
        try:
            folder = QFileDialog.getExistingDirectory(self, "choose folder", "C:/")
            if folder:
                for file_name in os.listdir(folder):
                    if file_name.endswith(FILE_EXTENSION):
                        self.database.append_new_file(os.path.join(folder, file_name))
                self.reset_model()
                self.logger.info('User: Open New Folder')
        except:
            self.logger.info('System Error: Fail to Open New Folder!')

    def reset_model(self):
        """重新设置模型"""
        try:
            file_list = self.database.file_name_list
            self.file_name_model.setStringList(file_list)
            self.file_names.setModel(self.file_name_model)
            self.file_name_line.setModel(self.file_name_model)
        except:
            self.logger.info('System Error: Fail to Reset File Manager Model!')

    def set_progressbar(self, state=True):
        """设置进度条"""
        try:
            if state:
                self.progressbar.setRange(0, 0)
            else:
                self.progressbar.setRange(0, 1)
        except:
            self.logger.info('System Error: Fail to Set Progressbar!')

    def select_current_file(self, qModelIndex):
        """文件列表选中事件"""
        try:
            index = qModelIndex.row()
            self.file_name_line.setCurrentIndex(index)
        except:
            self.logger.info('System Error: Fail to Select Current File!')

    def show_menu(self):
        """右键菜单"""
        def DeleteItem():
            try:
                self.database.delete_file(self.database.current_obj_id)
                self.reset_model()
                self.logger.info(f'User: Delete File:{self.database.current_obj_id}')
            except:
                self.logger.info('System Error: Fail to Delete File!')
        try:
            popMenu = QMenu()
            popMenu.addAction(QAction(u'Delete', self, triggered=DeleteItem))
            popMenu.exec_(QCursor.pos())
        except:
            self.logger.info('System Error: Fail to Create Item Menu!')


"""
带搜索功能的下拉列表框
"""


class SearchComboBox(QComboBox):
    def __init__(self, parent=None):
        super(SearchComboBox, self).__init__(parent)
        self.setStyleSheet("QComboBox{color:#E0E0E0}"
                           "QComboBox QAbstractItemView {"  # 下拉选项样式
                           "color:#CCFFE5; "
                           "background: transparent; "
                           "}")
        self.setEditable(True)
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)  # 大小写不敏感
        self.pFilterModel.setSourceModel(self.model())
        # 添加一个使用筛选器模型的QCompleter
        self.completer = QCompleter(self.pFilterModel, self)
        # 始终显示所有(过滤后的)补全结果
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        self.setCompleter(self.completer)
        # Qcombobox编辑栏文本变化时对应的槽函数
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)

    # 在模型更改时，更新过滤器和补全器的模型
    def setModel(self, model):
        super(SearchComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # 回应回车按钮事件
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Enter & e.key() == Qt.Key_Return:
            text = self.currentText()
            index = self.findText(text, Qt.MatchExactly | Qt.MatchCaseSensitive)
            self.setCurrentIndex(index)
            self.hidePopup()
            super(SearchComboBox, self).keyPressEvent(e)
        else:
            super(SearchComboBox, self).keyPressEvent(e)


"""
IconButton: 自定义图标按钮
"""


class IconButton(QPushButton):
    def __init__(self, icon: str, size: int, parent=None):
        super(IconButton, self).__init__(parent)
        self.setStyleSheet(icon)
        self.setMaximumSize(size, size)
        self.setMinimumSize(size, size)


