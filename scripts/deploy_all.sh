#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Flare Swap App - Automated Build, Push, and Deploy to Confidential VM (AMD SEV)${NC}"
echo "This script will build the Docker image, push it to GHCR, and deploy to a Google Cloud Confidential VM."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found. Please create it based on .env.template.${NC}"
    exit 1
fi

# Source the .env file
echo "Loading environment variables from .env file..."
source .env

# Hardcoded values for image building
USERNAME="gabinfay"
REPO_NAME="flare-bot"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
TAG="v${TIMESTAMP}"
IMAGE_NAME="ghcr.io/${USERNAME}/${REPO_NAME}:${TAG}"
LATEST_IMAGE_NAME="ghcr.io/${USERNAME}/${REPO_NAME}:latest"

# Check for required variables
if [ -z "$INSTANCE_NAME" ] || [ -z "$GEMINI_API_KEY" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: Required environment variables are missing in .env file.${NC}"
    echo "Please make sure INSTANCE_NAME, GEMINI_API_KEY, and GITHUB_TOKEN are set."
    exit 1
fi

# PART 1: BUILD AND PUSH DOCKER IMAGE
echo -e "\n${GREEN}STEP 1: Building and pushing Docker image${NC}"

echo "Logging in to GitHub Container Registry"
echo $GITHUB_TOKEN | docker login ghcr.io -u ${USERNAME} --password-stdin

# Create and use a new builder instance with multi-platform support
echo "Setting up Docker Buildx for multi-platform builds"
docker buildx create --name multiplatform-builder --use || true
docker buildx use multiplatform-builder
docker buildx inspect --bootstrap

echo "Building and pushing multi-platform Docker image: ${IMAGE_NAME}"
# Build and push for both ARM64 and AMD64 platforms
docker buildx build --platform linux/amd64,linux/arm64 \
  --tag ${IMAGE_NAME} \
  --tag ${LATEST_IMAGE_NAME} \
  --push \
  .

echo -e "${GREEN}Successfully built and pushed multi-platform image ${IMAGE_NAME}${NC}"
echo "Also tagged and pushed as ${LATEST_IMAGE_NAME}"

# Update .env file with the new image reference
if grep -q "^TEE_IMAGE_REFERENCE=" .env; then
    # Replace the existing TEE_IMAGE_REFERENCE line
    sed -i.bak "s|^TEE_IMAGE_REFERENCE=.*|TEE_IMAGE_REFERENCE=${IMAGE_NAME}|" .env
    rm -f .env.bak
    echo "Updated TEE_IMAGE_REFERENCE in .env file to ${IMAGE_NAME}"
else
    # Add TEE_IMAGE_REFERENCE if it doesn't exist
    echo "TEE_IMAGE_REFERENCE=${IMAGE_NAME}" >> .env
    echo "Added TEE_IMAGE_REFERENCE to .env file"
fi

# Re-source the .env file to get the updated TEE_IMAGE_REFERENCE
source .env

# PART 2: DEPLOY TO CONFIDENTIAL VM
echo -e "\n${GREEN}STEP 2: Deploying to Confidential VM${NC}"

# Check if VM already exists
VM_EXISTS=$(gcloud compute instances list --filter="name=${INSTANCE_NAME}" --format="get(name)" 2>/dev/null)
if [ ! -z "$VM_EXISTS" ]; then
    echo -e "${YELLOW}VM with the name '${INSTANCE_NAME}' already exists. Deleting it...${NC}"
    gcloud compute instances delete $INSTANCE_NAME --zone=us-central1-c --quiet
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to delete the existing VM. Please check the error messages above.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Existing VM deleted successfully.${NC}"
fi

echo ""
echo "Deploying a Confidential VM with the following configuration:"
echo "Instance Name: $INSTANCE_NAME"
echo "TEE Image Reference: $TEE_IMAGE_REFERENCE"
echo "Zone: us-central1-c"
echo "Machine Type: n2d-standard-2"
echo "Attestation: Real (SIMULATE_ATTESTATION=false)"
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
tee-env-GITHUB_TOKEN=$GITHUB_TOKEN,\
tee-env-SIMULATE_ATTESTATION=$SIMULATE_ATTESTATION \
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
echo "Attestation: Real (SIMULATE_ATTESTATION=false)"
echo ""
echo "To view logs, run:"
echo "gcloud logging read \"resource.type=gce_instance AND resource.labels.instance_id=$(gcloud compute instances describe $INSTANCE_NAME --zone=us-central1-c --format='get(id)')\" --project=verifiable-ai-hackathon"
echo ""
echo "To restart the VM (to pull updated images), run:"
echo "gcloud compute instances stop $INSTANCE_NAME --zone=us-central1-c"
echo "gcloud compute instances start $INSTANCE_NAME --zone=us-central1-c"
echo ""
echo "Note: It may take a few minutes for the application to start. If you cannot access it immediately, please wait and try again." 