from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated, TypedDict

from c_api_scanner.deep_agent import SkillDispatchAgent
from c_api_scanner.models import ApiEndpoint, ScanReport


class ScanState(TypedDict, total=False):
    project_root: str
    directories: list[str]
    scanned_directories: Annotated[list[str], operator.add]
    endpoints: Annotated[list[ApiEndpoint], operator.add]
    warnings: Annotated[list[str], operator.add]
    report: ScanReport


def discover_directories(state: ScanState) -> dict[str, list[str]]:
    root = Path(state["project_root"]).resolve()
    directories: list[str] = []
    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if any(part in {".git", "__pycache__", "node_modules"} for part in directory.parts):
            continue
        has_c = any(child.is_file() and child.suffix.lower() in {".c", ".h"} for child in directory.iterdir())
        if has_c:
            directories.append(str(directory))
    return {"directories": directories}


def extract_with_skills(state: ScanState) -> dict[str, list[ApiEndpoint] | list[str]]:
    dispatcher = SkillDispatchAgent()
    endpoints: list[ApiEndpoint] = []
    warnings: list[str] = []
    scanned: list[str] = []
    for directory in state.get("directories", []):
        try:
            result = dispatcher.invoke_skill(directory)
            scanned.append(directory)
            endpoints.extend(
                ApiEndpoint(**endpoint)
                for endpoint in result["endpoints"]
            )
        except Exception as exc:
            warnings.append(f"{directory}: {exc}")
    return {"endpoints": endpoints, "warnings": warnings, "scanned_directories": scanned}


def build_report(state: ScanState) -> dict[str, ScanReport]:
    return {
        "report": ScanReport(
            project_root=str(Path(state["project_root"]).resolve()),
            endpoints=state.get("endpoints", []),
            scanned_directories=state.get("scanned_directories", []),
            warnings=state.get("warnings", []),
        )
    }


class _FallbackGraph:
    def invoke(self, inputs: ScanState, config: dict | None = None) -> ScanState:
        state: ScanState = dict(inputs)
        state.update(discover_directories(state))
        state.update(extract_with_skills(state))
        state.update(build_report(state))
        return state


def build_graph():
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception:
        return _FallbackGraph()

    graph = StateGraph(ScanState)
    graph.add_node("discover_directories", discover_directories)
    graph.add_node("extract_with_deepagents_skill_dispatch", extract_with_skills)
    graph.add_node("build_report", build_report)
    graph.add_edge(START, "discover_directories")
    graph.add_edge("discover_directories", "extract_with_deepagents_skill_dispatch")
    graph.add_edge("extract_with_deepagents_skill_dispatch", "build_report")
    graph.add_edge("build_report", END)
    return graph.compile(name="c-api-scanner")


graph = build_graph()
