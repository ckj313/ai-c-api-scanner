from __future__ import annotations

from pathlib import Path

from c_api_scanner.models import ApiEndpoint
from c_api_scanner.skill_document import SkillDocument, load_skill_documents
from c_api_scanner.skills import DirectorySkill, GenericCSkill, WebdisSkill


DEFAULT_SKILL_DOC_ROOT = Path(__file__).resolve().parent / "agent_skills"


class SkillRegistry:
    def __init__(
        self,
        skill_documents: list[SkillDocument],
        adapters: dict[str, DirectorySkill] | None = None,
    ) -> None:
        self.skill_documents = sorted(skill_documents, key=lambda skill: skill.priority, reverse=True)
        self.adapters = adapters or {
            "webdis": WebdisSkill(),
            "generic-c": GenericCSkill(),
        }

    @classmethod
    def default(cls) -> "SkillRegistry":
        return cls(load_skill_documents(DEFAULT_SKILL_DOC_ROOT))

    def select(self, directory: Path) -> SkillDocument:
        for skill in self.skill_documents:
            if skill.matches(directory):
                return skill
        fallback = next((skill for skill in self.skill_documents if skill.name == "generic-c"), None)
        if fallback:
            return fallback
        raise LookupError(f"no skill document matched {directory}")

    def extract_directory(self, directory: Path) -> list[ApiEndpoint]:
        skill = self.select(directory)
        adapter = self.adapters[skill.adapter]
        return [
            endpoint.with_context(skill=skill.name, skill_document=str(skill.path), directory=directory)
            for endpoint in adapter.extract(directory)
        ]
