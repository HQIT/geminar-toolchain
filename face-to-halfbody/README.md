# Face to Halfbody

将头像与身体模板合成上半身照片，基于 InsightFace inswapper。

## 安装

```bash
pip install -e .
```

### 模型下载

模型文件较大（~1GB），不包含在 git 仓库中，需手动下载。

**1. 下载 buffalo_l（人脸检测/识别）**

```bash
cd models
mkdir -p models
wget https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
unzip buffalo_l.zip -d models/
rm buffalo_l.zip
```

**2. 下载 inswapper_128.onnx（换脸模型）**

从 https://huggingface.co/deepinsight/inswapper/tree/main 下载 `inswapper_128.onnx`，放到 `models/` 目录。

**目录结构**

```
models/
├── inswapper_128.onnx
└── models/
    └── buffalo_l/
        ├── 1k3d68.onnx
        ├── 2d106det.onnx
        ├── det_10g.onnx
        ├── genderage.onnx
        └── w600k_r50.onnx
```

## 使用

### Python 库

```python
from face_to_halfbody import compose

# 使用模板 ID
result = compose("face.jpg", "template_01", "output.jpg")

# 使用自定义模板文件
result = compose("face.jpg", "/path/to/template.jpg", "output.jpg")

# 返回 numpy 数组，不保存文件
result = compose("face.jpg", "template_01")
```

### 命令行

```bash
# 使用模板 ID
face-to-halfbody -f face.jpg -t template_01 -o output.jpg

# 使用自定义模板文件
face-to-halfbody -f face.jpg -t /path/to/template.jpg -o output.jpg

# 仅使用 CPU
face-to-halfbody -f face.jpg -t template_01 -o output.jpg --cpu

# 列出可用模板
face-to-halfbody --list-templates
```

## 模板

将身体模板图片放到 `templates/` 目录，支持 .jpg/.jpeg/.png 格式。

模板要求：
- 包含清晰的人脸（用于定位替换位置）
- 上半身照片，包含手部
- 分辨率建议 768x768 或更高

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `INSWAPPER_MODEL` | inswapper 模型路径 | `models/inswapper_128.onnx` |

## 已知限制

- **人脸分辨率**：inswapper_128 模型输出的人脸固定为 128x128，合成后人脸清晰度有限。如需更高清晰度，考虑使用 SimSwap-512 或添加人脸增强后处理。

