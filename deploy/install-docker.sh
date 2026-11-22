#!/usr/bin/env bash
set -euo pipefail

# Install Docker Engine and Docker Compose on Ubuntu 24.04

# Update package information
sudo apt-get update

# Install required packages
sudo apt-get install -y ca-certificates curl

# Create Docker keyring directory
sudo install -m 0755 -d /etc/apt/keyrings

# Download Docker's official signing key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the official Docker APT repository
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# Install Docker Engine and Compose plugin
sudo apt-get update
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Enable Docker at startup
sudo systemctl enable --now docker

# Verify installation
sudo docker --version
sudo docker compose version

echo "Docker installation completed successfully."
