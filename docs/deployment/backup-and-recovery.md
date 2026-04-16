# Backup & Recovery

## Database Backup

**Manual backup:**
```bash
# Backup MySQL
docker exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow > backup-$(date +%Y%m%d).sql

# Restore MySQL
docker exec -i mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow < backup-20260416.sql
```

**Automated daily backups (cron):**
```bash
#!/bin/bash
# backup-ragflow.sh
BACKUP_DIR="/backups/ragflow"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# Database
docker exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow > $BACKUP_DIR/db-$DATE.sql

# MinIO data
docker exec minio mc mirror \
  minio/ragflow $BACKUP_DIR/minio-$DATE

# Compress
tar -czf $BACKUP_DIR/ragflow-$DATE.tar.gz \
  $BACKUP_DIR/db-$DATE.sql $BACKUP_DIR/minio-$DATE

# Delete old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/ragflow-$DATE.tar.gz"
```

## Elasticsearch Index Backup

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/mnt/backups"
    }
  }'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/ragflow-backup" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "ragflow-chunks"}'

# List snapshots
curl "localhost:9200/_snapshot/backup/_all"

# Restore snapshot
curl -X POST "localhost:9200/_snapshot/backup/ragflow-backup/_restore"
```

## Kubernetes Volume Snapshots

```bash
# Create snapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: ragflow-db-snapshot
  namespace: ragflow
spec:
  volumeSnapshotClassName: csi-hostpath-snapclass
  source:
    persistentVolumeClaimName: mysql-data
EOF

# Restore from snapshot
# See Kubernetes CSI documentation for your storage provider
```

## Recovery Procedures

**From database backup:**
```bash
# Stop application
docker compose down

# Restore database
docker compose up -d mysql
docker exec -i mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ragflow < backup-20260416.sql

# Restart application
docker compose up -d
```

**From Elasticsearch snapshot:**
```bash
# Close indices
curl -X POST "localhost:9200/ragflow-chunks/_close"

# Restore snapshot
curl -X POST "localhost:9200/_snapshot/backup/ragflow-backup/_restore" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "ragflow-chunks"}'

# Open indices
curl -X POST "localhost:9200/ragflow-chunks/_open"
```

## Backup Verification

```bash
# Verify database backup integrity
mysql -u root -p${MYSQL_ROOT_PASSWORD} < backup-20260416.sql \
  -e "SELECT COUNT(*) FROM document;"

# Verify Elasticsearch backup
curl "localhost:9200/_snapshot/backup/ragflow-backup/_status"

# Test restore in staging environment
docker compose -f docker-compose.staging.yml up
# Restore to staging DB
# Run tests to verify data integrity
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
