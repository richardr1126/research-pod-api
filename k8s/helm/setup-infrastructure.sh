#!/bin/bash

# Setup script for general helm chart installations (infrastructure components)
# For local k3s server deployment

# Source shared environment variables
source "$(dirname "$0")/../env.sh"

# Exit on any error
set -e

# Parse command line arguments
CLEAR=false

for arg in "$@"; do
  if [ "$arg" == "--clear" ]; then
    CLEAR=true
  else
    echo "Unknown parameter: $arg"
    echo "Usage: $0 [--clear]"
    echo "  --clear: Clear existing infrastructure resources before setup"
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

# Clear existing infrastructure resources if --clear flag is set
if [ "$CLEAR" = true ]; then
  echo "Clearing existing infrastructure resources..."
  helm uninstall -n cert-manager cert-manager external-dns --wait --ignore-not-found
  helm uninstall -n yugabyte yugabyte --wait --ignore-not-found
  helm uninstall -n monitoring prometheus loki --wait --ignore-not-found
  helm uninstall kafka kafka-ui redis ingress-nginx --wait --ignore-not-found
  
  echo "Deleting cert-manager CRDs..."
  kubectl delete crd certificates.cert-manager.io --ignore-not-found
  kubectl delete crd certificaterequests.cert-manager.io --ignore-not-found
  kubectl delete crd challenges.acme.cert-manager.io --ignore-not-found
  kubectl delete crd clusterissuers.cert-manager.io --ignore-not-found
  kubectl delete crd issuers.cert-manager.io --ignore-not-found
  kubectl delete crd orders.acme.cert-manager.io --ignore-not-found

  echo "Deleting namespaces and persistent volume claims..."
  kubectl delete namespaces yugabyte cert-manager monitoring --wait --ignore-not-found
  kubectl delete pvc --all --force --ignore-not-found
  
  sleep 10
fi

# Add helm repositories
echo "Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo add kafbat-ui https://kafbat.github.io/helm-charts
helm repo add jetstack https://charts.jetstack.io
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add yugabytedb https://charts.yugabyte.com
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install cert-manager for Let's Encrypt
# echo "Installing cert-manager..."
# helm upgrade --install -n cert-manager cert-manager jetstack/cert-manager \
#   --create-namespace \
#   --version v1.17.1 \
#   -f ./cert-manager/values.yaml \
#   --wait

# # Install ExternalDNS for Cloudflare (if Cloudflare token is provided)
# if [ ! -z "$CLOUDFLARE_API_TOKEN" ]; then
#   echo "Installing ExternalDNS..."
#   kubectl create secret generic cloudflare-dns \
#     --namespace cert-manager \
#     --from-literal=cloudflare_api_token=$CLOUDFLARE_API_TOKEN \
#     --dry-run=client -o yaml | kubectl apply -f -
#   helm upgrade --install external-dns oci://registry-1.docker.io/bitnamicharts/external-dns \
#     --version 8.7.10 \
#     -f ./ingress/external-dns-values.yaml \
#     --namespace cert-manager \
#     --wait
# else
#   echo "Skipping ExternalDNS installation (CLOUDFLARE_API_TOKEN not provided)"
# fi

# # Wait for cert-manager to be ready
# echo "Waiting for cert-manager to be ready..."
# kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=60s
# kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=60s
# kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=60s

# # Create keystore password secret first
# echo "Creating letsencrypt-prod-key secret..."
# kubectl create secret generic letsencrypt-prod-key \
#   --dry-run=client -o yaml | kubectl apply -f -

# # Create cluster issuer secrets
# echo "Creating Let's Encrypt cluster issuer secrets..."
# kubectl apply -f ./cert-manager/cluster-issuer.yaml

kubectl wait --for=condition=Ready clusterissuer/letsencrypt-prod --timeout=60s

# Install NGINX Ingress Controller (commented out for k3s since it often comes with Traefik)
# echo "Installing NGINX Ingress Controller..."
# helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
#   --version 4.12.1 \
#   -f ./ingress/nginx-values.yaml \
#   --wait

# # Install kube-prometheus-stack
# echo "Installing kube-prometheus-stack..."
# helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
#   --version 70.4.1 \
#   -f ./prometheus-grafana-stack.yaml \
#   --namespace monitoring \
#   --create-namespace \
#   --wait

# # Install Loki
# echo "Installing Loki..."
# helm upgrade --install loki grafana/loki-stack \
#   --namespace monitoring \
#   --set loki.isDefault=false \
#   --wait 

# Install Redis standalone master
echo "Installing Redis..."
helm upgrade --install redis oci://registry-1.docker.io/bitnamicharts/redis \
  --version 20.11.4 \
  -f redis-values.yaml \
  --wait

# Install Kafka bitnami chart
echo "Installing Kafka..."
helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka \
  --version 31.4.1 \
  -f kafka-values.yaml \
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
  kubectl exec -it kafka-client -- kafka-topics.sh \
    --create \
    --if-not-exists \
    --bootstrap-server kafka.default.svc.cluster.local:9092 \
    --command-config /tmp/client.properties \
    --replication-factor 2 \
    --partitions 2 \
    --topic "$topic"
done

# Clean up the client pod
echo "Cleaning up Kafka client pod..."
kubectl delete pod kafka-client --ignore-not-found

echo "Installing kafka UI chart..."
helm upgrade --install kafka-ui kafbat-ui/kafka-ui \
  --version 1.5.0 \
  -f kafka-ui-values.yaml \
  --wait

# Cleanup old ybdb secret
kubectl delete secrets -n yugabyte yugabyte-tls-client-cert --ignore-not-found
kubectl delete secrets -n default yugabyte-tls-client-cert --ignore-not-found

# Install yugabytedb
# echo "Installing YugabyteDB..."
# helm upgrade --install yugabyte yugabytedb/yugabyte --namespace yugabyte --create-namespace \
#   --version 2024.2.2 \
#   -f yugabyte-values.yaml \
#   --wait \
#   --timeout 15m

# # Copy YugabyteDB TLS client cert secret to default namespace
# echo "Copying YugabyteDB TLS client cert secret to default namespace..."
# kubectl get secret yugabyte-tls-client-cert -n yugabyte -o yaml | \
#   sed 's/namespace: yugabyte/namespace: default/' | \
#   kubectl apply -f -

# Create the researchpod user and database
echo "Creating researchpod user and database..."
kubectl exec --namespace yugabyte -it yb-tserver-0 -- /bin/bash -c 'export PGPASSWORD=yugabyte; /home/yugabyte/bin/ysqlsh -h yb-tserver-0.yb-tservers.yugabyte -U yugabyte -d yugabyte -c "CREATE USER researchpod WITH PASSWORD '\''researchpod-password'\'' SUPERUSER CREATEDB CREATEROLE; CREATE DATABASE researchpod OWNER researchpod;"' || true

# Connect to ysql shell
echo "Adding vector extension to YugabyteDB..."
kubectl exec --namespace yugabyte -it yb-tserver-0 -- /bin/bash -c 'export PGPASSWORD=researchpod-password; /home/yugabyte/bin/ysqlsh -h yb-tserver-0.yb-tservers.yugabyte -U researchpod -d researchpod -c "CREATE EXTENSION IF NOT EXISTS vector;"' || true

echo "Grafana admin password:"
kubectl --namespace monitoring get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

echo "Infrastructure setup complete!"
echo ""
echo "Next steps:"
echo "1. Run './deploy-apps.sh --build' to build and deploy your application components"
echo "2. Check that all pods are running: kubectl get pods --all-namespaces"
echo "3. Access Grafana dashboard using the password printed above"
