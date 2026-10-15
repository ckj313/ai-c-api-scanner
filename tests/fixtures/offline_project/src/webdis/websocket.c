void ws_execute(struct client *c) {
    if (strncmp(c->path, "/.json", 6) == 0) {
        json_ws_extract(c);
    }
    if (strncmp(c->path, "/.raw", 5) == 0) {
        raw_ws_extract(c);
    }
}
