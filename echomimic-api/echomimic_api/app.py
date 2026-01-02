"""
FastAPI 应用入口 - EchoMimic V2 API
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import get_api_config, get_inference_config
from .inference import initialize, generate, download_file

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

DEFAULT_POSE_DIR = os.path.join(
    os.getenv("ECHOMIMIC_PATH", "/app/echomimic_v2"),
    "assets/halfbody_demo/pose/01"
)

class GenerationConfig(BaseModel):
    """生成配置"""
    facecrop_dilation_ratio: float = 2.0
    width: int = 768
    height: int = 768

class GenerationRequest(BaseModel):
    """生成请求"""
    ref_image_url: str  # 参考图片 URL 或本地路径
    audio_url: str      # 音频 URL 或本地路径
    pose_dir: str = DEFAULT_POSE_DIR  # 姿态数据目录（默认 01）
    config: Optional[GenerationConfig] = None  # 生成配置
    
    # 可选参数（向后兼容）
    length: int = 120
    steps: int = 30
    cfg: float = 2.5
    fps: int = 24
    sample_rate: int = 16000
    context_frames: int = 12
    context_overlap: int = 3
    seed: int = -1


class GenerationResponse(BaseModel):
    """生成响应"""
    success: bool
    output_path: Optional[str] = None
    seed: Optional[int] = None
    error: Optional[str] = None


# ==================== Application ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 强制使用本地模型，禁止从 huggingface 下载
    os.environ["HF_HUB_OFFLINE"] = "1"
    
    config = get_api_config()
    logger.info(f"Initializing EchoMimic V2...")
    logger.info(f"  echomimic_path: {config.echomimic_path}")
    logger.info(f"  pretrained_weights: {config.pretrained_weights}")
    
    try:
        initialize(config.echomimic_path, config.pretrained_weights)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")


app = FastAPI(
    title="EchoMimic V2 API",
    description="EchoMimic V2 数字人生成 API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "v2"}


@app.post("/a2v", response_model=GenerationResponse)
async def audio_to_video(request: GenerationRequest):
    """
    音频驱动数字人视频生成
    
    需要提供：
    - ref_image_url: 参考图片
    - audio_url: 音频文件
    - pose_dir: 姿态数据目录（容器内完整路径）
    """
    # 下载/验证图片
    image_path = download_file(request.ref_image_url)
    if not image_path:
        raise HTTPException(status_code=400, detail="Failed to download/find image")
    
    # 下载/验证音频
    audio_path = download_file(request.audio_url)
    if not audio_path:
        raise HTTPException(status_code=400, detail="Failed to download/find audio")
    
    # 验证姿态目录
    if not os.path.isdir(request.pose_dir):
        raise HTTPException(status_code=400, detail=f"Pose directory not found: {request.pose_dir}")
    
    # 从 config 获取参数
    cfg_obj = request.config or GenerationConfig()
    
    # 调用生成
    success, output_path, error = generate(
        image_path=image_path,
        audio_path=audio_path,
        pose_dir=request.pose_dir,
        width=cfg_obj.width,
        height=cfg_obj.height,
        length=request.length,
        steps=request.steps,
        cfg=request.cfg,
        fps=request.fps,
        sample_rate=request.sample_rate,
        context_frames=request.context_frames,
        context_overlap=request.context_overlap,
        seed=request.seed,
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=error or "Generation failed")
    
    return GenerationResponse(
        success=True,
        output_path=output_path,
        seed=request.seed,
    )


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    """获取生成的视频文件"""
    config = get_api_config()
    
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(config.output_dir, filename),
        os.path.join(config.echomimic_path, "outputs", filename),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="video/mp4")
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/poses")
async def list_poses():
    """列出可用的预设姿态目录"""
    config = get_api_config()
    pose_base = os.path.join(config.echomimic_path, "assets/halfbody_demo/pose")
    
    if not os.path.exists(pose_base):
        return {"poses": []}
    
    poses = []
    for name in os.listdir(pose_base):
        pose_path = os.path.join(pose_base, name)
        if os.path.isdir(pose_path):
            npy_count = len([f for f in os.listdir(pose_path) if f.endswith('.npy')])
            poses.append({
                "name": name,
                "path": pose_path,
                "frames": npy_count,
            })
    
    return {"poses": poses}


if __name__ == "__main__":
    import uvicorn
    
    config = get_api_config()
    uvicorn.run(app, host=config.host, port=config.port)
