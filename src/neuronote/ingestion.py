from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path
from typing import Any

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


def materialize_input(file: Any, suffix: str | None = None) -> tuple[str, bytes | None, Path | None]:
    if isinstance(file, dict):
        name = str(file.get("name", f"input{suffix or '.txt'}"))
        content = file.get("content", "")
        if isinstance(content, bytes):
            return name, content, None
        return name, str(content).encode("utf-8"), None

    if isinstance(file, (str, Path)):
        path = Path(file)
        return path.name, None, path

    name = getattr(file, "name", f"input{suffix or '.txt'}")
    if hasattr(file, "getvalue"):
        return str(name), bytes(file.getvalue()), None
    if hasattr(file, "read"):
        data = file.read()
        return str(name), data if isinstance(data, bytes) else str(data).encode("utf-8"), None
    return str(name), str(file).encode("utf-8"), None


def write_temp_file(name: str, data: bytes) -> Path:
    suffix = Path(name).suffix or ".tmp"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(data)
        return Path(handle.name)
    finally:
        handle.close()


def persist_input_file(file: Any, upload_dir: Path | None = None) -> tuple[str, Path]:
    name, data, path = materialize_input(file, ".txt")
    target_dir = upload_dir or get_settings().upload_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(name)
    target = _unique_path(target_dir / safe_name)
    if path is not None:
        shutil.copy2(path, target)
    else:
        target.write_bytes(data or b"")
    return name, target


def extract_pdf_text(path: Path) -> str:
    try:
        import fitz
    except ImportError:
        logger.info("PyMuPDF unavailable for %s", path)
        return f"PDF parsing pending for {path.name}: PyMuPDF is not installed in this Python environment."

    text_parts: list[str] = []
    with fitz.open(path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            page_text = page.get_text("text").strip()
            if page_text:
                text_parts.append(page_text)
                continue
            ocr_text = ocr_pdf_page(page, page_index)
            if ocr_text:
                text_parts.append(ocr_text)
    return "\n\n".join(text_parts).strip()


def extract_pdf_pages(path: Path) -> list[dict[str, object]]:
    try:
        import fitz
    except ImportError:
        return []

    pages: list[dict[str, object]] = []
    with fitz.open(path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            page_text = page.get_text("text").strip()
            pages.append(
                {
                    "page": page_index,
                    "text": page_text,
                    "preview": _clip_text(page_text, 500),
                }
            )
    return pages


def extract_pdf_images(path: Path, output_dir: Path | None = None, limit: int = 12) -> list[dict[str, object]]:
    try:
        import fitz
    except ImportError:
        return []

    target_dir = (output_dir or get_settings().output_dir) / "pdf_images" / path.stem
    target_dir.mkdir(parents=True, exist_ok=True)
    images: list[dict[str, object]] = []
    with fitz.open(path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            for image_index, image in enumerate(page.get_images(full=True), start=1):
                if len(images) >= limit:
                    return images
                xref = image[0]
                extracted = pdf.extract_image(xref)
                extension = extracted.get("ext", "png")
                image_bytes = extracted.get("image", b"")
                if not image_bytes:
                    continue
                image_path = target_dir / f"page-{page_index}-image-{image_index}.{extension}"
                image_path.write_bytes(image_bytes)
                images.append(
                    {
                        "page": page_index,
                        "path": str(image_path),
                        "label": f"Page {page_index} image {image_index}",
                    }
                )
    return images


def ocr_pdf_page(page: Any, page_index: int) -> str:
    pixmap = page.get_pixmap()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"-page-{page_index}.png") as image_file:
        pixmap.save(image_file.name)
        image_path = Path(image_file.name)
    try:
        return extract_image_text(image_path)
    finally:
        image_path.unlink(missing_ok=True)


def extract_image_text(file: Any) -> str:
    name, data, path = materialize_input(file, ".png")
    temp_path: Path | None = None
    if path is None:
        temp_path = write_temp_file(name, data or b"")
        path = temp_path

    settings = get_settings()
    try:
        completed = subprocess.run(  # nosec B603
            [settings.tesseract_cmd, str(path), "stdout"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
        logger.info("Tesseract returned no text for %s: %s", path, completed.stderr.strip())
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        logger.info("Tesseract unavailable for %s: %s", path, exc)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

    return f"OCR pending for {name}"


def transcribe_audio(file: Any) -> str:
    name, data, path = materialize_input(file, ".wav")
    temp_path: Path | None = None
    if path is None:
        temp_path = write_temp_file(name, data or b"")
        path = temp_path

    settings = get_settings()
    try:
        if settings.whisper_cpp_cmd and settings.whisper_model_path:
            completed = subprocess.run(  # nosec B603
                [settings.whisper_cpp_cmd, "-m", str(settings.whisper_model_path), "-f", str(path), "-otxt"],
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                return completed.stdout.strip()
            logger.info("Whisper.cpp returned no transcript for %s: %s", path, completed.stderr.strip())
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        logger.info("Whisper.cpp unavailable for %s: %s", path, exc)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

    return f"Audio transcription pending for {name}"


def extract_document_text(file: Any) -> tuple[str, str]:
    name, data, path = materialize_input(file, ".txt")
    temp_path: Path | None = None
    if path is None and data is not None:
        temp_path = write_temp_file(name, data)
        path = temp_path

    try:
        suffix = Path(name).suffix.lower()
        if suffix == ".pdf" and path:
            return name, extract_pdf_text(path)
        if data is not None:
            return name, data.decode("utf-8", errors="ignore")
        if path:
            return name, path.read_text(encoding="utf-8", errors="ignore")
        return name, ""
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


def _safe_filename(name: str) -> str:
    path = Path(name)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip(".-") or "upload"
    suffix = path.suffix or ".txt"
    return f"{stem}{suffix}"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not create a unique upload path for {path.name}")


def _clip_text(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3]}..."
