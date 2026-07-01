#!/usr/bin/env python3
import sys, os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from file_system import FileSystem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fs = FileSystem()
        self.current_open_path = None
        self.init_ui()
        self.refresh_all()

    def init_ui(self):
        self.setWindowTitle("文件管理系统 - 实验八")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; }
            QPushButton { background: #313244; border: none; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background: #45475a; }
            QPushButton#primary { background: #89b4fa; color: #1e1e2e; }
            QPushButton#primary:hover { background: #74c7ec; }
            QPushButton#danger { background: #f38ba8; color: #1e1e2e; }
            QPushButton#danger:hover { background: #eba0ac; }
            QPushButton#success { background: #a6e3a1; color: #1e1e2e; }
            QPushButton#success:hover { background: #94e2d5; }
            QLineEdit, QTextEdit { background: #181825; border: 1px solid #45475a; border-radius: 4px; padding: 4px; }
            QTableWidget { background: #181825; alternate-background-color: #1e1e2e; border: 1px solid #45475a; }
            QHeaderView::section { background: #313244; padding: 4px; border: none; }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; }
            QTabBar::tab { background: #313244; padding: 6px 14px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #45475a; }
            QGroupBox { border: 1px solid #45475a; border-radius: 6px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #89b4fa; }
            QStatusBar { background: #181825; color: #6c7086; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QFrame()
        top.setStyleSheet("background: #313244; border-radius: 8px; padding: 6px;")
        top_layout = QHBoxLayout(top)
        name_label = QLabel("👤 张三 | 学号: 2024001")
        name_label.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        self.user_status = QLabel("🔐 未登录")
        self.user_status.setStyleSheet("color: #f9e2af;")
        top_layout.addWidget(self.user_status)
        time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time_label.setStyleSheet("color: #6c7086;")
        top_layout.addWidget(time_label)
        timer = QTimer(self); timer.timeout.connect(lambda: time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        timer.start(1000)
        layout.addWidget(top)

        tabs = QTabWidget()
        self.login_tab = self._create_login_tab()
        self.file_tab = self._create_file_tab()
        self.user_tab = self._create_user_tab()
        self.opt_tab = self._create_opt_tab()
        tabs.addTab(self.login_tab, "登录/注册")
        tabs.addTab(self.file_tab, "文件管理")
        tabs.addTab(self.user_tab, "用户管理")
        tabs.addTab(self.opt_tab, "系统优化")
        layout.addWidget(tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _create_login_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 40, 50, 40)

        title = QLabel("🔐 用户登录 / 注册")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        g1 = QGroupBox("登录")
        g1_layout = QGridLayout(g1)
        g1_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.login_user = QLineEdit(); self.login_user.setPlaceholderText("admin")
        g1_layout.addWidget(self.login_user, 0, 1)
        g1_layout.addWidget(QLabel("密码:"), 1, 0)
        self.login_pass = QLineEdit(); self.login_pass.setEchoMode(QLineEdit.Password); self.login_pass.setPlaceholderText("admin123")
        g1_layout.addWidget(self.login_pass, 1, 1)
        btn_login = QPushButton("登录"); btn_login.setObjectName("primary"); btn_login.clicked.connect(self._login)
        g1_layout.addWidget(btn_login, 2, 0, 1, 2)
        layout.addWidget(g1)

        g2 = QGroupBox("注册新用户")
        g2_layout = QGridLayout(g2)
        g2_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.reg_user = QLineEdit(); self.reg_user.setPlaceholderText("至少3字符")
        g2_layout.addWidget(self.reg_user, 0, 1)
        g2_layout.addWidget(QLabel("密码:"), 1, 0)
        self.reg_pass = QLineEdit(); self.reg_pass.setEchoMode(QLineEdit.Password); self.reg_pass.setPlaceholderText("至少6字符")
        g2_layout.addWidget(self.reg_pass, 1, 1)
        g2_layout.addWidget(QLabel("确认:"), 2, 0)
        self.reg_confirm = QLineEdit(); self.reg_confirm.setEchoMode(QLineEdit.Password)
        g2_layout.addWidget(self.reg_confirm, 2, 1)
        btn_reg = QPushButton("注册"); btn_reg.setObjectName("success"); btn_reg.clicked.connect(self._register)
        g2_layout.addWidget(btn_reg, 3, 0, 1, 2)
        layout.addWidget(g2)
        layout.addStretch()
        return tab

    def _login(self):
        u = self.login_user.text().strip()
        p = self.login_pass.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return
        if self.fs.login_user(u, p):
            self.user_status.setText(f"✅ 已登录: {u}")
            self.user_status.setStyleSheet("color: #a6e3a1;")
            self.refresh_all()
            self.status_bar.showMessage(f"欢迎 {u}")
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")

    def _register(self):
        u = self.reg_user.text().strip()
        p = self.reg_pass.text().strip()
        c = self.reg_confirm.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return
        if p != c:
            QMessageBox.warning(self, "错误", "两次密码不一致")
            return
        if len(u) < 3 or len(p) < 6:
            QMessageBox.warning(self, "错误", "用户名≥3字符，密码≥6字符")
            return
        if self.fs.register_user(u, p):
            QMessageBox.information(self, "成功", f"用户 {u} 注册成功！请登录。")
            self.reg_user.clear(); self.reg_pass.clear(); self.reg_confirm.clear()
            self.refresh_users()
        else:
            QMessageBox.warning(self, "注册失败", "用户名已存在或不符合要求")

    def _create_file_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        nav = QHBoxLayout()
        self.path_display = QLineEdit("/")
        self.path_display.setReadOnly(True)
        nav.addWidget(self.path_display, 1)
        up_btn = QPushButton("上级"); up_btn.clicked.connect(self._go_up)
        nav.addWidget(up_btn)
        layout.addLayout(nav)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["权限", "大小", "修改时间", "名称", "类型"])
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.cellDoubleClicked.connect(self._on_file_double_click)
        layout.addWidget(self.file_table, 1)

        btns = QHBoxLayout()
        mkdir_btn = QPushButton("新建目录"); mkdir_btn.clicked.connect(self._mkdir)
        btns.addWidget(mkdir_btn)
        create_btn = QPushButton("新建文件"); create_btn.clicked.connect(self._create_file)
        btns.addWidget(create_btn)
        del_btn = QPushButton("删除"); del_btn.setObjectName("danger"); del_btn.clicked.connect(self._delete)
        btns.addWidget(del_btn)
        import_btn = QPushButton("导入"); import_btn.setObjectName("primary"); import_btn.clicked.connect(self._import)
        btns.addWidget(import_btn)
        export_btn = QPushButton("导出"); export_btn.clicked.connect(self._export)
        btns.addWidget(export_btn)
        info_btn = QPushButton("属性"); info_btn.clicked.connect(self._show_info)
        btns.addWidget(info_btn)
        btns.addStretch()
        open_btn = QPushButton("打开查看"); open_btn.setObjectName("primary"); open_btn.clicked.connect(self._open_selected)
        btns.addWidget(open_btn)
        layout.addLayout(btns)

        search = QHBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("搜索文件名...")
        search.addWidget(self.search_input, 1)
        search_btn = QPushButton("搜索"); search_btn.setObjectName("primary"); search_btn.clicked.connect(self._search)
        search.addWidget(search_btn)
        layout.addLayout(search)
        self.search_results = QListWidget(); self.search_results.setMaximumHeight(60); self.search_results.itemDoubleClicked.connect(self._on_search_click)
        layout.addWidget(self.search_results)

        viewer = QGroupBox("文件查看器")
        vlayout = QVBoxLayout(viewer)
        info_line = QHBoxLayout()
        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("font-weight: bold; color: #89b4fa;")
        info_line.addWidget(self.file_name_label)
        info_line.addStretch()
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #6c7086;")
        info_line.addWidget(self.file_info_label)
        vlayout.addLayout(info_line)

        self.file_content = QTextEdit()
        self.file_content.setPlaceholderText("双击文件或点击「打开查看」查看内容")
        self.file_content.setStyleSheet("font-family: 'Monospace'; font-size: 12px; background: #0f0f1a;")
        vlayout.addWidget(self.file_content)

        vbtns = QHBoxLayout()
        save_btn = QPushButton("保存"); save_btn.setObjectName("success"); save_btn.clicked.connect(self._save_content)
        vbtns.addWidget(save_btn)
        reload_btn = QPushButton("重新加载"); reload_btn.clicked.connect(self._reload)
        vbtns.addWidget(reload_btn)
        clear_btn = QPushButton("清空"); clear_btn.clicked.connect(self.file_content.clear)
        vbtns.addWidget(clear_btn)
        vbtns.addStretch()
        vlayout.addLayout(vbtns)
        layout.addWidget(viewer)

        return tab

    def _go_home(self):
        if self.fs.is_user_logged_in():
            self.fs.cd(f"/home/{self.fs.get_current_username()}")
            self.refresh_files()

    def _go_up(self):
        path = self.fs.cwd_path
        if path != "/":
            parent = os.path.dirname(path)
            self.fs.cd(parent if parent else "/")
            self.refresh_files()

    def _on_file_double_click(self, row, col):
        name_item = self.file_table.item(row, 3)
        type_item = self.file_table.item(row, 4)
        if name_item and type_item:
            name = name_item.text()
            if type_item.text() == "目录":
                self.fs.cd(self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name)
                self.refresh_files()
            else:
                self._open_file(name)

    def _open_file(self, name):
        path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
        self.current_open_path = path
        self.file_name_label.setText(f"文件: {name}")
        fd = self.fs.open_file(path)
        if fd >= 0:
            content = self.fs.read_file(fd)
            self.fs.close_file(fd)
            self.file_content.setText(content)
            lines = content.count('\n') + 1 if content else 0
            self.file_info_label.setText(f"行数: {lines} | 大小: {len(content)} 字节")
            self.status_bar.showMessage(f"已打开: {name}")
        else:
            QMessageBox.warning(self, "错误", f"无法打开文件: {name}")
            self.file_name_label.setText("未选择文件")

    def _open_selected(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "错误", "请先选择文件")
            return
        name_item = self.file_table.item(row, 3)
        type_item = self.file_table.item(row, 4)
        if name_item:
            if type_item.text() == "目录":
                self.fs.cd(self.fs.cwd_path + "/" + name_item.text() if self.fs.cwd_path != "/" else "/" + name_item.text())
                self.refresh_files()
            else:
                self._open_file(name_item.text())

    def _mkdir(self):
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        name, ok = QInputDialog.getText(self, "新建目录", "目录名:")
        if ok and name.strip():
            path = self.fs.cwd_path + "/" + name.strip() if self.fs.cwd_path != "/" else "/" + name.strip()
            if self.fs.mkdir(path):
                self.refresh_files()
                self.status_bar.showMessage(f"目录 {name} 创建成功")
            else:
                QMessageBox.warning(self, "错误", "创建失败")

    def _create_file(self):
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        name, ok = QInputDialog.getText(self, "新建文件", "文件名:")
        if ok and name.strip():
            path = self.fs.cwd_path + "/" + name.strip() if self.fs.cwd_path != "/" else "/" + name.strip()
            if self.fs.create_file(path):
                self.refresh_files()
                self._open_file(name.strip())
                self.status_bar.showMessage(f"文件 {name} 创建成功")
            else:
                QMessageBox.warning(self, "错误", "创建失败")

    def _delete(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "错误", "请先选择项目")
            return
        name_item = self.file_table.item(row, 3)
        if not name_item: return
        name = name_item.text()
        path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
        reply = QMessageBox.question(self, "确认删除", f"删除 '{name}' ?", QMessageBox.Yes|QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not self.fs.delete_file(path):
                if not self.fs.rmdir(path):
                    QMessageBox.warning(self, "错误", "删除失败")
                    return
            self.refresh_files()
            self.status_bar.showMessage(f"已删除 {name}")

    def _import(self):
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        fpath, _ = QFileDialog.getOpenFileName(self, "选择文件", os.path.expanduser("~"), "所有文件 (*.*)")
        if not fpath: return
        fname = os.path.basename(fpath)
        fs_path = self.fs.cwd_path + "/" + fname if self.fs.cwd_path != "/" else "/" + fname
        if self.fs.import_file(fpath, fs_path):
            self.refresh_files()
            self._open_file(fname)
            self.status_bar.showMessage(f"导入成功: {fname}")
        else:
            QMessageBox.warning(self, "错误", "导入失败")

    def _export(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "错误", "请先选择文件")
            return
        name_item = self.file_table.item(row, 3)
        type_item = self.file_table.item(row, 4)
        if not name_item or type_item.text() == "目录":
            QMessageBox.warning(self, "错误", "请选择文件")
            return
        name = name_item.text()
        save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", name)
        if not save_path: return
        fs_path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
        if self.fs.export_file(fs_path, save_path):
            self.status_bar.showMessage(f"导出成功: {name}")
        else:
            QMessageBox.warning(self, "错误", "导出失败")

    def _show_info(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "错误", "请先选择项目")
            return
        name_item = self.file_table.item(row, 3)
        if not name_item: return
        name = name_item.text()
        path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
        info = self.fs.get_file_info(path)
        QMessageBox.information(self, "文件信息", info)

    def _save_content(self):
        if not self.current_open_path:
            QMessageBox.warning(self, "错误", "没有打开的文件")
            return
        content = self.file_content.toPlainText()
        fd = self.fs.open_file(self.current_open_path)
        if fd >= 0:
            if self.fs.write_file(fd, content, False):
                self.status_bar.showMessage("保存成功")
                lines = content.count('\n') + 1 if content else 0
                self.file_info_label.setText(f"行数: {lines} | 大小: {len(content)} 字节")
            else:
                QMessageBox.warning(self, "错误", "保存失败")
            self.fs.close_file(fd)
        else:
            QMessageBox.warning(self, "错误", "无法打开文件")

    def _reload(self):
        if not self.current_open_path:
            QMessageBox.warning(self, "错误", "没有打开的文件")
            return
        name = os.path.basename(self.current_open_path)
        fd = self.fs.open_file(self.current_open_path)
        if fd >= 0:
            content = self.fs.read_file(fd)
            self.fs.close_file(fd)
            self.file_content.setText(content)
            lines = content.count('\n') + 1 if content else 0
            self.file_info_label.setText(f"行数: {lines} | 大小: {len(content)} 字节")
            self.status_bar.showMessage("重新加载完成")
        else:
            QMessageBox.warning(self, "错误", "重新加载失败")

    def _search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "错误", "请输入关键词")
            return
        result = self.fs.search_file(keyword)
        self.search_results.clear()
        if result == "文件未找到":
            self.search_results.addItem("未找到")
        else:
            lines = result.split('\n')   # 修复：先分割，再计算长度
            for line in lines:
                self.search_results.addItem(line)
            self.status_bar.showMessage(f"找到 {len(lines)} 个结果")

    def _on_search_click(self, item):
        path = item.text()
        if path.startswith('/'):
            name = os.path.basename(path)
            dirpath = os.path.dirname(path)
            self.fs.cd(dirpath)
            self.refresh_files()
            self._open_file(name)

    def _create_user_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QGroupBox("当前用户信息")
        info_layout = QFormLayout(info)
        self.user_info = QLabel("未登录")
        self.user_info.setStyleSheet("color: #f9e2af;")
        info_layout.addRow("状态:", self.user_info)
        self.uid_label = QLabel("-"); info_layout.addRow("UID:", self.uid_label)
        self.gid_label = QLabel("-"); info_layout.addRow("GID:", self.gid_label)
        self.home_label = QLabel("-"); info_layout.addRow("主目录:", self.home_label)
        logout_btn = QPushButton("登出"); logout_btn.setObjectName("danger"); logout_btn.clicked.connect(self._logout)
        info_layout.addRow(logout_btn)
        layout.addWidget(info)

        perm = QGroupBox("权限管理 (chmod)")
        perm_layout = QGridLayout(perm)
        perm_layout.addWidget(QLabel("文件路径:"), 0, 0)
        self.chmod_path = QLineEdit(); self.chmod_path.setPlaceholderText("/home/admin/test.txt")
        perm_layout.addWidget(self.chmod_path, 0, 1)
        perm_layout.addWidget(QLabel("权限模式:"), 1, 0)
        self.chmod_mode = QLineEdit(); self.chmod_mode.setPlaceholderText("755")
        perm_layout.addWidget(self.chmod_mode, 1, 1)
        chmod_btn = QPushButton("修改权限"); chmod_btn.setObjectName("primary"); chmod_btn.clicked.connect(self._chmod)
        perm_layout.addWidget(chmod_btn, 2, 0, 1, 2)
        layout.addWidget(perm)

        userlist = QGroupBox("系统用户列表")
        ulayout = QVBoxLayout(userlist)
        self.user_list = QListWidget()
        ulayout.addWidget(self.user_list)
        refresh_user_btn = QPushButton("刷新用户列表"); refresh_user_btn.clicked.connect(self.refresh_users)
        ulayout.addWidget(refresh_user_btn)
        layout.addWidget(userlist)

        return tab

    def _logout(self):
        self.fs.logout_user()
        self.user_status.setText("🔐 未登录")
        self.user_status.setStyleSheet("color: #f9e2af;")
        self.current_open_path = None
        self.file_name_label.setText("未选择文件")
        self.file_content.clear()
        self.file_info_label.setText("")
        self.refresh_all()

    def _chmod(self):
        path = self.chmod_path.text().strip()
        mode = self.chmod_mode.text().strip()
        if not path or not mode:
            QMessageBox.warning(self, "错误", "请填写完整")
            return
        if not mode.isdigit() or len(mode) != 3:
            QMessageBox.warning(self, "错误", "请输入3位数字")
            return
        if self.fs.chmod(path, int(mode, 8)):
            self.status_bar.showMessage(f"权限已修改: {path} -> {mode}")
        else:
            QMessageBox.warning(self, "错误", "修改失败")

    def _create_opt_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        g1 = QGroupBox("优化1: 磁盘碎片整理")
        g1.setStyleSheet("border: 1px solid #89b4fa;")
        g1_layout = QVBoxLayout(g1)
        desc = QLabel("采用加权碎片评分算法，优先整理碎片率高的文件。")
        desc.setStyleSheet("color: #a6adc8;")
        g1_layout.addWidget(desc)
        h1 = QHBoxLayout()
        self.defrag_btn = QPushButton("执行碎片整理"); self.defrag_btn.setObjectName("primary"); self.defrag_btn.clicked.connect(self._defrag)
        h1.addWidget(self.defrag_btn)
        self.defrag_status = QLabel("就绪"); self.defrag_status.setStyleSheet("color: #6c7086;")
        h1.addWidget(self.defrag_status)
        h1.addStretch()
        g1_layout.addLayout(h1)
        self.defrag_report = QTextEdit(); self.defrag_report.setMaximumHeight(100); self.defrag_report.setStyleSheet("background: #0f0f1a;")
        g1_layout.addWidget(self.defrag_report)
        layout.addWidget(g1)

        g2 = QGroupBox("优化2: 边缘缓存系统")
        g2.setStyleSheet("border: 1px solid #a6e3a1;")
        g2_layout = QVBoxLayout(g2)
        desc2 = QLabel("基于LRU淘汰策略，自动缓存热点文件内容。")
        desc2.setStyleSheet("color: #a6adc8;")
        g2_layout.addWidget(desc2)
        h2 = QHBoxLayout()
        cache_btn = QPushButton("刷新缓存统计"); cache_btn.setObjectName("success"); cache_btn.clicked.connect(self._refresh_cache)
        h2.addWidget(cache_btn)
        clear_btn = QPushButton("清空缓存"); clear_btn.clicked.connect(self._clear_cache)
        h2.addWidget(clear_btn)
        h2.addStretch()
        g2_layout.addLayout(h2)
        self.cache_stats = QTextEdit(); self.cache_stats.setMaximumHeight(100); self.cache_stats.setStyleSheet("background: #0f0f1a;")
        g2_layout.addWidget(self.cache_stats)
        layout.addWidget(g2)

        g3 = QGroupBox("系统信息")
        g3_layout = QVBoxLayout(g3)
        self.sys_info = QTextEdit(); self.sys_info.setReadOnly(True); self.sys_info.setMaximumHeight(100); self.sys_info.setStyleSheet("background: #0f0f1a;")
        g3_layout.addWidget(self.sys_info)
        refresh_sys = QPushButton("刷新系统信息"); refresh_sys.clicked.connect(self._refresh_sys)
        g3_layout.addWidget(refresh_sys)
        layout.addWidget(g3)
        layout.addStretch()
        return tab

    def _defrag(self):
        self.defrag_status.setText("正在扫描...")
        self.defrag_status.setStyleSheet("color: #f9e2af;")
        self.defrag_btn.setEnabled(False)
        QTimer.singleShot(100, lambda: self._do_defrag())

    def _do_defrag(self):
        try:
            report = self.fs.get_defragmentation_report()
            self.defrag_report.setText(report)
            result = self.fs.defragment()
            self.defrag_report.append("\n" + result)
            self.defrag_status.setText("✅ 完成")
            self.defrag_status.setStyleSheet("color: #a6e3a1;")
            self.status_bar.showMessage("碎片整理完成")
        except Exception as e:
            self.defrag_status.setText("❌ 错误")
            self.defrag_status.setStyleSheet("color: #f38ba8;")
        self.defrag_btn.setEnabled(True)

    def _refresh_cache(self):
        self.cache_stats.setText(self.fs.get_cache_stats())

    def _clear_cache(self):
        self.fs.clear_cache()
        self._refresh_cache()
        self.status_bar.showMessage("缓存已清空")

    def _refresh_sys(self):
        self.sys_info.setText(self.fs.get_system_info())

    def refresh_all(self):
        self.refresh_files()
        self.refresh_users()
        self._refresh_sys()
        self._refresh_cache()
        self._update_user_info()

    def refresh_files(self):
        if not self.fs.is_user_logged_in():
            self.file_table.setRowCount(0)
            self.path_display.setText("/")
            return
        self.path_display.setText(self.fs.cwd_path)
        entries = self.fs.ls()
        self.file_table.setRowCount(len(entries))
        for row, line in enumerate(entries):
            parts = line.split()
            if len(parts) >= 4:
                self.file_table.setItem(row, 0, QTableWidgetItem(parts[0]))
                self.file_table.setItem(row, 1, QTableWidgetItem(parts[1]))
                time_str = parts[2] + " " + parts[3]
                self.file_table.setItem(row, 2, QTableWidgetItem(time_str))
                name = " ".join(parts[4:]) if len(parts) > 4 else ""
                is_dir = name.endswith("/")
                if is_dir:
                    name = name[:-1]
                    ftype = "目录"
                else:
                    ftype = "文件"
                self.file_table.setItem(row, 3, QTableWidgetItem(name))
                self.file_table.setItem(row, 4, QTableWidgetItem(ftype))

    def refresh_users(self):
        self.user_list.clear()
        for u in self.fs.get_all_users():
            self.user_list.addItem(f"{u.username} (UID: {u.uid})")

    def _update_user_info(self):
        if self.fs.is_user_logged_in():
            user = self.fs.current_user
            self.user_info.setText(f"已登录: {user.username}")
            self.user_info.setStyleSheet("color: #a6e3a1;")
            self.uid_label.setText(str(user.uid))
            self.gid_label.setText(str(user.gid))
            self.home_label.setText(user.home)
        else:
            self.user_info.setText("未登录")
            self.user_info.setStyleSheet("color: #f9e2af;")
            self.uid_label.setText("-")
            self.gid_label.setText("-")
            self.home_label.setText("-")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
