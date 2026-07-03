#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from ai_integration import AIFunctionInjector

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    AIFunctionInjector.inject_to_main_window(win)
    win.show()
    sys.exit(app.exec_())
