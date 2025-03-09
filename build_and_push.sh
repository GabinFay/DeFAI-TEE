#!/bin/bash
set -e

# Hardcoded values
USERNAME="gabinfay"
REPO_NAME="flare-bot"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
TAG="v${TIMESTAMP}"
IMAGE_NAME="ghcr.io/${USERNAME}/${REPO_NAME}:${TAG}"
LATEST_IMAGE_NAME="ghcr.io/${USERNAME}/${REPO_NAME}:latest"

# Read GitHub token from environment
if [ -z "$GITHUB_TOKEN" ]; then
  # If not in environment, try to read from .env file
  if [ -f .env ]; then
    export $(grep "^GITHUB_TOKEN=" .env | xargs)
  fi
  
  if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN not found in environment or .env file"
    exit 1
  fi
fi

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

echo "Successfully built and pushed multi-platform image ${IMAGE_NAME}"
echo "Also tagged and pushed as ${LATEST_IMAGE_NAME}"

# Update .env file with the new image reference if it exists
if [ -f .env ]; then
  # Check if TEE_IMAGE_REFERENCE exists in .env
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
fi 