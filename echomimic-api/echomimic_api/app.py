"""
FastAPI 应用入口 - 提供 REST API 接口
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import get_api_config, InferenceConfig
from .inference import initialize, generate, download_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class GenerationConfigModel(BaseModel):
    """生成配置（兼容现有 EchoMimicProvider）"""
    width: Optional[int] = None
    height: Optional[int] = None
    facecrop_dilation_ratio: float = 0.5
    # 可扩展更多参数


class GenerationRequest(BaseModel):
    """生成请求"""
    ref_image_url: str
    audio_url: str
    config: Optional[GenerationConfigModel] = None
    prompt: Optional[str] = ""
    negative_prompt: Optional[str] = None
    seed: int = -1


class GenerationResponse(BaseModel):
    """生成响应"""
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None


# ==================== Application ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化模型
    config = get_api_config()
    logger.info(f"Initializing with echomimic_path: {config.echomimic_path}")
    
    try:
        initialize(config.echomimic_path)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # 关闭时清理（如有需要）
    logger.info("Shutting down...")


app = FastAPI(
    title="EchoMimic API",
    description="非侵入式 echomimic_v3 API wrapper",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.post("/a2v", response_model=GenerationResponse)
async def audio_to_video(request: GenerationRequest):
    """
    音频驱动数字人视频生成
    
    兼容现有 EchoMimicProvider 的接口格式
    """
    # 下载文件
    image_path = download_file(request.ref_image_url)
    if not image_path:
        raise HTTPException(status_code=400, detail="Failed to download image")
    
    audio_path = download_file(request.audio_url)
    if not audio_path:
        raise HTTPException(status_code=400, detail="Failed to download audio")
    
    # 获取默认负向提示词
    default_config = InferenceConfig()
    negative_prompt = request.negative_prompt or default_config.negative_prompt
    
    # 调用生成
    success, output_path, error = generate(
        image_path=image_path,
        audio_path=audio_path,
        prompt=request.prompt or "",
        negative_prompt=negative_prompt,
        seed=request.seed,
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=error or "Generation failed")
    
    return GenerationResponse(
        success=True,
        output_path=output_path,
    )


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    """获取生成的视频文件"""
    config = get_api_config()
    file_path = os.path.join(config.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    
    config = get_api_config()
    uvicorn.run(app, host=config.host, port=config.port)

