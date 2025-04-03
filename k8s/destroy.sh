#!/bin/bash

# Source shared environment variables
source "$(dirname "$0")/env.sh"

# Function to display usage
usage() {
    echo "Usage: $0 [--azure | --docean | --gcp]"
    echo "  --azure   Destroy Azure resources"
    echo "  --docean  Destroy Digital Ocean resources"
    echo "  --gcp     Destroy Google Cloud resources"
    exit 1
}

destroy_kubectl() {
    echo "Destroying kubectl resources..."
    helm uninstall -n cert-manager cert-manager external-dns
    helm uninstall kafka kafka-ui research-consumer web-api ingress-nginx redis --ignore-not-found
    helm delete yugabyte -n yugabyte
    kubectl delete pvc --all --force
    kubectl delete namespaces yugabyte cert-manager

    echo "Kubectl resources destruction completed!"
}

# Function to destroy Azure resources
destroy_azure() {
    echo "Destroying Azure resources..."
    destroy_kubectl # Destroy kubectl resources first
    
    # Delete the AKS cluster
    echo "Deleting AKS cluster..."
    az aks delete \
        --resource-group $AZ_RESOURCE_GROUP \
        --name $CLUSTER_NAME \
        --yes --no-wait

    # Delete the Azure Container Registry
    echo "Deleting Azure Container Registry..."
    az acr delete \
        --resource-group $AZ_RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --yes

    # Delete the resource group
    echo "Deleting resource group..."
    az group delete \
        --name $AZ_RESOURCE_GROUP \
        --yes

    echo "Azure resources destruction completed!"
}

# Function to destroy Digital Ocean resources
destroy_docean() {
    echo "Destroying Digital Ocean resources..."
    destroy_kubectl # Destroy kubectl resources first

    # Delete the Kubernetes cluster
    echo "Deleting Kubernetes cluster..."
    doctl kubernetes cluster delete $CLUSTER_NAME-do --force --dangerous

    # Delete the container registry
    echo "Deleting container registry..."
    doctl registry delete $REGISTRY_NAME --force

    echo "Digital Ocean resources destruction completed!"
}

# Function to destroy GCP resources
destroy_gcp() {
    echo "Destroying Google Cloud resources..."
    destroy_kubectl # Destroy kubectl resources first

    # Delete the GKE cluster
    echo "Deleting GKE cluster..."
    gcloud container clusters delete $CLUSTER_NAME-gcp \
        --region $GCP_REGION \
        --project $GCP_PROJECT_ID \
        --quiet

    # Delete the Artifact Registry repository
    echo "Deleting Artifact Registry repository..."
    gcloud artifacts repositories delete $REGISTRY_NAME \
        --location=$GCP_REGION \
        --project $GCP_PROJECT_ID \
        --quiet

    echo "Google Cloud resources destruction completed!"
}

# Parse command line arguments
if [ $# -ne 1 ]; then
    usage
fi

case "$1" in
    --azure)
        destroy_azure
        ;;
    --docean)
        destroy_docean
        ;;
    --gcp)
        destroy_gcp
        ;;
    *)
        usage
        ;;
esac