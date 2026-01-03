"""
CLI for ppt-to-pdf
"""

import argparse
import logging
import sys
import json

from .converter import convert


def main():
    parser = argparse.ArgumentParser(
        description="PPTX 转 PDF + 提取备注"
    )
    parser.add_argument("input", help="输入 PPTX 文件")
    parser.add_argument("-o", "--output-dir", required=True, help="输出目录")
    parser.add_argument("--no-notes", action="store_true", help="不提取备注")
    parser.add_argument("--output-json", action="store_true", help="JSON 格式输出")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    try:
        result = convert(
            input_path=args.input,
            output_dir=args.output_dir,
            extract_notes_flag=not args.no_notes
        )
        
        if args.output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"PDF: {result['pdf']}")
            print(f"Pages: {result['count']}")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

