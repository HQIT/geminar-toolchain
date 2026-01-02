# EchoMimic API

EchoMimic V2 API wrapper。

## 快速开始

### Docker 部署

```bash
docker-compose up -d
```

### 本地开发

```bash
# 1. 设置环境变量
export ECHOMIMIC_PATH=./echomimic_v2
export PRETRAINED_WEIGHTS=./echomimic_v2/pretrained_weights

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python -m uvicorn echomimic_api.app:app --host 0.0.0.0 --port 8000
```

## API 接口

### POST /a2v

音频驱动数字人视频生成。

**请求体**:

```json
{
  "ref_image_url": "http://example.com/portrait.jpg",
  "audio_url": "http://example.com/speech.wav",
  "config": {
    "width": 768,
    "height": 768
  },
  "prompt": "",
  "seed": -1
}
```

**响应**:

```json
{
  "success": true,
  "output_path": "/app/outputs/20241225_120000_audio.mp4"
}
```

### GET /health

健康检查。

### GET /outputs/{filename}

获取生成的视频文件。

## 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `ECHOMIMIC_PATH` | echomimic_v2 目录路径 | `./echomimic_v2` |
| `PRETRAINED_WEIGHTS` | 预训练权重路径 | `./echomimic_v2/pretrained_weights` |
| `OUTPUT_DIR` | 输出目录 | `outputs` |
| `API_HOST` | 监听地址 | `0.0.0.0` |
| `API_PORT` | 监听端口 | `8000` |

## 与 portrait-to-talking 集成

只需修改环境变量：

```bash
export ECHOMIMIC_URL=http://localhost:8000/a2v
```

现有 `EchoMimicProvider` 代码无需修改。

## 架构说明

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ portrait-to-   │     │  echomimic-api   │     │  echomimic_v2   │
│    talking      │────▶│  (FastAPI)       │────▶│  (本地目录)      │
│ EchoMimicProvider│    │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 预训练权重

权重文件不纳入 git 管理，需手动下载放置到 `pretrained_weights/` 目录。

### 文件清单

| 文件路径 | 大小 |
|---------|------|
| `sd-image-variations-diffusers/unet/diffusion_pytorch_model.bin` | 3.3G |
| `denoising_unet_acc.pth` | 3.2G |
| `motion_module_acc.pth` | 1.7G |
| `reference_unet.pth` | 1.6G |
| `pose_encoder.pth` | 1.6G |
| `denoising_unet.pth` | 1.6G |
| `sd-image-variations-diffusers/safety_checker/pytorch_model.bin` | 1.2G |
| `sd-image-variations-diffusers/image_encoder/pytorch_model.bin` | 1.2G |
| `motion_module.pth` | 867M |
| `sd-vae-ft-mse/diffusion_pytorch_model.safetensors` | 320M |
| `sd-vae-ft-mse/diffusion_pytorch_model.bin` | 320M |
| `sd-image-variations-diffusers/vae/diffusion_pytorch_model.bin` | 320M |
| `audio_processor/tiny.pt` | 73M |

### 下载方式

从 HuggingFace 或模型源下载后放置到 `pretrained_weights/` 目录。

## License

MIT

