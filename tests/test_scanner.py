import json
import tempfile
import unittest
from pathlib import Path

from c_api_scanner.registry import SkillRegistry


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "offline_project"


class ScannerTests(unittest.TestCase):
    def test_registry_selects_directory_specific_and_fallback_skills(self) -> None:
        registry = SkillRegistry.default()

        webdis_skill = registry.select(FIXTURE_ROOT / "src" / "webdis")
        generic_skill = registry.select(FIXTURE_ROOT / "src" / "generic")

        self.assertEqual((webdis_skill.name, webdis_skill.adapter), ("webdis", "webdis"))
        self.assertIn("Redis-over-HTTP", webdis_skill.content)
        self.assertEqual((generic_skill.name, generic_skill.adapter), ("generic-c", "generic-c"))
        self.assertIn("Generic C Route Extraction Skill", generic_skill.content)

    def test_webdis_skill_extracts_http_and_websocket_apis_from_local_sample(self) -> None:
        registry = SkillRegistry.default()
        endpoints = registry.extract_directory(FIXTURE_ROOT / "src" / "webdis")
        endpoints_by_route = {(endpoint.path, method) for endpoint in endpoints for method in endpoint.methods}

        expected = {
            ("/{redis-command}[/{arg}...]", "GET"),
            ("/{redis-command}[/{arg}...]", "PUT"),
            ("/{request-body redis-command}", "POST"),
            ("/crossdomain.xml", "GET"),
            ("/*", "OPTIONS"),
            ("/.json websocket", "WEBSOCKET"),
            ("/.raw websocket", "WEBSOCKET"),
        }
        self.assertEqual(endpoints_by_route, expected)
        self.assertTrue(all(endpoint.skill == "webdis" for endpoint in endpoints))
        self.assertTrue(all(endpoint.skill_document.endswith("webdis/SKILL.md") for endpoint in endpoints))
        self.assertTrue(all(endpoint.evidence for endpoint in endpoints))

    def test_cli_writes_json_report_for_offline_project(self) -> None:
        from c_api_scanner.cli import main

        with tempfile.TemporaryDirectory() as raw_dir:
            output = Path(raw_dir) / "reports" / "api-report.json"

            exit_code = main([str(FIXTURE_ROOT), "--output", str(output), "--format", "json", "--no-langsmith"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["project_root"], str(FIXTURE_ROOT.resolve()))
            self.assertEqual(payload["summary"]["warning_count"], 0)
            self.assertEqual(payload["summary"]["endpoint_count"], 9)
            self.assertEqual(
                {item["skill"] for item in payload["endpoints"]},
                {"webdis", "generic-c"},
            )
            self.assertEqual(
                sum(item["skill"] == "webdis" for item in payload["endpoints"]),
                6,
            )
            report_routes = {
                (item["path"], method)
                for item in payload["endpoints"]
                for method in item["methods"]
            }
            self.assertEqual(
                report_routes,
                {
                    ("/{redis-command}[/{arg}...]", "GET"),
                    ("/{redis-command}[/{arg}...]", "PUT"),
                    ("/{request-body redis-command}", "POST"),
                    ("/crossdomain.xml", "GET"),
                    ("/*", "OPTIONS"),
                    ("/.json websocket", "WEBSOCKET"),
                    ("/.raw websocket", "WEBSOCKET"),
                    ("/health", "UNKNOWN"),
                    ("/metrics", "UNKNOWN"),
                    ("/v1/items", "UNKNOWN"),
                },
            )
            self.assertTrue(all(item["source_file"] and item["line"] > 0 for item in payload["endpoints"]))


if __name__ == "__main__":
    unittest.main()
