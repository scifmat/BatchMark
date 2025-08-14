"""
文件处理服务
负责批量处理图片文件的导入、导出和命名
"""

import os
import uuid
from pathlib import Path
from typing import List, Tuple
from PIL import Image
from App.models.config import OutputConfig

class FileService:
    """文件处理服务"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    @staticmethod
    def get_supported_images(directory: str) -> List[str]:
        """获取目录下所有支持的图片文件"""
        image_files = []
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    ext = Path(file).suffix.lower()
                    if ext in FileService.SUPPORTED_FORMATS:
                        image_files.append(file_path)
        return sorted(image_files)
    
    @staticmethod
    def validate_image(file_path: str) -> bool:
        """验证图片文件是否有效"""
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_image_info(file_path: str) -> Tuple[int, int, str]:
        """获取图片信息（宽度、高度、格式）"""
        try:
            with Image.open(file_path) as img:
                return img.width, img.height, img.format
        except Exception as e:
            print(f"获取图片信息失败: {e}")
            return 0, 0, "Unknown"
    
    @staticmethod
    def generate_output_path(input_path: str, output_config: OutputConfig, 
                           index: int = 0, total: int = 1) -> str:
        """生成输出文件路径"""
        input_file = Path(input_path)
        
        # 确定输出目录
        if output_config.output_dir:
            output_dir = Path(output_config.output_dir)
        else:
            output_dir = input_file.parent / "watermarked"
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取原始文件名（不含扩展名）
        original_name = input_file.stem
        
        # 根据命名规则生成新文件名
        if output_config.name_rule == "original":
            new_name = original_name
        elif output_config.name_rule == "numbered":
            new_name = f"{original_name}_{index+1:03d}"
        elif output_config.name_rule == "timestamp":
            timestamp = str(uuid.uuid4())[:8]
            new_name = f"{original_name}_{timestamp}"
        else:
            new_name = original_name
        
        # 添加后缀
        if output_config.suffix:
            new_name = f"{new_name}_{output_config.suffix}"
        
        # 确定扩展名
        if output_config.output_format == "keep_original":
            extension = input_file.suffix.lower()
        else:
            extension = f".{output_config.output_format.lower()}"
        
        return str(output_dir / f"{new_name}{extension}")
    
    @staticmethod
    def get_file_size(file_path: str) -> str:
        """获取文件大小（人类可读格式）"""
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except Exception:
            return "Unknown"
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str):
        """清理临时文件"""
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    @staticmethod
    def get_available_space(directory: str) -> int:
        """获取目录可用空间（字节）"""
        try:
            stat = os.statvfs(directory) if hasattr(os, 'statvfs') else None
            if stat:
                return stat.f_bavail * stat.f_frsize
            else:
                # Windows系统
                import shutil
                total, used, free = shutil.disk_usage(directory)
                return free
        except Exception:
            return 0
    
    @staticmethod
    def estimate_output_size(input_files: List[str], output_config: OutputConfig) -> int:
        """估算输出文件总大小"""
        total_input_size = 0
        for file in input_files:
            try:
                total_input_size += os.path.getsize(file)
            except Exception:
                continue
        
        # 考虑压缩率和格式转换的影响
        compression_factor = 1.0
        if output_config.output_format.lower() == "jpg":
            compression_factor = 0.8 * (output_config.jpg_quality / 100.0)
        elif output_config.output_format.lower() == "png":
            compression_factor = 1.2
        
        return int(total_input_size * compression_factor)
    
    @staticmethod
    def validate_output_directory(directory: str) -> Tuple[bool, str]:
        """验证输出目录"""
        try:
            path = Path(directory)
            if path.exists() and path.is_file():
                return False, "指定路径是文件而非目录"
            
            # 尝试创建目录
            path.mkdir(parents=True, exist_ok=True)
            
            # 检查写入权限
            test_file = path / ".test_write"
            test_file.touch()
            test_file.unlink()
            
            return True, "目录有效"
            
        except PermissionError:
            return False, "没有写入权限"
        except Exception as e:
            return False, f"目录验证失败: {str(e)}"