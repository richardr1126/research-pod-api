#!/bin/bash

# Install azure CLI if not already installed
# brew install azure-cli

# Source shared environment variables
source "$(dirname "$0")/env.sh"

# Authenticate with Azure (you'll need to be logged in)
# az login

# Parse command line arguments
RUN_INSTALL=true
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --no-install) RUN_INSTALL=false ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Create resource group
az group create --name $AZ_RESOURCE_GROUP --location $AZ_LOCATION

# Create AKS cluster with autoscaling
echo "Creating AKS cluster..."
az aks create \
  --resource-group $AZ_RESOURCE_GROUP \
  --name $CLUSTER_NAME-az \
  --node-count $AZ_NODE_COUNT \
  --node-vm-size $AZ_NODE_SIZE \
  --enable-cluster-autoscaler \
  --min-count $MIN_NODES \
  --max-count $MAX_NODES \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials for kubectl
echo "Getting kubectl credentials..."
az aks get-credentials --resource-group $AZ_RESOURCE_GROUP --name $CLUSTER_NAME-az

# Create Azure Container Registry
echo "Creating Azure Container Registry..."
az acr create \
  --resource-group $AZ_RESOURCE_GROUP \
  --name $AZ_ACR_NAME \
  --sku Standard

# Connect ACR with AKS
echo "Connecting ACR to AKS..."
az aks update \
  --resource-group $AZ_RESOURCE_GROUP \
  --name $CLUSTER_NAME-az \
  --attach-acr $AZ_ACR_NAME

# Login to ACR
echo "Logging into ACR..."
az acr login --name $AZ_ACR_NAME

# Build and push multi-architecture images
echo "Building and pushing consumer image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${AZ_ACR_NAME}.azurecr.io/research-consumer:latest \
    --push \
    ../research

echo "Building and pushing web API image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${AZ_ACR_NAME}.azurecr.io/web-api:latest \
    --push \
    ../web

# Run the setup script with Azure configuration unless --no-install was specified
echo "Running main setup script..."
cd helm
if [ "$RUN_INSTALL" = true ]; then
    ./setup.sh --azure
else
    echo "Skipping helm setup (--no-install flag was used)"
fi

echo "Azure setup complete! You can now access your cluster with kubectl."

