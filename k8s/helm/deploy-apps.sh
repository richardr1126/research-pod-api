#!/bin/bash

# Deploy script for building and deploying local charts (research-pod application components)

# Source shared environment variables
source "$(dirname "$0")/../env.sh"

# Set up GitHub Container Registry
REGISTRY="ghcr.io/richardr1126"
CONSUMER_IMAGE="${REGISTRY}/research-consumer"
WEB_API_IMAGE="${REGISTRY}/web-api"

# Exit on any error
set -e

# Parse command line arguments
BUILD=false
CLEAR=false

for arg in "$@"; do
  if [ "$arg" == "--build" ]; then
    BUILD=true
  elif [ "$arg" == "--clear" ]; then
    CLEAR=true
  else
    echo "Unknown parameter: $arg"
    echo "Usage: $0 [--build] [--clear]"
    echo "  --build: Build and push Docker images before deploying"
    echo "  --clear: Clear existing application resources before deployment"
    exit 1
  fi
done

# Check if research/.env exists
if [ ! -f "../../research/.env" ]; then
  echo "Error: research/.env file not found"
  echo "Please copy research/template.env to research/.env and fill in your API keys"
  exit 1
fi

# Source the .env file
source "../../research/.env"

# Check for GitHub PAT
if [ -z "$GITHUB_PAT" ]; then
  echo "Error: GITHUB_PAT environment variable not set"
  echo "Please set your GitHub Personal Access Token in the .env file"
  exit 1
fi

# Clear existing application resources if --clear flag is set
if [ "$CLEAR" = true ]; then
  echo "Clearing existing application resources..."
  helm uninstall research-consumer web-api --wait --ignore-not-found
  kubectl delete pvc --all --force --ignore-not-found
  sleep 5
fi

if [ "$BUILD" = true ]; then
  # Login to GitHub Container Registry
  echo "Logging in to GitHub Container Registry..."
  echo $GITHUB_PAT | docker login ghcr.io -u richardr1126 --password-stdin

  # Build and push both images
  echo "Building and pushing consumer image..."
  docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t $CONSUMER_IMAGE:latest \
    --push \
    ../../research
  
  echo "Building and pushing web API image..."
  docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t $WEB_API_IMAGE:latest \
    --push \
    ../../web

  echo "All images built and pushed successfully!"
fi

# Create Kubernetes secret from environment variables
echo "Creating Kubernetes secrets..."
kubectl create secret generic researchpod-secrets \
  --from-literal=GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --from-literal=AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY \
  --from-literal=AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
  --from-literal=SQLALCHEMY_DATABASE_URI=$SQLALCHEMY_DATABASE_URI \
  --from-literal=AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
  --from-literal=TAVILY_API_KEY=$TAVILY_API_KEY \
  --dry-run=client -o yaml | kubectl apply -f -

# Install/upgrade custom application charts
echo "Installing research-consumer chart..."
helm upgrade --install research-consumer ./research-consumer \
  --set image.repository=${CONSUMER_IMAGE} \
  --wait

echo "Installing web-api chart..."
helm upgrade --install web-api ./web-api \
  --set image.repository=${WEB_API_IMAGE} \
  --wait

echo "Application deployment complete!"
