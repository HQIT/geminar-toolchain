"""命令行接口"""

import argparse
import sys
from pathlib import Path

from .composer import FaceComposer, TEMPLATES_DIR


def main():
    parser = argparse.ArgumentParser(
        description="将头像与身体模板合成上半身照片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用模板 ID
  face-to-halfbody -f face.jpg -t template_01 -o output.jpg
  
  # 使用自定义模板文件
  face-to-halfbody -f face.jpg -t /path/to/template.jpg -o output.jpg
  
  # 列出可用模板
  face-to-halfbody --list-templates
""",
    )
    
    parser.add_argument(
        "-f", "--face",
        type=str,
        help="头像图片路径",
    )
    parser.add_argument(
        "-t", "--template",
        type=str,
        help="模板图片路径或模板 ID",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出图片路径",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="列出可用的模板",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="仅使用 CPU（不使用 GPU）",
    )
    
    args = parser.parse_args()
    
    # 列出模板
    if args.list_templates:
        print(f"模板目录: {TEMPLATES_DIR}")
        if not TEMPLATES_DIR.exists():
            print("(目录不存在)")
            return 0
        
        templates = []
        for f in TEMPLATES_DIR.iterdir():
            if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                templates.append(f.stem)
        
        if templates:
            print("可用模板:")
            for t in sorted(templates):
                print(f"  - {t}")
        else:
            print("(无可用模板)")
        return 0
    
    # 检查必需参数
    if not args.face:
        parser.error("需要指定头像图片 (-f/--face)")
    if not args.template:
        parser.error("需要指定模板 (-t/--template)")
    if not args.output:
        parser.error("需要指定输出路径 (-o/--output)")
    
    # 检查文件存在
    face_path = Path(args.face)
    if not face_path.exists():
        print(f"错误: 头像文件不存在: {face_path}", file=sys.stderr)
        return 1
    
    # 设置 providers
    if args.cpu:
        providers = ["CPUExecutionProvider"]
    else:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    
    try:
        print(f"加载模型...")
        composer = FaceComposer(providers=providers)
        
        print(f"处理中...")
        print(f"  头像: {args.face}")
        print(f"  模板: {args.template}")
        
        composer.compose(
            face_image=args.face,
            template=args.template,
            output_path=args.output,
        )
        
        print(f"完成: {args.output}")
        return 0
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

