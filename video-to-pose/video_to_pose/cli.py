"""
命令行接口
"""

import argparse
import logging
import sys

from .extractor import extract


def main():
    parser = argparse.ArgumentParser(
        prog="video-to-pose",
        description="从视频中提取pose数据",
    )
    
    parser.add_argument("video", help="输入视频路径")
    parser.add_argument("-o", "--output", required=True, help="输出pose目录")
    parser.add_argument("--max-frames", type=int, help="最大帧数")
    parser.add_argument("--max-size", type=int, default=768, help="输出尺寸 (默认: 768)")
    parser.add_argument("--model-dir", help="DWPose模型目录 (默认: 环境变量DWPOSE_MODEL_DIR)")
    parser.add_argument("--device", default="cuda", help="运行设备 (默认: cuda)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    
    # 执行提取
    result = extract(
        video_path=args.video,
        output_dir=args.output,
        model_dir=args.model_dir,
        max_frames=args.max_frames,
        max_size=args.max_size,
        device=args.device,
    )
    
    if result.success:
        print(f"✓ 提取完成: {result.frames} 帧")
        print(f"  输出目录: {result.output_dir}")
    else:
        print(f"✗ 失败: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

