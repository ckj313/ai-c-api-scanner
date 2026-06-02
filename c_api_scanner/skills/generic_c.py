from __future__ import annotations

import re
from pathlib import Path

from c_api_scanner.models import ApiEndpoint
from c_api_scanner.skills.base import DirectorySkill, iter_c_files, read_lines


class GenericCSkill(DirectorySkill):
    name = "generic-c"
    description = "Generic C web framework route registrations"
    priority = -100

    _patterns = [
        re.compile(r'evhttp_set_cb\s*\([^,]+,\s*"(?P<path>[^"]+)"\s*,\s*(?P<handler>[A-Za-z_][A-Za-z0-9_]*)'),
        re.compile(r'mg_http_match_uri\s*\([^,]+,\s*"(?P<path>[^"]+)"'),
        re.compile(r'(?:route|uri)\s*=\s*"(?P<path>/[^"]*)"'),
    ]
    _non_api_prefixes = ("/tmp/", "/var/", "/usr/", "/etc/", "/dev/")

    def matches(self, directory: Path) -> bool:
        return bool(iter_c_files(directory))

    def extract(self, directory: Path) -> list[ApiEndpoint]:
        endpoints: list[ApiEndpoint] = []
        for source in iter_c_files(directory):
            lines = read_lines(source)
            for line_no, line in enumerate(lines, start=1):
                for pattern in self._patterns:
                    match = pattern.search(line)
                    if not match:
                        continue
                    if match.group("path").startswith(self._non_api_prefixes):
                        continue
                    handler = match.groupdict().get("handler") or "unknown"
                    endpoints.append(
                        ApiEndpoint(
                            source_file=str(source),
                            line=line_no,
                            methods=["UNKNOWN"],
                            path=match.group("path"),
                            handler=handler,
                            confidence=0.45,
                            evidence=line.strip(),
                            notes="generic route pattern",
                        )
                    )
        return endpoints
