#!/bin/bash

# Source shared environment variables
source "$(dirname "$0")/../env.sh"

# Exit on any error
set -e

# Parse command line arguments
BUILD=false
BUILD_WEB=false
BUILD_CONSUMER=false
DIGITAL_OCEAN=false
AZURE=false
GCP=false
CLEAR=false
GPU=false

for arg in "$@"; do
  if [ "$arg" == "--build" ]; then
    BUILD=true
  elif [ "$arg" == "--build-web" ]; then
    BUILD_WEB=true
  elif [ "$arg" == "--build-consumer" ]; then
    BUILD_CONSUMER=true
  elif [ "$arg" == "--docean" ]; then
    DIGITAL_OCEAN=true
  elif [ "$arg" == "--azure" ]; then
    AZURE=true
  elif [ "$arg" == "--gcp" ]; then
    GCP=true
  elif [ "$arg" == "--clear" ]; then
    CLEAR=true
  elif [ "$arg" == "--gpu" ]; then
    GPU=true
  else
    echo "Unknown parameter: $arg"
    exit 1
  fi
done

# Validate that exactly one environment flag is set
ENV_FLAGS=0
[ "$DIGITAL_OCEAN" = true ] && ((ENV_FLAGS++))
[ "$AZURE" = true ] && ((ENV_FLAGS++))
[ "$GCP" = true ] && ((ENV_FLAGS++))

if [ $ENV_FLAGS -ne 1 ]; then
  echo "Error: Exactly one environment flag must be specified:"
  echo "  --docean   : Deploy to DigitalOcean"
  echo "  --azure    : Deploy to Azure"
  echo "  --gcp      : Deploy to Google Cloud"
  echo "Optional flags:"
  echo "  --build    : Build web and consumer, push, and upgrade all Helm charts"
  echo "  --build-web: Build, push, and upgrade just web-api Helm chart"
  echo "  --build-consumer: Build, push, and upgrade just research-consumer Helm chart"
  echo "  --clear    : Clear existing resources before setup"
  echo "  --gpu      : Enable GPU support and deploy Kokoro TTS service (Azure/GCP only)"
  exit 1
fi

# Set image repository based on registry choice
if [ "$DIGITAL_OCEAN" = true ]; then
  REGISTRY="registry.digitalocean.com/${REGISTRY_NAME}"
  echo "Using DigitalOcean registry: $REGISTRY"
elif [ "$AZURE" = true ]; then
  REGISTRY="${REGISTRY_NAME}.azurecr.io"
  echo "Using Azure Container Registry: $REGISTRY"
elif [ "$GCP" = true ]; then
  REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REGISTRY_NAME}"
  echo "Using Google Cloud Artifact Registry: $REGISTRY"
fi

CONSUMER_IMAGE="${REGISTRY}/research-consumer"
WEB_API_IMAGE="${REGISTRY}/web-api"

# Early check for individual component builds
if [ "$BUILD_WEB" = true ] || [ "$BUILD_CONSUMER" = true ]; then
  if [ "$DIGITAL_OCEAN" = true ]; then
    doctl registry login
  elif [ "$AZURE" = true ]; then
    az acr login --name $REGISTRY_NAME
  elif [ "$GCP" = true ]; then
    gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
  fi

  # Build and upgrade only the requested component(s)
  if [ "$BUILD_CONSUMER" = true ]; then
    echo "Building and pushing consumer image..."
    docker buildx build \
      --platform linux/amd64,linux/arm64 \
      -t $CONSUMER_IMAGE:latest \
      --push \
      ../../research

    echo "Upgrading research-consumer chart..."
    helm upgrade --install research-consumer ./research-consumer \
      --set image.repository=${CONSUMER_IMAGE} \
      --set image.pullPolicy=${IMAGE_PULL_POLICY} \
      --wait
  fi

  if [ "$BUILD_WEB" = true ]; then
    echo "Building and pushing web API image..."
    docker buildx build \
      --platform linux/amd64,linux/arm64 \
      -t $WEB_API_IMAGE:latest \
      --push \
      ../../web

    echo "Upgrading web-api chart..."
    helm upgrade --install web-api ./web-api \
      --set image.repository=${WEB_API_IMAGE} \
      --set image.pullPolicy=${IMAGE_PULL_POLICY} \
      --wait
  fi

  echo "Component build and upgrade complete!"
  exit 0
fi

# Clear existing resources if --clear flag is set
if [ "$CLEAR" = true ]; then
  echo "Running helm uninstall cert-manager, external-dns..."
  helm uninstall -n cert-manager cert-manager external-dns --wait --ignore-not-found

  echo "Running helm uninstall yugabyte..."
  helm uninstall -n yugabyte yugabyte --wait --ignore-not-found

  echo "Running helm uninstall kafka, kafka-ui, research-consumer, web-api, ingress-nginx, redis..."
  helm uninstall kafka kafka-ui research-consumer web-api redis ingress-nginx --wait --ignore-not-found
  
  echo "Deleting cert-manager CRDs..."
  kubectl delete crd certificates.cert-manager.io --ignore-not-found
  kubectl delete crd certificaterequests.cert-manager.io --ignore-not-found
  kubectl delete crd challenges.acme.cert-manager.io --ignore-not-found
  kubectl delete crd clusterissuers.cert-manager.io --ignore-not-found
  kubectl delete crd issuers.cert-manager.io --ignore-not-found
  kubectl delete crd orders.acme.cert-manager.io --ignore-not-found

  echo "Deleting YugabyteDB CRDs..."
  kubectl delete crd ybclusters.yugabyte.com --ignore-not-found

  echo "Deleting namespaces and persistent volume claims..."
  kubectl delete namespaces yugabyte cert-manager --wait --ignore-not-found
  kubectl delete pvc --all --force
  
  sleep 10
fi

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
    doctl registry login
  elif [ "$AZURE" = true ]; then
    echo "Building and pushing Docker images to Azure Container Registry..."
    az acr login --name $REGISTRY_NAME
  elif [ "$GCP" = true ]; then
    echo "Building and pushing Docker images to Google Artifact Registry..."
    gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
  fi

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
fi

# Create Kubernetes secret from environment variables
echo "Creating Kubernetes secrets..."
kubectl create secret generic api-secrets \
  --from-literal=DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  --from-literal=OPENAI_API_KEY=$OPENAI_API_KEY \
  --from-literal=AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY \
  --from-literal=AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
  --from-literal=SQLALCHEMY_DATABASE_URI=$SQLALCHEMY_DATABASE_URI \
  --from-literal=AZURE_STORAGE_CONNECTION_STRING=$AZURE_STORAGE_CONNECTION_STRING \
  --dry-run=client -o yaml | kubectl apply -f -

# Add helm repositories
echo "Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo add kafbat-ui https://kafbat.github.io/helm-charts
helm repo add jetstack https://charts.jetstack.io
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add yugabytedb https://charts.yugabyte.com
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install cert-manager for Let's Encrypt
echo "Installing cert-manager..."
helm upgrade --install -n cert-manager cert-manager jetstack/cert-manager \
  --create-namespace \
  -f ./cert-manager/values.yaml \
  --wait

# Install ExternalDNS for Cloudflare
echo "Installing ExternalDNS..."
kubectl create secret generic cloudflare-dns \
  --namespace cert-manager \
  --from-literal=cloudflare_api_token=$CLOUDFLARE_API_TOKEN \
  --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install external-dns oci://registry-1.docker.io/bitnamicharts/external-dns \
  -f ./ingress/external-dns-values.yaml \
  --namespace cert-manager \
  --wait

# Wait for cert-manager to be ready
echo "Waiting for cert-manager to be ready..."
kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=60s
kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=60s
kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=60s

# Create keystore password secret first
echo "Creating letsencrypt-prod-key secret..."
kubectl create secret generic letsencrypt-prod-key \
  --dry-run=client -o yaml | kubectl apply -f -

# Create cluster issuer secrets
echo "Creating Let's Encrypt cluster issuer secrets..."
kubectl apply -f ./cert-manager/cluster-issuer.yaml

kubectl wait --for=condition=Ready clusterissuer/letsencrypt-prod --timeout=60s

# Install NGINX Ingress Controller
echo "Installing NGINX Ingress Controller..."
if [ "$AZURE" = true ]; then
  # Azure has weird issues with the default NGINX Ingress Controller
  helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -f ./ingress/nginx-values.yaml \
  -f ./ingress/azure-nginx-values.yaml \
  --wait
else
  helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -f ./ingress/nginx-values.yaml \
  --wait
fi

# Install Kafka bitnami chart
echo "Installing Kafka..."
helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka \
  -f kafka-values.yaml \
  --wait

# Install Redis standalone master
echo "Installing Redis..."
helm upgrade --install redis oci://registry-1.docker.io/bitnamicharts/redis \
  -f redis-values.yaml \
  --wait

echo "Saving Kafka TLS certificates..."
# Create a directory for certificates if it doesn't exist
mkdir -p ./certs
# Extract the CA certificate to a separate file
kubectl get secret kafka-tls -o jsonpath='{.data.kafka-ca\.crt}' | base64 -d > ./certs/kafka-ca.crt
# Create the client.properties file with proper formatting
cat > ./certs/client.properties << EOF
security.protocol=SSL
ssl.truststore.type=PEM
ssl.truststore.location=/tmp/kafka-ca.crt
EOF

kubectl delete pod kafka-client --ignore-not-found
# Create Kafka client pod for topic management
echo "Creating Kafka client pod..."
kubectl run kafka-client --restart='Never' --image docker.io/bitnami/kafka:3.9.0-debian-12-r12 --namespace default --command -- sleep infinity
echo "Waiting for Kafka client pod to be ready..."
kubectl wait --for=condition=Ready pod/kafka-client --timeout=60s

# Copy both the properties and certificate files to the pod
echo "Copying Kafka certificates to pod..."
kubectl cp ./certs/kafka-ca.crt kafka-client:/tmp/kafka-ca.crt
kubectl cp ./certs/client.properties kafka-client:/tmp/client.properties

# Set proper permissions
kubectl exec kafka-client -- chmod 644 /tmp/kafka-ca.crt

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
    --command-config /tmp/client.properties \
    --replication-factor 3 \
    --partitions 3 \
    --topic "$topic" \
    $retention_config
done

# Clean up the client pod
echo "Cleaning up Kafka client pod..."
kubectl delete pod kafka-client --ignore-not-found

echo "Installing kafka UI chart..."
helm upgrade --install kafka-ui kafbat-ui/kafka-ui -f kafka-ui-values.yaml --wait

# Cleanup old ybdb secret
kubectl delete secrets -n yugabyte yugabyte-tls-client-cert --ignore-not-found
kubectl delete secrets -n default yugabyte-tls-client-cert --ignore-not-found

# Install yugabytedb
echo "Installing YugabyteDB..."
# helm install yb-demo yugabytedb/yugabyte --version 2.25.0 --namespace yb-demo --wait
helm upgrade --install yugabyte yugabytedb/yugabyte --namespace yugabyte --create-namespace \
  -f yugabyte-values.yaml \
  --wait

# Copy YugabyteDB TLS client cert secret to default namespace
echo "Copying YugabyteDB TLS client cert secret to default namespace..."
kubectl get secret yugabyte-tls-client-cert -n yugabyte -o yaml | \
  sed 's/namespace: yugabyte/namespace: default/' | \
  kubectl apply -f -

# Install custom charts with appropriate settings
echo "Installing web-api chart..."
helm upgrade --install web-api ./web-api \
  --set image.repository=${WEB_API_IMAGE} \
  --set image.pullPolicy=${IMAGE_PULL_POLICY} \
  --wait

echo "Installing research-consumer charts..."
helm upgrade --install research-consumer ./research-consumer \
  --set image.repository=${CONSUMER_IMAGE} \
  --set image.pullPolicy=${IMAGE_PULL_POLICY} \
  --wait

if [ "$GPU" = true ]; then
  echo "Installing GPU Operator..."
  helm upgrade -i gpu-operator nvidia/gpu-operator \
    --version v24.9.2 \
    --namespace gpu-operator --create-namespace \
    -f gpu-operator-values.yaml \
    --wait

  echo "GPU operator install drivers..., this may take a while"
  kubectl wait --for=condition=Ready pod -l app=nvidia-cuda-validator --timeout=600s -n gpu-operator  

  echo "Installing Kokoro-FastAPI chart..."
  if [ "$AZURE" = true ]; then
    helm upgrade --install kokoro-fastapi ./kokoro-fastapi \
      -f ./kokoro-fastapi/aks-values.yaml \
      --wait
  elif [ "$GCP" = true ]; then
    helm upgrade --install kokoro-fastapi ./kokoro-fastapi \
      -f ./kokoro-fastapi/gke-values.yaml \
      --wait
  else
    echo "Not installing Kokoro on DigitalOcean."
    exit 1
  fi
fi


# Install prometheus stack
#echo "Installing Prometheus stack..."
#helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack --wait

echo "Setup complete!"

# Make cert files
# echo "Creating cert files..."
# mkdir -p ../../web/certs
# kubectl get secret crt-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > ../../web/certs/tls.crt
# kubectl get secret crt-secret -o jsonpath='{.data.tls\.key}' | base64 -d > ../../web/certs/tls.key

# # Download Let's Encrypt Staging CA certificate
# curl https://letsencrypt.org/certs/staging/letsencrypt-stg-root-x1.pem -o ../../web/certs/ca.crt

# chmod 600 ../../web/certs/tls.key
# chmod 644 ../../web/certs/tls.crt
# chmod 644 ../../web/certs/ca.crt

