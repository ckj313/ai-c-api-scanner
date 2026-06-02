---
name: generic-c
description: Fallback extractor for common C HTTP route registration patterns.
priority: -100
adapter: generic-c
match:
  any_files:
    - api.c
    - routes.c
    - router.c
    - server.c
    - http.c
---

# Generic C Route Extraction Skill

Use this skill only when no more specific directory skill matches.

## Extraction Rules

Look for explicit HTTP route registration or route matching patterns, including:

- `evhttp_set_cb(base, "/path", handler, ...)`
- `mg_http_match_uri(connection, "/path")`
- assignments to variables named `route` or `uri`

Avoid filesystem paths such as `/tmp/...`, `/var/...`, `/usr/...`, `/etc/...`, and `/dev/...`; these are not Web API endpoints.

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

Use `UNKNOWN` for method when the C pattern does not prove the method.
