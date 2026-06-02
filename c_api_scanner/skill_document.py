from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkillDocument:
    name: str
    description: str
    priority: int
    adapter: str
    path: Path
    content: str
    required_files: tuple[str, ...] = ()
    any_files: tuple[str, ...] = ()

    def matches(self, directory: Path) -> bool:
        if self.required_files and not all((directory / item).exists() for item in self.required_files):
            return False
        if self.any_files and not any((directory / item).exists() for item in self.any_files):
            return False
        return bool(self.required_files or self.any_files)


def load_skill_documents(root: Path) -> list[SkillDocument]:
    documents = []
    for path in sorted(root.glob("*/SKILL.md")):
        documents.append(load_skill_document(path))
    return sorted(documents, key=lambda item: item.priority, reverse=True)


def load_skill_document(path: Path) -> SkillDocument:
    raw = path.read_text(encoding="utf-8")
    metadata, content = _split_frontmatter(raw)
    match = metadata.get("match", {})
    return SkillDocument(
        name=str(metadata["name"]),
        description=str(metadata.get("description", "")),
        priority=int(metadata.get("priority", 0)),
        adapter=str(metadata.get("adapter", metadata["name"])),
        path=path,
        content=content,
        required_files=tuple(match.get("required_files", [])),
        any_files=tuple(match.get("any_files", [])),
    )


def _split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML-like frontmatter")
    end = raw.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter must end with ---")
    frontmatter = raw[4:end]
    content = raw[end + 5:]
    return _parse_simple_yaml(frontmatter), content


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    section: str | None = None
    list_key: str | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"invalid frontmatter line: {raw_line}")
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = _parse_scalar(value)
                section = None
            else:
                result[key] = {}
                section = key
            list_key = None
            continue

        if section != "match":
            raise ValueError(f"unsupported nested frontmatter section: {raw_line}")

        match = result.setdefault("match", {})
        if indent == 2:
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"invalid frontmatter line: {raw_line}")
            key = key.strip()
            value = value.strip()
            if value:
                match[key] = _parse_scalar(value)
                list_key = None
            else:
                match[key] = []
                list_key = key
            continue

        if indent == 4 and line.startswith("- ") and list_key:
            match[list_key].append(_parse_scalar(line[2:]))
            continue
        raise ValueError(f"unsupported frontmatter line: {raw_line}")

    return result


def _parse_scalar(value: str) -> str | int | bool:
    if value in {"true", "false"}:
        return value == "true"
    if value.isdigit():
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value
