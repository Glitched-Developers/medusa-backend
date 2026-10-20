"""Prometheus metrics for API, cache, and schedule refresh operations."""

from prometheus_client import Counter, Histogram, make_asgi_app

api_requests = Counter("medusa_api_requests_total", "API requests", ["method", "path", "status"])
upstream_requests = Counter("medusa_upstream_requests_total", "Upstream requests", ["resource", "result"])
cache_operations = Counter("medusa_cache_operations_total", "Cache operations", ["operation", "result"])
schedule_updates = Counter("medusa_schedule_updates_total", "Schedule refreshes", ["result"])
upstream_latency = Histogram("medusa_upstream_request_duration_seconds", "Upstream request duration", ["resource"])

metrics_app = make_asgi_app()
