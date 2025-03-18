# Common cluster configuration
export CLUSTER_NAME=research-pod-cluster
export MIN_NODES=3
export MAX_NODES=5
export AUTO_SCALING=true
export REGISTRY_NAME=researchpodcontainerregistry

# Digital Ocean specific
export DO_REGION=sfo3  # San Francisco 3
export DO_NODE_SIZE=s-2vcpu-4gb  # View sizes @ https://slugs.do-api.dev

# Azure specific
export AZ_RESOURCE_GROUP=research-pod-rg
export AZ_LOCATION=westus
export AZ_NODE_COUNT=3
export AZ_NODE_SIZE=Standard_B2s_v2  # 2 vCPUs, 8GB RAM

# Google Cloud specific
export GCP_PROJECT_ID=inspired-terra-452206-b0
export GCP_REGION=us-west1
export GCP_ZONE=us-west1-a
export GCP_MACHINE_TYPE=e2-medium  # 2 vCPUs (shared), 4GB RAM

# Registry configuration
export PROJECT_TAG=research-pod