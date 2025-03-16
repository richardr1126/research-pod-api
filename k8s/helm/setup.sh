#!/bin/bash

# Add completion function at the start of the script
_setup_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--build --docean --azure --gcp --clear"

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

# Register the completion function
complete -F _setup_completion setup.sh

# Only run the completion if we're being sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    return
fi

# Source shared environment variables
source "$(dirname "$0")/../env.sh"

# Exit on any error
set -e

# Parse command line arguments
BUILD=false
DIGITAL_OCEAN=false
AZURE=false
GCP=false
CLEAR=false

for arg in "$@"; do
  if [ "$arg" == "--build" ]; then
    BUILD=true
  elif [ "$arg" == "--docean" ]; then
    DIGITAL_OCEAN=true
  elif [ "$arg" == "--azure" ]; then
    AZURE=true
  elif [ "$arg" == "--gcp" ]; then
    GCP=true
  elif [ "$arg" == "--clear" ]; then
    CLEAR=true
  fi
done

# Clear existing resources if --clear flag is set
if [ "$CLEAR" = true ]; then
    echo "Clearing existing resources..."
    helm uninstall -n cert-manager cert-manager external-dns --wait --ignore-not-found
    helm uninstall kafka kafka-ui research-consumer --wait --ignore-not-found
    kubectl delete secrets --all
    kubectl delete clusterissuer --all
    kubectl delete certificaterequests.cert-manager.io --all
    kubectl delete certificates.cert-manager.io --all

    sleep 10
fi

kubectl delete pod kafka-client --ignore-not-found

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
    echo "  --build    : Build and push Docker images"
    echo "  --clear    : Clear existing resources before setup"
    exit 1
fi

# Set image repository based on registry choice
if [ "$DIGITAL_OCEAN" = true ]; then
    REGISTRY="registry.digitalocean.com/${DO_REGISTRY_NAME}"
    echo "Using DigitalOcean registry: $REGISTRY"
elif [ "$AZURE" = true ]; then
    REGISTRY="${AZ_ACR_NAME}.azurecr.io"
    echo "Using Azure Container Registry: $REGISTRY"
elif [ "$GCP" = true ]; then
    REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GCP_REGISTRY_NAME}"
    echo "Using Google Cloud Artifact Registry: $REGISTRY"
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

    elif [ "$AZURE" = true ]; then
        echo "Building and pushing Docker images to Azure Container Registry..."
        # Ensure we're logged into ACR
        az acr login --name $AZ_ACR_NAME

    elif [ "$GCP" = true ]; then
        echo "Building and pushing Docker images to Google Artifact Registry..."
        # Configure Docker for GCP Artifact Registry
        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
    fi

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
fi

# Create Kubernetes secret from environment variables
echo "Creating Kubernetes secrets..."
kubectl create secret generic api-secrets \
    --from-literal=DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
    --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
    --from-literal=AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
    --from-literal=AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    --dry-run=client -o yaml | kubectl apply -f -

# Add helm repositories
echo "Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo add kafbat-ui https://kafbat.github.io/helm-charts
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager for Let's Encrypt
echo "Installing cert-manager..."
helm upgrade --install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --set crds.enabled=true

# Install ExternalDNS for Cloudflare
echo "Installing ExternalDNS..."
kubectl create secret generic cloudflare-dns \
    --namespace cert-manager \
    --from-literal=cloudflare_api_token=$CLOUDFLARE_API_TOKEN \
    --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install external-dns oci://registry-1.docker.io/bitnamicharts/external-dns \
    -f external-dns-values.yaml \
    --namespace cert-manager \
    --wait

# Wait for cert-manager to be ready
echo "Waiting for cert-manager to be ready..."
kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=60s
kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=60s
kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=60s

# Create keystore password secret first
echo "Creating letsencrypt-staging-key secret..."
kubectl create secret generic letsencrypt-staging-key \
    --dry-run=client -o yaml | kubectl apply -f -
# Create cluster issuer secrets
echo "Creating Let's Encrypt cluster issuer secrets..."
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    # Email address for expiration notices
    email: me@richardroberson.dev
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      # Secret that will contain the ACME private key
      name: letsencrypt-staging-key
    solvers:
    # Use DNS-01 challenge with Cloudflare
    - dns01:
        cloudflare:
          email: me@richardroberson.dev
          apiTokenSecretRef:
            name: cloudflare-dns
            key: cloudflare_api_token
      selector:
        dnsZones:
        - "richardr.dev"
EOF

kubectl wait --for=condition=Ready clusterissuer/letsencrypt-staging --timeout=60s

kubectl create secret generic kafka-jks \
    --from-literal=keystore-password=kafka123 \
    --from-literal=truststore-password=kafka123 \
    --dry-run=client -o yaml | kubectl apply -f -

# Generate SSL certificates for Kafka
echo "Generating SSL certificates for Kafka..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: crt
  namespace: default
spec:
  secretName: crt-secret
  duration: 8760h # 1 year
  renewBefore: 720h # 30 days
  commonName: "*.richardr.dev"
  dnsNames:
  - "*.richardr.dev"
  issuerRef:
    name: letsencrypt-staging
    kind: ClusterIssuer
  keystores:
    jks:
      create: true
      passwordSecretRef:
        name: kafka-jks
        key: keystore-password
    pkcs12:
      create: true
      passwordSecretRef: # Truststore password
        name: kafka-jks
        key: truststore-password
EOF

# Wait for the certificate to be ready
echo "Waiting for Kafka certificate to be ready..."
kubectl wait --for=condition=Ready certificate/crt --timeout=1000s

kubectl get secrets crt-secret -o yaml

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
helm upgrade --install kafka-ui kafbat-ui/kafka-ui -f kafka-ui-values.yaml --wait

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

# Make cert files
echo "Creating cert files..."
mkdir -p ../../web/certs
kubectl get secret crt-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > ../../web/certs/tls.crt
kubectl get secret crt-secret -o jsonpath='{.data.tls\.key}' | base64 -d > ../../web/certs/tls.key

# Download Let's Encrypt Staging CA certificate
curl https://letsencrypt.org/certs/staging/letsencrypt-stg-root-x1.pem -o ../../web/certs/ca.crt

chmod 600 ../../web/certs/tls.key
chmod 644 ../../web/certs/tls.crt
chmod 644 ../../web/certs/ca.crt

