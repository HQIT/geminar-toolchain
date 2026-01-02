"""
Pose提取逻辑 - 复用echomimic_v2的DWPose代码
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Tuple
import logging

import numpy as np
import decord
from tqdm import tqdm

# 添加echomimic_v2到path
_base = os.path.dirname(__file__)
_echomimic_v2_path = os.path.join(_base, "../../echomimic-api/echomimic_v2")
sys.path.insert(0, _echomimic_v2_path)

# import DWposeDetector类（不是全局实例）
from src.models.dwpose.dwpose_detector import DWposeDetector

logger = logging.getLogger(__name__)

DEFAULT_MAX_SIZE = 768


@dataclass
class ExtractResult:
    """提取结果"""
    success: bool
    output_dir: Optional[str] = None
    frames: int = 0
    error: Optional[str] = None


def get_model_paths(model_dir: Optional[str] = None) -> Tuple[str, str]:
    """获取模型路径"""
    if model_dir is None:
        model_dir = os.environ.get(
            "DWPOSE_MODEL_DIR",
            os.path.join(_base, "../../echomimic-api/pretrained_weights/dwpose")
        )
    
    model_det = os.path.join(model_dir, "yolox_l.onnx")
    model_pose = os.path.join(model_dir, "dw-ll_ucoco_384.onnx")
    
    return model_det, model_pose


def resize_and_pad_param(imh: int, imw: int, max_size: int) -> Tuple[int, int, int, int, int, int]:
    """计算resize和padding参数"""
    half = max_size // 2
    if imh > imw:
        imh_new = max_size
        imw_new = int(round(imw / imh * imh_new))
        half_w = imw_new // 2
        rb, re = 0, max_size
        cb = half - half_w
        ce = cb + imw_new
    else:
        imw_new = max_size
        imh_new = int(round(imh / imw * imw_new))
        imh_new = max_size
        half_h = imh_new // 2
        cb, ce = 0, max_size
        rb = half - half_h
        re = rb + imh_new
    
    return imh_new, imw_new, rb, re, cb, ce


def get_pose_params(detected_poses: List[dict], height: int, width: int, max_size: int) -> dict:
    """计算pose参数"""
    w_min_all, w_max_all, h_min_all, h_max_all = [], [], [], []
    mid_all = []
    
    for num, detected_pose in enumerate(detected_poses):
        detected_poses[num]['num'] = num
        candidate_body = detected_pose['bodies']['candidate']
        score_body = detected_pose['bodies']['score']
        candidate_face = detected_pose['faces']
        score_face = detected_pose['faces_score']
        candidate_hand = detected_pose['hands']
        score_hand = detected_pose['hands_score']

        # 选取置信度最高的face
        if candidate_face.shape[0] > 1:
            index = 0
            candidate_face = candidate_face[index]
            score_face = score_face[index]
            detected_poses[num]['faces'] = candidate_face.reshape(1, candidate_face.shape[0], candidate_face.shape[1])
            detected_poses[num]['faces_score'] = score_face.reshape(1, score_face.shape[0])
        else:
            candidate_face = candidate_face[0]
            score_face = score_face[0]

        # 选取置信度最高的body
        if score_body.shape[0] > 1:
            tmp_score = []
            for k in range(score_body.shape[0]):
                tmp_score.append(score_body[k].mean())
            index = np.argmax(tmp_score)
            candidate_body = candidate_body[index * 18:(index + 1) * 18, :]
            score_body = score_body[index]
            score_hand = score_hand[(index * 2):(index * 2 + 2), :]
            candidate_hand = candidate_hand[(index * 2):(index * 2 + 2), :, :]
        else:
            score_body = score_body[0]

        body_pose = np.concatenate((candidate_body,))
        mid_ = body_pose[1, 0]
        face_pose = candidate_face

        h_min, h_max = np.min(face_pose[:, 1]), np.max(body_pose[:7, 1])
        h_ = h_max - h_min
        
        mid_w = mid_
        w_min = mid_w - h_ // 2
        w_max = mid_w + h_ // 2
        
        w_min_all.append(w_min)
        w_max_all.append(w_max)
        h_min_all.append(h_min)
        h_max_all.append(h_max)
        mid_all.append(mid_w)

    w_min = np.min(w_min_all)
    w_max = np.max(w_max_all)
    h_min = np.min(h_min_all)
    h_max = np.max(h_max_all)
    mid = np.mean(mid_all)

    margin_ratio = 0.25
    h_margin = (h_max - h_min) * margin_ratio
    
    h_min = max(h_min - h_margin * 0.65, 0)
    h_max = min(h_max + h_margin * 0.5, 1)

    h_min_real = int(h_min * height)
    h_max_real = int(h_max * height)
    mid_real = int(mid * width)
    
    height_new = h_max_real - h_min_real + 1
    width_new = height_new
    w_min_real = mid_real - height_new // 2

    w_max_real = w_min_real + width_new
    w_min = w_min_real / width
    w_max = w_max_real / width

    imh_new, imw_new, rb, re, cb, ce = resize_and_pad_param(height_new, width_new, max_size)
    
    return {
        'draw_pose_params': [imh_new, imw_new, rb, re, cb, ce],
        'pose_params': [w_min, w_max, h_min, h_max],
        'video_params': [h_min_real, h_max_real, w_min_real, w_max_real],
    }


def save_pose_frame(
    detected_pose: dict,
    pose_params: List[float],
    draw_pose_params: List[int],
    save_dir: str
):
    """保存单帧pose数据"""
    w_min, w_max, h_min, h_max = pose_params
    num = detected_pose['num']
    
    candidate_body = detected_pose['bodies']['candidate']
    candidate_face = detected_pose['faces'][0]
    candidate_hand = detected_pose['hands']
    
    # 归一化坐标
    candidate_body[:, 0] = (candidate_body[:, 0] - w_min) / (w_max - w_min)
    candidate_body[:, 1] = (candidate_body[:, 1] - h_min) / (h_max - h_min)
    candidate_face[:, 0] = (candidate_face[:, 0] - w_min) / (w_max - w_min)
    candidate_face[:, 1] = (candidate_face[:, 1] - h_min) / (h_max - h_min)
    candidate_hand[:, :, 0] = (candidate_hand[:, :, 0] - w_min) / (w_max - w_min)
    candidate_hand[:, :, 1] = (candidate_hand[:, :, 1] - h_min) / (h_max - h_min)
    
    detected_pose['bodies']['candidate'] = candidate_body
    detected_pose['faces'] = candidate_face.reshape(1, candidate_face.shape[0], candidate_face.shape[1])
    detected_pose['hands'] = candidate_hand
    detected_pose['draw_pose_params'] = draw_pose_params
    
    np.save(os.path.join(save_dir, f'{num}.npy'), detected_pose)


def extract(
    video_path: str,
    output_dir: str,
    model_dir: Optional[str] = None,
    max_frames: Optional[int] = None,
    max_size: int = DEFAULT_MAX_SIZE,
    device: str = "cuda",
) -> ExtractResult:
    """
    从视频中提取pose数据
    
    Args:
        video_path: 输入视频路径
        output_dir: 输出目录
        model_dir: DWPose模型目录
        max_frames: 最大帧数
        max_size: 输出尺寸
        device: 运行设备
    
    Returns:
        ExtractResult
    """
    # 检查视频文件
    if not os.path.exists(video_path):
        return ExtractResult(success=False, error=f"Video not found: {video_path}")
    
    # 获取模型路径
    model_det, model_pose = get_model_paths(model_dir)
    
    if not os.path.exists(model_det):
        return ExtractResult(success=False, error=f"Model not found: {model_det}")
    if not os.path.exists(model_pose):
        return ExtractResult(success=False, error=f"Model not found: {model_pose}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 初始化检测器
        logger.info(f"Loading DWPose models from {os.path.dirname(model_det)}")
        detector = DWposeDetector(model_det, model_pose, device=device)
        
        # 读取视频
        logger.info(f"Reading video: {video_path}")
        vr = decord.VideoReader(video_path, ctx=decord.cpu(0))
        sample_stride = max(1, int(vr.get_avg_fps() / 24))
        
        frames = vr.get_batch(list(range(0, len(vr), sample_stride))).asnumpy()
        if max_frames is not None:
            frames = frames[:max_frames]
        
        height, width, _ = frames[0].shape
        logger.info(f"Video: {len(frames)} frames, {width}x{height}")
        
        # 提取pose
        logger.info("Extracting poses...")
        detected_poses = [detector(frm) for frm in tqdm(frames, desc="DWPose")]
        detector.release_memory()
        
        # 计算pose参数
        logger.info("Computing pose parameters...")
        res_params = get_pose_params(detected_poses, height, width, max_size)
        
        # 保存pose数据
        logger.info(f"Saving poses to {output_dir}")
        for detected_pose in tqdm(detected_poses, desc="Saving"):
            save_pose_frame(
                detected_pose,
                res_params['pose_params'],
                res_params['draw_pose_params'],
                output_dir
            )
        
        return ExtractResult(
            success=True,
            output_dir=output_dir,
            frames=len(detected_poses)
        )
        
    except Exception as e:
        logger.error(f"Extract failed: {e}")
        return ExtractResult(success=False, error=str(e))

