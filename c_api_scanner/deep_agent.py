from __future__ import annotations

from pathlib import Path
from typing import Any

from c_api_scanner.registry import SkillRegistry


class SkillDispatchAgent:
    """Small deterministic dispatcher mirroring the DeepAgents tool boundary."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self.registry = registry or SkillRegistry.default()

    def invoke_skill(self, directory: str) -> dict[str, Any]:
        path = Path(directory)
        skill = self.registry.select(path)
        endpoints = self.registry.extract_directory(path)
        return {
            "directory": str(path),
            "skill": skill.name,
            "skill_document": str(skill.path),
            "skill_instructions": skill.content,
            "endpoint_count": len(endpoints),
            "endpoints": [endpoint.to_dict() for endpoint in endpoints],
        }


def build_deep_agent(model: str | None = None, registry: SkillRegistry | None = None) -> Any:
    """Build a DeepAgents agent when installed, otherwise return the local dispatcher.

    The deterministic fallback keeps CI and scheduled scans usable without API keys.
    Installing `deepagents` enables a Studio-visible agent wrapper with the same
    skill-dispatch tool.
    """

    dispatcher = SkillDispatchAgent(registry)
    try:
        from deepagents import create_deep_agent
    except Exception:
        return dispatcher

    def extract_directory_api(directory: str) -> dict[str, Any]:
        """Select the best Markdown skill document and extract C web API endpoints."""
        return dispatcher.invoke_skill(directory)

    return create_deep_agent(
        model=model or "openai:gpt-5.4-mini",
        tools=[extract_directory_api],
        system_prompt=(
            "You are a C web API extraction agent. For each source directory, call "
            "extract_directory_api. That tool selects the matching Markdown SKILL.md "
            "document and returns the instructions plus extracted endpoints. Preserve "
            "file, line, method, path, handler, confidence, evidence, skill, and "
            "skill_document exactly."
        ),
        subagents=[
            {
                "name": "directory-skill-dispatcher",
                "description": "Selects and runs the correct extraction skill for a C source directory.",
                "tools": [extract_directory_api],
            }
        ],
    )
