from __future__ import annotations

import re
from pathlib import Path

from c_api_scanner.models import ApiEndpoint
from c_api_scanner.skills.base import DirectorySkill, iter_c_files, read_lines


class GenericCSkill(DirectorySkill):
    name = "generic-c"
    description = "Generic C web framework route registrations"
    priority = -100

    # Match code tokens with string/comment contents masked. The route literal is
    # read from the original line at the same offset after a pattern matches.
    _patterns = (
        (re.compile(r"\bevhttp_set_cb\s*\(\s*[^,]+,"), True),
        (re.compile(r"\bmg_http_match_uri\s*\(\s*[^,]+,"), False),
        (re.compile(r"\b(?:route|uri)\s*="), False),
    )
    _c_string = re.compile(r'\s*"((?:\\.|[^"\\])*)"')
    _handler = re.compile(r"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)")
    _non_api_prefixes = ("/tmp/", "/var/", "/usr/", "/etc/", "/dev/")

    def matches(self, directory: Path) -> bool:
        return bool(iter_c_files(directory))

    def extract(self, directory: Path) -> list[ApiEndpoint]:
        endpoints: list[ApiEndpoint] = []
        for source in iter_c_files(directory):
            lines = read_lines(source)
            masked_lines = _mask_c_comments_and_strings(lines)
            for line_no, line in enumerate(lines, start=1):
                masked = masked_lines[line_no - 1]
                for pattern, has_handler in self._patterns:
                    for match in pattern.finditer(masked):
                        path_match = self._c_string.match(line, match.end())
                        if not path_match:
                            continue
                        path = path_match.group(1)
                        if not path.startswith("/") or path.startswith(self._non_api_prefixes):
                            continue
                        handler = "unknown"
                        if has_handler:
                            handler_match = self._handler.match(line, path_match.end())
                            if not handler_match:
                                continue
                            handler = handler_match.group(1)
                        endpoints.append(
                            ApiEndpoint(
                                source_file=str(source),
                                line=line_no,
                                methods=["UNKNOWN"],
                                path=path,
                                handler=handler,
                                confidence=0.45,
                                evidence=line.strip(),
                                notes="generic route pattern",
                            )
                        )
        return endpoints


def _mask_c_comments_and_strings(lines: list[str]) -> list[str]:
    """Mask comments and literals while preserving columns and line numbers."""
    text = "\n".join(lines)
    masked = list(text)
    state = "code"
    escaped = False
    index = 0
    while index < len(text):
        current = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if current == "/" and following == "/":
                masked[index] = masked[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if current == "/" and following == "*":
                masked[index] = masked[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if current == '"':
                masked[index] = " "
                state = "string"
            elif current == "'":
                masked[index] = " "
                state = "char"
        elif state in {"string", "char"}:
            masked[index] = " "
            if escaped:
                escaped = False
            elif current == "\\":
                escaped = True
            elif (state == "string" and current == '"') or (state == "char" and current == "'"):
                state = "code"
        elif state == "line_comment":
            if current == "\n":
                state = "code"
            else:
                masked[index] = " "
        elif state == "block_comment":
            if current == "*" and following == "/":
                masked[index] = masked[index + 1] = " "
                state = "code"
                index += 2
                continue
            if current != "\n":
                masked[index] = " "
        index += 1
    return "".join(masked).splitlines()
