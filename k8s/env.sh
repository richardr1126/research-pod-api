# Common cluster configuration
export CLUSTER_NAME=research-pod-cluster
export MIN_NODES=3
export MAX_NODES=5
export AUTO_SCALING=true

# Digital Ocean specific
export DO_REGION=sfo3  # San Francisco 3
export DO_NODE_SIZE=s-2vcpu-8gb-amd  # View sizes @ https://slugs.do-api.dev
export DO_REGISTRY_NAME=research-pod-registry

# Azure specific
export AZ_RESOURCE_GROUP=research-pod-rg
export AZ_LOCATION=westus
export AZ_ACR_NAME=researchpodacr
export AZ_NODE_COUNT=3
export AZ_NODE_SIZE=Standard_B2s_v2  # 2 vCPUs, 4GB RAM

# Registry configuration
export PROJECT_TAG=research-pod