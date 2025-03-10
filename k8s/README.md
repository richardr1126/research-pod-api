# Kubernetes Setup Guide

This guide explains how to deploy our research pod system using either Minikube (for local testing) or cloud providers (Azure/DigitalOcean). 

## Prerequisites

- kubectl installed and configured
- Helm v3.x installed
- Docker with buildx support
- Python 3.12+
- One of the following:
  - Minikube for local testing
  - Azure CLI for AKS deployment
  - Digital Ocean CLI (doctl) for DO deployment

## Important Note About Minikube and LoadBalancer Services

⚠️ **WARNING**: Minikube has known issues with LoadBalancer services. Services of type LoadBalancer won't automatically receive external IPs in Minikube unless you:
1. Run `minikube tunnel` in a separate terminal window
2. Keep the tunnel running for the entire duration of your testing
3. Use sudo password when prompted

Without the tunnel running, LoadBalancer services will remain in "pending" state and won't be accessible externally.

## Setup Options

### 1. Local Testing with Minikube

1. Start Minikube:
```bash
minikube start
```

2. **IMPORTANT**: Open a new terminal and run:
```bash
minikube tunnel
```
Keep this terminal open - it's required for LoadBalancer services to work.

3. Configure Docker to use Minikube's registry:
```bash
eval $(minikube docker-env)
```

4. Set up environment variables:
```bash
cp ../research/template.env ../research/.env
```
Edit `.env` and add your API keys (contact team lead for access).

5. Run the setup script:
```bash
cd helm
chmod +x setup.sh
./setup.sh
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

After running any of the setup options above:

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

1. For Minikube local testing:
```bash
# Get service URLs
minikube service kafka-ui --url     # For Kafka UI
```

2. Make sure the web server is running on localhost:8888 with correct KAFKA_BOOTSTRAP_SERVERS env var
```bash
cd ..
docker compose up -f docker-compose.web.yml --build
```
> Note for Minikube you need to have the web server not running in Docker and running from your host machine python from localhost:8888. Then set KAFKA_BOOTSTRAP_SERVERS to 127.0.0.1:9094,127.0.0.1:9094,127.0.0.1:9094 (need `minikube tunnel` running)

# Test API endpoint
curl -X POST http://localhost:8888/v1/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing advances"}'
```

## Monitoring

1. Access Kafka UI:
- Minikube: `minikube service kafka-ui --url`
- Cloud: Get LoadBalancer IP from `kubectl get svc kafka-ui`

2. View logs:
```bash
# For specific service
kubectl logs -f deployment/research-consumer

# For all services (using stern)
stern ".*" --all-namespaces
```

## Cleanup

### Local Minikube:
```bash
# Stop and delete cluster
minikube stop
minikube delete

# Optional: Clear local Docker images
docker system prune -a
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
   - For Minikube: Make sure `minikube tunnel` is running
   - For Cloud: Check quota limits and network policies

2. Pod CrashLoopBackOff:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

3. Kafka connection issues:
   - Check broker connectivity:
   ```bash
   kubectl exec -it kafka-0 -- nc -vz localhost 9092
   ```
   - Verify configuration:
   ```bash
   kubectl get cm kafka-config -o yaml
   ```

4. Image pull errors:
   - For Minikube: Make sure you ran `eval $(minikube docker-env)`
   - For Cloud: Check registry credentials and network policies

## Next Steps

- Set up monitoring with Prometheus/Grafana
- Configure backup and disaster recovery
- Implement auto-scaling policies
- Add SSL/TLS encryption for Kafka
- Set up CI/CD pipelines