"""
命令行接口
"""

import argparse
import logging
import sys

from .converter import convert


def main():
    parser = argparse.ArgumentParser(
        prog="page-to-video",
        description="将图片和音频合成为视频",
    )
    
    parser.add_argument("image", help="图片文件路径")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("-o", "--output", help="输出视频路径")
    parser.add_argument("--width", type=int, default=1920, help="视频宽度 (默认: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="视频高度 (默认: 1080)")
    parser.add_argument("--fps", type=int, default=25, help="帧率 (默认: 25)")
    parser.add_argument("--crf", type=int, default=23, help="视频质量 (默认: 23，越小越好)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    
    # 执行转换
    result = convert(
        image=args.image,
        audio=args.audio,
        output=args.output,
        width=args.width,
        height=args.height,
        fps=args.fps,
        crf=args.crf,
    )
    
    if result.success:
        print(f"✓ 输出: {result.output_path}")
    else:
        print(f"✗ 失败: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

