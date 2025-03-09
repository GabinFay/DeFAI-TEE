#!/bin/bash
set -e

# Load environment variables
source .env

# Set default values if not provided
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
IMAGE_NAME=${IMAGE_NAME:-"flare-bot"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
REGION=${REGION:-"us-central1"}
ZONE=${ZONE:-"us-central1-a"}
MACHINE_TYPE=${MACHINE_TYPE:-"n2d-standard-2"}
VM_NAME=${VM_NAME:-"flare-bot-tee"}

# Build and push the Docker image
echo "Building and pushing Docker image..."
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG .
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG

# Deploy to Confidential VM
echo "Deploying to Confidential VM..."
gcloud compute instances create-with-container $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --subnet=default \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --image=projects/confidential-space-images/global/images/confidential-space-debug-v0-10-0 \
  --image-project=confidential-space-images \
  --confidential-compute \
  --shielded-secure-boot \
  --container-image=gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG \
  --container-restart-policy=always \
  --container-env=GEMINI_API_KEY=$GEMINI_API_KEY,ETHEREUM_RPC_URL=$ETHEREUM_RPC_URL,BASE_RPC_URL=$BASE_RPC_URL,FLARE_RPC_URL=$FLARE_RPC_URL,WALLET_ADDRESS=$WALLET_ADDRESS,PRIVATE_KEY=$PRIVATE_KEY,SIMULATE_ATTESTATION=$SIMULATE_ATTESTATION \
  --tags=http-server,https-server

# Create firewall rules if they don't exist
echo "Ensuring firewall rules exist..."
gcloud compute firewall-rules describe allow-http 2>/dev/null || \
  gcloud compute firewall-rules create allow-http \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server

gcloud compute firewall-rules describe allow-https 2>/dev/null || \
  gcloud compute firewall-rules create allow-https \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=https-server

# Get the external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Deployment complete!"
echo "Your application is available at: https://$EXTERNAL_IP"
echo "Note: You may see a certificate warning in your browser since we're using a self-signed certificate."
echo "You can safely proceed by clicking 'Advanced' and then 'Proceed to $EXTERNAL_IP (unsafe)'." 