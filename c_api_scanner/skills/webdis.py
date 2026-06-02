from __future__ import annotations

from pathlib import Path

from c_api_scanner.models import ApiEndpoint
from c_api_scanner.skills.base import DirectorySkill, read_lines


class WebdisSkill(DirectorySkill):
    name = "webdis"
    description = "webdis dynamic Redis-over-HTTP and WebSocket command extractor"
    priority = 100

    def matches(self, directory: Path) -> bool:
        worker = directory / "worker.c"
        websocket = directory / "websocket.c"
        cmd_header = directory / "cmd.h"
        return worker.exists() and websocket.exists() and cmd_header.exists()

    def extract(self, directory: Path) -> list[ApiEndpoint]:
        endpoints: list[ApiEndpoint] = []
        worker = directory / "worker.c"
        websocket = directory / "websocket.c"
        if worker.exists():
            endpoints.extend(self._extract_worker(worker))
        if websocket.exists():
            endpoints.extend(self._extract_websocket(websocket))
        return endpoints

    def _extract_worker(self, source: Path) -> list[ApiEndpoint]:
        lines = read_lines(source)
        endpoints: list[ApiEndpoint] = []
        methods_for_path: set[str] = set()
        path_line = 0
        post_line = 0
        crossdomain_line = 0
        options_line = 0

        for index, line in enumerate(lines, start=1):
            if "case HTTP_GET" in line or "case HTTP_PUT" in line:
                current_method = "GET" if "HTTP_GET" in line else "PUT"
                for lookahead in lines[index - 1:index + 12]:
                    if "cmd_run" in lookahead and "c->path" in lookahead:
                        methods_for_path.add(current_method)
                        path_line = path_line or index
                        break
            if "case HTTP_POST" in line:
                for lookahead in lines[index - 1:index + 8]:
                    if "cmd_run" in lookahead and "c->body" in lookahead:
                        post_line = index
                        break
            if "/crossdomain.xml" in line:
                crossdomain_line = index
            if "case HTTP_OPTIONS" in line:
                options_line = index

        if methods_for_path:
            endpoints.append(
                ApiEndpoint(
                    source_file=str(source),
                    line=path_line,
                    methods=sorted(methods_for_path),
                    path="/{redis-command}[/{arg}...]",
                    handler="worker_process_client -> cmd_run(path)",
                    confidence=0.92,
                    evidence="cmd_run(c->w, c, 1+c->path, c->path_sz-1, ...)",
                    notes="Dynamic Redis command API encoded in HTTP path.",
                )
            )
        if post_line:
            endpoints.append(
                ApiEndpoint(
                    source_file=str(source),
                    line=post_line,
                    methods=["POST"],
                    path="/{request-body redis-command}",
                    handler="worker_process_client -> cmd_run(body)",
                    confidence=0.9,
                    evidence="cmd_run(c->w, c, c->body, c->body_sz, ...)",
                    notes="POST body is parsed as the Redis command payload.",
                )
            )
        if crossdomain_line:
            endpoints.append(
                ApiEndpoint(
                    source_file=str(source),
                    line=crossdomain_line,
                    methods=["GET"],
                    path="/crossdomain.xml",
                    handler="http_crossdomain",
                    confidence=0.95,
                    evidence='memcmp(c->path, "/crossdomain.xml", 16)',
                    notes="Static policy endpoint.",
                )
            )
        if options_line:
            endpoints.append(
                ApiEndpoint(
                    source_file=str(source),
                    line=options_line,
                    methods=["OPTIONS"],
                    path="/*",
                    handler="http_send_options",
                    confidence=0.82,
                    evidence="case HTTP_OPTIONS: http_send_options(c)",
                    notes="CORS/preflight handler.",
                )
            )
        return endpoints

    def _extract_websocket(self, source: Path) -> list[ApiEndpoint]:
        lines = read_lines(source)
        endpoints: list[ApiEndpoint] = []
        for index, line in enumerate(lines, start=1):
            if 'strncmp(c->path, "/.json"' in line:
                endpoints.append(
                    ApiEndpoint(
                        source_file=str(source),
                        line=index,
                        methods=["WEBSOCKET"],
                        path="/.json websocket",
                        handler="ws_execute -> json_ws_extract",
                        confidence=0.9,
                        evidence=line.strip(),
                        notes="WebSocket JSON command format selector.",
                    )
                )
            if 'strncmp(c->path, "/.raw"' in line:
                endpoints.append(
                    ApiEndpoint(
                        source_file=str(source),
                        line=index,
                        methods=["WEBSOCKET"],
                        path="/.raw websocket",
                        handler="ws_execute -> raw_ws_extract",
                        confidence=0.9,
                        evidence=line.strip(),
                        notes="WebSocket raw command format selector.",
                    )
                )
        return endpoints
