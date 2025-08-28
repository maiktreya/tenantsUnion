#!/bin/bash

# ========================================================================================
# Certificate renewal script for DuckDNS domains
# This script should be run via crontab to automatically renew certificates
#
# USAGE:
# 1. Make executable: chmod +x renew-certificates.sh
# 2. Add to crontab: 0 12 * * * /path/to/your/project/renew-certificates.sh
# 3. Or run manually: ./renew-certificates.sh
# ========================================================================================

# Change to script directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

domain="${HOSTNAME:-inquilinato.duckdns.org}"
duckdns_token="${DUCKDNS_TOKEN}"
data_path="./build/nginx/certbot"

echo "$(date): Starting certificate renewal check for $domain"

# Validate environment
if [ -z "$domain" ] || [ -z "$duckdns_token" ]; then
    echo "Error: Missing HOSTNAME or DUCKDNS_TOKEN in environment"
    exit 1
fi

# Create credentials file temporarily
echo "dns_duckdns_token = $duckdns_token" > "$data_path/duckdns_credentials.ini"
chmod 600 "$data_path/duckdns_credentials.ini"

# Attempt renewal
docker compose run --rm --entrypoint "\
    certbot renew \
    --dns-duckdns \
    --dns-duckdns-credentials /etc/letsencrypt/duckdns_credentials.ini \
    --dns-duckdns-propagation-seconds 120 \
    --non-interactive" \
    -v "$PWD/$data_path/duckdns_credentials.ini:/etc/letsencrypt/duckdns_credentials.ini:ro" \
    certbot

if [ $? -eq 0 ]; then
    echo "$(date): Certificate renewal check completed successfully"

    # Reload nginx if certificates were actually renewed
    echo "$(date): Reloading nginx configuration"
    docker compose exec nginx nginx -s reload

    echo "$(date): Nginx reloaded successfully"
else
    echo "$(date): Certificate renewal failed"
fi

# Clean up credentials file
rm -f "$data_path/duckdns_credentials.ini"

echo "$(date): Certificate renewal process completed"