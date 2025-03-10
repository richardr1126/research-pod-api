#!/bin/bash

# Source shared environment variables
source "$(dirname "$0")/../env.sh"

# Make sure does not exist
kubectl delete pod kafka-client --ignore-not-found

# Exit on any error
set -e

# Parse command line arguments
BUILD=false
DIGITAL_OCEAN=false
AZURE=false
for arg in "$@"; do
  if [ "$arg" == "--build" ]; then
    BUILD=true
  elif [ "$arg" == "--docean" ]; then
    DIGITAL_OCEAN=true
  elif [ "$arg" == "--azure" ]; then
    AZURE=true
  fi
done

# Set image repository based on registry choice
if [ "$DIGITAL_OCEAN" = true ]; then
    REGISTRY="registry.digitalocean.com/${DO_REGISTRY_NAME}"
    IMAGE_PULL_POLICY="Always"
    echo "Using DigitalOcean registry: $REGISTRY"
elif [ "$AZURE" = true ]; then
    REGISTRY="${AZ_ACR_NAME}.azurecr.io"
    IMAGE_PULL_POLICY="Always"
    echo "Using Azure Container Registry: $REGISTRY"
else
    REGISTRY="${PROJECT_TAG}"
    IMAGE_PULL_POLICY="Never"
    echo "Using local registry"
fi

CONSUMER_IMAGE="${REGISTRY}/research-consumer"
WEB_API_IMAGE="${REGISTRY}/web-api"

# Check if research/.env exists
if [ ! -f "../../research/.env" ]; then
    echo "Error: research/.env file not found"
    echo "Please copy research/template.env to research/.env and fill in your API keys"
    exit 1
fi

# Source the .env file
source "../../research/.env"

if [ "$BUILD" = true ]; then
    if [ "$DIGITAL_OCEAN" = true ]; then
        echo "Building and pushing Docker images to DigitalOcean registry..."
        # Ensure we're logged into DO registry
        doctl registry login
        
        # Build and push consumer image
        echo "Building and pushing consumer image..."
        docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t registry.digitalocean.com/$CONSUMER_IMAGE:latest \
            --push \
            ../../research
        
        # Build and push web API image
        echo "Building and pushing web API image..."
        docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t registry.digitalocean.com/$WEB_API_IMAGE:latest \
            --push \
            ../../web
    elif [ "$AZURE" = true ]; then
        echo "Building and pushing Docker images to Azure Container Registry..."
        # Ensure we're logged into ACR
        az acr login --name $ACR_NAME
        
        # Build and push consumer image
        echo "Building and pushing consumer image..."
        docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t $CONSUMER_IMAGE:latest \
            --push \
            ../../research
        
        # Build and push web API image
        echo "Building and pushing web API image..."
        docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t $WEB_API_IMAGE:latest \
            --push \
            ../../web
    else
        echo "Building Docker images locally..."
        eval $(minikube docker-env)
        
        docker build -t ${CONSUMER_IMAGE}:latest ../../research
        docker build -t ${WEB_API_IMAGE}:latest ../../web
    fi
fi

# Create Kubernetes secret from environment variables
echo "Creating Kubernetes secrets..."
kubectl create secret generic api-secrets \
    --from-literal=DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
    --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
    --from-literal=AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
    --from-literal=AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create registry secrets based on environment
if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_TOKEN" ] && [ "$AZURE" = false ] && [ "$DIGITAL_OCEAN" = false ]; then
    echo "Creating Docker Hub secret..."
    kubectl create secret docker-registry dockerhub-secret \
        --docker-server=https://index.docker.io/v1/ \
        --docker-username=$DOCKER_USERNAME \
        --docker-password=$DOCKER_TOKEN \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "Skipping Docker Hub secret creation for cloud..."
fi

# Add helm repositories
echo "Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update    

# Install Kafka with any registry secret to prevent pull rate limits
echo "Installing Kafka..."
if [ "$DIGITAL_OCEAN" = true ]; then
    echo "Installing Kafka with DigitalOcean registry secrets..."
    helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka \
        -f kafka-values.yaml \
        --set image.pullSecrets[0]=research-pod-registry \
        --wait
elif [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_TOKEN" ] && [ "$AZURE" = false ]; then
    echo "Installing Kafka with Docker Hub secrets..."
    helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka \
        -f kafka-values.yaml \
        --set image.pullSecrets[0]=dockerhub-secret \
        --wait
else
    echo "Installing Kafka without registry secrets..."
    helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka -f kafka-values.yaml --wait
fi

# Create Kafka client pod for topic management
echo "Creating Kafka client pod..."
kubectl run kafka-client --restart='Never' --image docker.io/bitnami/kafka:3.9.0-debian-12-r12 --namespace default --command -- sleep infinity
echo "Waiting for Kafka client pod to be ready..."
kubectl wait --for=condition=Ready pod/kafka-client --timeout=60s

echo "Creating Kafka topics..."
# Create Kafka topics with common settings
TOPICS=("research-results" "research-errors" "scrape-requests")
for topic in "${TOPICS[@]}"; do
    retention_config=""
    if [ "$topic" != "research-errors" ]; then
        retention_config="--config retention.ms=86400000"
    fi
    
    kubectl exec -it kafka-client -- kafka-topics.sh \
        --create \
        --if-not-exists \
        --bootstrap-server kafka.default.svc.cluster.local:9092 \
        --replication-factor 3 \
        --partitions 3 \
        --topic "$topic" \
        $retention_config
done

echo "Installing kafka UI chart..."
helm upgrade --install kafka-ui kafka-ui/kafka-ui -f kafka-ui-values.yaml --wait

# Install custom charts with appropriate settings
echo "Installing custom charts..."
helm upgrade --install research-consumer ./research-consumer \
    --set image.repository=${CONSUMER_IMAGE} \
    --set image.pullPolicy=${IMAGE_PULL_POLICY} \
    --wait

# Install prometheus stack
#echo "Installing Prometheus stack..."
#helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack --wait

# Clean up the client pod
echo "Cleaning up Kafka client pod..."
kubectl delete pod kafka-client

echo "Setup complete!"

