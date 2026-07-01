#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from ai_assistant import add_ai_button_to_main_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    add_ai_button_to_main_window(win)
    win.show()
    sys.exit(app.exec_())
