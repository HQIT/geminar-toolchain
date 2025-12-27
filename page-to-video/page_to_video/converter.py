"""
核心转换逻辑 - 调用 ffmpeg
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def parse_intro_outro(value: str) -> Tuple[float, float]:
    """
    解析 intro/outro 参数。
    
    格式: "duration" 或 "duration:fade"
    例如: "2" -> (2.0, 0.0), "2:0.5" -> (2.0, 0.5)
    """
    if not value:
        return (0.0, 0.0)
    
    parts = value.split(":")
    duration = float(parts[0])
    fade = float(parts[1]) if len(parts) > 1 else 0.0
    return (duration, fade)


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


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
    intro: str = "",
    outro: str = "",
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
        intro: 开头静音设置，格式 "duration:fade"，如 "2:0.5"
        outro: 结尾静音设置，格式 "duration:fade"，如 "2:0.5"
        
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
    
    # 解析 intro/outro 参数
    intro_duration, intro_fade = parse_intro_outro(intro)
    outro_duration, outro_fade = parse_intro_outro(outro)
    
    # 构建音频滤镜
    audio_filters = []
    
    # 获取音频时长用于计算 fade out 位置
    audio_duration = get_audio_duration(audio)
    
    # 添加开头静音（使用 adelay）
    if intro_duration > 0:
        delay_ms = int(intro_duration * 1000)
        audio_filters.append(f"adelay={delay_ms}|{delay_ms}")
    
    # 添加渐强效果
    if intro_fade > 0:
        audio_filters.append(f"afade=t=in:st={intro_duration}:d={intro_fade}")
    
    # 添加渐弱效果
    if outro_fade > 0:
        fade_out_start = intro_duration + audio_duration - outro_fade
        audio_filters.append(f"afade=t=out:st={fade_out_start}:d={outro_fade}")
    
    # 添加结尾静音（使用 apad）
    if outro_duration > 0:
        audio_filters.append(f"apad=pad_dur={outro_duration}")
    
    # 计算总时长
    total_duration = intro_duration + audio_duration + outro_duration
    
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
        "-t", str(total_duration),  # 指定总时长
        "-pix_fmt", "yuv420p",  # 兼容性
    ]
    
    # 添加音频滤镜
    if audio_filters:
        cmd.extend(["-af", ",".join(audio_filters)])
    
    cmd.append(output)
    
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

