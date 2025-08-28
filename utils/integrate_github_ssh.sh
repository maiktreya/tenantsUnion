#!/bin/bash

# ==============================================================================
# Minimal Development Setup Script
# ==============================================================================
# This script provides a streamlined setup for a DEVELOPMENT or TESTING
# environment. It clones the private repo and launches the app stack
# directly, without Nginx, firewall, or SSL configuration.
#
# USAGE:
# 1. Update the GITHUB_REPO_SSH variable below.
# 2. Make this script executable: chmod +x minimal_dev_setup.sh
# 3. Run with sudo: sudo ./minimal_dev_setup.sh your-email@example.com
# ==============================================================================

# --- Script Configuration ---
set -e # Exit immediately on error.

# --- Variables ---
EMAIL=$1
PROJECT_DIR="tenantsUnion"
# IMPORTANT: UPDATE THIS WITH YOUR REPOSITORY'S SSH CLONE URL
GITHUB_REPO_SSH="git@github.com:maiktreya/tenantsUnion.git"

# --- Helper Functions ---
info() { echo -e "\033[1;34m[INFO] $1\033[0m"; }
success() { echo -e "\033[1;32m[SUCCESS] $1\033[0m"; }
warn() { echo -e "\033[1;33m[WARNING] $1\033[0m"; }
error() { echo -e "\033[1;31m[ERROR] $1\033[0m"; exit 1; }

# --- Pre-flight Checks ---
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root. Please use sudo."
fi
if [ -z "$EMAIL" ]; then
    echo "Usage: $0 <your-email@example.com>"
    exit 1
fi

# --- Step 1: Install Prerequisites ---
info "Installing Git and Docker..."
apt-get update > /dev/null
apt-get install -y git docker.io docker-compose > /dev/null
success "Dependencies installed."

# --- Step 2: Setup GitHub SSH Access ---
info "Setting up SSH access for private GitHub repository..."
SSH_DIR="/root/.ssh"
SSH_KEY_PATH="$SSH_DIR/id_ed25519"
mkdir -p "$SSH_DIR" && chmod 700 "$SSH_DIR"

if [ ! -f "$SSH_KEY_PATH" ]; then
    info "Generating a new SSH key for GitHub..."
    ssh-keygen -t ed25519 -C "$EMAIL" -f "$SSH_KEY_PATH" -N ""
    success "New SSH key generated."
fi

info "ACTION REQUIRED: Add the following SSH public key to your repository's Deploy Keys."
warn "Go to: Your Repo > Settings > Deploy Keys > Add deploy key (Read-only access is recommended)."
echo -e "\n--- SSH Public Key ---\n"
cat "${SSH_KEY_PATH}.pub"
echo -e "\n--- End of Key ---\n"
read -p "Press [Enter] to continue once the deploy key has been added..."

# --- Step 3: Clone Repository & Configure ---
if [ -d "$PROJECT_DIR" ]; then
    warn "Project directory '$PROJECT_DIR' already exists. Skipping clone."
    cd "$PROJECT_DIR"
else
    info "Cloning the private project repository..."
    GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -i $SSH_KEY_PATH" git clone "$GITHUB_REPO_SSH"
    cd "$PROJECT_DIR"
    success "Repository cloned."
fi

info "Setting up .env file..."
if [ ! -f ".env" ]; then
    NICEGUI_SECRET=$(openssl rand -hex 32)
    cat > .env << EOF
# === PostgreSQL Credentials ===
POSTGRES_USER=app_user
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb
POSTGRES_DB_SCHEMA=sindicato_inq
POSTGRES_API_URL=http://server:3000
NICEGUI_STORAGE_SECRET=${NICEGUI_SECRET}
EOF
    success ".env file created."
fi

# --- Step 4: Launch The Application ---
info "Building and launching the development application stack..."
# Using the "Frontend" profile exposes the app directly on port 8081
docker-compose --profile Frontend up -d

success "Development environment is now running!"
info "You can access the application at: http://<your-server-ip>:8081"
info "To view logs, run: docker-compose logs -f"
