# Common cluster configuration
export CLUSTER_NAME=research-pod-cluster
export MIN_NODES=3
export MAX_NODES=5
export AUTO_SCALING=true
export REGISTRY_NAME=researchpodcontainerregistry

# Digital Ocean specific
export DO_REGION=sfo3  # San Francisco 3
export DO_NODE_SIZE=s-2vcpu-8gb-amd  # View sizes @ https://slugs.do-api.dev

# Azure specific
export AZ_RESOURCE_GROUP=research-pod-rg
export AZ_LOCATION=westus
export AZ_NODE_SIZE=Standard_B2s_v2  # 2 vCPUs, 8GB RAM
# GPU configuration
export AZ_GPU_POOL_NAME=t4gpus
export AZ_GPU_VM_SIZE=Standard_NC4as_T4_v3
export AZ_GPU_NODE_COUNT=2
export AZ_GPU_MIN_COUNT=2
export AZ_GPU_MAX_COUNT=2
export AZ_GPU_TAINTS="sku=gpu:NoSchedule,kubernetes.azure.com/scalesetpriority=spot:NoSchedule"

# Google Cloud specific
export GCP_PROJECT_ID=inspired-terra-452206-b0
export GCP_REGION=us-west1
export GCP_ZONE=us-west1-b
export GCP_MACHINE_TYPE=e2-standard-2  # 2 vCPUs, 8GB RAM
# GPU configuration
export GCP_DISK_TYPE=pd-ssd
export GCP_DISK_SIZE=75
export GCP_GPU_POOL_NAME=gpu-t4-pool
export GCP_GPU_MACHINE_TYPE=n1-standard-4
export GCP_GPU_DISK_TYPE=pd-balanced
export GCP_GPU_DISK_SIZE=75
export GCP_GPU_TYPE=nvidia-tesla-t4
export GCP_GPU_COUNT=1
export GCP_GPU_NODE_COUNT=1

# Registry configuration
export PROJECT_TAG=research-pod