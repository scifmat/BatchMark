#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BatchMark - 批量图片文字水印工具
主程序入口
"""

import sys
import os

# 添加App目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'App'))

from PyQt5.QtWidgets import QApplication
from App.ui.main_window import MainWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("BatchMark")
    app.setApplicationVersion("1.0.0")

    # 设置应用样式
    app.setStyle('Fusion')
    # 设置应用图标（兼容 PyInstaller onefile）
    try:
        from PyQt5.QtGui import QIcon
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
        icon_path_ico = os.path.join(base_dir, 'App', 'static', 'imges', 'app.ico')
        icon_path_png = os.path.join(base_dir, 'App', 'static', 'imges', 'app.png')
        if os.path.exists(icon_path_ico):
            app.setWindowIcon(QIcon(icon_path_ico))
        elif os.path.exists(icon_path_png):
            app.setWindowIcon(QIcon(icon_path_png))
    except Exception as e:
        # 设置图标失败不影响应用启动
        print(f"设置应用图标失败: {e}")


    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())