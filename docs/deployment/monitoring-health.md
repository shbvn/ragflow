# Monitoring & Health Checks

## Health Check Endpoints

```bash
# API health
curl http://localhost:9380/api/v1/health
# Response: {"status": "ok", "version": "0.24.0"}

# Database connectivity
curl http://localhost:9380/api/v1/system/health
# Response: {"db": "ok", "cache": "ok", "search": "ok"}

# Service status
curl http://localhost:9380/api/v1/system/status
# Response: detailed service statuses
```

## Docker Health Checks

```yaml
# docker-compose.yml
services:
  ragflow-server:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9380/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Kubernetes Liveness/Readiness

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 9380
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/system/health
    port: 9380
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Prometheus Metrics

Enable Prometheus scraping:

```yaml
# service_conf.yaml
prometheus:
  enabled: true
  port: 9090
  metrics:
    - api_requests_total
    - api_response_time_seconds
    - embedding_queue_size
    - search_latency_seconds
```

Access metrics at `http://localhost:9090/metrics`

## Logging

```bash
# View application logs with filtering
docker logs -f ragflow-server | grep -i "error\|warning"

# Export logs to file
docker logs ragflow-server > /tmp/ragflow.log 2>&1

# Real-time tail in Kubernetes
kubectl logs -f deployment/ragflow -n ragflow

# Historical logs (last 1 hour)
kubectl logs --since=1h deployment/ragflow -n ragflow
```

## Alerting Setup

**Prometheus alerts (prometheus-rules.yaml):**
```yaml
groups:
  - name: ragflow
    rules:
      - alert: HighSearchLatency
        expr: histogram_quantile(0.95, search_latency_seconds) > 1
        for: 5m
        annotations:
          summary: "Search latency exceeds 1s"
      
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "API error rate exceeds 1%"
      
      - alert: ElasticsearchDown
        expr: up{job="elasticsearch"} == 0
        for: 1m
        annotations:
          summary: "Elasticsearch is down"
```

## Monitoring Dashboard

**Grafana dashboard configuration:**
```json
{
  "dashboard": {
    "title": "RAGFlow Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{"expr": "rate(api_requests_total[1m])"}]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{"expr": "histogram_quantile(0.95, api_response_time_seconds)"}]
      },
      {
        "title": "Search Latency",
        "targets": [{"expr": "histogram_quantile(0.95, search_latency_seconds)"}]
      },
      {
        "title": "Embedding Queue Size",
        "targets": [{"expr": "embedding_queue_size"}]
      }
    ]
  }
}
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
