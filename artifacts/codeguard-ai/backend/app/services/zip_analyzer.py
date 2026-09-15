import io
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from .code_extractor import SPECIAL_TEXT_FILES, TEXT_EXTENSIONS

IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}

MAX_UNCOMPRESSED_BYTES = 1 * 1024 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100_000
IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".idea",
    ".next",
    ".pytest_cache",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}


class UnsafeZipError(ValueError):
    """Raised when an archive cannot be safely extracted."""


def _safe_member_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if member.is_absolute() or ".." in member.parts:
        raise UnsafeZipError("The ZIP contains an unsafe path.")
    return root / Path(*member.parts)


def _is_ignored_member(member_name: str) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in PurePosixPath(member_name.replace("\\", "/")).parts)


def _is_extractable_member(member_name: str) -> bool:
    path = PurePosixPath(member_name.replace("\\", "/"))
    return (
        path.name in SPECIAL_TEXT_FILES
        or path.suffix.lower() in TEXT_EXTENSIONS
        or path.suffix.lower() in IMAGE_EXTENSIONS
    )


def extract_zip_safely(zip_bytes: bytes) -> tuple[Path, int]:
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise UnsafeZipError("The uploaded file is not a valid ZIP archive.")

    extraction_root = Path(tempfile.mkdtemp(prefix="codeguard-project-")).resolve()
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_ENTRIES:
                raise UnsafeZipError("The ZIP contains too many files.")
            total_uncompressed = sum(max(info.file_size, 0) for info in members)
            if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise UnsafeZipError("The uncompressed project is larger than 1 GB.")

            extractable_members: list[zipfile.ZipInfo] = []
            for info in members:
                destination = _safe_member_path(extraction_root, info.filename)
                if info.is_dir():
                    if _is_ignored_member(info.filename):
                        continue
                    extractable_members.append(info)
                    continue
                # ZIP mode bits identify symbolic links before extraction.
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise UnsafeZipError("The ZIP contains an unsupported symbolic link.")
                if _is_ignored_member(info.filename) or not _is_extractable_member(info.filename):
                    continue
                extractable_members.append(info)
            archive.extractall(extraction_root, members=extractable_members)
            extracted_files = sum(not info.is_dir() for info in extractable_members)
    except (OSError, zipfile.BadZipFile) as error:
        shutil.rmtree(extraction_root, ignore_errors=True)
        if isinstance(error, zipfile.BadZipFile):
            raise UnsafeZipError("The uploaded file is not a readable ZIP archive.") from error
        raise UnsafeZipError("The project could not be extracted safely.") from error
    except Exception:
        shutil.rmtree(extraction_root, ignore_errors=True)
        raise
    return extraction_root, extracted_files


def new_project_id() -> str:
    return uuid.uuid4().hex