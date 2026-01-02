"""
推理逻辑封装 - EchoMimic V2
"""

import os
import sys
import gc
import random
import logging
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Tuple

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)

# 全局上下文
_ctx: dict = {}
_initialized: bool = False


def _add_to_path(echomimic_path: str):
    """将 echomimic_v2 添加到 Python 路径"""
    if echomimic_path not in sys.path:
        sys.path.insert(0, echomimic_path)
        logger.info(f"Added echomimic_v2 to path: {echomimic_path}")


def download_file(url: str) -> Optional[str]:
    """下载文件，支持本地路径和 HTTP URL"""
    parsed = urlparse(url)
    
    if parsed.scheme == "" or parsed.scheme == "file":
        local_path = parsed.path if parsed.scheme == "file" else url
        if os.path.exists(local_path):
            return local_path
        logger.error(f"Local file not found: {local_path}")
        return None
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        ext = os.path.splitext(parsed.path)[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(response.content)
            return f.name
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None


def initialize(echomimic_path: str, pretrained_weights: str, acc_mode: bool = None):
    """
    初始化 EchoMimic V2 模型
    
    Args:
        echomimic_path: EchoMimic V2 目录路径
        pretrained_weights: 预训练权重目录路径
        acc_mode: 是否使用加速模式（None 时从环境变量 ECHOMIMIC_ACC_MODE 读取）
    """
    global _initialized, _ctx
    
    if _initialized:
        logger.info("Already initialized")
        return
    
    # 从环境变量读取 acc_mode
    if acc_mode is None:
        acc_mode = os.getenv("ECHOMIMIC_ACC_MODE", "false").lower() in ("true", "1", "yes")
    
    _add_to_path(echomimic_path)
    
    # 切换工作目录
    original_cwd = os.getcwd()
    os.chdir(echomimic_path)
    
    try:
        mode_str = "ACC" if acc_mode else "Normal"
        logger.info(f"Loading EchoMimic V2 models ({mode_str} mode)...")
        
        # 导入依赖
        from diffusers import AutoencoderKL, DDIMScheduler
        from src.models.unet_2d_condition import UNet2DConditionModel
        from src.models.unet_3d_emo import EMOUNet3DConditionModel
        from src.models.whisper.audio2feature import load_audio_model
        from src.models.pose_encoder import PoseEncoder
        
        # 根据模式选择 pipeline
        if acc_mode:
            from src.pipelines.pipeline_echomimicv2_acc import EchoMimicV2Pipeline
        else:
            from src.pipelines.pipeline_echomimicv2 import EchoMimicV2Pipeline
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16
        
        logger.info(f"Device: {device}, dtype: {dtype}")
        
        # VAE
        vae = AutoencoderKL.from_pretrained(
            os.path.join(pretrained_weights, "sd-vae-ft-mse"),
            local_files_only=True
        ).to(device, dtype=dtype)
        
        # Reference UNet
        reference_unet = UNet2DConditionModel.from_pretrained(
            os.path.join(pretrained_weights, "sd-image-variations-diffusers"),
            subfolder="unet",
            use_safetensors=False,
            local_files_only=True
        ).to(dtype=dtype, device=device)
        reference_unet.load_state_dict(
            torch.load(os.path.join(pretrained_weights, "reference_unet.pth"), weights_only=True)
        )
        
        # 根据模式选择模型权重
        if acc_mode:
            motion_module_file = "motion_module_acc.pth"
            denoising_unet_file = "denoising_unet_acc.pth"
        else:
            motion_module_file = "motion_module.pth"
            denoising_unet_file = "denoising_unet.pth"
        
        # Denoising UNet
        motion_module_path = os.path.join(pretrained_weights, motion_module_file)
        if not os.path.exists(motion_module_path):
            raise FileNotFoundError(f"{motion_module_file} not found: {motion_module_path}")
        
        denoising_unet = EMOUNet3DConditionModel.from_pretrained_2d(
            os.path.join(pretrained_weights, "sd-image-variations-diffusers"),
            motion_module_path,
            subfolder="unet",
            unet_additional_kwargs={
                "use_inflated_groupnorm": True,
                "unet_use_cross_frame_attention": False,
                "unet_use_temporal_attention": False,
                "use_motion_module": True,
                "cross_attention_dim": 384,
                "motion_module_resolutions": [1, 2, 4, 8],
                "motion_module_mid_block": True,
                "motion_module_decoder_only": False,
                "motion_module_type": "Vanilla",
                "motion_module_kwargs": {
                    "num_attention_heads": 8,
                    "num_transformer_block": 1,
                    "attention_block_types": ["Temporal_Self", "Temporal_Self"],
                    "temporal_position_encoding": True,
                    "temporal_position_encoding_max_len": 32,
                    "temporal_attention_dim_div": 1,
                }
            },
        ).to(dtype=dtype, device=device)
        denoising_unet.load_state_dict(
            torch.load(os.path.join(pretrained_weights, denoising_unet_file), weights_only=True),
            strict=False
        )
        
        # Pose Encoder
        pose_net = PoseEncoder(320, conditioning_channels=3, block_out_channels=(16, 32, 96, 256)).to(
            dtype=dtype, device=device
        )
        pose_net.load_state_dict(
            torch.load(os.path.join(pretrained_weights, "pose_encoder.pth"), weights_only=True)
        )
        
        # Audio Processor
        audio_processor = load_audio_model(
            model_path=os.path.join(pretrained_weights, "audio_processor/tiny.pt"),
            device=device
        )
        
        # Scheduler
        sched_kwargs = {
            "beta_start": 0.00085,
            "beta_end": 0.012,
            "beta_schedule": "linear",
            "clip_sample": False,
            "steps_offset": 1,
            "prediction_type": "v_prediction",
            "rescale_betas_zero_snr": True,
            "timestep_spacing": "trailing"
        }
        scheduler = DDIMScheduler(**sched_kwargs)
        
        # Pipeline
        pipe = EchoMimicV2Pipeline(
            vae=vae,
            reference_unet=reference_unet,
            denoising_unet=denoising_unet,
            audio_guider=audio_processor,
            pose_encoder=pose_net,
            scheduler=scheduler,
        )
        pipe = pipe.to(device, dtype=dtype)
        
        # 保存到上下文
        _ctx["pipe"] = pipe
        _ctx["device"] = device
        _ctx["dtype"] = dtype
        _ctx["echomimic_path"] = echomimic_path
        _ctx["acc_mode"] = acc_mode
        
        _initialized = True
        logger.info(f"EchoMimic V2 initialized successfully ({mode_str} mode)")
        
    finally:
        os.chdir(original_cwd)


def generate(
    image_path: str,
    audio_path: str,
    pose_dir: str,
    width: int = 768,
    height: int = 768,
    length: int = 120,
    steps: int = 30,
    cfg: float = 2.5,
    fps: int = 24,
    sample_rate: int = 16000,
    context_frames: int = 12,
    context_overlap: int = 3,
    seed: int = -1,
) -> Tuple[bool, str, Optional[str]]:
    """
    生成数字人视频
    
    Args:
        image_path: 参考图片路径
        audio_path: 音频文件路径
        pose_dir: 姿态数据目录（包含 0.npy, 1.npy, ...）
        width: 视频宽度
        height: 视频高度
        length: 视频帧数
        steps: 推理步数
        cfg: CFG scale
        fps: 帧率
        sample_rate: 音频采样率
        context_frames: 上下文帧数
        context_overlap: 上下文重叠
        seed: 随机种子
        
    Returns:
        (success, output_path, error_message)
    """
    if not _initialized:
        return False, "", "Service not initialized"
    
    pipe = _ctx.get("pipe")
    device = _ctx.get("device")
    dtype = _ctx.get("dtype")
    echomimic_path = _ctx.get("echomimic_path")
    
    if not pipe:
        return False, "", "Pipeline not found"
    
    # 切换工作目录
    original_cwd = os.getcwd()
    os.chdir(echomimic_path)
    
    try:
        # 导入工具函数
        from src.utils.util import save_videos_grid
        from src.utils.dwpose_util import draw_pose_select_v2
        from moviepy.editor import VideoFileClip, AudioFileClip
        
        gc.collect()
        torch.cuda.empty_cache()
        
        # 准备输出目录（使用环境变量配置）
        shared_dir = os.getenv("SHARED_DIR", "/app/shared")
        output_dir = os.path.join(shared_dir, "outputs")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = Path(output_dir)
        save_dir.mkdir(exist_ok=True, parents=True)
        save_name = f"{save_dir}/{timestamp}"
        
        # 设置随机种子
        if seed is not None and seed > -1:
            generator = torch.manual_seed(seed)
        else:
            seed = random.randint(100, 1000000)
            generator = torch.manual_seed(seed)
        
        # 加载参考图片
        ref_image_pil = Image.open(image_path).resize((width, height))
        
        # 加载音频
        audio_clip = AudioFileClip(audio_path)
        
        # 计算实际帧数（以音频长度为准）
        pose_files = [f for f in os.listdir(pose_dir) if f.endswith('.npy')]
        pose_count = len(pose_files)
        actual_length = min(length, int(audio_clip.duration * fps))
        
        if actual_length <= 0:
            return False, "", "No valid frames to generate"
        if pose_count <= 0:
            return False, "", "No pose files found"
        
        # 加载姿态数据（pose不够则循环）
        pose_list = []
        for index in range(actual_length):
            pose_index = index % pose_count  # 循环使用pose
            tgt_musk_path = os.path.join(pose_dir, f"{pose_index}.npy")
            
            if not os.path.exists(tgt_musk_path):
                return False, "", f"Pose file not found: {tgt_musk_path}"
            
            detected_pose = np.load(tgt_musk_path, allow_pickle=True).tolist()
            imh_new, imw_new, rb, re, cb, ce = detected_pose['draw_pose_params']
            
            # 用pose原始尺寸生成pose图
            pose_size = re  # pose原始尺寸（正方形）
            tgt_musk = np.zeros((pose_size, pose_size, 3)).astype('uint8')
            im = draw_pose_select_v2(detected_pose, imh_new, imw_new, ref_w=800)
            im = np.transpose(np.array(im), (1, 2, 0))
            tgt_musk[rb:re, cb:ce, :] = im
            
            # resize到目标尺寸
            tgt_musk_pil = Image.fromarray(tgt_musk).convert('RGB').resize((width, height))
            pose_list.append(
                torch.Tensor(np.array(tgt_musk_pil)).to(dtype=dtype, device=device).permute(2, 0, 1) / 255.0
            )
        
        poses_tensor = torch.stack(pose_list, dim=1).unsqueeze(0)
        
        # 调整音频长度
        audio_clip = audio_clip.set_duration(actual_length / fps)
        
        # 生成视频
        video = pipe(
            ref_image_pil,
            audio_path,
            poses_tensor[:, :, :actual_length, ...],
            width,
            height,
            actual_length,
            steps,
            cfg,
            generator=generator,
            audio_sample_rate=sample_rate,
            context_frames=context_frames,
            fps=fps,
            context_overlap=context_overlap,
            start_idx=0,
        ).videos
        
        final_length = min(video.shape[2], poses_tensor.shape[2], actual_length)
        video_sig = video[:, :, :final_length, :, :]
        
        # 保存视频（无音频）
        save_videos_grid(
            video_sig,
            save_name + "_woa.mp4",
            n_rows=1,
            fps=fps,
        )
        
        # 添加音频
        video_clip_sig = VideoFileClip(save_name + "_woa.mp4")
        video_clip_sig = video_clip_sig.set_audio(audio_clip)
        output_path = save_name + ".mp4"
        video_clip_sig.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=2)
        
        # 清理临时文件
        os.remove(save_name + "_woa.mp4")
        
        logger.info(f"Generated video: {output_path}, seed: {seed}")
        return True, output_path, None
        
    except Exception as e:
        logger.exception("Generation failed")
        return False, "", str(e)
    
    finally:
        os.chdir(original_cwd)
        gc.collect()
        torch.cuda.empty_cache()
