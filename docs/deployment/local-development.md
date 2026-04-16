# Local Development Deployment

## Docker Compose Setup (Recommended)

### 1. Clone Repository

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow
```

### 2. Configure Environment

```bash
cd docker
cp .env.example .env
# Edit .env with your settings
```

**Essential variables:**
```bash
MYSQL_ROOT_PASSWORD=<strong_password>
MYSQL_PASSWORD=<strong_password>
MINIO_ROOT_PASSWORD=<strong_password>
OPENAI_API_KEY=<your_key>
```

### 3. Start Services

**CPU-only:**
```bash
docker compose -f docker-compose.yml up -d
```

**GPU-enabled (NVIDIA CUDA):**
```bash
docker compose -f docker-compose.yml --profile gpu up -d
```

**Backing services only (no RAGFlow server):**
```bash
docker compose -f docker-compose-base.yml up -d
```

### 4. Verify Services

```bash
docker compose ps

# Expected output:
# NAME                    STATUS
# ragflow-server         Up 2 minutes
# ragflow-admin          Up 2 minutes
# nginx                  Up 2 minutes
# mysql                  Up 2 minutes
# redis                  Up 2 minutes
# minio                  Up 2 minutes
# elasticsearch          Up 2 minutes
```

### 5. Access Application

**Web UI:** http://localhost  
**Admin API:** http://localhost:9381  
**API:** http://localhost:9380/api/v1  
**Swagger UI:** http://localhost/api/docs  

**Default Credentials:**
- User: `admin@ragflow.io`
- Password: `password123` (change immediately)

### 6. Verify Core Functionality

```bash
# Health check
curl http://localhost:9380/api/v1/health
# {"status": "ok", "version": "0.24.0"}

# Create test knowledge base
curl -X POST http://localhost:9380/api/v1/knowledgebases \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test KB"}'
```

### 7. Manage Services

```bash
# Stop all services
docker compose down

# Stop with volume deletion (data loss - be careful)
docker compose down -v

# View logs
docker logs -f ragflow-server

# Execute command in container
docker exec -it ragflow-server bash

# Update images
docker compose pull && docker compose up -d
```

## Local Python Development

For source code modifications:

```bash
# Install dependencies
uv sync --python 3.12 --all-extras

# Download required models/data
uv run download_deps.py

# Start backing services
docker compose -f docker/docker-compose-base.yml up -d

# Start Python API server
export PYTHONPATH=$(pwd)
source .venv/bin/activate
bash docker/launch_backend_service.sh

# In another terminal, start frontend
cd web
npm install
npm run dev
```

## Common Issues

**MySQL connection refused:**
```bash
docker compose up -d mysql
docker logs mysql
```

**Port already in use:**
```bash
# Change port in docker-compose.yml
# Or kill existing process:
lsof -i :9380 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
