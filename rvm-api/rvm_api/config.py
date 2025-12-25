"""
配置管理
"""

import os
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API 服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    output_dir: str = "outputs"
    
    # RobustVideoMatting 路径
    rvm_path: str = ""
    
    # 模型配置
    model_type: str = "mobilenetv3"  # mobilenetv3 或 resnet50
    model_path: str = ""  # 模型权重路径
    downsample_ratio: float = 0.25  # 下采样比例


def get_api_config() -> APIConfig:
    """获取 API 配置"""
    return APIConfig(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        output_dir=os.getenv("OUTPUT_DIR", "outputs"),
        rvm_path=os.getenv("RVM_PATH", "/app/RobustVideoMatting"),
        model_type=os.getenv("MODEL_TYPE", "mobilenetv3"),
        model_path=os.getenv("MODEL_PATH", ""),
        downsample_ratio=float(os.getenv("DOWNSAMPLE_RATIO", "0.25")),
    )

