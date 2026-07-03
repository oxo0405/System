#!/usr/bin/env python3
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from ai_service import get_ai_service


class Worker(QObject):
    finished = pyqtSignal(object)
    
    def __init__(self, func):
        super().__init__()
        self.func = func
    
    def run(self):
        result = self.func()
        self.finished.emit(result)


class AIFunctionInjector:
    
    @staticmethod
    def inject_to_main_window(main_window):
        main_window.ai_service = get_ai_service()
        
        main_window._ai_summary = lambda: AIFunctionInjector._ai_summary(main_window)
        main_window._ai_search = lambda: AIFunctionInjector._ai_search(main_window)
        
        AIFunctionInjector._add_ai_buttons(main_window)
        
        print("✅ AI功能注入成功")
    
    @staticmethod
    def _add_ai_buttons(self):
        file_tab = None
        central_widget = self.centralWidget()
        if central_widget:
            main_layout = central_widget.layout()
            if main_layout:
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if isinstance(widget, QTabWidget):
                            for j in range(widget.count()):
                                if widget.tabText(j) == "文件管理":
                                    file_tab = widget.widget(j)
                                    break
                            break
        
        if not file_tab:
            print("❌ 未找到文件管理tab")
            return
        
        file_layout = file_tab.layout()
        if not file_layout:
            print("❌ 未找到文件管理tab的布局")
            return
        
        btn_layout = None
        for i in range(file_layout.count()):
            item = file_layout.itemAt(i)
            if item:
                layout = item.layout()
                if layout and isinstance(layout, QHBoxLayout):
                    for j in range(layout.count()):
                        sub_item = layout.itemAt(j)
                        if sub_item:
                            widget = sub_item.widget()
                            if widget and isinstance(widget, QPushButton) and widget.text() == "属性":
                                btn_layout = layout
                                break
                    if btn_layout:
                        break
        
        if not btn_layout:
            print("❌ 未找到包含'属性'按钮的布局")
            return
        
        info_btn_index = -1
        for i in range(btn_layout.count()):
            item = btn_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and isinstance(widget, QPushButton) and widget.text() == "属性":
                    info_btn_index = i
                    break
        
        if info_btn_index < 0:
            print("❌ 未找到'属性'按钮")
            return
        
        sep = QWidget()
        sep.setFixedWidth(8)
        btn_layout.insertWidget(info_btn_index + 1, sep)
        
        ai_summary_btn = QPushButton("🤖 AI摘要")
        ai_summary_btn.setObjectName("primary")
        ai_summary_btn.setStyleSheet("""
            QPushButton#primary { 
                background: #cba6f7; 
                color: #1e1e2e; 
                font-weight: bold;
            }
            QPushButton#primary:hover { 
                background: #b4befe; 
            }
        """)
        ai_summary_btn.clicked.connect(self._ai_summary)
        btn_layout.insertWidget(info_btn_index + 2, ai_summary_btn)
        
        ai_search_btn = QPushButton("🔍 AI搜索")
        ai_search_btn.setObjectName("primary")
        ai_search_btn.setStyleSheet("""
            QPushButton#primary { 
                background: #f9e2af; 
                color: #1e1e2e;
                font-weight: bold;
            }
            QPushButton#primary:hover { 
                background: #fae4b0; 
            }
        """)
        ai_search_btn.clicked.connect(self._ai_search)
        btn_layout.insertWidget(info_btn_index + 3, ai_search_btn)
        
        print("✅ AI按钮添加成功")
    
    @staticmethod
    def _ai_summary(self):
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        
        if not self.ai_service.is_available():
            QMessageBox.warning(self, "API错误", 
                "AI服务未配置，请检查API密钥")
            return
        
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "错误", "请先选择文件")
            return
        
        name_item = self.file_table.item(row, 3)
        type_item = self.file_table.item(row, 4)
        if not name_item or type_item.text() == "目录":
            QMessageBox.warning(self, "错误", "请选择文件（不能是目录）")
            return
        
        name = name_item.text()
        path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
        
        fd = self.fs.open_file(path)
        if fd < 0:
            QMessageBox.warning(self, "错误", f"无法打开文件: {name}")
            return
        
        content = self.fs.read_file(fd)
        self.fs.close_file(fd)
        
        if not content or len(content.strip()) == 0:
            QMessageBox.warning(self, "提示", "文件内容为空，无法生成摘要")
            return
        
        progress = QProgressDialog("正在生成摘要，请稍候...", "取消", 0, 0, self)
        progress.setWindowTitle("AI摘要")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()
        
        def do_summary():
            try:
                summary = self.ai_service.generate_summary(content)
                return summary
            except Exception as e:
                return f"生成失败: {str(e)}"
        
        def show_result(summary):
            progress.close()
            msg = QMessageBox(self)
            msg.setWindowTitle(f"AI摘要 - {name}")
            msg.setIcon(QMessageBox.Information)
            msg.setText(f"📄 《{name}》的摘要：")
            msg.setDetailedText(summary)
            msg.setStyleSheet("""
                QMessageBox QTextEdit {
                    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                    font-size: 12px;
                    background: #0f0f1a;
                    color: #cdd6f4;
                }
            """)
            msg.exec_()
        
        thread = QThread()
        worker = Worker(do_summary)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(show_result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
    
    @staticmethod
    def _ai_search(self):
        if not self.fs.is_user_logged_in():
            QMessageBox.warning(self, "错误", "请先登录")
            return
        
        if not self.ai_service.is_available():
            QMessageBox.warning(self, "API错误", 
                "AI服务未配置，请检查API密钥")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 AI智能搜索")
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet("""
            QDialog { background: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QLineEdit { 
                background: #181825; 
                border: 1px solid #45475a; 
                border-radius: 4px; 
                padding: 6px;
                color: #cdd6f4;
            }
            QListWidget { 
                background: #181825; 
                border: 1px solid #45475a;
                color: #cdd6f4;
            }
            QTextEdit { 
                background: #181825; 
                border: 1px solid #45475a;
                color: #cdd6f4;
            }
            QComboBox {
                background: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px;
                color: #cdd6f4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("搜索:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入搜索关键词或描述...")
        input_layout.addWidget(search_input, 1)
        
        search_btn = QPushButton("🔍 搜索")
        search_btn.setObjectName("primary")
        search_btn.setStyleSheet("""
            QPushButton#primary { 
                background: #89b4fa; 
                color: #1e1e2e; 
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#primary:hover { 
                background: #74c7ec; 
            }
        """)
        input_layout.addWidget(search_btn)
        layout.addLayout(input_layout)
        
        scope_layout = QHBoxLayout()
        scope_layout.addWidget(QLabel("搜索范围:"))
        scope_combo = QComboBox()
        scope_combo.addItems(["当前目录", "所有文件"])
        scope_layout.addWidget(scope_combo)
        scope_layout.addStretch()
        layout.addLayout(scope_layout)
        
        layout.addWidget(QLabel("搜索结果:"))
        result_list = QListWidget()
        result_list.setStyleSheet("background: #0f0f1a;")
        layout.addWidget(result_list, 1)
        
        layout.addWidget(QLabel("详情:"))
        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setMaximumHeight(150)
        layout.addWidget(detail_text)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        def do_search():
            query = search_input.text().strip()
            if not query:
                QMessageBox.warning(dialog, "错误", "请输入搜索关键词")
                return
            
            scope = scope_combo.currentText()
            result_list.clear()
            detail_text.clear()
            
            files_content = []
            if scope == "当前目录":
                entries = self.fs.ls()
                for entry in entries:
                    parts = entry.split()
                    if len(parts) >= 5:
                        name = " ".join(parts[4:])
                        if name.endswith("/"):
                            continue
                        name = name.rstrip('/')
                        path = self.fs.cwd_path + "/" + name if self.fs.cwd_path != "/" else "/" + name
                        fd = self.fs.open_file(path)
                        if fd >= 0:
                            content = self.fs.read_file(fd)
                            self.fs.close_file(fd)
                            if content and len(content.strip()) > 0:
                                files_content.append((name, content))
            else:
                def walk_collect(fcb, base):
                    entries = self.fs._get_dir_entries(fcb)
                    for e in entries:
                        if e['type'] == 0:
                            path = base + '/' + e['name'] if base != '/' else '/' + e['name']
                            fd = self.fs.open_file(path)
                            if fd >= 0:
                                content = self.fs.read_file(fd)
                                self.fs.close_file(fd)
                                if content and len(content.strip()) > 0:
                                    files_content.append((e['name'], content))
                        else:
                            sub = self.fs._find_fcb(base + '/' + e['name'] if base != '/' else '/' + e['name'])
                            if sub:
                                walk_collect(sub, base + '/' + e['name'] if base != '/' else '/' + e['name'])
                walk_collect(self.fs.root, "")
            
            if not files_content:
                QMessageBox.warning(dialog, "提示", "没有可搜索的文件内容")
                return
            
            progress = QProgressDialog("正在搜索，请稍候...", "取消", 0, 0, dialog)
            progress.setWindowTitle("AI搜索")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            def do_search_work():
                try:
                    results = self.ai_service.smart_search(query, files_content)
                    return results
                except Exception as e:
                    return [("错误", f"搜索失败: {str(e)}", 0.0)]
            
            def show_results(results):
                progress.close()
                if not results:
                    result_list.addItem("没有找到相关结果")
                    return
                
                for name, snippet, score in results[:30]:
                    if len(snippet) > 150:
                        snippet = snippet[:150] + "..."
                    item_text = f"{name} (相关度: {score:.2f})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, (name, snippet))
                    result_list.addItem(item)
                
                if result_list.count() > 0:
                    result_list.setCurrentRow(0)
                    item = result_list.currentItem()
                    if item:
                        name, snippet = item.data(Qt.UserRole)
                        detail_text.setPlainText(f"文件: {name}\n\n相关片段:\n{snippet}")
            
            def on_item_clicked(item):
                if item:
                    name, snippet = item.data(Qt.UserRole)
                    detail_text.setPlainText(f"文件: {name}\n\n相关片段:\n{snippet}")
            
            result_list.itemClicked.connect(on_item_clicked)
            
            thread = QThread()
            worker = Worker(do_search_work)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(show_results)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.start()
        
        search_btn.clicked.connect(do_search)
        search_input.returnPressed.connect(do_search)
        
        dialog.exec_()
