#include <event2/http.h>

void install_routes(struct evhttp *base) {
    evhttp_set_cb(base, "/health", health_handler, NULL);
    if (mg_http_match_uri(c, "/metrics")) { serve_metrics(c); }
    const char *route = "/v1/items";
}
