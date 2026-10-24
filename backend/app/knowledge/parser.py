"""PDF 解析：按页提取文本。

策略：
1. 先用 pypdf 提取文本层；
2. 某页无文本（扫描件）时，用 PyMuPDF 渲染成图片 + RapidOCR 中文识别回退；
3. OCR 失败仍返回空文本，由调用方记录告警。
"""
import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

_OCR_INITIALIZED = False
_OCR = None


def _get_ocr():
    """懒加载 RapidOCR（首次调用约需数秒初始化）。"""
    global _OCR, _OCR_INITIALIZED
    if not _OCR_INITIALIZED:
        from rapidocr_onnxruntime import RapidOCR
        _OCR = RapidOCR()
        _OCR_INITIALIZED = True
        logger.info("RapidOCR 中文识别引擎已加载")
    return _OCR


@dataclass
class PdfPage:
    """单页提取结果。source 为文档名（不含扩展名），page_no 从 1 开始。"""

    source: str
    page_no: int
    text: str


def _ocr_page(path: Path, page_no: int) -> str:
    """渲染指定页为图片并 OCR，返回识别文本。"""
    import pymupdf  # PyMuPDF 2.x（fitz 名称已弃用）

    ocr = _get_ocr()
    with pymupdf.open(str(path)) as doc:
        page = doc[page_no - 1]
        # 放大渲染提高识别率（约 180 DPI）
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5))
        img_bytes = pix.tobytes("png")
    result, _ = ocr(img_bytes)
    if not result:
        return ""
    lines = []
    for item in result:
        text = item[1].strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def parse_pdf(path: Path, ocr_fallback: bool = True) -> list[PdfPage]:
    """解析单个 PDF，返回含文本的页列表；无文本页被丢弃。"""
    reader = PdfReader(str(path))
    pages: list[PdfPage] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:  # 个别页面损坏时跳过，不中断整份文档
            logger.warning("页面 %s 提取失败：%s", path.name, exc)
            continue
        if not text and ocr_fallback:
            try:
                text = _ocr_page(path, i)
            except Exception as exc:
                logger.warning("页面 %s OCR 失败：%s", path.name, exc)
                text = ""
        if text:
            pages.append(PdfPage(source=path.stem, page_no=i, text=text))
    return pages
