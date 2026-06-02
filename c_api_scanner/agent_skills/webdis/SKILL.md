---
name: webdis
description: Extract Webdis Redis-over-HTTP and WebSocket API surfaces from the src directory.
priority: 100
adapter: webdis
match:
  required_files:
    - worker.c
    - websocket.c
    - cmd.h
---

# Webdis Redis-over-HTTP C API Extraction Skill

Use this skill when a directory contains the Webdis request dispatcher:

- `worker.c`
- `websocket.c`
- `cmd.h`

The API surface is dynamic. Do not look for a fixed REST route table. Webdis exposes Redis commands through HTTP paths, request bodies, and WebSocket message formats.

## Extraction Rules

1. Inspect `worker_process_client` in `worker.c`.
2. Treat `case HTTP_GET` followed by `cmd_run(..., 1+c->path, c->path_sz-1, ...)` as:
   - method: `GET`
   - path: `/{redis-command}[/{arg}...]`
3. Treat `case HTTP_PUT` followed by `cmd_run(..., 1+c->path, c->path_sz-1, ..., c->body, c->body_sz)` as:
   - method: `PUT`
   - path: `/{redis-command}[/{arg}...]`
4. Treat `case HTTP_POST` followed by `cmd_run(..., c->body, c->body_sz, ...)` as:
   - method: `POST`
   - path: `/{request-body redis-command}`
5. Treat the `/crossdomain.xml` comparison as a static `GET /crossdomain.xml` endpoint.
6. Treat `case HTTP_OPTIONS` followed by `http_send_options(c)` as `OPTIONS /*`.
7. Inspect `ws_execute` in `websocket.c`.
8. Treat `strncmp(c->path, "/.json", 6)` as `WEBSOCKET /.json websocket`.
9. Treat `strncmp(c->path, "/.raw", 5)` as `WEBSOCKET /.raw websocket`.

## Output Requirements

Return JSON-compatible endpoint records. Every endpoint must include:

- `source_file`
- `line`
- `methods`
- `path`
- `handler`
- `confidence`
- `evidence`
- `notes`

Evidence must quote or summarize the C condition or call that proves the endpoint. Prefer dynamic route descriptions over fabricated concrete Redis command examples.
