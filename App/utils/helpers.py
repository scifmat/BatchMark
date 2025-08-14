"""
工具函数模块
提供通用的辅助函数
"""

import os
import json
from pathlib import Path
from typing import Any, Dict
from App.models.config import WatermarkConfig, OutputConfig, Template

class Helpers:
    """通用工具类"""
    
    @staticmethod
    def get_config_dir() -> str:
        """获取配置目录路径"""
        try:
            import appdirs
            return appdirs.user_config_dir("BatchMark")
        except ImportError:
            # 备用方案
            return os.path.join(os.path.expanduser("~"), ".BatchMark")
    
    @staticmethod
    def ensure_config_dir() -> str:
        """确保配置目录存在"""
        config_dir = Helpers.get_config_dir()
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @staticmethod
    def save_template(template: Template) -> bool:
        """保存模板配置"""
        try:
            config_dir = Helpers.ensure_config_dir()
            template_file = os.path.join(config_dir, f"{template.name}.json")
            
            template_data = {
                "name": template.name,
                "watermark_config": {
                    "text": template.watermark_config.text,
                    "font_family": template.watermark_config.font_family,
                    "font_size": template.watermark_config.font_size,
                    "color": template.watermark_config.color,
                    "opacity": template.watermark_config.opacity,
                    "count": template.watermark_config.count,
                    "rotation": template.watermark_config.rotation
                },
                "output_config": {
                    "output_dir": template.output_config.output_dir,
                    "output_format": template.output_config.output_format,
                    "jpg_quality": template.output_config.jpg_quality,
                    "name_rule": template.output_config.name_rule,
                    "suffix": template.output_config.suffix
                }
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False
    
    @staticmethod
    def load_template(name: str) -> Template:
        """加载模板配置"""
        try:
            config_dir = Helpers.get_config_dir()
            template_file = os.path.join(config_dir, f"{name}.json")
            
            if not os.path.exists(template_file):
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            watermark_config = WatermarkConfig(**data["watermark_config"])
            output_config = OutputConfig(**data["output_config"])
            
            return Template(name=data["name"], 
                          watermark_config=watermark_config, 
                          output_config=output_config)
            
        except Exception as e:
            print(f"加载模板失败: {e}")
            return None
    
    @staticmethod
    def list_templates() -> list:
        """获取所有模板列表"""
        try:
            config_dir = Helpers.get_config_dir()
            templates = []
            
            if os.path.exists(config_dir):
                for file in os.listdir(config_dir):
                    if file.endswith('.json'):
                        template_name = Path(file).stem
                        template = Helpers.load_template(template_name)
                        if template:
                            templates.append(template)
            
            return templates
            
        except Exception as e:
            print(f"获取模板列表失败: {e}")
            return []
    
    @staticmethod
    def delete_template(name: str) -> bool:
        """删除模板"""
        try:
            config_dir = Helpers.get_config_dir()
            template_file = os.path.join(config_dir, f"{name}.json")
            
            if os.path.exists(template_file):
                os.remove(template_file)
                return True
            
            return False
            
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False
    
    @staticmethod
    def get_default_fonts() -> list:
        """获取系统可用字体列表"""
        fonts = []
        
        # Windows系统字体
        if os.name == 'nt':
            font_dirs = [
                "C:/Windows/Fonts",
                os.path.expanduser("~\AppData\Local\Microsoft\Windows\Fonts")
            ]
            
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for file in os.listdir(font_dir):
                        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                            font_name = Path(file).stem
                            fonts.append(font_name)
        
        # 添加通用字体
        common_fonts = ["Arial", "Microsoft YaHei", "SimSun", "SimHei", "KaiTi"]
        fonts.extend(common_fonts)
        
        # 去重并排序
        return sorted(list(set(fonts)))
    
    @staticmethod
    def is_valid_color(color: str) -> bool:
        """验证颜色格式"""
        if not color:
            return False
        
        color = color.lstrip('#')
        if len(color) != 6:
            return False
        
        try:
            int(color, 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_color_from_rgb(r: int, g: int, b: int) -> str:
        """从RGB值获取十六进制颜色"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def get_rgb_from_color(color: str) -> tuple:
        """从十六进制颜色获取RGB值"""
        color = color.lstrip('#')
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    @staticmethod
    def create_backup(original_path: str) -> str:
        """创建备份文件"""
        try:
            backup_dir = os.path.join(os.path.dirname(original_path), 'backup')
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            
            filename = Path(original_path).name
            backup_path = os.path.join(backup_dir, f"{filename}.backup")
            
            import shutil
            shutil.copy2(original_path, backup_path)
            return backup_path
            
        except Exception as e:
            print(f"创建备份失败: {e}")
            return ""
    
    @staticmethod
    def get_system_info() -> dict:
        """获取系统信息"""
        import platform
        
        return {
            "os": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "processor": platform.processor()
        }