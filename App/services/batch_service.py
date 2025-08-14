"""
批量处理服务
协调水印引擎和文件服务进行批量图片处理
"""

import os
import threading
from typing import List, Callable, Optional
from dataclasses import dataclass
from App.models.config import WatermarkConfig, OutputConfig
from App.core.watermark_engine import WatermarkEngine
from App.services.file_service import FileService

@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    input_path: str
    output_path: str
    error_message: str = ""
    file_size: str = ""

class BatchService:
    """批量处理服务"""
    
    def __init__(self):
        self.engine = WatermarkEngine()
        self.file_service = FileService()
        self.is_running = False
        self.current_progress = 0
        self.total_files = 0
        self.cancel_requested = False
        
    def process_batch(self, image_files: List[str], 
                     watermark_config: WatermarkConfig,
                     output_config: OutputConfig,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None,
                     completion_callback: Optional[Callable[[List[ProcessingResult]], None]] = None) -> None:
        """批量处理图片"""
        
        def process_thread():
            self.is_running = True
            self.current_progress = 0
            self.total_files = len(image_files)
            self.cancel_requested = False
            
            results = []
            
            try:
                for i, image_path in enumerate(image_files):
                    if self.cancel_requested:
                        break
                    
                    self.current_progress = i + 1
                    
                    # 更新进度
                    if progress_callback:
                        progress_callback(i + 1, self.total_files, f"处理中: {os.path.basename(image_path)}")
                    
                    # 生成输出路径
                    output_path = self.file_service.generate_output_path(
                        image_path, output_config, i, self.total_files
                    )
                    
                    # 处理图片
                    success = self.engine.add_watermark(image_path, watermark_config, output_path)
                    
                    # 获取文件大小
                    file_size = self.file_service.get_file_size(output_path) if success else ""
                    
                    # 记录结果
                    result = ProcessingResult(
                        success=success,
                        input_path=image_path,
                        output_path=output_path,
                        error_message="" if success else "处理失败",
                        file_size=file_size
                    )
                    results.append(result)
                    
            except Exception as e:
                # 处理过程中的异常
                for i, image_path in enumerate(image_files[len(results):]):
                    results.append(ProcessingResult(
                        success=False,
                        input_path=image_path,
                        output_path="",
                        error_message=str(e)
                    ))
            
            finally:
                self.is_running = False
                if completion_callback:
                    completion_callback(results)
        
        # 启动处理线程
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
    
    def cancel_processing(self):
        """取消处理"""
        self.cancel_requested = True
    
    def get_preview(self, image_path: str, watermark_config: WatermarkConfig) -> Optional:
        """获取预览图"""
        return self.engine.preview_watermark(image_path, watermark_config)
    
    def validate_files(self, image_files: List[str]) -> List[str]:
        """验证图片文件"""
        valid_files = []
        for file_path in image_files:
            if self.file_service.validate_image(file_path):
                valid_files.append(file_path)
        return valid_files
    
    def estimate_processing_time(self, image_files: List[str]) -> int:
        """估算处理时间（秒）"""
        # 基于图片数量和大小的简单估算
        total_size = 0
        for file_path in image_files:
            try:
                total_size += os.path.getsize(file_path)
            except Exception:
                continue
        
        # 假设平均1MB需要1秒
        estimated_seconds = max(1, total_size // (1024 * 1024))
        
        # 添加基础处理时间
        estimated_seconds += len(image_files) * 2
        
        return estimated_seconds
    
    def get_processing_status(self) -> dict:
        """获取当前处理状态"""
        return {
            'is_running': self.is_running,
            'current_progress': self.current_progress,
            'total_files': self.total_files,
            'cancel_requested': self.cancel_requested
        }
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        temp_dir = os.path.join(os.getcwd(), 'temp')
        self.file_service.cleanup_temp_files(temp_dir)
    
    def get_disk_space_info(self, output_dir: str, image_files: List[str], 
                          output_config: OutputConfig) -> dict:
        """获取磁盘空间信息"""
        estimated_size = self.file_service.estimate_output_size(image_files, output_config)
        available_space = self.file_service.get_available_space(output_dir)
        
        return {
            'estimated_output_size': estimated_size,
            'available_space': available_space,
            'sufficient_space': available_space > estimated_size,
            'estimated_size_human': self._format_size(estimated_size),
            'available_space_human': self._format_size(available_space)
        }
    
    def _format_size(self, bytes_size: int) -> str:
        """格式化文件大小"""
        return self.file_service.get_file_size(str(bytes_size))