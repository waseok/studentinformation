"""PDF/이미지 파일 수집."""

from __future__ import annotations

from pathlib import Path

PDF_EXT = {".pdf"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def collect_files(paths: list[str | Path]) -> list[Path]:
    """파일 경로 또는 폴더를 펼쳐 PDF/이미지 목록 반환."""
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for pat in ("**/*.pdf", "**/*.PDF", "**/*.png", "**/*.jpg"):
                out.extend(sorted(path.glob(pat)))
        elif path.is_file():
            suf = path.suffix.lower()
            if suf in PDF_EXT or suf in IMG_EXT:
                out.append(path)
    # 중복 제거 순서 유지
    seen: set[str] = set()
    uniq: list[Path] = []
    for x in out:
        k = str(x.resolve())
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() in PDF_EXT
