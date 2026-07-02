# ai_integration.py - AI界面集成（新建文件）
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class AIIntegration:
    def __init__(self, main_window, ai_service):
        self.main = main_window
        self.ai = ai_service
        self._connect_signals()
        self._add_ai_buttons()
    
    def _connect_signals(self):
        self.ai.summary_ready.connect(self._on_summary)
        self.ai.search_ready.connect(self._on_search)
        self.ai.status_update.connect(self.main.status_bar.showMessage)
        self.ai.error_occurred.connect(lambda e: QMessageBox.warning(self.main, "AI错误", e))
    
    def _add_ai_buttons(self):
        tab = self.main.centralWidget().layout().itemAt(1).widget()
        for i in range(tab.count()):
            if tab.tabText(i) == "文件管理":
                file_tab = tab.widget(i)
                for j in range(file_tab.layout().count()):
                    item = file_tab.layout().itemAt(j)
                    if item and isinstance(item.layout(), QHBoxLayout):
                        btn_layout = item.layout()
                        self.summary_btn = QPushButton("🤖 AI摘要")
                        self.summary_btn.setObjectName("primary")
                        self.summary_btn.clicked.connect(self._do_summary)
                        btn_layout.insertWidget(btn_layout.count() - 2, self.summary_btn)
                        self.search_btn = QPushButton("🔍 AI检索")
                        self.search_btn.setObjectName("primary")
                        self.search_btn.clicked.connect(self._do_search)
                        btn_layout.insertWidget(btn_layout.count() - 2, self.search_btn)
                        break
                for j in range(file_tab.layout().count()):
                    item = file_tab.layout().itemAt(j)
                    if item and isinstance(item.widget(), QGroupBox) and "文件查看器" in item.widget().title():
                        viewer = item.widget()
                        self.ai_label = QLabel("🤖 AI摘要: 点击「AI摘要」生成")
                        self.ai_label.setStyleSheet("color: #a6e3a1; background: #181825; padding: 8px; border-radius: 4px;")
                        self.ai_label.setWordWrap(True)
                        self.ai_label.setMaximumHeight(80)
                        viewer.layout().insertWidget(0, self.ai_label)
                        break
                break
    
    def _get_file_table(self):
        tab = self.main.centralWidget().layout().itemAt(1).widget()
        for i in range(tab.count()):
            if tab.tabText(i) == "文件管理":
                for j in range(tab.widget(i).layout().count()):
                    item = tab.widget(i).layout().itemAt(j)
                    if item and isinstance(item.widget(), QTableWidget):
                        return item.widget()
        return None
    
    def _get_file_path_and_content(self):
        table = self._get_file_table()
        if not table or table.currentRow() < 0:
            QMessageBox.warning(self.main, "提示", "请先选择一个文件")
            return None, None
        
        name_item = table.item(table.currentRow(), 3)
        type_item = table.item(table.currentRow(), 4)
        if not name_item or type_item.text() == "目录":
            QMessageBox.warning(self.main, "提示", "请选择文件（非目录）")
            return None, None
        
        file_name = name_item.text()
        file_path = self.main.fs.cwd_path + "/" + file_name if self.main.fs.cwd_path != "/" else "/" + file_name
        
        fd = self.main.fs.open_file(file_path)
        if fd < 0:
            QMessageBox.warning(self.main, "错误", "无法打开文件")
            return None, None
        content = self.main.fs.read_file(fd)
        self.main.fs.close_file(fd)
        return file_name, content
    
    def _do_summary(self):
        file_name, content = self._get_file_path_and_content()
        if not file_name or not content:
            return
        self.ai_label.setText("🤖 正在生成摘要...")
        self.ai_label.setStyleSheet("color: #f9e2af; background: #181825; padding: 8px; border-radius: 4px;")
        self.ai.generate_summary(file_name, content)
    
    def _do_search(self):
        query, ok = QInputDialog.getText(self.main, "AI智能检索", "请输入搜索描述：")
        if not ok or not query.strip():
            return
        
        file_contents = {}
        def walk(fcb, base):
            entries = self.main.fs._get_dir_entries(fcb)
            for e in entries:
                if e['type'] == 0:
                    path = base + '/' + e['name'] if base != '/' else '/' + e['name']
                    target = self.main.fs._find_fcb(path)
                    if target and target.content:
                        file_contents[path] = target.content[:1000]
                elif e['type'] == 1:
                    walk(e, base + '/' + e['name'] if base != '/' else '/' + e['name'])
        walk(self.main.fs.root, "")
        
        if not file_contents:
            QMessageBox.warning(self.main, "提示", "没有可检索的文件")
            return
        
        self.main.status_bar.showMessage("正在执行AI智能检索...")
        self.ai.smart_search(query.strip(), file_contents)
    
    def _on_summary(self, file_path, summary):
        self.ai_label.setText(f"🤖 AI摘要 ({file_path}):\n{summary[:200]}{'...' if len(summary) > 200 else ''}")
        self.ai_label.setStyleSheet("color: #a6e3a1; background: #181825; padding: 8px; border-radius: 4px;")
    
    def _on_search(self, query, results):
        if not results:
            QMessageBox.information(self.main, "AI检索", f"未找到与「{query}」相关的文件")
            return
        dialog = QDialog(self.main)
        dialog.setWindowTitle("AI检索结果")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("background: #0f0f1a; font-family: 'Monospace'; font-size: 12px;")
        result_text = f"🔍 检索: 「{query}」\n\n"
        for i, r in enumerate(results, 1):
            result_text += f"{i}. 📄 {r.get('file', '未知')}\n   💡 {r.get('reason', '相关')}\n\n"
        text.setText(result_text)
        layout.addWidget(text)
        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn, alignment=Qt.AlignRight)
        dialog.exec_()
