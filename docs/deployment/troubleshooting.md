# Troubleshooting

## Common Issues

### Issue 1: MySQL Connection Refused

**Diagnosis:**
```bash
docker ps | grep mysql
docker logs mysql
docker exec -it ragflow-server \
  mysql -h mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"
```

**Solutions:**
- Ensure MySQL service is running: `docker compose up -d mysql`
- Check credentials in `.env`
- Verify network connectivity: `docker network ls`, `docker network inspect docker_default`

### Issue 2: Elasticsearch Connection Timeout

**Diagnosis:**
```bash
curl http://localhost:9200/_cluster/health
docker logs elasticsearch
curl http://localhost:9200/_cat/indices
```

**Solutions:**
- Increase heap memory: `-Xmx2g -Xms2g`
- Check disk space: `df -h`
- Verify heap usage: `curl http://localhost:9200/_nodes/stats/jvm`

### Issue 3: High Memory Usage

**Diagnosis:**
```bash
docker stats
docker exec ragflow-server ps aux | grep python
docker exec ragflow-server python -m memory_profiler
```

**Solutions:**
- Reduce worker pool size: `MAX_WORKERS=4`
- Enable garbage collection: `PYTHONGC=1`
- Upgrade hardware or use HPA in Kubernetes

### Issue 4: Search Latency >1s

**Diagnosis:**
```bash
curl -X GET "localhost:9200/ragflow-chunks/_search?explain" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match": {"content": "test"}}}'
curl http://localhost:9200/ragflow-chunks/_stats
```

**Solutions:**
- Add index replicas: `PUT /ragflow-chunks/_settings {"number_of_replicas": 2}`
- Optimize queries: use filters before queries
- Increase embedding batch size

### Issue 5: Port Already in Use

**Diagnosis:**
```bash
lsof -i :9380
lsof -i :3306
lsof -i :9200
```

**Solutions:**
```bash
# Kill process using port
lsof -i :9380 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or change port in docker-compose.yml
```

### Issue 6: Out of Disk Space

**Diagnosis:**
```bash
df -h
docker system df
```

**Solutions:**
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Remove old logs
find /var/lib/docker -name "*.log" -mtime +30 -delete
```

## Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
docker compose down && docker compose up -d
docker logs -f ragflow-server
```

## Performance Debugging

**Check database queries:**
```bash
# Enable MySQL slow query log
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "SET GLOBAL slow_query_log='ON';"

# View slow queries
docker exec mysql tail -f /var/log/mysql/slow.log
```

**Profile Python code:**
```bash
docker exec ragflow-server python -m cProfile -s cumtime app.py
```

**Monitor Elasticsearch performance:**
```bash
curl "localhost:9200/_nodes/stats/indices"
curl "localhost:9200/_cat/shards"
```

## Getting Help

**Check logs for error messages:**
```bash
docker logs ragflow-server 2>&1 | tail -50 | grep -i error
```

**Export diagnostic bundle:**
```bash
docker compose logs > /tmp/ragflow-logs.txt
docker stats --no-stream > /tmp/docker-stats.txt
docker ps -a > /tmp/containers.txt
```

**Contact support with:**
- Error messages (full stack trace)
- Docker stats output
- Environment configuration (sanitized)
- Steps to reproduce

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
