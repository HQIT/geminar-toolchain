"""
PPTX 转 PDF + 提取备注
"""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_notes(pptx_path: Path, output_dir: Path) -> list[str]:
    """
    从 PPTX 提取备注。
    
    Args:
        pptx_path: PPTX 文件路径
        output_dir: 输出目录
        
    Returns:
        备注列表
    """
    from pptx import Presentation
    
    prs = Presentation(str(pptx_path))
    notes = []
    
    for i, slide in enumerate(prs.slides, 1):
        note_text = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            note_text = slide.notes_slide.notes_text_frame.text.strip()
        
        notes.append(note_text)
        
        # 保存到文件
        note_file = output_dir / f"{i}.txt"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write(note_text)
        
        if note_text:
            logger.info(f"Page {i}: {len(note_text)} chars")
        else:
            logger.info(f"Page {i}: (no notes)")
    
    return notes


def convert_to_pdf(pptx_path: Path, output_dir: Path) -> Path:
    """
    将 PPTX 转为 PDF。
    
    Args:
        pptx_path: PPTX 文件路径
        output_dir: 输出目录
        
    Returns:
        PDF 文件路径
    """
    pptx_path = pptx_path.resolve()
    output_dir = output_dir.resolve()
    
    cmd = [
        "soffice", "--headless", "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(pptx_path)
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        raise RuntimeError(f"Conversion failed: {result.stderr}")
    
    pdf_path = output_dir / f"{pptx_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not created: {pdf_path}")
    
    return pdf_path


def convert(
    input_path: str,
    output_dir: str,
    extract_notes_flag: bool = True
) -> dict:
    """
    转换 PPTX 到 PDF 并提取备注。
    
    Args:
        input_path: PPTX 文件路径
        output_dir: 输出目录
        extract_notes_flag: 是否提取备注
        
    Returns:
        {
            "pdf": PDF 路径,
            "notes": 备注列表,
            "count": 页数
        }
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Converting: {input_path}")
    
    # 提取备注
    notes = []
    if extract_notes_flag:
        logger.info("Extracting notes...")
        notes = extract_notes(input_path, output_dir)
    
    # 转 PDF
    logger.info("Converting to PDF...")
    pdf_path = convert_to_pdf(input_path, output_dir)
    
    logger.info(f"Done: {pdf_path}")
    
    return {
        "pdf": str(pdf_path),
        "notes": notes,
        "count": len(notes)
    }
