import tempfile
import unittest
from pathlib import Path

from c_api_scanner.skills.generic_c import GenericCSkill


class GenericCSkillTests(unittest.TestCase):
    def test_extracts_supported_route_registration_patterns(self) -> None:
        source = """\
#include <event2/http.h>

void install_routes(struct evhttp *base) {
    evhttp_set_cb(base, "/health", health_handler, NULL);
    if (mg_http_match_uri(c, "/metrics")) { serve_metrics(c); }
    const char *route = "/v1/items";
}
"""
        endpoints = self._extract(source)

        self.assertEqual(
            {(endpoint.path, endpoint.handler) for endpoint in endpoints},
            {
                ("/health", "health_handler"),
                ("/metrics", "unknown"),
                ("/v1/items", "unknown"),
            },
        )
        self.assertEqual([endpoint.line for endpoint in endpoints], [4, 5, 6])
        self.assertTrue(all(endpoint.methods == ["UNKNOWN"] for endpoint in endpoints))
        self.assertTrue(all(endpoint.confidence == 0.45 for endpoint in endpoints))

    def test_ignores_comments_quoted_examples_and_non_api_filesystem_paths(self) -> None:
        source = r'''\
// evhttp_set_cb(base, "/commented", comment_handler, NULL);
/* mg_http_match_uri(c, "/also-commented") */
const char *log_message = "route = \"/quoted-example\"";
const char *file_path = "/tmp/secret.sock";
const char *resource = "/var/lib/data";
const char *unrelated = "/looks-like-a-route";
'''

        self.assertEqual(self._extract(source), [])

    def test_malformed_and_unrelated_registration_lookalikes_are_not_routes(self) -> None:
        source = """\
evhttp_set_cb(base, health_handler, "/wrong-argument-order", NULL);
mg_http_match_uri(c, route_name);
const char *not_route = "/not-a-route";
uri = get_uri();
"""

        self.assertEqual(self._extract(source), [])

    def _extract(self, source: str):
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            (directory / "routes.c").write_text(source, encoding="utf-8")
            return GenericCSkill().extract(directory)


if __name__ == "__main__":
    unittest.main()
