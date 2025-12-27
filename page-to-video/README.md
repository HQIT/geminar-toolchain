# page-to-video

将图片和音频合成为视频。

## 安装

```bash
cd page-to-video
pip install -e .
```

## 命令行使用

```bash
# 基本用法
python -m page_to_video slide.png speech.wav -o output.mp4

# 指定分辨率
python -m page_to_video slide.png speech.wav -o output.mp4 --width 1280 --height 720

# 添加开头/结尾静音和渐变效果
python -m page_to_video slide.png speech.wav -o output.mp4 --intro 2:0.5 --outro 2:0.5

# 详细输出
python -m page_to_video slide.png speech.wav -o output.mp4 -v
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `image` | 图片文件路径 |
| `audio` | 音频文件路径 |
| `-o, --output` | 输出视频路径 |
| `--width` | 视频宽度（默认 1920） |
| `--height` | 视频高度（默认 1080） |
| `--fps` | 帧率（默认 25） |
| `--crf` | 视频质量，越小越好（默认 23） |
| `--intro` | 开头静音，格式 `时长:渐强`，如 `2:0.5` |
| `--outro` | 结尾静音，格式 `时长:渐弱`，如 `2:0.5` |
| `-v, --verbose` | 详细输出 |

## Python API

```python
from page_to_video import convert, convert_batch

# 单个转换
result = convert("slide.png", "speech.wav", output="output.mp4")
print(result.output_path)

# 批量转换
items = [
    {"image": "slide_1.png", "audio": "audio_1.wav"},
    {"image": "slide_2.png", "audio": "audio_2.wav"},
]
results = convert_batch(items, output_dir="outputs/")
```

## 依赖

- ffmpeg（系统安装）

## License

MIT

