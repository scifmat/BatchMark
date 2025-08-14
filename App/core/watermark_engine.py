"""
水印处理引擎
负责图像处理和添加水印的核心功能
"""

from PIL import Image, ImageDraw, ImageFont
import math
from typing import Tuple, List
from App.models.config import WatermarkConfig

class WatermarkEngine:
    """水印处理引擎"""

    def __init__(self):
        self.font_cache = {}

    # 自适应参数（可按需在此调整默认值）
    FONT_RATIO: float = 0.04          # 建议 0.03 - 0.05
    MIN_FONT_SIZE: int = 12
    MAX_FONT_SIZE: int = 200
    MARGIN_RATIO: float = 0.10        # 边距占图片对应边长比例

    def _compute_effective_font_size(self, img_w: int, img_h: int, cfg: WatermarkConfig) -> int:
        """根据图片尺寸和默认比例，计算自适应字体大小；
        若未启用自适应，则按照用户手动设置（并做安全上下限裁剪）。"""
        if hasattr(cfg, 'adaptive_font') and not cfg.adaptive_font:
            return max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, int(getattr(cfg, 'font_size', self.MIN_FONT_SIZE))))
        min_side = max(1, min(img_w, img_h))
        ratio = getattr(cfg, 'font_ratio', None) or self.FONT_RATIO
        size = int(min_side * ratio)
        size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))
        return size

    def _determine_grid(self, count: int, img_w: int, img_h: int) -> Tuple[int, int]:
        """根据图片长宽比为多水印选择合适的行列数（rows, cols）。"""
        if count <= 1:
            return (1, 1)
        target = (img_w / img_h) if img_h else 1.0
        best = None
        for cols in range(1, count + 1):
            rows = math.ceil(count / cols)
            grid_ratio = cols / rows
            score = abs(grid_ratio - target)
            area_over = cols * rows - count
            # 先最小化纵横比分差，其次尽量不浪费单元（面积超出）
            key = (score, area_over)
            if best is None or key < best[0]:
                best = (key, (rows, cols))
        return best[1]

    def get_font(self, font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
        """获取字体对象，带缓存"""
        cache_key = (font_family, font_size)
        if cache_key not in self.font_cache:
            try:
                # Windows系统常用中文字体
                if font_family == "Microsoft YaHei":
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                else:
                    font_path = "C:/Windows/Fonts/arial.ttf"

                self.font_cache[cache_key] = ImageFont.truetype(font_path, font_size)
            except Exception:
                # 使用默认字体
                self.font_cache[cache_key] = ImageFont.load_default()

        return self.font_cache[cache_key]

    def calculate_positions(self, image_width: int, image_height: int,
                           count: int, text_width: int, text_height: int) -> List[Tuple[int, int]]:
        """计算水印位置，自适应网格布局：
        - 单个水印居中
        - 多个水印按图片长宽比选择合适的网格行列
        - 边距按图片边长比例计算，网格内均匀分布，避免重叠
        """
        positions: List[Tuple[int, int]] = []

        # 单个水印：居中
        if count <= 1:
            x = (image_width - text_width) // 2
            y = (image_height - text_height) // 2
            return [(int(x), int(y))]

        # 多个水印：确定网格
        rows, cols = self._determine_grid(count, image_width, image_height)
        rows = max(1, rows)
        cols = max(1, cols)

        # 自适应边距
        margin_x = image_width * self.MARGIN_RATIO
        margin_y = image_height * self.MARGIN_RATIO

        # 可用区域
        usable_w = max(0, image_width - 2 * margin_x)
        usable_h = max(0, image_height - 2 * margin_y)
        if usable_w == 0 or usable_h == 0:
            # 兜底：回退到居中单水印
            cx = (image_width - text_width) // 2
            cy = (image_height - text_height) // 2
            return [(int(cx), int(cy))]

        # 每个单元格尺寸
        cell_w = usable_w / cols
        cell_h = usable_h / rows

        # 在每个单元格内居中放置一个水印
        for i in range(count):
            r = i // cols
            c = i % cols
            # 单元格左上角
            cell_x = margin_x + c * cell_w
            cell_y = margin_y + r * cell_h
            # 将水印放在该单元格中心
            x = cell_x + (cell_w - text_width) / 2
            y = cell_y + (cell_h - text_height) / 2
            # 边界限制，确保不越界
            x = max(0, min(x, image_width - text_width))
            y = max(0, min(y, image_height - text_height))
            positions.append((int(x), int(y)))

        return positions

    def create_watermark_layer(self, image: Image.Image, config: WatermarkConfig) -> Image.Image:
        """创建水印图层"""
        # 获取字体
        font = self.get_font(config.font_family, config.font_size)

        # 创建绘图对象
        draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))

        # 计算文本尺寸（包含上/下行间距），并添加安全内边距，避免底部被裁切
        bbox = draw.textbbox((0, 0), config.text, font=font)
        left, top, right, bottom = bbox
        text_width = right - left
        text_height = bottom - top
        pad = max(2, int(getattr(font, 'size', 16) * 0.15))  # 约15%的字体尺寸作为内边距
        layer_w = text_width + pad * 2
        layer_h = text_height + pad * 2

        # 创建透明图层
        watermark_layer = Image.new('RGBA', (layer_w, layer_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # 解析颜色
        color_hex = config.color.lstrip('#')
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

        # 设置透明度
        alpha = int(255 * config.opacity / 100)

        # 绘制文字（偏移补偿bbox的left/top，并考虑内边距）
        draw.text((pad - left, pad - top), config.text, font=font, fill=(*rgb, alpha))

        # 旋转图层
        if config.rotation != 0:
            watermark_layer = watermark_layer.rotate(config.rotation, expand=True)

        return watermark_layer

    def add_watermark(self, image_path: str, config: WatermarkConfig, output_path: str) -> bool:
        """给图片添加水印，带自适应字体与布局"""
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGBA')
                img_w, img_h = img.width, img.height

                # 字体大小自适应（覆盖传入的 font_size）
                eff_font_size = self._compute_effective_font_size(img_w, img_h, config)
                adaptive_cfg = WatermarkConfig(
                    text=config.text,
                    font_family=config.font_family,
                    font_size=eff_font_size,
                    color=config.color,
                    opacity=config.opacity,
                    count=config.count,
                    rotation=config.rotation
                )

                # 创建水印图层
                watermark_layer = self.create_watermark_layer(img, adaptive_cfg)

                # 计算布局位置（自适应边距与网格）
                positions = self.calculate_positions(
                    img_w, img_h,
                    adaptive_cfg.count,
                    watermark_layer.width,
                    watermark_layer.height
                )

                # 逐个粘贴
                result = img.copy()
                for x, y in positions:
                    if 0 <= x < img_w and 0 <= y < img_h:
                        paste_x = max(0, int(x))
                        paste_y = max(0, int(y))
                        crop_w = min(watermark_layer.width, img_w - paste_x)
                        crop_h = min(watermark_layer.height, img_h - paste_y)
                        if crop_w > 0 and crop_h > 0:
                            crop_layer = watermark_layer.crop((0, 0, crop_w, crop_h))
                            result.paste(crop_layer, (paste_x, paste_y), crop_layer)

                if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                    result = result.convert('RGB')
                result.save(output_path, quality=95)
                return True
        except Exception as e:
            print(f"处理图片失败: {e}")
            return False

    def preview_watermark(self, image_path: str, config: WatermarkConfig, max_size: int = 800) -> Image.Image:
        """生成预览图，确保与实际输出布局比例一致"""
        try:
            with Image.open(image_path) as img:
                orig_w, orig_h = img.size
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                scaled_w, scaled_h = img.size
                scale = min(scaled_w / orig_w if orig_w else 1.0,
                            scaled_h / orig_h if orig_h else 1.0)

                # 按原图自适应计算字体，然后按缩放比例调整预览字体
                eff_font_size = self._compute_effective_font_size(orig_w, orig_h, config)
                preview_font_size = max(self.MIN_FONT_SIZE, int(eff_font_size * max(0.1, scale)))

                preview_config = WatermarkConfig(
                    text=config.text,
                    font_family=config.font_family,
                    font_size=preview_font_size,
                    color=config.color,
                    opacity=config.opacity,
                    count=config.count,
                    rotation=config.rotation
                )

                watermark_layer = self.create_watermark_layer(img, preview_config)

                # 使用与 add_watermark 一致的网格逻辑（基于缩放后图像尺寸与预览层尺寸）
                positions = self.calculate_positions(
                    img.width, img.height,
                    preview_config.count,
                    watermark_layer.width,
                    watermark_layer.height
                )

                preview = img.convert('RGBA')
                for x, y in positions:
                    if 0 <= x < img.width and 0 <= y < img.height:
                        preview.paste(watermark_layer, (x, y), watermark_layer)
                return preview

        except Exception as e:
            print(f"生成预览失败: {e}")
            return None