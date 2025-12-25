"""
推理逻辑封装 - 调用 echomimic_v3 但不修改其源码
"""

import os
import sys
import logging
import tempfile
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)

# 全局上下文，存储已加载的模型
_ctx: dict = {}
_initialized: bool = False


def _add_echomimic_to_path(echomimic_path: str):
    """将 echomimic_v3 添加到 Python 路径"""
    if echomimic_path not in sys.path:
        sys.path.insert(0, echomimic_path)
        logger.info(f"Added echomimic_v3 to path: {echomimic_path}")


def download_file(url: str) -> Optional[str]:
    """
    下载文件到临时目录，支持本地文件路径和 HTTP URL
    
    Args:
        url: 文件 URL 或本地路径
        
    Returns:
        本地文件路径，失败返回 None
    """
    parsed = urlparse(url)
    
    # 本地文件
    if parsed.scheme == "" or parsed.scheme == "file":
        local_path = parsed.path if parsed.scheme == "file" else url
        if os.path.exists(local_path):
            return local_path
        logger.error(f"Local file not found: {local_path}")
        return None
    
    # HTTP/HTTPS 下载
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # 从 URL 推断扩展名
        ext = os.path.splitext(parsed.path)[1] or ".tmp"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(response.content)
            return f.name
            
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None


def initialize(echomimic_path: str):
    """
    初始化 echomimic_v3 模型
    
    这个函数在服务启动时调用，加载模型到 GPU
    """
    global _initialized, _ctx
    
    if _initialized:
        logger.info("Already initialized")
        return
    
    _add_echomimic_to_path(echomimic_path)
    
    # 切换到 echomimic_v3 目录（某些相对路径依赖）
    original_cwd = os.getcwd()
    os.chdir(echomimic_path)
    
    try:
        # 导入 echomimic_v3 的 app 模块，触发模型加载
        # 注意：这会加载全局的 pipeline, wav2vec 等
        logger.info("Loading echomimic_v3 models...")
        
        import app as echomimic_app
        
        # 保存引用到上下文
        _ctx["echomimic_app"] = echomimic_app
        _ctx["generate_fn"] = echomimic_app.generate
        
        _initialized = True
        logger.info("echomimic_v3 initialized successfully")
        
    finally:
        os.chdir(original_cwd)


def generate(
    image_path: str,
    audio_path: str,
    prompt: str = "",
    negative_prompt: str = "",
    seed: int = -1,
) -> Tuple[bool, str, Optional[str]]:
    """
    生成数字人视频
    
    Args:
        image_path: 肖像图片路径
        audio_path: 音频文件路径
        prompt: 正向提示词
        negative_prompt: 负向提示词
        seed: 随机种子，-1 表示随机
        
    Returns:
        (success, output_path, error_message)
    """
    if not _initialized:
        return False, "", "Service not initialized"
    
    generate_fn = _ctx.get("generate_fn")
    if not generate_fn:
        return False, "", "Generate function not found"
    
    try:
        # 调用 echomimic_v3 的 generate 函数
        output_path, used_seed = generate_fn(
            image=image_path,
            audio=audio_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed_param=seed,
        )
        
        logger.info(f"Generated video: {output_path}, seed: {used_seed}")
        return True, output_path, None
        
    except Exception as e:
        logger.exception("Generation failed")
        return False, "", str(e)

