"""核心换脸逻辑"""

import os
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis


# 模板目录
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
# 模型目录
MODELS_DIR = Path(__file__).parent.parent / "models"


class FaceComposer:
    """人脸合成器 - 将头像换到身体模板上"""
    
    def __init__(self, providers: Optional[list] = None):
        """
        初始化合成器
        
        Args:
            providers: ONNX Runtime providers，默认自动检测
        """
        if providers is None:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        
        # 初始化人脸分析
        self.face_app = FaceAnalysis(
            name="buffalo_l",
            root=str(MODELS_DIR),
            providers=providers,
        )
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        # 加载换脸模型
        model_path = self._get_swapper_model()
        self.swapper = insightface.model_zoo.get_model(
            model_path,
            providers=providers,
        )
    
    def _get_swapper_model(self) -> str:
        """获取换脸模型路径"""
        # 支持环境变量指定
        if os.environ.get("INSWAPPER_MODEL"):
            model_path = os.environ["INSWAPPER_MODEL"]
            if os.path.exists(model_path):
                return model_path
        
        # 候选路径
        candidates = [
            Path(__file__).parent.parent / "models" / "inswapper_128.onnx",
            Path.home() / ".insightface" / "models" / "inswapper_128.onnx",
        ]
        
        for path in candidates:
            if path.exists():
                return str(path)
        
        raise FileNotFoundError(
            "换脸模型不存在，请下载 inswapper_128.onnx 到以下位置之一:\n"
            f"  - {candidates[0]}\n"
            f"  - {candidates[1]}\n"
            "或设置环境变量 INSWAPPER_MODEL 指定路径"
        )
    
    def compose(
        self,
        face_image: Union[str, Path, np.ndarray],
        template: Union[str, Path, np.ndarray],
        output_path: Optional[Union[str, Path]] = None,
    ) -> np.ndarray:
        """
        将头像合成到身体模板上
        
        Args:
            face_image: 头像图片路径或 numpy 数组
            template: 模板图片路径、模板ID 或 numpy 数组
            output_path: 输出路径，可选
            
        Returns:
            合成后的图片 (BGR numpy 数组)
        """
        # 加载头像
        if isinstance(face_image, (str, Path)):
            face_img = cv2.imread(str(face_image))
            if face_img is None:
                raise ValueError(f"无法加载头像图片: {face_image}")
        else:
            face_img = face_image
        
        # 加载模板
        template_img = self._load_template(template)
        
        # 检测头像中的人脸
        source_faces = self.face_app.get(face_img)
        if not source_faces:
            raise ValueError("头像中未检测到人脸")
        source_face = source_faces[0]
        
        # 检测模板中的人脸
        target_faces = self.face_app.get(template_img)
        if not target_faces:
            raise ValueError("模板中未检测到人脸")
        target_face = target_faces[0]
        
        # 执行换脸
        result = self.swapper.get(
            template_img,
            target_face,
            source_face,
            paste_back=True,
        )
        
        # 保存结果
        if output_path:
            cv2.imwrite(str(output_path), result)
        
        return result
    
    def _load_template(
        self, 
        template: Union[str, Path, np.ndarray]
    ) -> np.ndarray:
        """加载模板图片"""
        if isinstance(template, np.ndarray):
            return template
        
        template_path = Path(template)
        
        # 如果是模板 ID（不含路径分隔符且不含扩展名）
        if not template_path.suffix and "/" not in str(template):
            # 在模板目录查找
            for ext in [".jpg", ".jpeg", ".png"]:
                candidate = TEMPLATES_DIR / f"{template}{ext}"
                if candidate.exists():
                    template_path = candidate
                    break
            else:
                raise ValueError(f"未找到模板: {template}")
        
        img = cv2.imread(str(template_path))
        if img is None:
            raise ValueError(f"无法加载模板图片: {template_path}")
        
        return img
    
    def list_templates(self) -> list[str]:
        """列出可用的模板"""
        if not TEMPLATES_DIR.exists():
            return []
        
        templates = []
        for f in TEMPLATES_DIR.iterdir():
            if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                templates.append(f.stem)
        
        return sorted(templates)


# 全局实例（懒加载）
_composer: Optional[FaceComposer] = None


def get_composer() -> FaceComposer:
    """获取全局合成器实例"""
    global _composer
    if _composer is None:
        _composer = FaceComposer()
    return _composer


def compose(
    face_image: Union[str, Path, np.ndarray],
    template: Union[str, Path, np.ndarray],
    output_path: Optional[Union[str, Path]] = None,
) -> np.ndarray:
    """
    便捷函数：将头像合成到身体模板上
    
    Args:
        face_image: 头像图片路径或 numpy 数组
        template: 模板图片路径、模板ID 或 numpy 数组
        output_path: 输出路径，可选
        
    Returns:
        合成后的图片 (BGR numpy 数组)
    
    Example:
        >>> from face_to_halfbody import compose
        >>> result = compose("face.jpg", "template_01", "output.jpg")
    """
    return get_composer().compose(face_image, template, output_path)

