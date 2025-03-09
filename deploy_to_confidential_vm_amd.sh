#!/bin/bash

# This script deploys the Flare Swap app to a Google Cloud Confidential VM using AMD SEV
# Prerequisites: gcloud CLI installed and configured, .env file with required variables

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Flare Swap App - Deploy to Confidential VM (AMD SEV)${NC}"
echo "This script will deploy your application to a Google Cloud Confidential VM."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found. Please create it based on .env.template.${NC}"
    exit 1
fi

# Source the .env file
echo "Loading environment variables from .env file..."
source .env

# Check for required variables
if [ -z "$INSTANCE_NAME" ] || [ -z "$TEE_IMAGE_REFERENCE" ] || [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}Error: Required environment variables are missing in .env file.${NC}"
    echo "Please make sure INSTANCE_NAME, TEE_IMAGE_REFERENCE, and GEMINI_API_KEY are set."
    exit 1
fi

# Check if VM already exists
VM_EXISTS=$(gcloud compute instances list --filter="name=${INSTANCE_NAME}" --format="get(name)" 2>/dev/null)
if [ ! -z "$VM_EXISTS" ]; then
    echo -e "${YELLOW}Warning: A VM with the name '${INSTANCE_NAME}' already exists.${NC}"
    read -p "Do you want to delete the existing VM and create a new one? (y/n): " DELETE_VM
    if [[ $DELETE_VM == "y" || $DELETE_VM == "Y" ]]; then
        echo -e "${YELLOW}Deleting existing VM '${INSTANCE_NAME}'...${NC}"
        gcloud compute instances delete $INSTANCE_NAME --zone=us-central1-c --quiet
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to delete the existing VM. Please check the error messages above.${NC}"
            exit 1
        fi
        echo -e "${GREEN}Existing VM deleted successfully.${NC}"
    else
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Confirm deployment
echo ""
echo "You are about to deploy a Confidential VM with the following configuration:"
echo "Instance Name: $INSTANCE_NAME"
echo "TEE Image Reference: $TEE_IMAGE_REFERENCE"
echo "Zone: us-central1-c"
echo "Machine Type: n2d-standard-2"
echo ""
read -p "Do you want to continue? (y/n): " CONFIRM
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Creating Confidential VM instance...${NC}"

# Create the Confidential VM with all environment variables from .env
gcloud compute instances create $INSTANCE_NAME \
  --project=verifiable-ai-hackathon \
  --zone=us-central1-c \
  --machine-type=n2d-standard-2 \
  --network-interface=network-tier=PREMIUM,nic-type=GVNIC,stack-type=IPV4_ONLY,subnet=default \
  --metadata=tee-image-reference=$TEE_IMAGE_REFERENCE,\
tee-container-log-redirect=true,\
tee-env-GEMINI_API_KEY=$GEMINI_API_KEY,\
tee-env-ETHEREUM_RPC_URL=$ETHEREUM_RPC_URL,\
tee-env-BASE_RPC_URL=$BASE_RPC_URL,\
tee-env-FLARE_RPC_URL=$FLARE_RPC_URL,\
tee-env-WALLET_ADDRESS=$WALLET_ADDRESS,\
tee-env-PRIVATE_KEY=$PRIVATE_KEY,\
tee-env-REACT_APP_RAINBOW_PROJECT_ID=$REACT_APP_RAINBOW_PROJECT_ID,\
tee-env-GITHUB_TOKEN=$GITHUB_TOKEN \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=confidential-sa@verifiable-ai-hackathon.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --min-cpu-platform="AMD Milan" \
  --tags=flare-ai-core,http-server,https-server \
  --create-disk=auto-delete=yes,boot=yes,\
device-name=$INSTANCE_NAME,\
image=projects/confidential-space-images/global/images/confidential-space-debug-250100,mode=rw,size=11,type=pd-standard \
  --shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --labels=goog-ec-src=vm_add-gcloud \
  --reservation-affinity=any \
  --confidential-compute-type=SEV

# Check if VM creation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create the VM. Please check the error messages above.${NC}"
    exit 1
fi

# Get the external IP of the VM
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=us-central1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Create firewall rule to allow HTTP port 80 if it doesn't exist
FIREWALL_EXISTS=$(gcloud compute firewall-rules list --filter="name=allow-http" --format="get(name)")
if [ -z "$FIREWALL_EXISTS" ]; then
    echo ""
    echo -e "${GREEN}Creating firewall rule for HTTP port 80...${NC}"
    gcloud compute firewall-rules create allow-http \
        --project=verifiable-ai-hackathon \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:80 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=flare-ai-core
fi

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Your Confidential VM has been deployed with the following details:"
echo "Instance Name: $INSTANCE_NAME"
echo "External IP: $EXTERNAL_IP"
echo "Access your application at: http://$EXTERNAL_IP"
echo ""
echo "To view logs, run:"
echo "gcloud logging read \"resource.type=gce_instance AND resource.labels.instance_id=$(gcloud compute instances describe $INSTANCE_NAME --zone=us-central1-c --format='get(id)')\" --project=verifiable-ai-hackathon"
echo ""
echo "To restart the VM (to pull updated images), run:"
echo "gcloud compute instances stop $INSTANCE_NAME --zone=us-central1-c"
echo "gcloud compute instances start $INSTANCE_NAME --zone=us-central1-c"
echo ""
echo "Note: It may take a few minutes for the application to start. If you cannot access it immediately, please wait and try again." 