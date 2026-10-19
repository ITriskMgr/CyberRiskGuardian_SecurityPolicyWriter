"""Optical character recognition for scanned PDFs and images — runs on this computer only.

Engines, in order of preference:
  1. Tesseract (command-line program; macOS: `brew install tesseract tesseract-lang`, Windows: UB Mannheim
     installer, Linux: `apt install tesseract-ocr tesseract-ocr-fra`). Path override: PB_TESSERACT.
  2. RapidOCR (`pip install rapidocr-onnxruntime`), a pure-Python fallback.
OCR text is never sent to an external service by this module. Every OCR passage carries a confidence value,
and the user must ask for OCR explicitly for each document (spec §6.2).
"""
from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
from dataclasses import dataclass

MAX_OCR_PAGES = 100
RENDER_SCALE = 300 / 72  # ≈300 dpi


class OCRUnavailable(Exception):
    pass


@dataclass
class OCRPage:
    page: int
    text: str
    confidence: float  # 0–100


def _tesseract() -> str | None:
    return os.environ.get("PB_TESSERACT") or shutil.which("tesseract")


def _tess_langs(exe: str) -> list[str]:
    try:
        out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=20).stdout
        return [x.strip() for x in out.splitlines()[1:] if x.strip()]
    except Exception:
        return []


def engine_info() -> dict:
    exe = _tesseract()
    if exe:
        langs = _tess_langs(exe)
        return {"engine": "tesseract", "languages": [l for l in ("eng", "fra") if l in langs], "available": True}
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return {"engine": "rapidocr", "languages": ["latin"], "available": True}
    except Exception:
        return {"engine": None, "languages": [], "available": False}


def _ocr_tesseract(png: bytes, exe: str, langs: list[str]) -> tuple[str, float]:
    lang = "+".join(langs) if langs else "eng"
    r = subprocess.run([exe, "stdin", "stdout", "-l", lang, "--psm", "3", "tsv"], input=png, capture_output=True, timeout=180)
    if r.returncode != 0:
        raise OCRUnavailable("Tesseract failed: " + r.stderr.decode(errors="replace")[:200])
    rows = list(csv.DictReader(io.StringIO(r.stdout.decode("utf-8", errors="replace")), delimiter="\t", quoting=csv.QUOTE_NONE))
    lines: dict[tuple, list[str]] = {}
    confs = []
    for row in rows:
        word = (row.get("text") or "").strip()
        try:
            conf = float(row.get("conf") or -1)
        except ValueError:
            conf = -1
        if not word or conf < 0:
            continue
        confs.append(conf)
        key = (int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))
        lines.setdefault(key, []).append(word)
    paras: dict[tuple, list[str]] = {}
    for (b, p, _l), words in sorted(lines.items()):
        paras.setdefault((b, p), []).append(" ".join(words))
    text = "\n\n".join(" ".join(ls) for ls in paras.values())
    return text, (sum(confs) / len(confs)) if confs else 0.0


def _ocr_rapid(png: bytes) -> tuple[str, float]:
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    result, _ = engine(png)
    if not result:
        return "", 0.0
    texts = [r[1] for r in result]
    confs = [float(r[2]) * 100 for r in result]
    return "\n".join(texts), sum(confs) / len(confs)


def ocr_image_bytes(png: bytes) -> tuple[str, float]:
    exe = _tesseract()
    if exe:
        return _ocr_tesseract(png, exe, [l for l in ("eng", "fra") if l in _tess_langs(exe)])
    try:
        return _ocr_rapid(png)
    except ImportError as e:
        raise OCRUnavailable("No OCR engine is installed.") from e


def _to_png(img) -> bytes:
    buf = io.BytesIO()
    img.convert("L").save(buf, format="PNG")
    return buf.getvalue()


def ocr_document(data: bytes, kind: str, pages: list[int] | None = None) -> list[OCRPage]:
    """OCR a scanned PDF (selected 1-based pages, or all) or an image file."""
    if not engine_info()["available"]:
        raise OCRUnavailable("No OCR engine is installed.")
    out: list[OCRPage] = []
    if kind == "pdf":
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(data)
        try:
            n = len(pdf)
            wanted = [p for p in (pages or range(1, n + 1)) if 1 <= p <= n][:MAX_OCR_PAGES]
            for pno in wanted:
                bitmap = pdf[pno - 1].render(scale=RENDER_SCALE)
                text, conf = ocr_image_bytes(_to_png(bitmap.to_pil()))
                out.append(OCRPage(pno, text.strip(), round(conf, 1)))
        finally:
            pdf.close()
    else:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.load()
        frames = getattr(img, "n_frames", 1)
        for i in range(min(frames, MAX_OCR_PAGES)):
            img.seek(i)
            text, conf = ocr_image_bytes(_to_png(img))
            out.append(OCRPage(i + 1, text.strip(), round(conf, 1)))
    return out
