# Configuration Management

## Environment Variables

Create `.env` file in `docker/` directory:

```bash
# Core Settings
API_PROXY_SCHEME=python              # python, go, or hybrid
RAGFLOW_VERSION=0.24.0
ENVIRONMENT=production               # development, staging, production

# Database
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=ragflow
MYSQL_ROOT_PASSWORD=<strong_password>
MYSQL_USER=ragflow
MYSQL_PASSWORD=<strong_password>

# Search Engine
DOC_ENGINE=elasticsearch            # elasticsearch, infinity, opensearch
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200

# Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<strong_password>
MINIO_BUCKET=ragflow
MINIO_ENDPOINT=http://minio:9000

# Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<optional>

# LLM Configuration
OPENAI_API_KEY=<your_key>
OPENAI_BASE_URL=https://api.openai.com/v1

# Application
SECRET_KEY=<generate_random_32_chars>
JWT_SECRET=<generate_random_32_chars>
DEBUG=false

# Nginx
NGINX_PORT=80
NGINX_SSL_PORT=443
ENABLE_SSL=false

# Logging
LOG_LEVEL=INFO
```

## Service Configuration

**docker/service_conf.yaml:**
```yaml
database:
  driver: mysql
  host: ${MYSQL_HOST}
  port: ${MYSQL_PORT}
  database: ${MYSQL_DATABASE}
  user: ${MYSQL_USER}
  password: ${MYSQL_PASSWORD}

search_engine:
  engine: ${DOC_ENGINE}
  endpoint: ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}

storage:
  type: minio
  endpoint: ${MINIO_ENDPOINT}
  bucket: ${MINIO_BUCKET}
  access_key: ${MINIO_ROOT_USER}
  secret_key: ${MINIO_ROOT_PASSWORD}

cache:
  type: redis
  host: ${REDIS_HOST}
  port: ${REDIS_PORT}

llm:
  default_chat_model: gpt-4
  default_embedding_model: text-embedding-3-small
  embedding_batch_size: 100
```

## Switching Document Engines

**From Elasticsearch to Infinity:**

```bash
# 1. Set environment variable
export DOC_ENGINE=infinity

# 2. Restart containers
docker compose down
docker compose up -d

# 3. Verify connection
curl http://localhost:9380/api/v1/health
```

**From Python API to Go API:**

```bash
# 1. Update proxy scheme
export API_PROXY_SCHEME=go

# 2. Restart services
docker compose down
docker compose up -d
```

## Multi-Environment Compose Files

```bash
# Development (verbose logging, hot reload)
docker compose -f docker-compose.yml \
  -f docker-compose.dev.yml up

# Staging (similar to production)
docker compose -f docker-compose.yml \
  -f docker-compose.staging.yml up -d

# Production (scale services, resource limits)
docker compose -f docker-compose.yml \
  -f docker-compose.prod.yml up -d
```

## Building Custom Images

```bash
# Build for local architecture
docker build -f Dockerfile -t my-ragflow:latest .

# Build for specific platform
docker build --platform linux/amd64 \
  -f Dockerfile \
  -t infiniflow/ragflow:custom .

# Push to registry
docker tag my-ragflow:latest my-registry/ragflow:latest
docker push my-registry/ragflow:latest
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
