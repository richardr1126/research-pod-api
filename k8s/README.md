# Kubernetes Setup Guide

This guide explains how to deploy our research pod system using cloud providers (Azure/DigitalOcean). For local testing, we use Docker Compose.

## Prerequisites

- kubectl installed and configured
- Helm v3.x installed
- Docker with buildx support
- Python 3.12+
- One of the following for cloud deployment:
  - Azure CLI for AKS deployment
  - Digital Ocean CLI (doctl) for DO deployment

## Setup Options

### 1. Local Testing with Docker Compose

The simplest way to test locally is using Docker Compose:

1. Set up environment variables:
```bash
cp ../research/template.env ../research/.env
```
Edit `.env` and add your API keys (contact team lead for access).

2. Start the services:
```bash
docker compose up -f docker-compose.web.yml --build
```

3. Test the API endpoint:
```bash
curl -X POST http://localhost:8888/v1/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing advances"}'
```

### 2. Azure Kubernetes Service (AKS)

1. Login to Azure:
```bash
az login
```

2. Run the Azure setup script:
```bash
./azure.sh
```

This script will:
- Create a resource group
- Set up AKS cluster
- Configure Azure Container Registry (ACR)
- Deploy all services

### 3. Digital Ocean Kubernetes

1. Authenticate with DO:
```bash
doctl auth init
```

2. Run the Digital Ocean setup script:
```bash
./digitalocean.sh
```

This script will:
- Create a Kubernetes cluster
- Set up container registry
- Deploy all services

## Verify Your Setup

After running any of the cloud setup options:

1. Check pod status:
```bash
kubectl get pods
```
All pods should show "Running" status.

2. Verify services:
```bash
kubectl get svc
```
Note: For Minikube, LoadBalancer services need `minikube tunnel` running.


## Testing the Setup

1. Make sure the web server is running on localhost:8888 with correct KAFKA_BOOTSTRAP_SERVERS env var
```bash
cd ..
docker compose up -f docker-compose.web.yml --build
```

2. Test the API endpoint
```bash
curl -X POST http://localhost:8888/v1/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing advances"}'
```

## Monitoring

1. Access Kafka UI:
- Cloud: Get LoadBalancer IP from `kubectl get svc kafka-ui`

2. View logs:
```bash
# For specific service
stern kafka # or research-consumer, kafka-ui, etc.

# For all services
stern ".*" --all-namespaces
```

## Cleanup

### Local Docker Compose:
```bash
docker compose down -v
docker system prune -a  # Optional: Clear local Docker images
```

### Azure:
```bash
./destroy.sh --azure
```

### Digital Ocean:
```bash
./destroy.sh --docean
```

## Troubleshooting

1. LoadBalancer services stuck in "pending":
   - Check quota limits and network policies

2. Pod CrashLoopBackOff:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

3. Image pull errors:
   - Check registry credentials and network policies

## Next Steps

- Set up monitoring with Prometheus/Grafana
- Configure backup and disaster recovery
- Implement auto-scaling policies
- Add SSL/TLS encryption for Kafka
- Set up CI/CD pipelines