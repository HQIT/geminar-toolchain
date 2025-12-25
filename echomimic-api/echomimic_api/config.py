"""
配置管理
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
    
    # echomimic_v3 路径（可通过环境变量配置）
    echomimic_path: str = field(
        default_factory=lambda: os.getenv("ECHOMIMIC_PATH", "/app/echomimic_v3")
    )


@dataclass  
class InferenceConfig:
    """推理参数配置"""
    seed: int = -1  # -1 表示随机
    prompt: str = ""
    negative_prompt: str = (
        "Gesture is bad. Gesture is unclear. Strange and twisted hands. "
        "Bad hands. Bad fingers. Unclear and blurry hands. "
        "手部快速摆动, 手指频繁抽搐, 夸张手势, 重复机械性动作."
    )
    
    # 可扩展的额外参数
    width: Optional[int] = None
    height: Optional[int] = None


def get_api_config() -> APIConfig:
    """获取 API 配置"""
    return APIConfig(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        output_dir=os.getenv("OUTPUT_DIR", "outputs"),
        echomimic_path=os.getenv("ECHOMIMIC_PATH", "/app/echomimic_v3"),
    )

