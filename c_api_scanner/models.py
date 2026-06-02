from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApiEndpoint:
    source_file: str
    line: int
    methods: list[str]
    path: str
    handler: str
    confidence: float
    evidence: str
    skill: str = ""
    skill_document: str = ""
    directory: str = ""
    notes: str = ""

    def with_context(self, *, skill: str, skill_document: str, directory: Path) -> "ApiEndpoint":
        return ApiEndpoint(
            source_file=self.source_file,
            line=self.line,
            methods=self.methods,
            path=self.path,
            handler=self.handler,
            confidence=self.confidence,
            evidence=self.evidence,
            skill=skill,
            skill_document=skill_document,
            directory=str(directory),
            notes=self.notes,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanReport:
    project_root: str
    endpoints: list[ApiEndpoint] = field(default_factory=list)
    scanned_directories: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root,
            "generated_at": self.generated_at,
            "summary": {
                "endpoint_count": len(self.endpoints),
                "directory_count": len(self.scanned_directories),
                "warning_count": len(self.warnings),
            },
            "scanned_directories": self.scanned_directories,
            "warnings": self.warnings,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
        }
