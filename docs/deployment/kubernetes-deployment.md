# Kubernetes Deployment (Production)

## Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify setup
kubectl cluster-info
helm version
```

## Deploy via Helm Chart

### 1. Add Repository

```bash
helm repo add ragflow https://charts.ragflow.io
helm repo update
```

### 2. Create Values File

**values-prod.yaml:**
```yaml
replicaCount: 3

image:
  repository: infiniflow/ragflow
  tag: "0.24.0"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 4Gi

mysql:
  enabled: true
  auth:
    rootPassword: <strong_password>
    username: ragflow
    password: <strong_password>
  primary:
    persistence:
      size: 100Gi
      storageClassName: fast-ssd

redis:
  enabled: true
  auth:
    enabled: true
    password: <strong_password>

elasticsearch:
  enabled: true
  replicas: 3
  persistence:
    size: 200Gi
    storageClassName: fast-ssd

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: ragflow.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ragflow-tls
      hosts:
        - ragflow.example.com

env:
  API_PROXY_SCHEME: "python"
  DOC_ENGINE: "elasticsearch"
  LOG_LEVEL: "INFO"
```

### 3. Install Release

```bash
# Create namespace
kubectl create namespace ragflow

# Install Helm chart
helm install ragflow ragflow/ragflow \
  -n ragflow \
  -f values-prod.yaml

# Verify installation
kubectl get pods -n ragflow
kubectl get svc -n ragflow
kubectl get pvc -n ragflow
```

### 4. Monitor Deployment

```bash
# Watch rollout
kubectl rollout status deployment/ragflow -n ragflow

# Check logs
kubectl logs -f deployment/ragflow -n ragflow

# Get service endpoints
kubectl get ingress -n ragflow
```

## Scaling

```bash
# Scale API replicas
kubectl scale deployment ragflow -n ragflow --replicas=5

# Auto-scale based on CPU
kubectl autoscale deployment ragflow \
  -n ragflow \
  --min=3 --max=10 \
  --cpu-percent=70

# Check HPA status
kubectl get hpa -n ragflow
```

## Database Migrations

```bash
# Run migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ragflow-migration
  namespace: ragflow
spec:
  template:
    spec:
      containers:
      - name: migration
        image: infiniflow/ragflow:0.24.0
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: MYSQL_HOST
          value: mysql
      restartPolicy: Never
  backoffLimit: 3
EOF

# Check job status
kubectl get jobs -n ragflow
kubectl logs job/ragflow-migration -n ragflow
```

## Helm Chart Updates

```bash
# Check for chart updates
helm search repo ragflow

# Upgrade to new version
helm upgrade ragflow ragflow/ragflow \
  -n ragflow \
  -f values-prod.yaml

# Check upgrade status
kubectl rollout status deployment/ragflow -n ragflow
```

## Troubleshooting

```bash
# Check pod events
kubectl describe pod <pod-name> -n ragflow

# View application logs
kubectl logs <pod-name> -n ragflow

# Execute command in pod
kubectl exec -it <pod-name> -n ragflow -- bash

# Check resource usage
kubectl top nodes
kubectl top pods -n ragflow
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
