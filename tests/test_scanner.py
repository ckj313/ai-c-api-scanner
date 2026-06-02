import json
import tempfile
import unittest
from pathlib import Path

from c_api_scanner.registry import SkillRegistry


class ScannerTests(unittest.TestCase):
    def test_registry_uses_directory_specific_skill(self) -> None:
        repo = Path(__file__).resolve().parents[1] / "fixtures" / "webdis"
        if not repo.exists():
            self.skipTest("webdis fixture is not cloned")
        registry = SkillRegistry.default()

        skill = registry.select(repo / "src")

        self.assertEqual(skill.name, "webdis")
        self.assertEqual(skill.adapter, "webdis")
        self.assertEqual(skill.path.name, "SKILL.md")
        self.assertIn("Redis-over-HTTP", skill.content)

    def test_webdis_skill_extracts_dynamic_http_and_websocket_apis(self) -> None:
        repo = Path(__file__).resolve().parents[1] / "fixtures" / "webdis"
        if not repo.exists():
            self.skipTest("webdis fixture is not cloned")

        registry = SkillRegistry.default()
        endpoints = registry.extract_directory(repo / "src")
        paths = {endpoint.path for endpoint in endpoints}
        methods_by_path = {endpoint.path: set(endpoint.methods) for endpoint in endpoints}

        self.assertIn("/{redis-command}[/{arg}...]", paths)
        self.assertTrue({"GET", "PUT"}.issubset(methods_by_path["/{redis-command}[/{arg}...]"]))
        self.assertIn("/{request-body redis-command}", paths)
        self.assertIn("POST", methods_by_path["/{request-body redis-command}"])
        self.assertIn("/crossdomain.xml", paths)
        self.assertIn("/.json websocket", paths)
        self.assertIn("/.raw websocket", paths)

    def test_cli_writes_json_report(self) -> None:
        from c_api_scanner.cli import main

        repo = Path(__file__).resolve().parents[1] / "fixtures" / "webdis"
        if not repo.exists():
            self.skipTest("webdis fixture is not cloned")
        with tempfile.TemporaryDirectory() as raw_dir:
            out = Path(raw_dir) / "report.json"

            exit_code = main([str(repo), "--output", str(out), "--format", "json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(payload["project_root"].endswith("fixtures/webdis"))
            self.assertGreaterEqual(payload["summary"]["endpoint_count"], 4)
            self.assertTrue(any(item["skill"] == "webdis" for item in payload["endpoints"]))
            self.assertTrue(all(item["skill_document"].endswith("webdis/SKILL.md") for item in payload["endpoints"] if item["skill"] == "webdis"))


if __name__ == "__main__":
    unittest.main()
