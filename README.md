# BatchMark - 批量图片文字水印工具

## 项目简介
BatchMark 是一款专为图片资源添加水印的桌面端工具，支持批量处理，操作简单高效。

## 功能特点
- 🖼️ 支持批量导入图片（JPG/PNG/GIF/BMP）
- 📝 自定义文字水印（支持中英文）
- 🎨 可调字体、字号、颜色、透明度
- 🔢 通过水印数量实现自动网格布局
- ⚡ 实时预览效果
- 📁 批量输出，支持JPG/PNG格式
- 💾 保存常用配置模板

## 环境要求
- Python 3.8+
- Windows 10/11, macOS 12+, Ubuntu 20.04+

## 快速开始

### 1. 激活虚拟环境
```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖（已使用国内源）
```bash
pip install -r requirements.txt
```

### 3. 运行程序
```bash
python main.py
```

### 4. 打包为可执行文件
```bash
# Windows
pyinstaller --onefile --windowed main.py

# macOS
pyinstaller --onefile --windowed --icon=icon.icns main.py
```

## 项目结构
```
BatchMark/
├── App/                    # 应用代码
│   ├── ui/                # 用户界面
│   ├── core/              # 核心算法
│   ├── services/          # 业务逻辑
│   ├── models/            # 数据模型
│   ├── utils/             # 工具函数
│   └── tests/             # 测试文件
├── Docs/                  # 文档
├── venv/                  # 虚拟环境
├── main.py               # 程序入口
├── requirements.txt      # 依赖列表
└── README.md            # 项目说明
```

## 使用说明

### 添加水印
1. 点击"选择图片"或拖拽图片到预览区域
2. 在右侧设置面板配置水印参数
3. 设置水印数量实现自动布局
4. 选择输出目录和格式
5. 点击"开始处理"按钮

### 参数说明
- **水印文本**: 支持中英文，最多2行
- **字体大小**: 10-200像素
- **水印数量**: 1-20个，自动网格布局
- **透明度**: 0-100%，建议30-70%
- **旋转角度**: 0-360度
- **输出格式**: JPG或PNG
- **JPG质量**: 50-100%，默认90%

## 开发说明

### 添加新功能
1. 在相应模块目录下创建新文件
2. 遵循现有代码风格
3. 添加必要的注释和文档

### 运行测试
```bash
python -m pytest App/tests/
```

## 注意事项
- 程序为本地运行，不会上传图片到服务器
- 大图片处理可能需要较长时间
- 确保输出目录有足够磁盘空间

## 技术支持
如有问题，请查看日志文件或联系开发团队。

## Windows 可执行文件分发说明

- 系统要求：Windows 10/11（64位）
- 使用方法：将 dist/BatchMark.exe 拷贝至目标电脑，直接双击运行；首次启动可能稍慢（单文件会解压到临时目录）
- 常见问题处理：
  - SmartScreen 提示“已保护你的电脑/未知发布者”：点击“更多信息”→“仍要运行”
  - 杀软/企业管控拦截：将 BatchMark.exe 加入白名单或允许列表
  - 缺少运行库（极少见）：若提示缺少 VCRUNTIME/MSVCP 等，安装“Microsoft Visual C++ 2015-2022 Redistributable (x64)”
  - 权限问题：请选择有写入权限的输出目录（不要选 Program Files 等受限目录）
- 故障排查：
  - 在 exe 同目录打开“命令提示符”，运行：
    ```bat
    BatchMark.exe
    ```
    若有报错信息会显示在终端，便于定位；可将输出截图发给开发者协助分析

## 打包部署指南

使用 PyInstaller（已验证可行）。推荐命令：

- 单文件（onefile）发布，隐藏控制台、包含图标与资源：
  ```powershell
  .\venv\Scripts\pyinstaller.exe ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name BatchMark ^
    --icon App\static\imges\app.ico ^
    --add-data "App\static\imges;App\static\imges" ^
    main.py
  ```
- 目录（onedir）发布，启动更快：
  ```powershell
  .\venv\Scripts\pyinstaller.exe ^
    --noconfirm ^
    --windowed ^
    --name BatchMark ^
    --icon App\static\imges\app.ico ^
    --add-data "App\static\imges;App\static\imges" ^
    main.py
  ```
- 资源与图标说明：
  - 资源目录为 App/static/imges（注意拼写 imges），图标为 app.ico 或 app.png
  - 运行时代码已兼容 PyInstaller 单文件目录：
    ```python
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    ```
- 打包后验证：
  1) 在 dist/ 下启动 BatchMark.exe
  2) 验证图标显示、拖拽/选择图片、预览、参数调整、进度弹窗、导出结果
  3) 在干净环境（未装 Python）测试一次

## 项目架构说明（更新）

```
App/
├─ core/                 # 核心算法
│  └─ watermark_engine.py   # 自适应字体计算、网格布局、旋转与透明度、预览生成
├─ services/             # 业务服务
│  ├─ file_service.py       # 文件扫描/验证、输出路径生成、磁盘空间与大小估算
│  └─ batch_service.py      # 批处理调度、进度回调、结果汇总
├─ ui/                  # 界面
│  └─ main_window.py       # 预览、参数面板、进度弹窗、拖拽/选择/导出逻辑
├─ models/              # 配置与数据结构
│  └─ config.py            # WatermarkConfig/OutputConfig/Template
├─ utils/
│  └─ helpers.py           # 配置模板保存/加载、通用工具
└─ static/imges/        # 应用图标与静态资源
```

- 核心算法简述：
  - 字体大小自适应：font_size = clamp(min(image_w, image_h) × ratio, [12, 200])；支持“自适应/手动”模式切换
  - 网格布局：根据图片宽高比自适应 rows×cols；可用区域为去除边距（边距=边长×0.1）；在单元格中心放置水印
  - 预览一致性：预览使用原图自适应字号按缩放比例同步，确保预览与导出布局一致
  - 边界与裁切：绘制时为文本添加内边距，旋转使用 expand=True，避免底部/边缘裁切

## 使用指南优化与最佳实践

- 新增功能说明：
  - 自适应字体开关：可切换自适应/手动字号；自适应比例可调（0.01–0.20）
  - 颜色选择器：选择文字颜色（默认红色 #FF0000），实时刷新预览
  - 进度弹窗：显示进度条、当前文件、完成计数；完成后自动关闭并弹出摘要
- 常见使用场景：
  - 批量打水印：拖拽整目录或多选文件 → 配置水印 → 选择输出目录 → 开始处理
  - 大图/多图：建议分批处理；确保输出盘符剩余空间充足
- 最佳实践：
  - 透明度 30–70% 一般观感最佳；数量 3/4/6/9 较为常用
  - 自适应比例常用范围 0.03–0.05；遇到超宽/超长图可微调获得更均衡的布局
  - 输出 JPG 时质量 85–95 兼顾体积与清晰度
