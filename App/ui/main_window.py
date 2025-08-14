"""
主窗口UI
"""

import os
from typing import List
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QSlider,
                             QComboBox, QFileDialog, QProgressBar,
                             QTextEdit, QGroupBox, QGridLayout, QSplitter,
                             QMessageBox, QApplication, QColorDialog, QLineEdit, QSizePolicy,
                             QCheckBox, QDoubleSpinBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, QEvent
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDragEnterEvent, QDropEvent, QColor, QFontMetrics

from App.models.config import WatermarkConfig, OutputConfig
from App.services.batch_service import BatchService, ProcessingResult
from App.services.file_service import FileService
from App.utils.helpers import Helpers

class ProcessingWorker(QObject):
    """处理工作线程"""
    progress_updated = pyqtSignal(int, int, str)
    processing_finished = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.image_files = []
        self.watermark_config = None
        self.output_config = None

    def set_params(self, image_files: List[str], watermark_config, output_config):
        """设置处理参数"""
        self.image_files = image_files
        self.watermark_config = watermark_config
        self.output_config = output_config

    def process(self):
        """开始处理"""
        from App.services.batch_service import BatchService
        service = BatchService()

        def progress_callback(current, total, message):
            self.progress_updated.emit(current, total, message)

        def completion_callback(results):
            self.processing_finished.emit(results)

        service.process_batch(
            self.image_files,
            self.watermark_config,
            self.output_config,
            progress_callback,
            completion_callback
        )

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.watermark_config = WatermarkConfig()
        self.output_config = OutputConfig()
        self.image_files = []
        self.current_preview_index = 0
        self.batch_service = BatchService()

        self.init_ui()
        self.setup_connections()
        self.setWindowTitle("BatchMark - 批量图片水印工具")
        self.setGeometry(100, 100, 1200, 800)

        # 启用拖放
        self.setAcceptDrops(True)

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧预览区域
        self.preview_widget = self.create_preview_panel()
        splitter.addWidget(self.preview_widget)

        # 右侧设置面板
        self.settings_widget = self.create_settings_panel()
        splitter.addWidget(self.settings_widget)

        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def create_preview_panel(self):
        """创建预览面板"""
        panel = QGroupBox("图片预览")
        layout = QVBoxLayout()

        # 图片显示区域
        self.image_label = QLabel("拖拽图片到此处或点击选择")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f9f9f9;
                color: #666;
            }
        """)

        # 导航控制区域
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("← 上一张")
        self.prev_btn.setEnabled(False)
        self.prev_btn.setFixedHeight(30)

        self.image_index_label = QLabel("0/0")
        self.image_index_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("下一张 →")
        self.next_btn.setEnabled(False)
        self.next_btn.setFixedHeight(30)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_index_label)
        nav_layout.addWidget(self.next_btn)

        # 选择图片按钮
        self.select_images_btn = QPushButton("选择图片")
        self.select_images_btn.setFixedHeight(35)

        layout.addWidget(self.image_label)
        layout.addLayout(nav_layout)
        layout.addWidget(self.select_images_btn)
        panel.setLayout(layout)
        return panel

    def create_settings_panel(self):
        """创建设置面板"""
        panel = QGroupBox("水印设置")
        layout = QVBoxLayout()

        # 水印文本（紧凑布局）
        text_group = QGroupBox("水印文本")
        text_group.setStyleSheet("""
            QGroupBox { border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 12px; }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; /* 与默认一致，避免缩进差异 */
                padding: 2px 6px 0 6px;       /* 上方留出2px避免裁切 */
            }
        """)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(8, 6, 8, 6)
        text_layout.setSpacing(4)
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(56)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.text_edit.setPlainText(self.watermark_config.text)
        text_layout.addWidget(self.text_edit)
        text_group.setLayout(text_layout)

        # 字体设置
        font_group = QGroupBox("字体设置")
        font_layout = QGridLayout()

        # 字体大小
        font_layout.addWidget(QLabel("字体大小:"), 0, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 200)
        self.font_size_spin.setValue(self.watermark_config.font_size)
        font_layout.addWidget(self.font_size_spin, 0, 1)
        # 自适应字体选项
        self.adaptive_checkbox = QCheckBox("自适应字体")
        self.adaptive_checkbox.setChecked(getattr(self.watermark_config, 'adaptive_font', True))
        font_layout.addWidget(self.adaptive_checkbox, 0, 2)

        font_layout.addWidget(QLabel("自适应比例:"), 1, 2)
        self.font_ratio_spin = QDoubleSpinBox()
        self.font_ratio_spin.setRange(0.01, 0.20)
        self.font_ratio_spin.setSingleStep(0.005)
        self.font_ratio_spin.setDecimals(3)
        self.font_ratio_spin.setValue(getattr(self.watermark_config, 'font_ratio', 0.04))
        font_layout.addWidget(self.font_ratio_spin, 1, 3)

        # 手动字体大小在自适应启用时置灰
        self.font_size_spin.setEnabled(not self.adaptive_checkbox.isChecked())
        self.font_ratio_spin.setEnabled(self.adaptive_checkbox.isChecked())


        # 水印数量
        font_layout.addWidget(QLabel("水印数量:"), 1, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(self.watermark_config.count)
        font_layout.addWidget(self.count_spin, 1, 1)

        # 旋转角度
        font_layout.addWidget(QLabel("旋转角度:"), 2, 0)
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(0, 360)
        self.rotation_spin.setValue(45)  # 默认45度
        font_layout.addWidget(self.rotation_spin, 2, 1)

        # 文字颜色
        font_layout.addWidget(QLabel("文字颜色:"), 3, 0)
        self.color_btn = QPushButton("选择颜色")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.watermark_config.color}; border: 1px solid #ccc; border-radius: 3px;")  # 默认随配置显示红色
        color_select_layout = QHBoxLayout()
        color_select_layout.addWidget(self.color_btn)
        color_select_layout.addWidget(self.color_preview)
        color_select_layout.addStretch()
        font_layout.addLayout(color_select_layout, 3, 1)

        font_group.setLayout(font_layout)

        # 透明度设置
        opacity_group = QGroupBox("透明度")
        opacity_layout = QVBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(self.watermark_config.opacity)
        self.opacity_label = QLabel(f"{self.watermark_config.opacity}%")
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        opacity_group.setLayout(opacity_layout)

        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()

        # 输出目录
        self.output_dir_btn = QPushButton("选择输出目录")
        self.output_dir_field = QLineEdit()
        self.output_dir_field.setReadOnly(True)
        self.output_dir_field.setPlaceholderText("未选择")
        # 关键：Ignored 避免根据内容撑开父布局宽度
        self.output_dir_field.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.output_dir_field.setFixedHeight(26)
        self.output_dir_field.setStyleSheet("QLineEdit { color: #555; padding: 4px; }")

        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPG", "PNG"])
        format_layout.addWidget(self.format_combo)

        # JPG质量
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("JPG质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(50, 100)
        self.quality_spin.setValue(self.output_config.jpg_quality)
        quality_layout.addWidget(self.quality_spin)

        # 输出目录行：按钮 + 自动换行的路径标签
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.output_dir_btn)
        dir_row.addWidget(self.output_dir_field, 1)
        output_layout.addLayout(dir_row)
        output_layout.addLayout(format_layout)
        output_layout.addLayout(quality_layout)
        output_group.setLayout(output_layout)

        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.setFixedHeight(40)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # 添加到布局（按钮固定在底部：先添加弹性空间，再放按钮）
        layout.addWidget(text_group)
        layout.addWidget(font_group)
        layout.addWidget(opacity_group)
        layout.addWidget(output_group)
        # 先添加可伸缩空间，把后续控件推到底部
        layout.addStretch()
        # 在按钮上方增加间距（8-12px），这里取10px
        layout.addSpacing(10)
        # 将处理按钮放在面板底部
        layout.addWidget(self.process_btn)
        layout.addWidget(self.progress_bar)

        panel.setLayout(layout)
        return panel

    def setup_connections(self):
        """设置信号连接"""
        # 图片选择
        self.select_images_btn.clicked.connect(self.select_images)

        # 导航控制
        self.prev_btn.clicked.connect(self.show_previous_image)
        self.next_btn.clicked.connect(self.show_next_image)

        # 输出目录
        self.output_dir_btn.clicked.connect(self.select_output_dir)

        # 水印设置
        self.text_edit.textChanged.connect(self.update_watermark_config)
        self.font_size_spin.valueChanged.connect(self.update_watermark_config)
        self.count_spin.valueChanged.connect(self.update_watermark_config)
        self.rotation_spin.valueChanged.connect(self.update_watermark_config)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_slider.valueChanged.connect(self.update_watermark_config)
        # 自适应相关
        if hasattr(self, 'adaptive_checkbox'):
            self.adaptive_checkbox.toggled.connect(self.on_adaptive_toggled)
        if hasattr(self, 'font_ratio_spin'):
            self.font_ratio_spin.valueChanged.connect(self.update_watermark_config)
        # 颜色选择
        if hasattr(self, 'color_btn'):
            self.color_btn.clicked.connect(self.choose_color)

        # 输出设置
        self.format_combo.currentTextChanged.connect(self.update_output_config)
        self.quality_spin.valueChanged.connect(self.update_output_config)

        # 处理按钮
        self.process_btn.clicked.connect(self.start_processing)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                from pathlib import Path
                ext = Path(file_path).suffix.lower()
                if ext in FileService.SUPPORTED_FORMATS:
                    files.append(file_path)
            elif os.path.isdir(file_path):
                files.extend(FileService.get_supported_images(file_path))

        if files:
            self.image_files = files
            self.update_image_count()
            self.show_preview()

    def select_images(self):
        """选择图片"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp)"
        )

        if files:
            self.image_files = files
            self.update_image_count()
            self.show_preview()

    def select_output_dir(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_config.output_dir = directory
            if hasattr(self, 'output_dir_field'):
                self.output_dir_field.setText(directory)

    def update_image_count(self):
        """更新图片数量显示"""
        total = len(self.image_files)
        if total > 0:
            self.current_preview_index = 0
            self.image_index_label.setText(f"1/{total}")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(total > 1)
            self.show_preview()
        else:
            self.image_label.setText("拖拽图片到此处或点击选择")
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #aaa;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                    color: #666;
                }
            """)
            self.image_index_label.setText("0/0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)

    def show_preview(self):
        """显示预览"""
        if self.image_files and 0 <= self.current_preview_index < len(self.image_files):
            try:
                # 获取当前图片路径
                current_image = self.image_files[self.current_preview_index]

                # 获取带水印的预览图
                preview_image = self.batch_service.get_preview(
                    current_image,
                    self.watermark_config
                )

                if preview_image:
                    # 将PIL Image转换为QPixmap
                    try:
                        from PIL import Image
                        from PyQt5.QtGui import QImage, QPixmap

                        # 将PIL图像转换为QImage
                        image = preview_image.convert('RGBA')
                        data = image.tobytes('raw', 'RGBA')
                        qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
                        pixmap = QPixmap.fromImage(qimage)

                        if not pixmap.isNull():
                            # 获取标签的可用大小
                            label_size = self.image_label.size()

                            # 计算保持宽高比的缩放尺寸
                            scaled_pixmap = pixmap.scaled(
                                label_size.width() - 20,  # 留出边距
                                label_size.height() - 20,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )

                            # 创建一个透明背景的pixmap来居中显示
                            final_pixmap = QPixmap(label_size.width(), label_size.height())
                            final_pixmap.fill(Qt.transparent)

                            # 计算居中位置
                            painter = None
                            try:
                                from PyQt5.QtGui import QPainter
                                painter = QPainter(final_pixmap)
                                x = (label_size.width() - scaled_pixmap.width()) // 2
                                y = (label_size.height() - scaled_pixmap.height()) // 2
                                painter.drawPixmap(x, y, scaled_pixmap)
                            finally:
                                if painter:
                                    painter.end()

                            self.image_label.setPixmap(final_pixmap)
                            self.image_label.setAlignment(Qt.AlignCenter)
                            self.image_label.setStyleSheet("")
                        else:
                            self.image_label.setText("无法生成预览")
                            self.image_label.setPixmap(QPixmap())
                    except Exception as e:
                        print(f"转换图片失败: {e}")
                        self.image_label.setText("图片转换失败")
                        self.image_label.setPixmap(QPixmap())
                else:
                    # 如果无法生成水印预览，显示原图
                    pixmap = QPixmap(current_image)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.image_label.size().width() - 4,
                            self.image_label.size().height() - 4,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.image_label.setPixmap(scaled_pixmap)
                        self.image_label.setStyleSheet("")
                    else:
                        self.image_label.setText("无法加载图片")
                        self.image_label.setPixmap(QPixmap())

            except Exception as e:
                print(f"预览生成失败: {e}")
                # 显示原图作为后备
                try:
                    current_image = self.image_files[self.current_preview_index]
                    pixmap = QPixmap(current_image)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.image_label.size().width() - 4,
                            self.image_label.size().height() - 4,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.image_label.setPixmap(scaled_pixmap)
                        self.image_label.setStyleSheet("")
                    else:
                        self.image_label.setText("无法加载图片")
                        self.image_label.setPixmap(QPixmap())
                except:
                    self.image_label.setText("预览生成失败")
                    self.image_label.setPixmap(QPixmap())

    def show_previous_image(self):
        """显示上一张图片"""
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            self.update_navigation_controls()
            self.show_preview()

    def show_next_image(self):
        """显示下一张图片"""
        if self.current_preview_index < len(self.image_files) - 1:
            self.current_preview_index += 1
            self.update_navigation_controls()
            self.show_preview()

    def update_navigation_controls(self):
        """更新导航控制状态"""
        total = len(self.image_files)
        if total > 0:
            current = self.current_preview_index + 1
            self.image_index_label.setText(f"{current}/{total}")
            self.prev_btn.setEnabled(self.current_preview_index > 0)
            self.next_btn.setEnabled(self.current_preview_index < total - 1)
    def choose_color(self):
        """选择水印颜色"""
        try:
            from PyQt5.QtGui import QColor
            initial = QColor(self.watermark_config.color)
            color = QColorDialog.getColor(initial, self, "选择文字颜色", QColorDialog.ShowAlphaChannel)
            if color.isValid():
                hex_color = color.name(QColor.HexRgb)
                self.watermark_config.color = hex_color
                if hasattr(self, 'color_preview'):
                    self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #ccc; border-radius: 3px;")
                self.show_preview()
        except Exception as e:
            print(f"选择颜色失败: {e}")
    def on_adaptive_toggled(self, checked: bool):
        """切换自适应/手动模式时，更新控件可用状态并刷新预览"""
        # 控件可用性切换
        if hasattr(self, 'font_size_spin'):
            self.font_size_spin.setEnabled(not checked)
        if hasattr(self, 'font_ratio_spin'):
            self.font_ratio_spin.setEnabled(checked)
        # 写入配置
        self.watermark_config.adaptive_font = bool(checked)
        # 自适应时把比例也写回配置
        if checked and hasattr(self, 'font_ratio_spin'):
            self.watermark_config.font_ratio = float(self.font_ratio_spin.value())
        # 刷新预览
        self.show_preview()


    def update_opacity_label(self):
        """更新透明度标签"""
        value = self.opacity_slider.value()
        self.opacity_label.setText(f"{value}%")

    def update_watermark_config(self):
        """更新水印配置"""
        self.watermark_config.text = self.text_edit.toPlainText()
        # 模式切换：自适应 vs 手动
        if hasattr(self, 'adaptive_checkbox') and self.adaptive_checkbox.isChecked():
            self.watermark_config.adaptive_font = True
            if hasattr(self, 'font_ratio_spin'):
                self.watermark_config.font_ratio = float(self.font_ratio_spin.value())
        else:
            self.watermark_config.adaptive_font = False
            self.watermark_config.font_size = self.font_size_spin.value()
        self.watermark_config.count = self.count_spin.value()
        self.watermark_config.rotation = self.rotation_spin.value()
        self.watermark_config.opacity = self.opacity_slider.value()

        # 更新预览
        self.show_preview()

    def update_output_config(self):
        """更新输出配置"""
        self.output_config.output_format = self.format_combo.currentText().lower()
        self.output_config.jpg_quality = self.quality_spin.value()

    def start_processing(self):
        """开始处理"""
        if not self.image_files:
            QMessageBox.warning(self, "警告", "请先选择图片文件")
            return

        if not self.output_config.output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return

        if not self.watermark_config.text.strip():
            QMessageBox.warning(self, "警告", "请输入水印文本")
            return

        # 验证输出目录
        valid, message = FileService.validate_output_directory(self.output_config.output_dir)
        if not valid:
            QMessageBox.warning(self, "警告", f"输出目录无效: {message}")
            return

        # 检查磁盘空间
        space_info = self.batch_service.get_disk_space_info(
            self.output_config.output_dir,
            self.image_files,
            self.output_config
        )

        if not space_info['sufficient_space']:
            reply = QMessageBox.question(
                self, "磁盘空间警告",
                f"可用空间可能不足\n"
                f"估计需要: {space_info['estimated_size_human']}\n"
                f"可用空间: {space_info['available_space_human']}\n"
                f"是否继续？"
            )
            if reply != QMessageBox.Yes:
                return

        # 进入处理流程
        self._begin_processing()

    def _create_progress_dialog(self, total: int):
        dlg = QDialog(self)
        dlg.setWindowTitle("正在处理...")
        v = QVBoxLayout(dlg)
        self._progress_label = QLabel("准备开始...")
        self._progress_count = QLabel(f"0/{total}")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, total)
        v.addWidget(self._progress_label)
        v.addWidget(self._progress_count)
        v.addWidget(self._progress_bar)
        dlg.setModal(True)
        dlg.setFixedWidth(420)
        self._progress_dlg = dlg

    def _close_progress_dialog(self):
        if hasattr(self, '_progress_dlg') and self._progress_dlg is not None:
            self._progress_dlg.close()
            self._progress_dlg = None
            self._progress_label = None
            self._progress_count = None
            self._progress_bar = None

    def _begin_processing(self):
        """弹窗并启动处理线程"""
        self.process_btn.setEnabled(False)
        total_files = len(self.image_files)
        try:
            self._create_progress_dialog(total_files)
            if hasattr(self, '_progress_dlg') and self._progress_dlg:
                self._progress_dlg.show()
        except Exception as e:
            print(f"创建进度弹窗失败: {e}")

        # 创建工作线程
        self.worker = ProcessingWorker()
        self.worker.set_params(self.image_files, self.watermark_config, self.output_config)

        self.worker.progress_updated.connect(self.update_progress)
        self.worker.processing_finished.connect(self.processing_complete)

        # 启动线程
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.process)
        self.thread.start()

    def update_progress(self, current: int, total: int, message: str):
        """更新进度（弹窗显示）"""
        if hasattr(self, '_progress_bar') and self._progress_bar:
            self._progress_bar.setValue(current)
        if hasattr(self, '_progress_count') and self._progress_count:
            self._progress_count.setText(f"{current}/{total}")
        if hasattr(self, '_progress_label') and self._progress_label:
            self._progress_label.setText(message)

    def processing_complete(self, results: List[ProcessingResult]):
        """处理完成"""
        self.process_btn.setEnabled(True)
        # 关闭弹窗
        try:
            self._close_progress_dialog()
        except Exception as e:
            print(f"关闭进度弹窗失败: {e}")

        # 统计结果
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)

        if success_count == total_count:
            QMessageBox.information(
                self, "完成",
                f"处理完成！\n成功处理了 {success_count} 张图片"
            )
        else:
            QMessageBox.warning(
                self, "完成但有错误",
                f"处理了 {total_count} 张图片\n"
                f"成功: {success_count} 张\n"
                f"失败: {total_count - success_count} 张"
            )

        # 处理完成后清空左侧预览
        self.image_files = []
        self.current_preview_index = 0
        self.image_label.setText("拖拽图片到此处或点击选择")
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f9f9f9;
                color: #666;
            }
        """)
        self.image_index_label.setText("0/0")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # 打开输出目录
        if self.output_config.output_dir and os.path.exists(self.output_config.output_dir):
            os.startfile(self.output_config.output_dir)

        # 清理线程
        self.thread.quit()
        self.thread.wait()

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 重新显示当前图片以适应新的大小
        self.show_preview()

    def closeEvent(self, event):
        """关闭事件"""
        # 保存当前配置
        config_dir = Helpers.ensure_config_dir()
        config_file = os.path.join(config_dir, "last_config.json")

        try:
            import json
            config_data = {
                "watermark_config": {
                    "text": self.watermark_config.text,
                    "font_size": self.watermark_config.font_size,
                    "count": self.watermark_config.count,
                    "rotation": self.watermark_config.rotation,
                    "opacity": self.watermark_config.opacity,
                    "color": self.watermark_config.color
                },
                "output_config": {
                    "output_dir": self.output_config.output_dir,
                    "format": self.output_config.format,
                    "jpg_quality": self.output_config.jpg_quality
                }
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存配置失败: {e}")

        event.accept()