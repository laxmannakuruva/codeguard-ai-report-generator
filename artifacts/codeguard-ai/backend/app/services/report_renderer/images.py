"""Select real project images from the extracted project directory."""

import base64
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
SKIP_RE = re.compile(
    r"(favicon|sprite|icon[-_]|logo|badge|watermark|placeholder|apple-touch|manifest)",
    re.I,
)
PREFERRED = ("_user_uploads", "user_uploads", "screenshot", "screens", "docs", "doc", "assets", "images", "img", "media")
MIN_SIDE = 50
MAX_N = 6


@dataclass
class ReportImage:
    data_uri: str
    caption: str
    source_path: str


def _humanize(s):
    s = re.sub(r"[_\-.]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    parts = [p if p.isupper() and len(p) <= 4 else p.capitalize() for p in s.split()]
    return " ".join(parts) or "Figure"


def _size(path):
    try:
        head = path.read_bytes()[:64]
    except OSError:
        return None
    if head.startswith(b"\x89PNG\r\n\x1a\n") and len(head) >= 24:
        return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    if head[:6] in (b"GIF87a", b"GIF89a") and len(head) >= 10:
        return int.from_bytes(head[6:8], "little"), int.from_bytes(head[8:10], "little")
    return None


def _uri(path):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or f"image/{path.suffix.lower().lstrip('.')}"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _score(path, root):
    score = 0
    parts = [p.lower() for p in path.relative_to(root).parts[:-1]]
    if any(any(pref in p for pref in PREFERRED) for p in parts):
        score += 5
    d = len(path.relative_to(root).parts)
    if 2 <= d <= 5:
        score += 2
    elif d > 6:
        score -= 1
    if path.suffix.lower() == ".png":
        score += 2
    elif path.suffix.lower() in (".jpg", ".jpeg"):
        score += 1
    return score


def select_project_images(root):
    if root is None:
        return []
    try:
        root = Path(root)
    except TypeError:
        return []
    if not root.exists() or not root.is_dir():
        return []

    cands = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUFFIXES:
            continue
        if SKIP_RE.search(str(p.relative_to(root))):
            continue
        s = _size(p)
        if not s:
            continue
        w, h = s
        if w < MIN_SIDE or h < MIN_SIDE:
            continue
        if max(w, h) / max(1, min(w, h)) > 4.0:
            continue
        cands.append((_score(p, root), p))

    cands.sort(key=lambda t: (-t[0], str(t[1])))
    out = []
    for _, p in cands:
        u = _uri(p)
        if not u:
            continue
        out.append(ReportImage(u, _humanize(p.stem), str(p.relative_to(root))))
        if len(out) >= MAX_N:
            break
    return out