#!/bin/bash

# ==============================================================================
# UFW Firewall Configuration Script for Sindicato App
# ==============================================================================
# This script configures UFW (Uncomplicated Firewall) with a secure set of
# rules for the application environment.
#
# It will:
# 1. Reset any existing UFW rules.
# 2. Set default policies to deny incoming and allow outgoing traffic.
# 3. Allow SSH connections (port 22) to prevent being locked out.
# 4. Allow HTTP (port 80) and HTTPS (port 443) for the web server.
# 5. Enable the firewall.
# ==============================================================================

# --- IMPORTANT: SSH Configuration ---
# If you use a non-standard port for SSH, change this value.
SSH_PORT="22"

echo "### Configuring UFW Firewall ###"

# Ensure UFW is installed
if ! [ -x "$(command -v ufw)" ]; then
  echo "UFW is not installed. Please install it first (e.g., sudo apt-get install ufw)"
  exit 1
fi

# Reset UFW to a clean state to avoid conflicting rules
echo "-> Resetting UFW to default settings..."
sudo ufw --force reset

# 1. Set default policies
echo "-> Setting default policies (DENY incoming, ALLOW outgoing)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 2. Allow essential services
# IMPORTANT: This rule is critical to maintain access to your server.
echo "-> Allowing SSH connections on port $SSH_PORT..."
sudo ufw allow $SSH_PORT/tcp comment 'Allow SSH connections'

# 3. Allow application-specific ports (for the Nginx reverse proxy)
echo "-> Allowing HTTP traffic on port 80..."
sudo ufw allow 80/tcp comment 'Allow HTTP traffic for Nginx'

echo "-> Allowing HTTPS traffic on port 443..."
sudo ufw allow 443/tcp comment 'Allow HTTPS traffic for Nginx'

# Note: Ports 5432 (PostgreSQL), 3001 (PostgREST), and 8081 (NiceGUI)
# are managed by Docker's internal network and should not be exposed
# publicly. Nginx is the only entry point.

# 4. Enable the firewall
echo "-> Enabling the firewall..."
sudo ufw enable

# 5. Show the configured rules
echo "### UFW Configuration Complete ###"
sudo ufw status verbose

echo "Firewall is now active and configured."