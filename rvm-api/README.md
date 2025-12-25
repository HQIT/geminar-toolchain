# RVM API

非侵入式 [RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting) API wrapper。

## 设计原则

- **零侵入**：不修改 RobustVideoMatting 源码
- **独立部署**：作为独立服务运行
- **模型常驻**：启动时加载模型，推理时无需重复加载

## 快速开始

### Docker 部署

```bash
docker-compose up -d
```

### 本地开发

```bash
# 1. 克隆 RobustVideoMatting
git clone https://github.com/PeterL1n/RobustVideoMatting.git /path/to/rvm

# 2. 设置环境变量
export RVM_PATH=/path/to/rvm

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python -m rvm_api
```

## API 接口

### POST /remove-background

视频去背景。

**请求体**:

```json
{
  "video_url": "http://example.com/video.mp4",
  "output_format": "composition",
  "downsample_ratio": 0.25
}
```

**output_format 选项**:
- `composition`: 合成视频（绿幕背景）
- `alpha`: alpha 通道视频
- `foreground`: 前景视频

**响应**:

```json
{
  "success": true,
  "output_path": "/app/outputs/xxx.mp4"
}
```

### GET /health

健康检查。

## 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `RVM_PATH` | RobustVideoMatting 目录 | `/app/RobustVideoMatting` |
| `OUTPUT_DIR` | 输出目录 | `outputs` |
| `MODEL_TYPE` | 模型类型 (mobilenetv3/resnet50) | `mobilenetv3` |
| `DOWNSAMPLE_RATIO` | 下采样比例 | `0.25` |
| `API_HOST` | 监听地址 | `0.0.0.0` |
| `API_PORT` | 监听端口 | `8000` |

## License

GPL-3.0 (与 RobustVideoMatting 一致)

