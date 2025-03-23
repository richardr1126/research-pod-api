# Kubernetes Setup Guide

This guide explains how to deploy our research pod system using cloud providers (Azure/DigitalOcean/GCP). For local testing, we use Docker Compose.

## Prerequisites

- kubectl installed and configured
- Helm v3.x installed
- Docker with buildx support for multi-architecture builds
- One of the following for cloud deployment **with access to at least 6 vCPUs in the respective regions**:
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
  - NVIDIA GPU Operator (if --gpu flag used)
  - Kokoro TTS service (if --gpu flag used)

You can add the `--no-install` flag to skip the Helm chart installation step:
```bash
./gcp.sh --no-install
```

### 3. Manual Helm Setup

If you need to manually run the Helm setup:

```bash
cd helm
./setup.sh [--azure|--docean|--gcp] [--build] [--clear] [--gpu]
```

Flags:
- `--azure`, `--docean`, or `--gcp`: Choose your cloud provider (required)
- `--build`: Build and push Docker images
- `--clear`: Clear existing resources before setup
- `--gpu`: Enable GPU support and deploy Kokoro TTS service (Azure/GCP only)

The setup script performs the following steps:

1. **Initial Setup**:
   - Validates environment flags and configuration
   - Loads environment variables from `research/.env`
   - Optionally clears existing resources with `--clear`

2. **Container Registry Setup**:
   - For DigitalOcean: Uses `registry.digitalocean.com/${REGISTRY_NAME}`
   - For Azure: Uses `${REGISTRY_NAME}.azurecr.io`
   - For GCP: Uses `${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REGISTRY_NAME}`

3. **Image Building** (if --build flag is used):
   - Builds multi-architecture images (linux/amd64,linux/arm64)
   - Builds and pushes research-consumer and web-api images

4. **Kubernetes Secret Creation**:
   - Creates api-secrets for API keys
   - Sets up CloudFlare DNS secrets
   - Creates JKS keystore secrets for Kafka

5. **Core Components Installation**:
   - Installs cert-manager for SSL certificate management
   - Sets up ExternalDNS for Cloudflare integration
   - Configures Let's Encrypt staging issuer
   - Generates SSL certificates for Kafka
   - Installs NGINX Ingress Controller (with Azure-specific configuration if needed)

6. **Database Setup**:
   - Installs YugabyteDB cluster with TLS enabled
   - Creates necessary users and databases
   - Copies TLS certificates to required namespaces
   - Sets up 3 master and 3 tserver nodes for high availability

7. **Service Deployment**:
   - Deploys Kafka with SSL/TLS encryption
   - Sets up Redis standalone master
   - Creates required Kafka topics:
     - research-results (24h retention)
     - research-errors
     - scrape-requests (24h retention)
   - Installs Kafka UI dashboard
   - Deploys research-consumer service
   - Deploys web-api service

Each component is installed with appropriate wait conditions to ensure proper initialization order.

## Component Details

### Cert Manager Configuration

The setup includes two main cert-manager resources:

1. **ClusterIssuer**: Configures Let's Encrypt staging with Cloudflare DNS validation
2. **Certificate**: Creates wildcard certificate for *.richardr.dev with:
   - 1 year duration
   - 30 day renewal window
   - JKS and PKCS12 keystore generation

### Kafka Setup

- Uses Bitnami Kafka chart
- Configures 3 replicas with SSL/TLS external access encryption
- Creates topics with appropriate retention policies
- Includes Kafka UI for monitoring (no encrytion yet)

### Redis Configuration

- Standalone master node configuration
- Persistent volume storage
- No auth or outside access, only internal service access

### YugabyteDB Configuration

- Distributed SQL database with PostgreSQL compatibility
- TLS encryption enabled using cert-manager
- 3 master and 3 tserver nodes for high availability
- YSQL authentication with custom user/password
- Client certificate authentication for secure connections
- Resource requests and limits configured for production use

### TTS Setup

When using the `--gpu` flag with Azure or GCP deployments:

1. **NVIDIA GPU Operator**: 
   - Automatically installs GPU drivers on nodes
   - Configures time-slicing for GPU sharing
   - Enables 4 replicas per GPU for better utilization

2. **Kokoro TTS Service**:
   - Accessible at `https://koko.richardr.dev`

### Connect to YugabyteDB

Use the included script to connect to YugabyteDB:
```bash
./ybdb.sh
```

This opens a PostgreSQL-compatible shell connected to the database cluster.

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

4. Verify YugabyteDB:
```bash
kubectl get pods -n yugabyte
kubectl get svc -n yugabyte
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

3. Database issues:
   - Check YugabyteDB master status:
     ```bash
     kubectl get pods -n yugabyte -l app=yb-master
     ```
   - Check YugabyteDB tserver status:
     ```bash
     kubectl get pods -n yugabyte -l app=yb-tserver
     ```
   - Verify TLS certificates:
     ```bash
     kubectl get secrets -n yugabyte yugabyte-tls-client-cert
     ```
   - Check database logs:
     ```bash
     kubectl logs -n yugabyte -l app=yb-master
     kubectl logs -n yugabyte -l app=yb-tserver
     ```

4. Image pull errors:
   - Check registry credentials
   - Verify image names and tags
   - Ensure proper registry authentication

5. Kafka connectivity issues:
   - Check SSL certificate status
   - Verify broker endpoints
   - Check topic creation status with kafka-client pod

6. DNS issues:
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