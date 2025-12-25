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
page-to-video slide.png speech.wav -o output.mp4

# 指定分辨率
page-to-video slide.png speech.wav -o output.mp4 --width 1280 --height 720

# 详细输出
page-to-video slide.png speech.wav -v
```

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

