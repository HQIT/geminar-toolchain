"""
核心转换逻辑 - 调用 ffmpeg
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConvertResult:
    """转换结果"""
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None


def convert(
    image: str,
    audio: str,
    output: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    crf: int = 23,
) -> ConvertResult:
    """
    将图片和音频合成为视频。
    
    Args:
        image: 图片路径
        audio: 音频路径
        output: 输出视频路径，不指定则生成临时文件
        width: 视频宽度
        height: 视频高度
        fps: 帧率
        video_codec: 视频编码器
        audio_codec: 音频编码器
        crf: 视频质量（越小质量越高，18-28 常用）
        
    Returns:
        ConvertResult
    """
    if not os.path.exists(image):
        return ConvertResult(success=False, error=f"Image not found: {image}")
    
    if not os.path.exists(audio):
        return ConvertResult(success=False, error=f"Audio not found: {audio}")
    
    # 生成输出路径
    if not output:
        fd, output = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
    
    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出文件
        "-loop", "1",  # 循环图片
        "-i", image,
        "-i", audio,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", video_codec,
        "-c:a", audio_codec,
        "-crf", str(crf),
        "-r", str(fps),
        "-shortest",  # 以最短的流为准（音频）
        "-pix_fmt", "yuv420p",  # 兼容性
        output,
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Output: {output}")
        return ConvertResult(success=True, output_path=output)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        logger.error(f"ffmpeg failed: {error_msg}")
        return ConvertResult(success=False, error=error_msg)
    
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return ConvertResult(success=False, error=str(e))


def convert_batch(
    items: List[dict],
    output_dir: Optional[str] = None,
    **kwargs,
) -> List[ConvertResult]:
    """
    批量转换。
    
    Args:
        items: 列表，每项包含 {"image": "...", "audio": "..."}
        output_dir: 输出目录
        **kwargs: 传递给 convert 的参数
        
    Returns:
        转换结果列表
    """
    results = []
    
    for i, item in enumerate(items):
        image = item.get("image")
        audio = item.get("audio")
        
        if not image or not audio:
            results.append(ConvertResult(
                success=False, 
                error=f"Item {i}: missing image or audio"
            ))
            continue
        
        # 生成输出路径
        output = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output = os.path.join(output_dir, f"page_{i:03d}.mp4")
        
        result = convert(image, audio, output=output, **kwargs)
        results.append(result)
    
    return results

