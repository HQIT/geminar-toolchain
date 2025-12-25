"""
FastAPI 应用入口
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import get_api_config
from .inference import initialize, remove_background, download_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class RemoveBackgroundRequest(BaseModel):
    """去背景请求"""
    video_url: str
    output_format: str = "composition"  # composition, alpha, foreground
    downsample_ratio: float = 0.25


class RemoveBackgroundResponse(BaseModel):
    """去背景响应"""
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None


# ==================== Application ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    config = get_api_config()
    logger.info(f"Initializing RVM with path: {config.rvm_path}")
    
    try:
        initialize(
            rvm_path=config.rvm_path,
            model_type=config.model_type,
            model_path=config.model_path,
        )
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")


app = FastAPI(
    title="RVM API",
    description="RobustVideoMatting 视频去背景 API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.post("/remove-background", response_model=RemoveBackgroundResponse)
async def api_remove_background(request: RemoveBackgroundRequest):
    """
    视频去背景
    """
    # 下载视频
    video_path = download_file(request.video_url)
    if not video_path:
        raise HTTPException(status_code=400, detail="Failed to download video")
    
    # 去背景
    config = get_api_config()
    output_dir = config.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    success, output_path, error = remove_background(
        input_video=video_path,
        output_format=request.output_format,
        downsample_ratio=request.downsample_ratio,
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=error or "Remove background failed")
    
    return RemoveBackgroundResponse(
        success=True,
        output_path=output_path,
    )


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    """获取输出文件"""
    config = get_api_config()
    file_path = os.path.join(config.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    
    config = get_api_config()
    uvicorn.run(app, host=config.host, port=config.port)

