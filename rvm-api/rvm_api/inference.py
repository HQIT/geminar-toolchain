"""
推理逻辑封装 - 调用 RobustVideoMatting
"""

import os
import sys
import logging
import tempfile
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 全局上下文
_ctx: dict = {}
_initialized: bool = False


def _add_rvm_to_path(rvm_path: str):
    """将 RobustVideoMatting 添加到 Python 路径"""
    if rvm_path and rvm_path not in sys.path:
        sys.path.insert(0, rvm_path)
        logger.info(f"Added RVM to path: {rvm_path}")


def download_file(url: str) -> Optional[str]:
    """下载文件到临时目录"""
    parsed = urlparse(url)
    
    # 本地文件
    if parsed.scheme == "" or parsed.scheme == "file":
        local_path = parsed.path if parsed.scheme == "file" else url
        if os.path.exists(local_path):
            return local_path
        logger.error(f"Local file not found: {local_path}")
        return None
    
    # HTTP 下载
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        ext = os.path.splitext(parsed.path)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(response.content)
            return f.name
            
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None


def initialize(rvm_path: str, model_type: str = "mobilenetv3", model_path: str = ""):
    """
    初始化 RobustVideoMatting 模型
    """
    global _initialized, _ctx
    
    if _initialized:
        logger.info("Already initialized")
        return
    
    _add_rvm_to_path(rvm_path)
    
    import torch
    
    # 加载模型
    logger.info(f"Loading RVM model: {model_type}")
    
    # 优先使用 torch.hub
    try:
        model = torch.hub.load("PeterL1n/RobustVideoMatting", model_type)
    except Exception:
        # fallback: 本地加载
        from model import MattingNetwork
        model = MattingNetwork(model_type).eval()
        
        if model_path and os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
    
    # 移到 GPU
    if torch.cuda.is_available():
        model = model.cuda()
        logger.info("Model loaded on CUDA")
    else:
        logger.info("Model loaded on CPU")
    
    model.eval()
    
    # 加载 convert_video 函数
    try:
        convert_video = torch.hub.load("PeterL1n/RobustVideoMatting", "converter")
    except Exception:
        from inference import convert_video
    
    _ctx["model"] = model
    _ctx["convert_video"] = convert_video
    _initialized = True
    
    logger.info("RVM initialized successfully")


def remove_background(
    input_video: str,
    output_path: Optional[str] = None,
    output_type: str = "video",
    downsample_ratio: float = 0.25,
    output_format: str = "composition",  # composition, alpha, foreground
) -> Tuple[bool, str, Optional[str]]:
    """
    视频去背景
    
    Args:
        input_video: 输入视频路径
        output_path: 输出路径
        output_type: 输出类型 video 或 png_sequence
        downsample_ratio: 下采样比例
        output_format: 输出格式
            - composition: 合成（绿幕背景）
            - alpha: alpha 通道
            - foreground: 前景
            
    Returns:
        (success, output_path, error_message)
    """
    if not _initialized:
        return False, "", "Service not initialized"
    
    model = _ctx.get("model")
    convert_video = _ctx.get("convert_video")
    
    if not model or not convert_video:
        return False, "", "Model not loaded"
    
    # 生成输出路径
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
    
    try:
        # 根据输出格式设置参数
        kwargs = {
            "model": model,
            "input_source": input_video,
            "output_type": output_type,
            "downsample_ratio": downsample_ratio,
        }
        
        if output_format == "composition":
            kwargs["output_composition"] = output_path
        elif output_format == "alpha":
            kwargs["output_alpha"] = output_path
        elif output_format == "foreground":
            kwargs["output_foreground"] = output_path
        else:
            kwargs["output_composition"] = output_path
        
        convert_video(**kwargs)
        
        logger.info(f"Output: {output_path}")
        return True, output_path, None
        
    except Exception as e:
        logger.exception("Remove background failed")
        return False, "", str(e)

