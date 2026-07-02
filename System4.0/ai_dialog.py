#!/usr/bin/env python3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from ai_service import get_ai_service


class AIDialog(QDialog):
    
    def __init__(self, fs, parent=None):
        super().__init__(parent)
        self.fs = fs
        self.ai_service = get_ai_service()
        self.parent_window = parent
        self.init_ui()
        self.check_service_status()
    
    def init_ui(self):
        self.setWindowTitle("AI 智能助手")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("""
            QDialog { background: #1e1e2e; color: #cdd6f4; }
            QPushButton { background: #313244; border: none; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background: #45475a; }
            QPushButton#primary { background: #89b4fa; color: #1e1e2e; }
            QPushButton#primary:hover { background: #74c7ec; }
            QPushButton#success { background: #a6e3a1; color: #1e1e2e; }
            QPushButton#success:hover { background: #94e2d5; }
            QPushButton#danger { background: #f38ba8; color: #1e1e2e; }
            QPushButton#danger:hover { background: #eba0ac; }
            QLineEdit, QTextEdit, QListWidget { 
                background: #181825; 
                border: 1px solid #45475a; 
                border-radius: 4px; 
                padding: 6px;
                color: #cdd6f4;
            }
            QGroupBox { 
                border: 1px solid #45475a; 
                border-radius: 6px; 
                margin-top: 12px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 6px; 
                color: #89b4fa;
            }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; }
            QTabBar::tab { background: #313244; padding: 6px 14px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #45475a; }
            QStatusBar { background: #181825; color: #6c7086; }
            QLabel#status_label { color: #6c7086; }
            QLabel#success_label { color: #a6e3a1; }
            QLabel#error_label { color: #f38ba8; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("AI 智能助手")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        header.addWidget(title)
        header.addStretch()
        
        self.status_indicator = QLabel("检查中...")
        self.status_indicator.setObjectName("status_label")
        header.addWidget(self.status_indicator)
        main_layout.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(self._create_summary_tab(), "文件摘要")
        tabs.addTab(self._create_search_tab(), "智能检索")
        main_layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def _create_summary_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        select_layout = QHBoxLayout()
        self.summary_file_combo = QComboBox()
        self.summary_file_combo.setPlaceholderText("选择当前目录下的文件...")
        select_layout.addWidget(self.summary_file_combo, 1)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("primary")
        refresh_btn.clicked.connect(self._refresh_file_list)
        select_layout.addWidget(refresh_btn)
        layout.addLayout(select_layout)

        action_layout = QHBoxLayout()
        self.summary_btn = QPushButton("生成摘要")
        self.summary_btn.setObjectName("success")
        self.summary_btn.clicked.connect(self._generate_summary)
        action_layout.addWidget(self.summary_btn)
        
        self.summary_status = QLabel("就绪")
        self.summary_status.setObjectName("status_label")
        action_layout.addWidget(self.summary_status)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        self.summary_result = QTextEdit()
        self.summary_result.setPlaceholderText("点击「生成摘要」按钮，AI 将分析文件内容并生成摘要...")
        self.summary_result.setReadOnly(True)
        self.summary_result.setStyleSheet("font-family: 'Monospace'; font-size: 12px;")
        layout.addWidget(self.summary_result)

        info = QLabel("提示：AI 将分析文件内容，生成 50-100 字的简洁摘要")
        info.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(info)

        return tab

    def _create_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词，例如：密码、配置、函数名...")
        search_layout.addWidget(self.search_input, 1)
        
        self.search_btn = QPushButton("智能搜索")
        self.search_btn.setObjectName("primary")
        self.search_btn.clicked.connect(self._smart_search)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        scope_layout = QHBoxLayout()
        self.scope_label = QLabel("搜索范围：")
        self.scope_label.setStyleSheet("color: #6c7086;")
        scope_layout.addWidget(self.scope_label)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["当前目录", "当前目录及子目录", "整个文件系统"])
        scope_layout.addWidget(self.scope_combo)
        scope_layout.addStretch()
        layout.addLayout(scope_layout)

        self.search_status = QLabel("就绪")
        self.search_status.setObjectName("status_label")
        layout.addWidget(self.search_status)

        self.search_result = QTextEdit()
        self.search_result.setPlaceholderText("输入关键词后点击「智能搜索」，AI 将分析文件内容并返回相关结果...")
        self.search_result.setReadOnly(True)
        self.search_result.setStyleSheet("font-family: 'Monospace'; font-size: 12px;")
        layout.addWidget(self.search_result)

        info = QLabel("提示：AI 将分析文件内容的相关性，按相关性排序并给出匹配原因")
        info.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(info)

        return tab

    def check_service_status(self):
        if self.ai_service.is_available():
            self.status_indicator.setText("已连接 (Ollama)")
            self.status_indicator.setObjectName("success_label")
            self.status_indicator.setStyleSheet("color: #a6e3a1;")
        else:
            self.status_indicator.setText("未连接 (请启动 Ollama)")
            self.status_indicator.setObjectName("error_label")
            self.status_indicator.setStyleSheet("color: #f38ba8;")
            QMessageBox.warning(self, "服务未连接", 
                "无法连接到 Ollama 服务！\n\n"
                "请确保：\n"
                "1. 已安装 Ollama\n"
                "2. 已运行 'ollama serve'\n"
                "3. 已下载模型 'ollama pull qwen2:0.5b'")
        
        self._refresh_file_list()

    def _refresh_file_list(self):
        self.summary_file_combo.clear()
        self.summary_file_combo.addItem("-- 请选择文件 --")
        
        if not self.fs or not self.fs.is_user_logged_in():
            return
        
        entries = self.fs.ls()
        for line in entries:
            parts = line.split()
            if len(parts) >= 5:
                name = " ".join(parts[4:])
                if not name.endswith('/'):
                    self.summary_file_combo.addItem(name)

    def _get_file_content(self, filename):
        if not filename or filename == "-- 请选择文件 --":
            return None
        
        path = self.fs.cwd_path + "/" + filename if self.fs.cwd_path != "/" else "/" + filename
        fd = self.fs.open_file(path)
        if fd >= 0:
            content = self.fs.read_file(fd)
            self.fs.close_file(fd)
            return content
        return None

    def _generate_summary(self):
        filename = self.summary_file_combo.currentText()
        if not filename or filename == "-- 请选择文件 --":
            QMessageBox.warning(self, "错误", "请先选择一个文件")
            return
        
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        
        if not self.ai_service.is_available():
            QMessageBox.warning(self, "错误", "AI 服务未连接，请检查 Ollama")
            return
        
        self.summary_btn.setEnabled(False)
        self.summary_status.setText("正在生成摘要...")
        self.summary_status.setObjectName("status_label")
        QApplication.processEvents()
        
        try:
            content = self._get_file_content(filename)
            if content is None:
                QMessageBox.warning(self, "错误", "无法读取文件: " + filename)
                return
            
            success, result = self.ai_service.generate_summary(content, filename)
            
            if success:
                self.summary_result.setText(result)
                self.summary_status.setText("摘要生成完成")
                self.summary_status.setObjectName("success_label")
            else:
                self.summary_result.setText("生成失败\n\n错误信息：" + result)
                self.summary_status.setText("生成失败")
                self.summary_status.setObjectName("error_label")
                
        except Exception as e:
            self.summary_result.setText("发生错误\n\n" + str(e))
            self.summary_status.setText("错误")
            self.summary_status.setObjectName("error_label")
        finally:
            self.summary_btn.setEnabled(True)

    def _smart_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "错误", "请输入搜索关键词")
            return
        
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        
        if not self.ai_service.is_available():
            QMessageBox.warning(self, "错误", "AI 服务未连接，请检查 Ollama")
            return
        
        self.search_btn.setEnabled(False)
        self.search_status.setText("正在搜索...")
        self.search_status.setObjectName("status_label")
        QApplication.processEvents()
        
        try:
            files = self._collect_files(query)
            
            if not files:
                self.search_result.setText("未找到任何文件可搜索")
                self.search_status.setText("无文件")
                return
            
            success, result = self.ai_service.smart_search(query, files)
            
            if success:
                self.search_result.setText(result)
                self.search_status.setText("搜索完成")
                self.search_status.setObjectName("success_label")
            else:
                self.search_result.setText("搜索失败\n\n错误信息：" + result)
                self.search_status.setText("搜索失败")
                self.search_status.setObjectName("error_label")
                
        except Exception as e:
            self.search_result.setText("发生错误\n\n" + str(e))
            self.search_status.setText("错误")
            self.search_status.setObjectName("error_label")
        finally:
            self.search_btn.setEnabled(True)

    def _collect_files(self, query=""):
        files = []
        scope = self.scope_combo.currentText()
        
        def walk_dir(path):
            try:
                entries = self.fs.list_directory(path)
                for line in entries:
                    parts = line.split()
                    if len(parts) >= 5:
                        name = " ".join(parts[4:])
                        is_dir = name.endswith('/')
                        if is_dir:
                            if scope != "当前目录":
                                sub_path = path + "/" + name[:-1] if path != "/" else "/" + name[:-1]
                                walk_dir(sub_path)
                        else:
                            content = self._get_file_content(name)
                            if content:
                                files.append((name, content))
            except:
                pass
        
        if scope == "当前目录":
            entries = self.fs.ls()
            for line in entries:
                parts = line.split()
                if len(parts) >= 5:
                    name = " ".join(parts[4:])
                    if not name.endswith('/'):
                        content = self._get_file_content(name)
                        if content:
                            files.append((name, content))
        else:
            walk_dir(self.fs.cwd_path)
        
        return files[:20]
