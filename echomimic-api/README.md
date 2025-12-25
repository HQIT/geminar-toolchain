# EchoMimic API

非侵入式 [echomimic_v3](https://github.com/antgroup/echomimic_v3) API wrapper。

## 设计原则

- **零侵入**：不修改 echomimic_v3 源码
- **独立部署**：作为独立服务运行
- **接口兼容**：兼容现有 `portrait-to-talking` 的 `EchoMimicProvider`

## 快速开始

### Docker 部署

```bash
docker-compose up -d
```

### 本地开发

```bash
# 1. 克隆 echomimic_v3
git clone https://github.com/antgroup/echomimic_v3.git /path/to/echomimic_v3

# 2. 设置环境变量
export ECHOMIMIC_PATH=/path/to/echomimic_v3

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
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
| `ECHOMIMIC_PATH` | echomimic_v3 目录路径 | `/app/echomimic_v3` |
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
│ portrait-to-   │     │  echomimic-api   │     │  echomimic_v3   │
│    talking      │────▶│  (FastAPI)       │────▶│  (原始项目)      │
│ EchoMimicProvider│    │  非侵入式 wrapper │     │  零修改          │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## License

MIT

