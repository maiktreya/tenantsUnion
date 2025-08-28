#!/bin/bash

# ==============================================================================
# Deployment Pipeline for Sindicato de Inquilinas Management System
# ==============================================================================
# This script automates the setup of the application on a fresh Ubuntu host.
# It handles dependency installation, configuration, firewall setup, SSL
# certificate generation, and application launch.
#
# USAGE:
# 1. Make this script executable:
#    chmod +x deploy_on_ubuntu.sh
#
# 2. Run the script with your domain and email:
#    sudo ./deploy_on_ubuntu.sh your-domain.com your-email@example.com
#
# You must run this script with sudo privileges.
# ==============================================================================

# --- Script Configuration ---
set -e # Exit immediately if a command exits with a non-zero status.

# --- Variables ---
DOMAIN=$1
EMAIL=$2
PROJECT_DIR="tenantsUnion"
GITHUB_REPO="https://github.com/maiktreya/tenantsUnion.git"

# --- Helper Functions for colored output ---
info() {
    echo -e "\033[1;34m[INFO] $1\033[0m"
}

success() {
    echo -e "\033[1;32m[SUCCESS] $1\033[0m"
}

warn() {
    echo -e "\033[1;33m[WARNING] $1\033[0m"
}

error() {
    echo -e "\033[1;31m[ERROR] $1\033[0m"
    exit 1
}

# --- Pre-flight Checks ---
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root. Please use sudo."
    fi
}

validate_input() {
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        echo "Usage: $0 <your-domain.com> <your-email@example.com>"
        exit 1
    fi
}

# --- Step 1: Install Prerequisites ---
install_dependencies() {
    info "Updating package lists..."
    apt-get update

    info "Installing Git, Docker, and Docker Compose..."
    apt-get install -y git ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update

    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    success "Dependencies installed successfully."
}

# --- Step 2: Clone Project Repository ---
clone_repository() {
    if [ -d "$PROJECT_DIR" ]; then
        warn "Project directory '$PROJECT_DIR' already exists. Skipping clone."
    else
        info "Cloning the project repository..."
        git clone "$GITHUB_REPO"
        success "Repository cloned successfully."
    fi
    cd "$PROJECT_DIR"
}

# --- Step 3: Configure Environment ---
setup_environment_file() {
    info "Setting up the .env configuration file..."
    if [ -f ".env" ]; then
        warn ".env file already exists. Skipping creation."
    else
        # Generate a random secret for NiceGUI storage
        NICEGUI_SECRET=$(openssl rand -hex 32)

        # Create the .env file from the template
        cat > .env << EOF
# === PostgreSQL Credentials ===
POSTGRES_USER=app_user
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb
POSTGRES_DB_SCHEMA=sindicato_inq
POSTGRES_API_URL=http://server:3000
NICEGUI_STORAGE_SECRET=${NICEGUI_SECRET}
EOF
        success ".env file created with a new NICEGUI_STORAGE_SECRET."
    fi
}

# --- Step 4: Setup Firewall ---
configure_firewall() {
    info "Configuring the firewall with UFW..."
    if ufw status | grep -q "Status: active"; then
        warn "UFW is already active. Skipping firewall setup."
    else
        # Use the existing script to set up the firewall
        chmod +x utils/setup_firewall.sh
        ./utils/setup_firewall.sh
        success "Firewall configured and enabled."
    fi
}

# --- Step 5: Generate SSL Certificates ---
generate_ssl_certificates() {
    info "Generating SSL certificates with Let's Encrypt..."
    # The init-letsencrypt.sh script handles dummy certs, starting nginx,
    # and requesting real certs.
    chmod +x utils/init-letsencrypt.sh
    ./utils/init-letsencrypt.sh "$DOMAIN" "$EMAIL"
    success "SSL certificates generated successfully."
}

# --- Step 6: Launch The Application ---
launch_application() {
    info "Building and launching the application containers..."
    # Using the "Secured" and "Frontend" profiles for production
    docker compose --profile Secured --profile Frontend up -d

    info "Waiting a few moments for services to start..."
    sleep 15

    success "Application is now running!"
    info "You can access it at: https://$DOMAIN"
    info "To check the status of the containers, run: docker compose ps"
    info "To view logs, run: docker compose logs -f"
}

# --- Main Execution Pipeline ---
main() {
    check_root
    validate_input
    install_dependencies
    clone_repository
    setup_environment_file
    configure_firewall
    generate_ssl_certificates
    launch_application
}

main "$@"
