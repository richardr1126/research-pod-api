#!/bin/bash

# Install gcloud CLI if not already installed
# brew install --cask google-cloud-sdk

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

# Authenticate with Google Cloud
# gcloud auth login
# gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable container.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com

# Create GKE cluster
echo "Creating GKE cluster..."
gcloud container clusters create $CLUSTER_NAME-gcp \
    --project $GCP_PROJECT_ID \
    --zone $GCP_ZONE \
    --machine-type $GCP_MACHINE_TYPE \
    --num-nodes $MIN_NODES \
    --enable-autorepair \
    --enable-autoupgrade \
    --enable-ip-alias \
    --enable-autoscaling \
    --min-nodes $MIN_NODES \
    --max-nodes $MAX_NODES \

# Add GPU node pool
echo "Creating GPU node pool..."
gcloud container node-pools create gpu-t4-pool \
    --cluster=$CLUSTER_NAME-gcp \
    --accelerator type=nvidia-tesla-t4,count=1 \
    --machine-type=n1-standard-1 \
    --num-nodes=1 \
    --zone=$GCP_ZONE \

# Get credentials for kubectl
echo "Getting kubectl credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME-gcp \
    --region $GCP_REGION \
    --project $GCP_PROJECT_ID

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create $REGISTRY_NAME \
    --repository-format=docker \
    --location=$GCP_REGION \
    --description="Research Pod Container Registry"

# Configure Docker to use GCP Artifact Registry
echo "Configuring Docker authentication..."
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

# Create GCP registry pull secret
echo "Creating GCP registry pull secret..."
kubectl create secret docker-registry $REGISTRY_NAME \
    --docker-server=${GCP_REGION}-docker.pkg.dev \
    --docker-username=_json_key \
    --docker-email=not@used.com \
    --docker-password="$(gcloud auth print-access-token)" \
    --dry-run=client -o yaml | kubectl apply -f -

# Build and push multi-architecture images
REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REGISTRY_NAME}"

echo "Building and pushing consumer image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${REGISTRY}/research-consumer:latest \
    --push \
    ../research

echo "Building and pushing web API image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${REGISTRY}/web-api:latest \
    --push \
    ../web

# Run the setup script with GCP configuration unless --no-install was specified
echo "Running main setup script..."
cd helm
if [ "$RUN_INSTALL" = true ]; then
    ./setup.sh --gcp
else
    echo "Skipping helm setup (--no-install flag was used)"
fi

echo "GCP setup complete! You can now access your cluster with kubectl."