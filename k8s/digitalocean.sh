#!/bin/bash

# Install doctl if not already installed
# brew install doctl

# Parse command line arguments
RUN_INSTALL=true
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --no-install) RUN_INSTALL=false ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Source shared environment variables
source "$(dirname "$0")/env.sh"

# Authenticate with Digital Ocean (you'll need an API token)
# doctl auth init

# Create Kubernetes cluster
doctl kubernetes cluster create $CLUSTER_NAME \
  --region $DO_REGION \
  --node-pool "name=$CLUSTER_NAME-pool;size=$DO_NODE_SIZE;auto-scale=$AUTO_SCALING;min-nodes=$MIN_NODES;max-nodes=$MAX_NODES" \
  --version latest \
  --auto-upgrade

# Configure kubectl
doctl kubernetes cluster kubeconfig save $CLUSTER_NAME

# Create container registry
doctl registry create $DO_REGISTRY_NAME \
  --region $DO_REGION

# Login to registry
doctl registry login

# Build and push consumer image
echo "Building and pushing consumer image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t registry.digitalocean.com/$DO_REGISTRY_NAME/research-consumer:latest \
    --push \
    ../research

# Build and push web API image
echo "Building and pushing web API image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t registry.digitalocean.com/$DO_REGISTRY_NAME/web-api:latest \
    --push \
    ../web

# Connect registry to the cluster
doctl kubernetes cluster registry add $CLUSTER_NAME

# Run setup script unless --no-install was specified
cd helm
if [ "$RUN_INSTALL" = true ]; then
    ./setup.sh --docean
else
    echo "Skipping helm setup (--no-install flag was used)"
fi