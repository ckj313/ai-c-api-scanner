from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from c_api_scanner.models import ApiEndpoint


class DirectorySkill(ABC):
    """Extractor contract for one directory-level C API implementation style."""

    name = "base"
    description = "base directory skill"
    priority = 0

    @abstractmethod
    def matches(self, directory: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def extract(self, directory: Path) -> list[ApiEndpoint]:
        raise NotImplementedError


def iter_c_files(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".c", ".h"}
    )


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()
