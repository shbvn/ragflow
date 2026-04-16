# Deployment Guide

Deploy RAGFlow v0.24.0 in various environments: local development, Docker Compose, and Kubernetes (production).

## Quick Start

**Local Development (Docker Compose):**
```bash
cd docker
cp .env.example .env
docker compose up -d
# Access at http://localhost
```

**Kubernetes (Production):**
```bash
helm repo add ragflow https://charts.ragflow.io
helm install ragflow ragflow/ragflow -n ragflow -f values-prod.yaml
```

## Deployment Guides

- [Local Development](./local-development.md) — Docker Compose setup
- [Docker Deployment](./docker-deployment.md) — Building custom images, multi-environment configs
- [Kubernetes Deployment](./kubernetes-deployment.md) — Helm charts, scaling, migrations
- [Configuration](./configuration.md) — Environment variables, service settings
- [Backup & Recovery](./backup-and-recovery.md) — Database backups, snapshots, restoration
- [Monitoring & Health](./monitoring-health.md) — Health checks, Prometheus metrics, logging
- [Troubleshooting](./troubleshooting.md) — Common issues and solutions
- [Security Hardening](./security-hardening.md) — SSL, network policies, encryption
- [Performance Tuning](./performance-tuning.md) — Database optimization, Elasticsearch tuning
- [Maintenance & Updates](./maintenance-updates.md) — Version upgrades, regular tasks

## System Requirements

**Development:**
- CPU: 4+ cores
- RAM: 8GB minimum
- Disk: 50GB free
- Docker & Docker Compose v2.0+

**Production (Single Node):**
- CPU: 8+ cores
- RAM: 32GB minimum
- Disk: 500GB+ (SSD)
- Network: 100Mbps+

**Kubernetes Cluster:**
- 3+ worker nodes
- 16GB RAM per node
- Kubernetes 1.24+
- Helm 3.0+

## Supported Environments
- Linux (Ubuntu 20.04+, CentOS 8+)
- macOS (Intel & Apple Silicon)
- Windows (WSL2)
- Docker (CPU & GPU profiles)
- Kubernetes (all versions 1.24+)

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
