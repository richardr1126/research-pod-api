# Kubernetes Setup Guide

This guide explains how to deploy our research pod system using cloud providers (Azure/DigitalOcean/GCP). For local testing, we use Docker Compose.

## Prerequisites

- kubectl installed and configured
- Helm v3.x installed
- Docker with buildx support for multi-architecture builds
- One of the following for cloud deployment:
  - Azure CLI for AKS deployment
  - Digital Ocean CLI (doctl) for DO deployment
  - Google Cloud CLI (gcloud) for GCP deployment
- Cloudflare API token for DNS management
- API keys for OpenAI and other services

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
docker compose up --build
```

### 2. Cloud Deployment (Azure, DigitalOcean, or GCP)

1. First, authenticate with your chosen cloud provider:

For Azure:
```bash
az login
```

For DigitalOcean:
```bash
doctl auth init
```

For GCP:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. Run the appropriate setup script:
```bash
# For Azure
./azure.sh

# For DigitalOcean
./digitalocean.sh

# For Google Cloud
./gcp.sh
```

Each script will:
- Create a Kubernetes cluster
- Set up container registry
- Configure DNS settings
- Deploy all required services including:
  - Kafka with SSL/TLS encryption
  - Redis
  - Kafka UI
  - External DNS
  - Cert Manager
  - NGINX Ingress Controller
  - Research Consumer service
  - Web API service

You can add the `--no-install` flag to skip the Helm chart installation step:
```bash
./gcp.sh --no-install
```

### 3. Manual Helm Setup

If you need to manually run the Helm setup:

```bash
cd helm
./setup.sh [--azure|--docean|--gcp] [--build] [--clear]
```

Flags:
- `--azure`, `--docean`, or `--gcp`: Choose your cloud provider (required)
- `--build`: Build and push Docker images
- `--clear`: Clear existing resources before setup

## Verify Your Setup

1. Check pod status:
```bash
kubectl get pods
```
All pods should show "Running" status.

2. Verify services:
```bash
kubectl get svc
```

3. Check certificates:
```bash
kubectl get certificates
```

## Monitoring and Management

1. Access Kafka UI:
   - Available at `https://kafka-ui.richardr.dev`

2. View logs:
```bash
# For specific service
stern research-consumer
stern web-api

# Using stern for multi-pod logs
stern "kafka|research-consumer|web-api" --all-namespaces
```

## Cleanup

To destroy your cloud infrastructure:

```bash
./destroy.sh [--azure|--docean|--gcp]
```

## Troubleshooting

1. Certificate issues:
```bash
kubectl describe certificate crt
kubectl describe clusterissuer letsencrypt-staging
```

2. Pod issues:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

3. Image pull errors:
   - Check registry credentials
   - Verify image names and tags
   - Ensure proper registry authentication

4. Kafka connectivity issues:
   - Check SSL certificate status
   - Verify broker endpoints
   - Check topic creation status with kafka-client pod

5. DNS issues:
   - Verify Cloudflare API token
   - Check External DNS pod logs
   - Ensure DNS records are propagating

## Architecture Notes

- Uses multi-architecture container images (amd64/arm64)
- SSL/TLS encryption for Kafka with Let's Encrypt certificates
- Cloudflare DNS integration for automatic DNS management
- Horizontal pod autoscaling enabled
- NGINX Ingress for load balancing
- Redis for caching/message queuing