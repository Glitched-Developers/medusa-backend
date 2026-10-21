"""Prometheus metrics exposed by the Medusa Backend.

The application exports these metrics through ``GET /metrics``. Prometheus
scrapes that endpoint; this module does not persist metric samples itself.
"""

from prometheus_client import Counter, Histogram, make_asgi_app

# Total API responses, partitioned by HTTP method, route, and status code.
api_requests = Counter(
    "medusa_api_requests_total", "API requests", ["method", "path", "status"]
)
# Total requests sent to the BSU upstream service and their outcomes.
upstream_requests = Counter(
    "medusa_upstream_requests_total", "Upstream requests", ["resource", "result"]
)
# Cache reads and writes, partitioned by operation and outcome.
cache_operations = Counter(
    "medusa_cache_operations_total", "Cache operations", ["operation", "result"]
)
# Cache hit/miss tracking for schedule and week lookups.
cache_hits = Counter(
    "medusa_cache_hits_total", "Cache hits", ["cache_type"]
)
cache_misses = Counter(
    "medusa_cache_misses_total", "Cache misses", ["cache_type"]
)
# Completed background schedule refreshes, partitioned by outcome.
schedule_updates = Counter(
    "medusa_schedule_updates_total", "Schedule refreshes", ["result"]
)
# Duration of upstream requests in seconds, partitioned by resource.
upstream_latency = Histogram(
    "medusa_upstream_request_duration_seconds",
    "Upstream request duration",
    ["resource"],
)

metrics_app = make_asgi_app()
