"""
数据模型 - 配置相关
"""

from dataclasses import dataclass
from typing import Optional
from PyQt5.QtGui import QColor, QFont

@dataclass
class WatermarkConfig:
    """水印配置"""
    text: str = "公司水印"
    font_family: str = "Microsoft YaHei"
    font_size: int = 36
    adaptive_font: bool = True  # 是否启用自适应字体大小
    font_ratio: float = 0.04    # 自适应字体比例，建议 0.03-0.05
    color: str = "#FF0000"  # 十六进制颜色
    opacity: int = 70  # 0-100
    count: int = 1  # 水印数量
    rotation: int = 45  # 0-360度

@dataclass
class OutputConfig:
    """输出配置"""
    output_dir: str = ""
    output_format: str = "JPG"  # JPG或PNG
    jpg_quality: int = 90  # 50-100
    name_rule: str = "suffix"  # keep或suffix
    suffix: str = "_watermarked"

@dataclass
class Template:
    """模板配置"""
    name: str
    watermark_config: WatermarkConfig
    output_config: OutputConfig