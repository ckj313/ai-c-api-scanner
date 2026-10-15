void worker_process_client(struct client *c) {
    switch (c->http_method) {
    case HTTP_GET:
        cmd_run(c->w, c, 1+c->path, c->path_sz-1, NULL, 0);
        break;
    case HTTP_PUT:
        cmd_run(c->w, c, 1+c->path, c->path_sz-1, c->body, c->body_sz);
        break;
    case HTTP_POST:
        cmd_run(c->w, c, c->body, c->body_sz, NULL, 0);
        break;
    case HTTP_OPTIONS:
        http_send_options(c);
        break;
    }
    if (memcmp(c->path, "/crossdomain.xml", 16) == 0) {
        http_crossdomain(c);
    }
}
