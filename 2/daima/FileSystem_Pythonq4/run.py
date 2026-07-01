#!/usr/bin/env python3
# run.py - 启动脚本
import sys
import os

def main():
    print("=" * 70)
    print("  操作系统实验八 - 增强型文件管理系统")
    print("  实现人: XXX (学号: XXXXXXXXXX)")
    print("=" * 70)
    print()
    print("  独创性优化:")
    print("    1. 增强型磁盘碎片整理算法 (加权碎片评分)")
    print("    2. 高效边缘缓存系统 (LRU淘汰 + 脏页回写)")
    print()
    print("  默认账号: admin / admin123")
    print("  默认账号: guest / guest123")
    print("=" * 70)
    print()
    
    # 导入并运行GUI
    try:
        from main_window import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保 main_window.py 和 file_system.py 在同一目录下")

if __name__ == "__main__":
    main()
