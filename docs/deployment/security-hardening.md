# Security Hardening

## Network Security

**Kubernetes Network Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ragflow-network-policy
  namespace: ragflow
spec:
  podSelector:
    matchLabels:
      app: ragflow
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ragflow
    ports:
    - protocol: TCP
      port: 9380
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # Allow HTTPS outbound
```

## Data Encryption

**Enable SSL in nginx:**
```bash
export ENABLE_SSL=true
export CERT_PATH=/etc/nginx/certs/ragflow.crt
export KEY_PATH=/etc/nginx/certs/ragflow.key

# Generate self-signed cert (dev only)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365

# Production: Use Let's Encrypt with cert-manager
```

## Database Hardening

**Change default credentials:**
```bash
# Connect to MySQL
docker exec -it mysql mysql -u root -p${MYSQL_ROOT_PASSWORD}

# Change root password
ALTER USER 'root'@'localhost' IDENTIFIED BY '<new_strong_password>';

# Disable root remote login
RENAME USER 'root'@'%' TO 'root_old'@'localhost';

# Create read-only replication user
CREATE USER 'replication'@'%' IDENTIFIED BY '<password>';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';

FLUSH PRIVILEGES;
```

## Secrets Management

**Use environment variables (never commit secrets):**
```bash
# .env (DO NOT COMMIT)
MYSQL_ROOT_PASSWORD=<strong_password>
OPENAI_API_KEY=<your_key>
JWT_SECRET=<random_32_chars>
```

**Kubernetes Secrets:**
```bash
# Create secret
kubectl create secret generic ragflow-secrets \
  -n ragflow \
  --from-literal=mysql-password=<password> \
  --from-literal=openai-api-key=<key>

# Use in deployment
env:
- name: MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: ragflow-secrets
      key: mysql-password
```

## Access Control

**Change default credentials immediately:**
```bash
# After first login, change admin password
curl -X POST http://localhost:9380/api/v1/users/password-change \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "password123", "new_password": "<new_password>"}'
```

**Enable 2FA:**
```bash
# User settings → Security → Enable 2FA
# Scan QR code with authenticator app
```

## Firewall Rules

**Docker network isolation:**
```bash
# Only expose necessary ports
docker run -p 127.0.0.1:9380:9380 ...  # Localhost only
docker run -p 0.0.0.0:80:80 ...         # Public port
```

**UFW (Ubuntu firewall):**
```bash
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

## Audit Logging

**Enable audit logs:**
```yaml
# service_conf.yaml
audit:
  enabled: true
  log_file: /var/log/ragflow/audit.log
  log_level: INFO
```

**Monitor for suspicious activity:**
```bash
# Failed login attempts
docker logs ragflow-server | grep "login.*failed"

# API token usage
docker logs ragflow-server | grep "authorization"

# Data access
docker logs ragflow-server | grep "SELECT.*document"
```

## Regular Security Tasks

**Weekly:**
- Review error logs for security issues
- Check for failed login attempts
- Verify backup integrity

**Monthly:**
- Update dependencies
- Review access logs
- Rotate API keys/passwords

**Quarterly:**
- Security audit
- Penetration testing
- Compliance check

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
