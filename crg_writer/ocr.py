"""Optical character recognition for scanned PDFs and images — on this computer only, after the person asks.

Standard library only. What it uses, when present:
  • Tesseract (command line) reads the page images: macOS `brew install tesseract tesseract-lang`,
    Windows the UB Mannheim installer, Linux `apt install tesseract-ocr tesseract-ocr-fra`.
    CRG_TESSERACT overrides the path.
  • A scanned PDF is first turned into page images with `pdftoppm` (Poppler: `brew install poppler`),
    or with the Python package pypdfium2 when it is installed.
  • RapidOCR (`pip install rapidocr-onnxruntime`) is used when Tesseract is absent.
OCR text never leaves the computer through this module, every page carries a confidence value, and facts
read from OCR get a lower confidence.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import csv
import glob
import io
import os
import shutil
import subprocess
import tempfile

MAX_PAGES = 100
MAX_BYTES = 60 * 1024 * 1024
IMAGE_MAGIC = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpeg", b"II*\x00": "tiff", b"MM\x00*": "tiff"}


class OCRUnavailable(Exception):
    pass


def _tesseract():
    return os.environ.get("CRG_TESSERACT") or shutil.which("tesseract") or next(
        (p for p in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract") if os.path.exists(p)), None)


def _pdftoppm():
    return shutil.which("pdftoppm") or next((p for p in ("/opt/homebrew/bin/pdftoppm", "/usr/local/bin/pdftoppm") if os.path.exists(p)), None)


def _langs(exe):
    try:
        out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=20).stdout
        have = [x.strip() for x in out.splitlines()[1:] if x.strip()]
        return [x for x in ("eng", "fra") if x in have]
    except Exception:                                         # noqa: BLE001
        return []


def _has(mod):
    try:
        __import__(mod)
        return True
    except Exception:                                         # noqa: BLE001
        return False


def info() -> dict:
    exe = _tesseract()
    eng = "tesseract" if exe else "rapidocr" if _has("rapidocr_onnxruntime") else None
    pdf = "pdftoppm" if _pdftoppm() else "pypdfium2" if _has("pypdfium2") else None
    return {"engine": eng, "languages": _langs(exe) if exe else (["latin"] if eng else []), "pdf": pdf,
            "available": bool(eng), "pdf_available": bool(eng and pdf),
            "install": {"en": "Install Tesseract (macOS: brew install tesseract tesseract-lang poppler; Windows: the UB Mannheim installer and Poppler; Linux: apt install tesseract-ocr tesseract-ocr-fra poppler-utils), then restart CyberRiskGuardian.",
                        "fr": "Installez Tesseract (macOS : brew install tesseract tesseract-lang poppler; Windows : l’installateur UB Mannheim et Poppler; Linux : apt install tesseract-ocr tesseract-ocr-fra poppler-utils), puis redémarrez CyberRiskGuardian."}}


def _ocr_tesseract(img: bytes, exe: str, langs: list[str]):
    r = subprocess.run([exe, "stdin", "stdout", "-l", "+".join(langs) or "eng", "--psm", "3", "tsv"], input=img, capture_output=True, timeout=180)
    if r.returncode != 0:
        raise OCRUnavailable("Tesseract failed: " + r.stderr.decode(errors="replace")[:200])
    rows = csv.DictReader(io.StringIO(r.stdout.decode("utf-8", errors="replace")), delimiter="\t", quoting=csv.QUOTE_NONE)
    lines, confs = {}, []
    for row in rows:
        word = (row.get("text") or "").strip()
        try:
            conf = float(row.get("conf") or -1)
        except ValueError:
            conf = -1
        if not word or conf < 0:
            continue
        confs.append(conf)
        lines.setdefault((int(row["block_num"]), int(row["par_num"]), int(row["line_num"])), []).append(word)
    paras = {}
    for (b, p, _l), words in sorted(lines.items()):
        paras.setdefault((b, p), []).append(" ".join(words))
    return "\n".join(" ".join(ls) for ls in paras.values()), (sum(confs) / len(confs)) if confs else 0.0


def _ocr_image(img: bytes):
    exe = _tesseract()
    if exe:
        return _ocr_tesseract(img, exe, _langs(exe))
    if _has("rapidocr_onnxruntime"):
        from rapidocr_onnxruntime import RapidOCR
        res, _ = RapidOCR()(img)
        if not res:
            return "", 0.0
        return "\n".join(r[1] for r in res), sum(float(r[2]) * 100 for r in res) / len(res)
    raise OCRUnavailable("No OCR engine is installed.")


def _pdf_pages(data: bytes, first: int, last: int):
    exe = _pdftoppm()
    if exe:
        with tempfile.TemporaryDirectory(prefix="crg-ocr-") as d:
            src = os.path.join(d, "in.pdf")
            with open(src, "wb") as fh:
                fh.write(data)
            r = subprocess.run([exe, "-r", "300", "-gray", "-png", "-f", str(first), "-l", str(last), src, os.path.join(d, "pg")],
                               capture_output=True, timeout=600)
            if r.returncode != 0:
                raise OCRUnavailable("The PDF could not be turned into images: " + r.stderr.decode(errors="replace")[:200])
            files = sorted(glob.glob(os.path.join(d, "pg-*.png")), key=lambda p: int(p.rsplit("-", 1)[1].split(".")[0]))
            for i, f in enumerate(files):
                with open(f, "rb") as fh:
                    yield first + i, fh.read()
        return
    if _has("pypdfium2"):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(data)
        try:
            for pno in range(first, last + 1):
                im = pdf[pno - 1].render(scale=300 / 72).to_pil().convert("L")
                buf = io.BytesIO()
                im.save(buf, format="PNG")
                yield pno, buf.getvalue()
        finally:
            pdf.close()
        return
    raise OCRUnavailable("Scanned PDFs need Poppler (pdftoppm) or the Python package pypdfium2.")


def _pdf_count(data: bytes) -> int:
    import re
    n = len(re.findall(rb"/Type\s*/Page[^s]", data))
    return max(1, n)


def ocr(data: bytes, name: str = "", pages: list[int] | None = None) -> dict:
    """OCR a scanned PDF (all pages, or the 1-based pages asked) or an image. Returns the text with page
    markers the evidence reader understands, and a confidence per page."""
    if len(data) > MAX_BYTES:
        raise OCRUnavailable("The file is larger than 60 MB.")
    if not info()["available"]:
        raise OCRUnavailable("No OCR engine is installed.")
    out = []
    if data[:5] == b"%PDF-":
        n = min(_pdf_count(data), MAX_PAGES)
        wanted = sorted({p for p in (pages or range(1, n + 1)) if 1 <= p <= n})
        if wanted:
            for pno, png in _pdf_pages(data, wanted[0], wanted[-1]):
                if pno in wanted:
                    t, c = _ocr_image(png)
                    out.append({"page": pno, "text": t.strip(), "confidence": round(c, 1)})
    elif any(data.startswith(m) for m in IMAGE_MAGIC):
        t, c = _ocr_image(data)
        out.append({"page": 1, "text": t.strip(), "confidence": round(c, 1)})
    else:
        raise OCRUnavailable("Only PDF, PNG, JPEG and TIFF files can be read with OCR.")
    text = "\n".join(f"--- Page {p['page']} ---\n{p['text']}" for p in out)
    conf = round(sum(p["confidence"] for p in out) / len(out), 1) if out else 0.0
    return {"name": name, "pages": out, "text": text, "confidence": conf, "engine": info()["engine"],
            "words": len(text.split())}
