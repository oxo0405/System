#!/usr/bin/env python3
# main_window.py - PyQt5 GUI界面（含文件查看器）
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 导入文件系统
from file_system import FileSystem


class FileSystemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fs = FileSystem()
        self.current_user = ""
        self.current_open_file = None  # 当前打开的文件路径
        self.init_ui()
        self.refresh_all()
        
    def init_ui(self):
        self.setWindowTitle("文件管理系统 - 操作系统实验八")
        self.setMinimumSize(1200, 800)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QWidget { background-color: #1a1a2e; color: #e0e0e0; font-family: 'Microsoft YaHei', sans-serif; }
            QPushButton {
                background-color: #2d2d44; border: 1px solid #3d3d5c;
                border-radius: 6px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background-color: #3d3d5c; border-color: #6c5ce7; }
            QPushButton#primary { background-color: #2980b9; border-color: #3498db; }
            QPushButton#primary:hover { background-color: #3498db; }
            QPushButton#success { background-color: #27ae60; border-color: #2ecc71; }
            QPushButton#success:hover { background-color: #2ecc71; }
            QPushButton#danger { background-color: #c0392b; border-color: #e74c3c; }
            QPushButton#danger:hover { background-color: #e74c3c; }
            QLineEdit, QTextEdit {
                background-color: #0f0f1a; border: 1px solid #2d2d44;
                border-radius: 4px; padding: 6px 10px;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #6c5ce7; }
            QTableWidget, QListWidget {
                background-color: #0f0f1a; border: 1px solid #2d2d44;
                border-radius: 4px;
                alternate-background-color: #1a1a30;
            }
            QTableWidget::item:selected, QListWidget::item:selected {
                background-color: #6c5ce7; color: white;
            }
            QHeaderView::section {
                background-color: #2d2d44; padding: 6px;
                border: 1px solid #3d3d5c; font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #2d2d44; border-radius: 6px;
                background-color: #1a1a2e;
            }
            QTabBar::tab {
                background-color: #2d2d44; padding: 8px 20px;
                border: 1px solid #3d3d5c; border-bottom: none;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background-color: #3d3d5c; border-color: #6c5ce7; }
            QGroupBox {
                border: 2px solid #2d2d44; border-radius: 6px;
                margin-top: 12px; padding-top: 6px; font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 16px;
                padding: 0 8px; color: #6c5ce7;
            }
            QStatusBar { background-color: #0f0f1a; color: #808090; padding: 4px; }
            QLabel#title { font-size: 16px; font-weight: bold; color: #6c5ce7; }
            QTextEdit#file_viewer {
                background-color: #0a0a14;
                border: 1px solid #2d2d44;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #e0e0e0;
            }
            QTextEdit#file_viewer:focus {
                border-color: #6c5ce7;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部信息栏
        top_bar = QFrame()
        top_bar.setStyleSheet("QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a1a3e,stop:1 #2d1b4e); border-radius: 8px; padding: 8px; }")
        top_layout = QHBoxLayout(top_bar)
        
        name_label = QLabel("👤 姓名: XXX | 学号: XXXXXXXXXX")
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #a29bfe;")
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        
        self.status_info = QLabel("🔐 未登录")
        self.status_info.setStyleSheet("font-size: 13px; color: #fd79a8;")
        top_layout.addWidget(self.status_info)
        
        time_label = QLabel()
        time_label.setStyleSheet("color: #808090; font-size: 12px;")
        time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        top_layout.addWidget(time_label)
        
        main_layout.addWidget(top_bar)
        
        # 主选项卡
        self.tabs = QTabWidget()
        self.create_login_tab()
        self.create_file_tab()
        self.create_user_tab()
        self.create_optimize_tab()
        main_layout.addWidget(self.tabs)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        timer = QTimer(self)
        timer.timeout.connect(lambda: time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        timer.start(1000)
    
    def create_login_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 40, 50, 40)
        
        title = QLabel("🔐 用户登录 / 注册")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        login_group = QGroupBox("登录")
        login_layout = QGridLayout(login_group)
        login_layout.setSpacing(12)
        
        login_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("输入用户名")
        self.login_username.returnPressed.connect(self.handle_login)
        login_layout.addWidget(self.login_username, 0, 1)
        
        login_layout.addWidget(QLabel("密码:"), 1, 0)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("输入密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.returnPressed.connect(self.handle_login)
        login_layout.addWidget(self.login_password, 1, 1)
        
        login_btn = QPushButton("🚪 登录")
        login_btn.setObjectName("primary")
        login_btn.clicked.connect(self.handle_login)
        login_layout.addWidget(login_btn, 2, 0, 1, 2)
        layout.addWidget(login_group)
        
        register_group = QGroupBox("注册新用户")
        register_layout = QGridLayout(register_group)
        register_layout.setSpacing(12)
        
        register_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("至少3个字符")
        register_layout.addWidget(self.register_username, 0, 1)
        
        register_layout.addWidget(QLabel("密码:"), 1, 0)
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("至少6个字符")
        self.register_password.setEchoMode(QLineEdit.Password)
        register_layout.addWidget(self.register_password, 1, 1)
        
        register_layout.addWidget(QLabel("确认密码:"), 2, 0)
        self.register_confirm = QLineEdit()
        self.register_confirm.setPlaceholderText("再次输入密码")
        self.register_confirm.setEchoMode(QLineEdit.Password)
        register_layout.addWidget(self.register_confirm, 2, 1)
        
        register_btn = QPushButton("📝 注册")
        register_btn.setObjectName("success")
        register_btn.clicked.connect(self.handle_register)
        register_layout.addWidget(register_btn, 3, 0, 1, 2)
        layout.addWidget(register_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "🔐 登录/注册")
    
    def create_file_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # 导航栏
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        self.path_display = QLineEdit("/")
        self.path_display.setReadOnly(True)
        self.path_display.setStyleSheet("QLineEdit { background-color: #0f0f1a; border: 1px solid #2d2d44; border-radius: 4px; padding: 6px 10px; color: #a29bfe; }")
        nav_layout.addWidget(self.path_display, 1)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_files)
        nav_layout.addWidget(refresh_btn)
        
        home_btn = QPushButton("🏠 主页")
        home_btn.clicked.connect(self.go_home)
        nav_layout.addWidget(home_btn)
        
        up_btn = QPushButton("⬆ 上级")
        up_btn.clicked.connect(self.go_up)
        nav_layout.addWidget(up_btn)
        layout.addLayout(nav_layout)
        
        # 文件列表
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels(["权限", "大小", "修改时间", "访问时间", "名称", "类型"])
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.cellDoubleClicked.connect(self.on_file_double_click)
        layout.addWidget(self.file_table, 1)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        mkdir_btn = QPushButton("📁 新建目录")
        mkdir_btn.clicked.connect(self.create_directory)
        btn_layout.addWidget(mkdir_btn)
        
        create_btn = QPushButton("📄 新建文件")
        create_btn.clicked.connect(self.create_file_dialog)
        btn_layout.addWidget(create_btn)
        
        delete_btn = QPushButton("🗑 删除")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        upload_btn = QPushButton("📤 导入")
        upload_btn.setObjectName("primary")
        upload_btn.clicked.connect(self.import_file)
        btn_layout.addWidget(upload_btn)
        
        download_btn = QPushButton("📥 导出")
        download_btn.clicked.connect(self.export_file)
        btn_layout.addWidget(download_btn)
        
        info_btn = QPushButton("ℹ️ 属性")
        info_btn.clicked.connect(self.show_file_info)
        btn_layout.addWidget(info_btn)
        
        btn_layout.addStretch()
        
        open_btn = QPushButton("📂 打开查看")
        open_btn.setObjectName("primary")
        open_btn.clicked.connect(self.open_selected_file)
        btn_layout.addWidget(open_btn)
        layout.addLayout(btn_layout)
        
        # 搜索
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索文件名...")
        search_layout.addWidget(self.search_input, 1)
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primary")
        search_btn.clicked.connect(self.search_file)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(80)
        self.search_results.itemDoubleClicked.connect(self.on_search_result_click)
        layout.addWidget(self.search_results)
        
        # ===== 文件查看器区域（增强版） =====
        viewer_group = QGroupBox("📄 文件查看器 / 编辑器")
        viewer_layout = QVBoxLayout(viewer_group)
        
        # 查看器工具栏
        viewer_toolbar = QHBoxLayout()
        
        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("color: #a29bfe; font-weight: bold;")
        viewer_toolbar.addWidget(self.file_name_label)
        
        viewer_toolbar.addStretch()
        
        # 行号显示
        self.line_count_label = QLabel("行数: 0")
        self.line_count_label.setStyleSheet("color: #808090; font-size: 11px;")
        viewer_toolbar.addWidget(self.line_count_label)
        
        # 编码显示
        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setStyleSheet("color: #808090; font-size: 11px;")
        viewer_toolbar.addWidget(self.encoding_label)
        
        viewer_layout.addLayout(viewer_toolbar)
        
        # 文件内容显示区域
        self.file_content = QTextEdit()
        self.file_content.setObjectName("file_viewer")
        self.file_content.setPlaceholderText(
            "📂 请双击文件或点击「打开查看」按钮查看文件内容\n\n"
            "支持查看文本文件内容，支持编辑和保存"
        )
        self.file_content.setLineWrapMode(QTextEdit.NoWrap)
        viewer_layout.addWidget(self.file_content)
        
        # 底部按钮
        viewer_bottom = QHBoxLayout()
        
        save_btn = QPushButton("💾 保存内容")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self.save_content)
        viewer_bottom.addWidget(save_btn)
        
        reload_btn = QPushButton("🔄 重新加载")
        reload_btn.clicked.connect(self.reload_file_content)
        viewer_bottom.addWidget(reload_btn)
        
        clear_btn = QPushButton("🗑 清空内容")
        clear_btn.clicked.connect(self.file_content.clear)
        viewer_bottom.addWidget(clear_btn)
        
        viewer_bottom.addStretch()
        
        # 文件大小显示
        self.file_size_label = QLabel("大小: 0 字节")
        self.file_size_label.setStyleSheet("color: #808090; font-size: 11px;")
        viewer_bottom.addWidget(self.file_size_label)
        
        viewer_layout.addLayout(viewer_bottom)
        
        layout.addWidget(viewer_group)
        self.tabs.addTab(tab, "📁 文件管理")
    
    def create_user_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        info_group = QGroupBox("👤 当前用户信息")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)
        
        self.user_info_label = QLabel("未登录")
        self.user_info_label.setStyleSheet("color: #fd79a8; font-weight: bold;")
        info_layout.addRow("状态:", self.user_info_label)
        
        self.user_uid_label = QLabel("-")
        info_layout.addRow("UID:", self.user_uid_label)
        
        self.user_gid_label = QLabel("-")
        info_layout.addRow("GID:", self.user_gid_label)
        
        self.user_home_label = QLabel("-")
        info_layout.addRow("主目录:", self.user_home_label)
        
        self.user_login_label = QLabel("-")
        info_layout.addRow("上次登录:", self.user_login_label)
        
        logout_btn = QPushButton("🚪 登出")
        logout_btn.setObjectName("danger")
        logout_btn.clicked.connect(self.handle_logout)
        info_layout.addRow(logout_btn)
        layout.addWidget(info_group)
        
        perm_group = QGroupBox("🔒 权限管理 (chmod)")
        perm_layout = QGridLayout(perm_group)
        perm_layout.setSpacing(10)
        
        perm_layout.addWidget(QLabel("文件路径:"), 0, 0)
        self.chmod_path = QLineEdit()
        self.chmod_path.setPlaceholderText("例如: /home/admin/test.txt")
        perm_layout.addWidget(self.chmod_path, 0, 1)
        
        perm_layout.addWidget(QLabel("权限模式:"), 1, 0)
        self.chmod_mode = QLineEdit()
        self.chmod_mode.setPlaceholderText("例如: 755")
        perm_layout.addWidget(self.chmod_mode, 1, 1)
        
        chmod_btn = QPushButton("修改权限")
        chmod_btn.setObjectName("primary")
        chmod_btn.clicked.connect(self.handle_chmod)
        perm_layout.addWidget(chmod_btn, 2, 0, 1, 2)
        layout.addWidget(perm_group)
        
        user_list_group = QGroupBox("👥 系统用户列表")
        user_list_layout = QVBoxLayout(user_list_group)
        
        self.user_list = QListWidget()
        user_list_layout.addWidget(self.user_list)
        
        refresh_user_btn = QPushButton("🔄 刷新用户列表")
        refresh_user_btn.clicked.connect(self.refresh_users)
        user_list_layout.addWidget(refresh_user_btn)
        layout.addWidget(user_list_group)
        
        self.tabs.addTab(tab, "👥 用户管理")
    
    def create_optimize_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        defrag_group = QGroupBox("🔧 优化1: 增强型磁盘碎片整理算法")
        defrag_group.setStyleSheet("QGroupBox { border: 2px solid #6c5ce7; } QGroupBox::title { color: #a29bfe; }")
        defrag_layout = QVBoxLayout(defrag_group)
        
        defrag_desc = QLabel(
            "采用加权碎片评分算法，优先整理碎片率高的文件，将文件块移动到连续区域，\n"
            "显著减少磁头寻道时间，提升文件访问性能。"
        )
        defrag_desc.setWordWrap(True)
        defrag_desc.setStyleSheet("color: #b0b0c0; font-size: 12px;")
        defrag_layout.addWidget(defrag_desc)
        
        defrag_btn_layout = QHBoxLayout()
        self.defrag_btn = QPushButton("🔧 执行碎片整理")
        self.defrag_btn.setObjectName("primary")
        self.defrag_btn.clicked.connect(self.handle_defragment)
        defrag_btn_layout.addWidget(self.defrag_btn)
        
        self.defrag_status = QLabel("就绪")
        self.defrag_status.setStyleSheet("color: #a0a0b0;")
        defrag_btn_layout.addWidget(self.defrag_status)
        defrag_btn_layout.addStretch()
        defrag_layout.addLayout(defrag_btn_layout)
        
        self.defrag_report = QTextEdit()
        self.defrag_report.setPlaceholderText("点击执行碎片整理查看分析报告...")
        self.defrag_report.setMaximumHeight(150)
        self.defrag_report.setStyleSheet("QTextEdit { background-color: #0a0a14; border: 1px solid #2d2d44; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; }")
        defrag_layout.addWidget(self.defrag_report)
        layout.addWidget(defrag_group)
        
        cache_group = QGroupBox("⚡ 优化2: 高效边缘缓存系统")
        cache_group.setStyleSheet("QGroupBox { border: 2px solid #00b894; } QGroupBox::title { color: #55efc4; }")
        cache_layout = QVBoxLayout(cache_group)
        
        cache_desc = QLabel(
            "基于LRU淘汰策略的边缘缓存，自动缓存热点文件内容，减少磁盘I/O操作。\n"
            "包含脏页回写机制，确保数据一致性。"
        )
        cache_desc.setWordWrap(True)
        cache_desc.setStyleSheet("color: #b0b0c0; font-size: 12px;")
        cache_layout.addWidget(cache_desc)
        
        cache_btn_layout = QHBoxLayout()
        cache_btn = QPushButton("📊 刷新缓存统计")
        cache_btn.setObjectName("success")
        cache_btn.clicked.connect(self.refresh_cache_stats)
        cache_btn_layout.addWidget(cache_btn)
        
        clear_cache_btn = QPushButton("🗑 清空缓存")
        clear_cache_btn.clicked.connect(self.clear_cache)
        cache_btn_layout.addWidget(clear_cache_btn)
        cache_btn_layout.addStretch()
        cache_layout.addLayout(cache_btn_layout)
        
        self.cache_stats = QTextEdit()
        self.cache_stats.setPlaceholderText("点击刷新查看缓存统计...")
        self.cache_stats.setMaximumHeight(150)
        self.cache_stats.setStyleSheet("QTextEdit { background-color: #0a0a14; border: 1px solid #2d2d44; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; }")
        cache_layout.addWidget(self.cache_stats)
        layout.addWidget(cache_group)
        
        sys_group = QGroupBox("📊 系统信息")
        sys_layout = QVBoxLayout(sys_group)
        
        self.sys_info = QTextEdit()
        self.sys_info.setReadOnly(True)
        self.sys_info.setMaximumHeight(120)
        self.sys_info.setStyleSheet("QTextEdit { background-color: #0a0a14; border: 1px solid #2d2d44; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; }")
        sys_layout.addWidget(self.sys_info)
        
        refresh_sys_btn = QPushButton("🔄 刷新系统信息")
        refresh_sys_btn.clicked.connect(self.refresh_system_info)
        sys_layout.addWidget(refresh_sys_btn)
        layout.addWidget(sys_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "⚡ 系统优化")
    
    # ==================== 核心功能 ====================
    
    def refresh_all(self):
        self.refresh_files()
        self.refresh_users()
        self.refresh_system_info()
        self.refresh_cache_stats()
        self.update_user_info()
    
    def update_user_info(self):
        if self.fs.is_user_logged_in():
            username = self.fs.get_current_username()
            self.current_user = username
            self.status_info.setText(f"✅ 已登录: {username}")
            self.status_info.setStyleSheet("font-size: 13px; color: #55efc4;")
            self.user_info_label.setText(f"已登录: {username}")
            self.user_info_label.setStyleSheet("color: #55efc4; font-weight: bold;")
        else:
            self.current_user = ""
            self.status_info.setText("🔐 未登录")
            self.status_info.setStyleSheet("font-size: 13px; color: #fd79a8;")
            self.user_info_label.setText("未登录")
            self.user_info_label.setStyleSheet("color: #fd79a8; font-weight: bold;")
            self.user_uid_label.setText("-")
            self.user_gid_label.setText("-")
            self.user_home_label.setText("-")
            self.user_login_label.setText("-")
    
    def refresh_files(self):
        if not self.fs.is_user_logged_in():
            self.file_table.setRowCount(0)
            self.path_display.setText("/")
            return
        
        try:
            path = self.fs.get_current_path()
            self.path_display.setText(path)
            entries = self.fs.ls()
            
            self.file_table.setRowCount(len(entries))
            for row, entry in enumerate(entries):
                parts = entry.split()
                if len(parts) >= 4:
                    self.file_table.setItem(row, 0, QTableWidgetItem(parts[0]))
                    self.file_table.setItem(row, 1, QTableWidgetItem(parts[1]))
                    time_str = parts[2] + " " + parts[3]
                    self.file_table.setItem(row, 2, QTableWidgetItem(time_str))
                    self.file_table.setItem(row, 3, QTableWidgetItem(time_str))
                    name = " ".join(parts[4:]) if len(parts) > 4 else ""
                    is_dir = name.endswith("/")
                    if is_dir:
                        name = name[:-1]
                        file_type = "📁 目录"
                    else:
                        file_type = "📄 文件"
                    self.file_table.setItem(row, 4, QTableWidgetItem(name))
                    self.file_table.setItem(row, 5, QTableWidgetItem(file_type))
        except Exception as e:
            self.status_bar.showMessage(f"刷新失败: {str(e)}")
    
    def refresh_users(self):
        self.user_list.clear()
        users = self.fs.get_all_users()
        for user in users:
            self.user_list.addItem(
                f"{user.username} (UID: {user.uid}, GID: {user.gid})"
            )
    
    def refresh_system_info(self):
        self.sys_info.setText(self.fs.get_system_info())
    
    def refresh_cache_stats(self):
        self.cache_stats.setText(self.fs.get_cache_stats())
    
    def show_message(self, msg):
        self.status_bar.showMessage(msg)
    
    def show_error(self, title, msg):
        QMessageBox.warning(self, title, msg)
    
    def show_info(self, title, msg):
        QMessageBox.information(self, title, msg)
    
    def require_login(self):
        if not self.fs.is_user_logged_in():
            self.show_error("错误", "请先登录！")
            return False
        return True
    
    # ==================== 登录/注册 ====================
    
    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        
        if not username or not password:
            self.show_error("登录失败", "用户名和密码不能为空！")
            return
        
        if self.fs.login_user(username, password):
            self.update_user_info()
            self.refresh_all()
            self.show_message(f"✅ 欢迎回来，{username}！")
            self.show_info("登录成功", f"欢迎 {username}！")
        else:
            self.show_error("登录失败", "用户名或密码错误！")
    
    def handle_register(self):
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm = self.register_confirm.text().strip()
        
        if not username or not password:
            self.show_error("注册失败", "用户名和密码不能为空！")
            return
        if password != confirm:
            self.show_error("注册失败", "两次输入的密码不一致！")
            return
        if len(username) < 3:
            self.show_error("注册失败", "用户名至少3个字符！")
            return
        if len(password) < 6:
            self.show_error("注册失败", "密码至少6个字符！")
            return
        
        if self.fs.register_user(username, password):
            self.show_info("注册成功", f"用户 {username} 注册成功！\n请登录。")
            self.register_username.clear()
            self.register_password.clear()
            self.register_confirm.clear()
            self.show_message(f"用户 {username} 注册成功")
            self.refresh_users()
        else:
            self.show_error("注册失败", "用户名已存在或密码不符合要求！")
    
    def handle_logout(self):
        self.fs.logout_user()
        self.current_user = ""
        self.current_open_file = None
        self.file_name_label.setText("未选择文件")
        self.file_content.clear()
        self.file_size_label.setText("大小: 0 字节")
        self.line_count_label.setText("行数: 0")
        self.update_user_info()
        self.refresh_files()
        self.show_message("已登出")
        self.show_info("登出", "已成功登出！")
    
    # ==================== 文件操作 ====================
    
    def go_home(self):
        if self.current_user:
            self.cd(f"/home/{self.current_user}")
    
    def go_up(self):
        path = self.path_display.text()
        if path != "/":
            parent = os.path.dirname(path)
            self.cd(parent if parent else "/")
    
    def cd(self, path):
        if not self.require_login():
            return
        if self.fs.cd(path):
            self.current_open_file = None
            self.file_name_label.setText("未选择文件")
            self.file_content.clear()
            self.file_size_label.setText("大小: 0 字节")
            self.line_count_label.setText("行数: 0")
            self.refresh_files()
        else:
            self.show_error("错误", f"无法切换到目录: {path}")
    
    def on_file_double_click(self, row, col):
        name_item = self.file_table.item(row, 4)
        type_item = self.file_table.item(row, 5)
        if name_item and type_item:
            name = name_item.text()
            if "目录" in type_item.text():
                self.cd(self.path_display.text() + "/" + name)
            else:
                self.open_file_by_name(name)
    
    def on_search_result_click(self, item):
        """点击搜索结果打开文件"""
        path = item.text()
        if path.startswith("/"):
            # 提取文件名
            name = os.path.basename(path)
            # 切换到文件所在目录
            dir_path = os.path.dirname(path)
            if self.fs.cd(dir_path):
                self.refresh_files()
                # 打开文件
                self.open_file_by_name(name)
    
    def open_file_by_name(self, name):
        if not self.require_login():
            return
        
        path = self.path_display.text() + "/" + name
        self.current_open_file = path
        
        # 更新标签
        self.file_name_label.setText(f"📄 {name}")
        
        fd = self.fs.open_file(path)
        if fd >= 0:
            content = self.fs.read_file(fd)
            self.fs.close_file(fd)
            
            if content:
                self.file_content.setText(content)
                # 更新统计信息
                lines = content.count("\n") + 1 if content else 0
                self.line_count_label.setText(f"行数: {lines}")
                self.file_size_label.setText(f"大小: {len(content)} 字节")
                self.show_message(f"📂 已打开文件: {name}")
            else:
                self.file_content.setText("(文件为空)")
                self.line_count_label.setText("行数: 0")
                self.file_size_label.setText("大小: 0 字节")
                self.show_message(f"📂 文件为空: {name}")
        else:
            self.show_error("错误", f"无法打开文件: {name}")
            self.file_name_label.setText("未选择文件")
    
    def reload_file_content(self):
        """重新加载当前文件内容"""
        if not self.current_open_file:
            self.show_error("错误", "没有打开的文件！")
            return
        
        name = os.path.basename(self.current_open_file)
        fd = self.fs.open_file(self.current_open_file)
        if fd >= 0:
            content = self.fs.read_file(fd)
            self.fs.close_file(fd)
            self.file_content.setText(content)
            lines = content.count("\n") + 1 if content else 0
            self.line_count_label.setText(f"行数: {lines}")
            self.file_size_label.setText(f"大小: {len(content)} 字节")
            self.show_message(f"🔄 已重新加载: {name}")
        else:
            self.show_error("错误", f"无法重新加载文件: {name}")
    
    def open_selected_file(self):
        row = self.file_table.currentRow()
        if row < 0:
            self.show_error("错误", "请选择要打开的文件！")
            return
        name_item = self.file_table.item(row, 4)
        type_item = self.file_table.item(row, 5)
        if name_item:
            if "目录" in type_item.text():
                self.cd(self.path_display.text() + "/" + name_item.text())
            else:
                self.open_file_by_name(name_item.text())
    
    def create_directory(self):
        if not self.require_login():
            return
        name, ok = QInputDialog.getText(self, "新建目录", "请输入目录名称:")
        if ok and name and name.strip():
            path = self.path_display.text() + "/" + name
            if self.fs.mkdir(path):
                self.show_message(f"📁 创建目录: {name}")
                self.refresh_files()
            else:
                self.show_error("错误", f"无法创建目录: {name}")
    
    def create_file_dialog(self):
        if not self.require_login():
            return
        name, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
        if ok and name and name.strip():
            path = self.path_display.text() + "/" + name
            if self.fs.create_file(path):
                self.show_message(f"📄 创建文件: {name}")
                self.refresh_files()
                # 自动打开新创建的文件
                self.open_file_by_name(name)
            else:
                self.show_error("错误", f"无法创建文件: {name}")
    
    def delete_selected(self):
        if not self.require_login():
            return
        row = self.file_table.currentRow()
        if row < 0:
            self.show_error("错误", "请选择要删除的项目！")
            return
        name_item = self.file_table.item(row, 4)
        if not name_item:
            return
        name = name_item.text()
        
        # 如果删除的是当前打开的文件，清空查看器
        if self.current_open_file and name in self.current_open_file:
            self.current_open_file = None
            self.file_name_label.setText("未选择文件")
            self.file_content.clear()
            self.file_size_label.setText("大小: 0 字节")
            self.line_count_label.setText("行数: 0")
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{name}' 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = self.path_display.text() + "/" + name
            if not self.fs.delete_file(path):
                if not self.fs.rmdir(path):
                    self.show_error("错误", f"无法删除: {name}")
                    return
            self.show_message(f"🗑 已删除: {name}")
            self.refresh_files()
    
    def import_file(self):
        if not self.require_login():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要导入的文件",
            os.path.expanduser("~"),
            "所有文件 (*.*);;文本文件 (*.txt);;Python文件 (*.py);;JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        if not os.path.exists(file_path):
            self.show_error("导入失败", f"文件不存在: {file_path}")
            return
        
        if not os.access(file_path, os.R_OK):
            self.show_error("导入失败", f"文件不可读: {file_path}\n请检查文件权限。")
            return
        
        file_name = os.path.basename(file_path)
        fs_path = self.path_display.text() + "/" + file_name
        
        self.status_bar.showMessage(f"📤 正在导入: {file_name}...")
        
        try:
            if self.fs.import_file(file_path, fs_path):
                self.show_message(f"✅ 导入成功: {file_name}")
                self.refresh_files()
                # 自动打开导入的文件
                self.open_file_by_name(file_name)
                self.show_info("导入成功", f"文件 '{file_name}' 已成功导入到文件系统！")
            else:
                self.show_error("导入失败", f"无法导入文件: {file_name}\n请检查文件系统空间和路径。")
        except Exception as e:
            self.show_error("导入异常", f"导入文件时发生错误:\n{str(e)}")
    
    def export_file(self):
        if not self.require_login():
            return
        
        row = self.file_table.currentRow()
        if row < 0:
            self.show_error("错误", "请选择要导出的文件！")
            return
        
        name_item = self.file_table.item(row, 4)
        type_item = self.file_table.item(row, 5)
        if not name_item or "目录" in type_item.text():
            self.show_error("错误", "请选择文件进行导出！")
            return
        
        name = name_item.text()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            name,
            "所有文件 (*.*);;文本文件 (*.txt)"
        )
        
        if not save_path:
            return
        
        fs_path = self.path_display.text() + "/" + name
        
        try:
            if self.fs.export_file(fs_path, save_path):
                self.show_message(f"✅ 导出成功: {name}")
                self.show_info("导出成功", f"文件已导出到:\n{save_path}")
            else:
                self.show_error("导出失败", f"无法导出文件: {name}")
        except Exception as e:
            self.show_error("导出异常", f"导出文件时发生错误:\n{str(e)}")
    
    def show_file_info(self):
        if not self.require_login():
            return
        row = self.file_table.currentRow()
        if row < 0:
            self.show_error("错误", "请选择要查看属性的项目！")
            return
        name_item = self.file_table.item(row, 4)
        if not name_item:
            return
        name = name_item.text()
        path = self.path_display.text() + "/" + name
        info = self.fs.get_file_info(path)
        self.show_info(f"📄 文件信息: {name}", info)
    
    def save_content(self):
        """保存文件内容"""
        if not self.require_login():
            return
        
        if not self.current_open_file:
            self.show_error("错误", "没有打开的文件！请先打开一个文件。")
            return
        
        content = self.file_content.toPlainText()
        name = os.path.basename(self.current_open_file)
        
        fd = self.fs.open_file(self.current_open_file)
        if fd >= 0:
            if self.fs.write_file(fd, content, False):
                self.show_message(f"💾 已保存: {name}")
                # 更新统计
                lines = content.count("\n") + 1 if content else 0
                self.line_count_label.setText(f"行数: {lines}")
                self.file_size_label.setText(f"大小: {len(content)} 字节")
                self.show_info("保存成功", f"文件 {name} 已保存！")
            else:
                self.show_error("保存失败", f"无法写入文件: {name}")
            self.fs.close_file(fd)
        else:
            self.show_error("保存失败", f"无法打开文件: {name}")
    
    def search_file(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.show_error("错误", "请输入搜索关键词！")
            return
        
        result = self.fs.search_file(keyword)
        self.search_results.clear()
        if result != "文件未找到":
            lines = result.split("\n")
            for line in lines:
                self.search_results.addItem(line)
            count = len(lines)
            self.show_message(f"🔍 找到 {count} 个结果 (双击打开)")
        else:
            self.search_results.addItem(f"未找到文件: {keyword}")
            self.show_message(f"未找到文件: {keyword}")
    
    def handle_chmod(self):
        if not self.require_login():
            return
        path = self.chmod_path.text().strip()
        mode = self.chmod_mode.text().strip()
        
        if not path or not mode:
            self.show_error("错误", "请填写完整信息！")
            return
        if not mode.isdigit() or len(mode) != 3:
            self.show_error("错误", "权限模式必须是3位数字（如 755）！")
            return
        
        if self.fs.chmod(path, int(mode, 8)):
            self.show_message(f"🔒 权限已修改: {path} -> {mode}")
            self.show_info("成功", f"文件 {path} 权限已修改为 {mode}")
        else:
            self.show_error("错误", f"无法修改权限: {path}")
    
    # ==================== 优化功能 ====================
    
    def handle_defragment(self):
        if not self.require_login():
            return
        
        self.defrag_status.setText("⏳ 正在扫描碎片...")
        self.defrag_status.setStyleSheet("color: #fdcb6e;")
        self.defrag_btn.setEnabled(False)
        
        def do_defrag():
            try:
                report = self.fs.get_defragmentation_report()
                self.defrag_report.setText(report)
                
                result = self.fs.defragment()
                self.defrag_report.append("\n" + result)
                
                self.defrag_status.setText("✅ 碎片整理完成！")
                self.defrag_status.setStyleSheet("color: #55efc4;")
                self.show_message("碎片整理完成")
                self.show_info("完成", "磁盘碎片整理已完成！")
                self.refresh_system_info()
            except Exception as e:
                self.defrag_status.setText(f"❌ 错误: {str(e)}")
                self.defrag_status.setStyleSheet("color: #fd79a8;")
            self.defrag_btn.setEnabled(True)
        
        QTimer.singleShot(100, do_defrag)
    
    def clear_cache(self):
        self.fs.clear_cache()
        self.show_message("🗑 缓存已清空")
        self.refresh_cache_stats()
        self.show_info("缓存清空", "缓存已成功清空！")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FileSystemGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
