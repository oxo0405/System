#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from ai_service import AIService
from ai_integration import AIIntegration

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    API_KEY="sk-psppfclovqencgwdhvsfsyabncmtvnobfqlrwgoezgfxpwsb"

    if API_KEY and API_KEY != "your-api-key-here":
        ai_service = AIService(api_key=API_KEY)
        ai_integration = AIIntegration(win, ai_service)
        win.status_bar.showMessage("🤖 AI功能已加载")
    else:
        win.status_bar.showMessage("⚠️ 未配置AI API密钥，AI功能不可用")
        print("提示: 请在run.py中设置API_KEY变量")

    sys.exit(app.exec_())
