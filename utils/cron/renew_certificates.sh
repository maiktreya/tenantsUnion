#!/usr/bin/env bash
set -euo pipefail

# Minimal renewal script — safely read needed .env variables and run certbot from repo root
repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
data_path="$repo_root/build/nginx/certbot"
cd "$repo_root"

# Read HOSTNAME and DUCKDNS_TOKEN from repo .env without sourcing it
HOSTNAME="$(grep -m1 '^HOSTNAME=' "$repo_root/.env" 2>/dev/null | cut -d= -f2- || echo '')"
DUCKDNS_TOKEN="$(grep -m1 '^DUCKDNS_TOKEN=' "$repo_root/.env" 2>/dev/null | cut -d= -f2- || echo '')"
HOSTNAME="${HOSTNAME:-inquilinato.duckdns.org}"

if [ -z "$DUCKDNS_TOKEN" ]; then
    echo "Error: DUCKDNS_TOKEN missing in $repo_root/.env" >&2
    exit 1
fi

echo "$(date): Starting certificate renewal check for $HOSTNAME"

# Create credentials file for certbot plugin in a safe temp file (avoids writing to root-owned dir)
creds_tmp="$(mktemp)"
printf 'dns_duckdns_token = %s\n' "$DUCKDNS_TOKEN" > "$creds_tmp"
chmod 600 "$creds_tmp"

# Ensure the custom certbot image exists (will auto-build if using docker compose)
# but also build it explicitly for cron safety
if ! docker image inspect custom-certbot:latest &>/dev/null; then
    echo "$(date): Building custom-certbot image..."
    docker build -t custom-certbot ./build/certbot || {
        echo "$(date): Failed to build custom-certbot image" >&2
        exit 1
    }
fi

# Run certbot renew once (use a higher propagation timeout)
# Use docker run directly with --dns to override Docker's embedded DNS timeout
# This ensures certbot can reach public nameservers for Let's Encrypt validation
docker run --rm \
    --dns 8.8.8.8 --dns 8.8.4.4 \
    -v "$creds_tmp:/etc/letsencrypt/duckdns_credentials.ini:ro" \
    -v "$data_path:/etc/letsencrypt" \
    -v "$data_path/www:/var/www/certbot" \
    custom-certbot:latest \
    renew --authenticator dns-duckdns --dns-duckdns-credentials /etc/letsencrypt/duckdns_credentials.ini \
    --dns-duckdns-propagation-seconds 300 --non-interactive

rc=$?
if [ $rc -eq 0 ]; then
    echo "$(date): Certificate renewal check completed successfully"
    docker compose exec nginx nginx -s reload 2>/dev/null || true
else
    echo "$(date): Certificate renewal failed (rc=$rc)"
fi

# Clean up credentials file
rm -f "$creds_tmp"

echo "$(date): Certificate renewal process completed"