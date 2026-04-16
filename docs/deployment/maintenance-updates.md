# Maintenance & Updates

## Regular Maintenance Tasks

### Weekly
- Review error logs, address critical issues
- Verify backup integrity
- Check disk space usage

### Monthly
- Update dependencies: `docker pull infiniflow/ragflow:0.24.0`
- Review performance metrics
- Clean up old task logs

**Clean task logs:**
```bash
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "DELETE FROM task WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);"
```

### Quarterly
- Full system audit
- Security vulnerability scanning
- Disaster recovery drill

## Version Upgrade

### Backup Before Upgrade

```bash
# 1. Backup database
docker exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow > backup-v0.23.sql

# 2. Backup Elasticsearch indices
curl -X PUT "localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{"type": "fs", "settings": {"location": "/mnt/backups"}}'

curl -X PUT "localhost:9200/_snapshot/backup/pre-upgrade" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "*"}'

# 3. Export configuration
cp docker/.env docker/.env.backup
docker compose config > docker-compose.backup.yml
```

### Upgrade Process

**From v0.23 to v0.24:**

```bash
# 1. Stop application
docker compose down

# 2. Update image
sed -i 's/0.23.0/0.24.0/g' docker-compose.yml
docker compose pull

# 3. Start services (runs migrations automatically)
docker compose up -d

# 4. Verify migration
sleep 30
docker logs ragflow-server | grep -i "migration\|upgrade"

# 5. Test functionality
curl http://localhost:9380/api/v1/health

# 6. If issues, rollback to backup
docker compose down
# Restore from backup
docker exec -i mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow < backup-v0.23.sql
docker compose up -d
```

## Kubernetes Updates

```bash
# Check for chart updates
helm search repo ragflow

# Upgrade to new version
helm upgrade ragflow ragflow/ragflow \
  -n ragflow \
  -f values-prod.yaml

# Watch rollout
kubectl rollout status deployment/ragflow -n ragflow

# Rollback if needed
helm rollback ragflow 1 -n ragflow
```

## Dependency Updates

**Python dependencies:**
```bash
# Check for outdated packages
uv pip list --outdated

# Update specific package
uv pip install --upgrade numpy

# Update all (use cautiously)
uv pip install --upgrade --all
```

**Node.js dependencies:**
```bash
# Check for outdated packages
npm outdated

# Update specific package
npm install express@latest

# Update all (run tests after)
npm upgrade
```

## Performance Optimization

### Database Maintenance

```bash
# Analyze table statistics
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "ANALYZE TABLE document, chunk, message;"

# Optimize tables (may lock tables)
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "OPTIMIZE TABLE document, chunk, message;"

# Check index usage
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "SELECT * FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = 'ragflow' ORDER BY SEQ_IN_INDEX;"
```

### Elasticsearch Maintenance

```bash
# Optimize index (reduce segment count)
curl -X POST "localhost:9200/ragflow-chunks/_forcemerge?max_num_segments=1"

# Shrink old indices
curl -X POST "localhost:9200/ragflow-chunks/_shrink/ragflow-chunks-optimized"

# Delete old indices
curl -X DELETE "localhost:9200/ragflow-chunks-old-*"
```

### Cache Cleanup

```bash
# Monitor Redis memory
docker exec redis redis-cli INFO memory

# Clear old cache entries
docker exec redis redis-cli FLUSHDB

# Set max memory policy
docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Capacity Planning

### Monitor Growth

```bash
# Database size
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb FROM information_schema.TABLES WHERE table_schema = 'ragflow';"

# Elasticsearch size
curl "localhost:9200/_cat/indices?v"

# Disk usage
docker exec ragflow-server df -h
```

### Scaling Decisions

| Metric | Threshold | Action |
|--------|-----------|--------|
| Database size | >100GB | Add read replicas, consider sharding |
| Search latency | >2s | Add ES replicas, increase shards |
| Memory usage | >80% | Increase resources, reduce cache |
| CPU usage | >70% sustained | Add worker replicas (Kubernetes) |

## Support & Documentation

**Official Resources:**
- Documentation: https://docs.ragflow.io
- GitHub Issues: https://github.com/infiniflow/ragflow/issues
- Community: https://discord.gg/ragflow
- Commercial Support: https://www.ragflow.io/pricing

**Reporting Issues:**
```bash
# Collect diagnostic bundle
mkdir /tmp/ragflow-diag
docker logs ragflow-server > /tmp/ragflow-diag/server.log 2>&1
docker logs mysql > /tmp/ragflow-diag/mysql.log 2>&1
docker stats --no-stream > /tmp/ragflow-diag/stats.txt
df -h > /tmp/ragflow-diag/disk.txt
docker ps -a > /tmp/ragflow-diag/containers.txt
tar -czf ragflow-diag-$(date +%Y%m%d).tar.gz /tmp/ragflow-diag/
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
