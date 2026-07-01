#!/usr/bin/env python3
import json
import os
import requests
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, prompt, model="qwen2:0.5b", timeout=120):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.is_running = True
        self.timeout = timeout
        
    def stop(self):
        self.is_running = False
        
    def run(self):
        try:
            self.progress.emit("正在连接AI服务...")
            
            if not self._check_ollama():
                self.error.emit("Ollama服务未启动，请在终端运行: ollama serve")
                return
            
            payload = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 512
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=self.timeout
            )
            
            if not self.is_running:
                return
                
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    content = result['response'].strip()
                    content = self._clean_output(content)
                    self.finished.emit(content)
                else:
                    self.error.emit("AI返回格式异常")
            else:
                self.error.emit(f"AI服务错误 ({response.status_code}): {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            self.error.emit("无法连接到Ollama服务\n请确保Ollama正在运行:\n  ollama serve")
        except requests.exceptions.Timeout:
            self.error.emit(f"请求超时（{self.timeout}秒），请检查网络或模型是否已下载")
        except Exception as e:
            self.error.emit(f"AI处理错误: {str(e)}")
    
    def _check_ollama(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if not any(self.model in name for name in model_names):
                    self.progress.emit(f"模型 {self.model} 未安装，正在尝试使用默认模型...")
                    if model_names:
                        self.model = model_names[0]
                        self.progress.emit(f"使用模型: {self.model}")
                        return True
                    return False
                return True
        except:
            return False
        return True
    
    def _clean_output(self, text):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)


class AIAssistant:
    
    def __init__(self, model="qwen2:0.5b"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self._available_models = []
        self._check_ollama()
        
    def _check_ollama(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                self._available_models = [m.get('name', '') for m in models]
                if self._available_models:
                    if not any(self.model in name for name in self._available_models):
                        self.model = self._available_models[0]
                    return True
        except:
            pass
        return False
    
    def get_status(self):
        if self._check_ollama():
            if self._available_models:
                return True, f"✅ {self.model} (可用)"
            return False, "⚠️ 无可用模型，请运行: ollama pull qwen2:0.5b"
        return False, "❌ Ollama服务未启动\n请运行: ollama serve"
    
    def get_available_models(self):
        self._check_ollama()
        return self._available_models
    
    def set_model(self, model):
        if model in self._available_models:
            self.model = model
            return True
        return False
    
    def generate_summary(self, content, filename="文件"):
        if not content or len(content.strip()) < 10:
            return "内容过短，无法生成摘要（至少需要10个字符）"
        
        max_len = 2000
        if len(content) > max_len:
            content = content[:max_len] + "\n... (内容已截断)"
        
        prompt = f"""请为以下文件生成简洁的中文摘要（50-100字）：

文件名: {filename}

文件内容:
{content}

要求：
1. 提取核心主题和关键信息
2. 用简洁的语言概括
3. 如果内容涉及代码，说明其功能
4. 只输出摘要内容，不要添加额外说明

摘要:"""
        
        return self._call_ollama(prompt)
    
    def intelligent_search(self, query, file_contents):
        if not query or not query.strip():
            return "请输入搜索关键词"
        
        if not file_contents:
            return "没有可搜索的文件内容"
        
        file_list = []
        total_len = 0
        for name, content in file_contents.items():
            if content and len(content.strip()) > 0:
                if len(content) > 300:
                    content = content[:300] + "..."
                file_list.append(f"【{name}】\n{content}")
                total_len += len(content)
                if total_len > 3000:
                    break
        
        if not file_list:
            return "所有文件内容为空，无法搜索"
        
        prompt = f"""请在以下文件内容中搜索与「{query}」相关的内容：

{chr(10).join(file_list)}

要求：
1. 找出与查询最相关的文件
2. 说明找到了什么相关内容
3. 按相关度从高到低排列
4. 只输出搜索结果，不要额外说明

搜索结果:"""
        
        return self._call_ollama(prompt)
    
    def code_explain(self, code_content, filename="代码文件"):
        if not code_content or len(code_content.strip()) < 10:
            return "代码内容过短"
        
        if len(code_content) > 2000:
            code_content = code_content[:2000] + "\n... (已截断)"
        
        prompt = f"""请解释以下代码的功能：

文件名: {filename}

代码:
{code_content}

要求：
1. 说明代码的主要功能
2. 指出关键函数或类的作用
3. 用中文回答，简洁明了
4. 只输出解释内容

解释:"""
        
        return self._call_ollama(prompt)
    
    def _call_ollama(self, prompt):
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "num_predict": 512
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    return self._clean_output(result['response'])
                return str(result)
            else:
                return f"API错误: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "⚠️ 无法连接到Ollama服务\n请确保已启动: ollama serve"
        except requests.exceptions.Timeout:
            return "⚠️ 请求超时，请检查网络或模型是否下载完成"
        except Exception as e:
            return f"⚠️ 错误: {str(e)}"
    
    def _clean_output(self, text):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)


class AIWindow(QMainWindow):
    
    def __init__(self, fs=None):
        super().__init__()
        self.fs = fs
        self.ai = AIAssistant()
        self.current_files = {}
        self.worker = None
        
        self.init_ui()
        self.check_ai_status()
        self.sync_files()
        
    def init_ui(self):
        self.setWindowTitle("🤖 AI智能助手 - 文件摘要与检索")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; }
            QPushButton { background: #313244; border: none; border-radius: 6px; padding: 8px 16px; font-size: 13px; }
            QPushButton:hover { background: #45475a; }
            QPushButton:pressed { background: #585b70; }
            QPushButton#primary { background: #89b4fa; color: #1e1e2e; }
            QPushButton#primary:hover { background: #74c7ec; }
            QPushButton#success { background: #a6e3a1; color: #1e1e2e; }
            QPushButton#success:hover { background: #94e2d5; }
            QPushButton#danger { background: #f38ba8; color: #1e1e2e; }
            QPushButton#danger:hover { background: #eba0ac; }
            QLineEdit, QTextEdit { background: #181825; border: 1px solid #45475a; border-radius: 4px; padding: 6px; font-size: 13px; }
            QComboBox { background: #181825; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; }
            QComboBox:hover { border-color: #89b4fa; }
            QComboBox::drop-down { border: none; }
            QGroupBox { border: 1px solid #45475a; border-radius: 8px; margin-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px; color: #89b4fa; font-weight: bold; }
            QProgressBar { background: #313244; border-radius: 4px; text-align: center; color: #cdd6f4; }
            QProgressBar::chunk { background: #89b4fa; border-radius: 4px; }
            QStatusBar { background: #181825; color: #6c7086; }
            QSplitter::handle { background: #45475a; }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; }
            QTabBar::tab { background: #313244; padding: 6px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #45475a; }
            QLabel#status_ok { color: #a6e3a1; }
            QLabel#status_error { color: #f38ba8; }
            QLabel#status_warn { color: #f9e2af; }
            QScrollBar:vertical { background: #181825; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #585b70; }
            QScrollBar:horizontal { background: #181825; height: 10px; border-radius: 5px; }
            QScrollBar::handle:horizontal { background: #45475a; border-radius: 5px; min-width: 20px; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        
        status_frame = QFrame()
        status_frame.setStyleSheet("background: #313244; border-radius: 8px; padding: 8px 12px;")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 4, 8, 4)
        
        status_layout.addWidget(QLabel("🤖 AI服务:"))
        self.ai_status_label = QLabel("检查中...")
        self.ai_status_label.setObjectName("status_warn")
        status_layout.addWidget(self.ai_status_label)
        
        status_layout.addStretch()
        
        status_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.setMaximumWidth(200)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        status_layout.addWidget(self.model_combo)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.check_ai_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_frame)
        
        tabs = QTabWidget()
        
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        summary_group = QGroupBox("📄 文件摘要生成")
        summary_layout = QVBoxLayout(summary_group)
        
        file_select_layout = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.setPlaceholderText("选择文件...")
        file_select_layout.addWidget(self.file_combo, 1)
        
        self.summary_btn = QPushButton("生成摘要")
        self.summary_btn.setObjectName("primary")
        self.summary_btn.clicked.connect(self.generate_summary)
        file_select_layout.addWidget(self.summary_btn)
        summary_layout.addLayout(file_select_layout)
        
        self.summary_output = QTextEdit()
        self.summary_output.setPlaceholderText("点击「生成摘要」获取AI分析...")
        self.summary_output.setMaximumHeight(180)
        summary_layout.addWidget(self.summary_output)
        
        left_layout.addWidget(summary_group, 1)
        
        search_group = QGroupBox("🔍 智能检索")
        search_layout = QVBoxLayout(search_group)
        
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.returnPressed.connect(self.intelligent_search)
        search_input_layout.addWidget(self.search_input, 1)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("success")
        self.search_btn.clicked.connect(self.intelligent_search)
        search_input_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_input_layout)
        
        self.search_output = QTextEdit()
        self.search_output.setPlaceholderText("输入关键词后点击「搜索」...")
        search_layout.addWidget(self.search_output)
        
        left_layout.addWidget(search_group, 2)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_group = QGroupBox("📝 文件内容预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_combo = QComboBox()
        self.preview_combo.currentTextChanged.connect(self.load_preview)
        preview_layout.addWidget(self.preview_combo)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("选择文件查看内容...")
        preview_layout.addWidget(self.preview_text)
        
        right_layout.addWidget(preview_group)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([550, 400])
        tab1_layout.addWidget(splitter)
        tabs.addTab(tab1, "摘要与检索")
        
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        code_group = QGroupBox("💻 代码解释器")
        code_layout = QVBoxLayout(code_group)
        
        code_select_layout = QHBoxLayout()
        self.code_combo = QComboBox()
        self.code_combo.setPlaceholderText("选择代码文件...")
        code_select_layout.addWidget(self.code_combo, 1)
        
        self.explain_btn = QPushButton("解释代码")
        self.explain_btn.setObjectName("primary")
        self.explain_btn.clicked.connect(self.explain_code)
        code_select_layout.addWidget(self.explain_btn)
        code_layout.addLayout(code_select_layout)
        
        self.code_output = QTextEdit()
        self.code_output.setPlaceholderText("选择代码文件后点击「解释代码」...")
        code_layout.addWidget(self.code_output)
        tabs.addTab(tab2, "代码解释")
        
        layout.addWidget(tabs, 1)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximum(0)
        layout.addWidget(self.progress)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.sync_files)
        self.refresh_timer.start(5000)
    
    def check_ai_status(self):
        ok, msg = self.ai.get_status()
        
        models = self.ai.get_available_models()
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        if self.ai.model in models:
            self.model_combo.setCurrentText(self.ai.model)
        
        if ok:
            self.ai_status_label.setText(f"✅ {self.ai.model}")
            self.ai_status_label.setObjectName("status_ok")
            self.status_bar.showMessage("AI服务就绪")
        else:
            self.ai_status_label.setText(f"❌ {msg}")
            self.ai_status_label.setObjectName("status_error")
            self.status_bar.showMessage("⚠️ AI服务不可用")
        self.ai_status_label.setStyleSheet("")
    
    def on_model_changed(self, model):
        if model and self.ai.set_model(model):
            self.check_ai_status()
    
    def sync_files(self):
        if not self.fs:
            return
            
        try:
            if not self.fs.is_user_logged_in():
                return
                
            entries = self.fs.ls()
            files = []
            for entry in entries:
                parts = entry.split()
                if len(parts) >= 5:
                    name = " ".join(parts[4:])
                    if name.endswith("/"):
                        continue
                    files.append(name)
            
            current = self.file_combo.currentText()
            
            self.file_combo.clear()
            self.preview_combo.clear()
            self.code_combo.clear()
            
            for f in sorted(files):
                self.file_combo.addItem(f)
                self.preview_combo.addItem(f)
                self.code_combo.addItem(f)
            
            if current in files:
                self.file_combo.setCurrentText(current)
                self.preview_combo.setCurrentText(current)
                self.code_combo.setCurrentText(current)
                
        except Exception as e:
            pass
    
    def load_preview(self, filename):
        if not filename or not self.fs:
            return
            
        try:
            if not self.fs.is_user_logged_in():
                self.preview_text.setText("请先登录")
                return
                
            path = self.fs.cwd_path + "/" + filename if self.fs.cwd_path != "/" else "/" + filename
            fd = self.fs.open_file(path)
            if fd >= 0:
                content = self.fs.read_file(fd)
                self.fs.close_file(fd)
                self.preview_text.setText(content)
                self.current_files[filename] = content
            else:
                self.preview_text.setText("无法打开文件")
        except Exception as e:
            self.preview_text.setText(f"加载失败: {str(e)}")
    
    def get_file_content(self, filename):
        if filename in self.current_files:
            return self.current_files[filename]
        
        if not self.fs:
            return None
            
        try:
            if not self.fs.is_user_logged_in():
                return None
                
            path = self.fs.cwd_path + "/" + filename if self.fs.cwd_path != "/" else "/" + filename
            fd = self.fs.open_file(path)
            if fd >= 0:
                content = self.fs.read_file(fd)
                self.fs.close_file(fd)
                self.current_files[filename] = content
                return content
        except:
            pass
        return None
    
    def generate_summary(self):
        filename = self.file_combo.currentText()
        if not filename:
            QMessageBox.warning(self, "错误", "请先选择一个文件")
            return
        
        content = self.get_file_content(filename)
        if content is None:
            QMessageBox.warning(self, "错误", "无法读取文件内容")
            return
        
        if not content or len(content.strip()) < 5:
            QMessageBox.warning(self, "提示", "文件内容为空或过短")
            return
        
        self.summary_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.summary_output.setText("⏳ 正在生成摘要...")
        self.status_bar.showMessage("正在调用AI生成摘要...")
        
        self.worker = AIWorker(
            self.ai.generate_summary(content, filename),
            self.ai.model
        )
        self.worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
        self.worker.finished.connect(self.on_summary_complete)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def on_summary_complete(self, result):
        self.summary_output.setText(result)
        self.summary_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status_bar.showMessage("摘要生成完成")
        self.worker = None
    
    def intelligent_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "错误", "请输入搜索关键词")
            return
        
        if not self.current_files:
            QMessageBox.warning(self, "提示", "没有可搜索的文件，请先在预览中打开文件")
            return
        
        self.search_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.search_output.setText("⏳ 正在搜索...")
        self.status_bar.showMessage("正在调用AI进行智能检索...")
        
        file_dict = {k: v for k, v in self.current_files.items() if v and len(v.strip()) > 0}
        
        self.worker = AIWorker(
            self.ai.intelligent_search(query, file_dict),
            self.ai.model
        )
        self.worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
        self.worker.finished.connect(self.on_search_complete)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def on_search_complete(self, result):
        self.search_output.setText(result)
        self.search_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status_bar.showMessage("搜索完成")
        self.worker = None
    
    def explain_code(self):
        filename = self.code_combo.currentText()
        if not filename:
            QMessageBox.warning(self, "错误", "请先选择一个代码文件")
            return
        
        content = self.get_file_content(filename)
        if content is None:
            QMessageBox.warning(self, "错误", "无法读取文件内容")
            return
        
        if not content or len(content.strip()) < 10:
            QMessageBox.warning(self, "提示", "代码内容过短")
            return
        
        self.explain_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.code_output.setText("⏳ 正在分析代码...")
        self.status_bar.showMessage("正在调用AI解释代码...")
        
        self.worker = AIWorker(
            self.ai.code_explain(content, filename),
            self.ai.model
        )
        self.worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
        self.worker.finished.connect(self.on_explain_complete)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def on_explain_complete(self, result):
        self.code_output.setText(result)
        self.explain_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status_bar.showMessage("代码解释完成")
        self.worker = None
    
    def on_ai_error(self, error_msg):
        self.summary_output.setText(f"⚠️ {error_msg}")
        self.search_output.setText(f"⚠️ {error_msg}")
        self.code_output.setText(f"⚠️ {error_msg}")
        self.summary_btn.setEnabled(True)
        self.search_btn.setEnabled(True)
        self.explain_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status_bar.showMessage("AI处理失败")
        self.worker = None
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()


def create_ai_window(fs=None):
    return AIWindow(fs)


def add_ai_button_to_main_window(main_window):
    if hasattr(main_window, '_ai_tab_added'):
        return
    
    tabs = None
    for child in main_window.centralWidget().children():
        if isinstance(child, QTabWidget):
            tabs = child
            break
    
    if not tabs:
        return
    
    ai_tab = QWidget()
    ai_layout = QVBoxLayout(ai_tab)
    
    btn_frame = QFrame()
    btn_frame.setStyleSheet("""
        QFrame {
            background: #313244;
            border-radius: 12px;
            padding: 30px;
        }
    """)
    btn_layout = QVBoxLayout(btn_frame)
    btn_layout.setAlignment(Qt.AlignCenter)
    
    open_ai_btn = QPushButton("🤖 打开AI智能助手")
    open_ai_btn.setObjectName("primary")
    open_ai_btn.setStyleSheet("""
        QPushButton#primary {
            font-size: 20px;
            font-weight: bold;
            padding: 20px 40px;
            border-radius: 12px;
            background: #89b4fa;
            color: #1e1e2e;
        }
        QPushButton#primary:hover {
            background: #74c7ec;
            transform: scale(1.02);
        }
    """)
    open_ai_btn.clicked.connect(lambda: show_ai_window(main_window))
    btn_layout.addWidget(open_ai_btn)
    
    desc_label = QLabel("使用AI大模型进行文件摘要生成、智能检索和代码解释")
    desc_label.setStyleSheet("color: #a6adc8; font-size: 14px; margin-top: 10px;")
    desc_label.setAlignment(Qt.AlignCenter)
    btn_layout.addWidget(desc_label)
    
    status_layout = QHBoxLayout()
    status_layout.setAlignment(Qt.AlignCenter)
    status_dot = QLabel("●")
    status_dot.setStyleSheet("color: #f9e2af; font-size: 14px;")
    status_text = QLabel("检查AI服务状态...")
    status_text.setStyleSheet("color: #6c7086; font-size: 12px;")
    status_layout.addWidget(status_dot)
    status_layout.addWidget(status_text)
    btn_layout.addLayout(status_layout)
    
    ai_layout.addWidget(btn_frame)
    ai_layout.addStretch()
    
    tabs.addTab(ai_tab, "🤖 AI助手")
    
    main_window._ai_tab_added = True
    main_window._ai_tab_index = tabs.count() - 1
    main_window._ai_status_dot = status_dot
    main_window._ai_status_text = status_text
    
    def update_ai_status():
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                main_window._ai_status_dot.setStyleSheet("color: #a6e3a1; font-size: 14px;")
                main_window._ai_status_text.setText("AI服务就绪 ✅")
                main_window._ai_status_text.setStyleSheet("color: #a6e3a1; font-size: 12px;")
            else:
                main_window._ai_status_dot.setStyleSheet("color: #f38ba8; font-size: 14px;")
                main_window._ai_status_text.setText("AI服务异常 ⚠️")
                main_window._ai_status_text.setStyleSheet("color: #f38ba8; font-size: 12px;")
        except:
            main_window._ai_status_dot.setStyleSheet("color: #f38ba8; font-size: 14px;")
            main_window._ai_status_text.setText("AI服务未启动 ❌")
            main_window._ai_status_text.setStyleSheet("color: #f38ba8; font-size: 12px;")
    
    QTimer.singleShot(500, update_ai_status)
    
    status_timer = QTimer(main_window)
    status_timer.timeout.connect(update_ai_status)
    status_timer.start(10000)
    main_window._ai_status_timer = status_timer


def show_ai_window(parent):
    try:
        if hasattr(parent, '_ai_window') and parent._ai_window is not None:
            parent._ai_window.raise_()
            parent._ai_window.activateWindow()
            return parent._ai_window
        
        fs = parent.fs if hasattr(parent, 'fs') else None
        ai_window = AIWindow(fs)
        ai_window.show()
        parent._ai_window = ai_window
        
        ai_window.destroyed.connect(lambda: setattr(parent, '_ai_window', None))
        
        return ai_window
    except Exception as e:
        QMessageBox.warning(parent, "错误", f"打开AI助手失败: {str(e)}")
        return None


def refresh_ai_files(main_window):
    if hasattr(main_window, '_ai_window') and main_window._ai_window:
        main_window._ai_window.sync_files()


if __name__ == "__main__":
    import sys
    from file_system import FileSystem
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    fs = FileSystem()
    fs.login_user("admin", "admin123")
    
    from main_window import MainWindow
    win = MainWindow()
    add_ai_button_to_main_window(win)
    win.show()
    
    sys.exit(app.exec_())
