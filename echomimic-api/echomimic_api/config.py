"""
配置管理 - EchoMimic V2
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIConfig:
    """API 服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    output_dir: str = "outputs"
    
    # echomimic_v2 路径
    echomimic_path: str = field(
        default_factory=lambda: os.getenv("ECHOMIMIC_PATH", "./echomimic_v2")
    )
    
    # 预训练权重路径
    pretrained_weights: str = field(
        default_factory=lambda: os.getenv("PRETRAINED_WEIGHTS", "./echomimic_v2/pretrained_weights")
    )


@dataclass  
class InferenceConfig:
    """推理参数配置"""
    width: int = 768
    height: int = 768
    length: int = 120  # 视频帧数
    steps: int = 30
    cfg: float = 2.5
    fps: int = 24
    sample_rate: int = 16000
    context_frames: int = 12
    context_overlap: int = 3
    seed: int = -1  # -1 表示随机
    quantization: bool = False  # int8 量化（低显存时开启）


def get_api_config() -> APIConfig:
    """获取 API 配置"""
    return APIConfig(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        output_dir=os.getenv("OUTPUT_DIR", "outputs"),
        echomimic_path=os.getenv("ECHOMIMIC_PATH", "./echomimic_v2"),
        pretrained_weights=os.getenv("PRETRAINED_WEIGHTS", "./echomimic_v2/pretrained_weights"),
    )


def get_inference_config() -> InferenceConfig:
    """获取推理配置"""
    return InferenceConfig()
