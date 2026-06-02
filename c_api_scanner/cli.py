from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from c_api_scanner.workflow import build_graph


def configure_langsmith(project_name: str) -> None:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", project_name)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract C web API endpoints with directory skills.")
    parser.add_argument("project_root", help="C project root to scan")
    parser.add_argument("--output", "-o", default="output/api-report.json", help="Report output path")
    parser.add_argument("--format", choices=["json"], default="json", help="Report format")
    parser.add_argument("--langsmith-project", default="c-api-scanner", help="LangSmith trace project name")
    parser.add_argument("--no-langsmith", action="store_true", help="Disable LangSmith tracing env defaults")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"project root does not exist: {root}")
    if not args.no_langsmith:
        configure_langsmith(args.langsmith_project)

    compiled = build_graph()
    result = compiled.invoke(
        {"project_root": str(root)},
        {"configurable": {"thread_id": f"scan:{root.name}"}},
    )
    report = result["report"].to_dict()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
