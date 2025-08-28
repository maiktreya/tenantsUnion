#!/bin/bash

# ========================================================================================
# This script automates SSL certificate setup for DuckDNS domains using DNS-01 challenge
# It handles the creation of dummy certificates, then requests real certificates via DNS
#
# USAGE:
# 1. Make this script executable: chmod +x init-letsencrypt-duckdns.sh
# 2. Set your environment variables in .env file:
#    - HOSTNAME=inquilinato.duckdns.org
#    - DUCKDNS_TOKEN=566ab832-c328-4750-865e-6cd9d979f68d
#    - EMAIL=garciaduchm@gmail.com (or your preferred email)
# 3. Run it: ./init-letsencrypt-duckdns.sh
# ========================================================================================

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# --- CONFIGURATION ---
domain="${HOSTNAME:-inquilinato.duckdns.org}"
email="${EMAIL:-garciaduchm@gmail.com}"
duckdns_token="${DUCKDNS_TOKEN:-566ab832-c328-4750-865e-6cd9d979f68d}"
data_path="./build/nginx/certbot"
rsa_key_size=4096
staging=0 # Set to 1 to use staging environment for testing

# --- VALIDATION ---
if [ -z "$domain" ]; then
    echo "Error: HOSTNAME not set in .env file or environment"
    exit 1
fi

if [ -z "$duckdns_token" ]; then
    echo "Error: DUCKDNS_TOKEN not set in .env file or environment"
    exit 1
fi

if [ -z "$email" ]; then
    echo "Error: EMAIL not set in .env file or environment"
    exit 1
fi

echo "Setting up SSL for domain: $domain"
echo "Using email: $email"
echo "DuckDNS token: ${duckdns_token:0:8}..."

if [ -d "$data_path" ]; then
    read -p "Existing data found for $domain. Continue and replace existing certificate? (y/N) " decision
    if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
        exit
    fi
fi

# --- DOWNLOAD TLS PARAMETERS ---
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
    echo "### Downloading recommended TLS parameters ..."
    mkdir -p "$data_path/conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
    echo
fi

# --- DUMMY CERTIFICATE CREATION ---
echo "### Creating dummy certificate for $domain ..."
path="/etc/letsencrypt/live/$domain"
mkdir -p "$data_path/conf/live/$domain"

# Dummy creation
docker compose --profile Secured run --rm --entrypoint "\
    openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot

# --- START NGINX ---
echo "### Starting nginx with dummy certificates ..."
docker compose --profile Secured up --force-recreate -d nginx
echo

# Wait for nginx to start
sleep 5

# --- CLEANUP DUMMY CERTIFICATES ---
echo "### Deleting dummy certificate for $domain ..."
# Dummy deletion
docker compose --profile Secured run --rm --entrypoint "\
    rm -Rf /etc/letsencrypt/live/$domain && \
    rm -Rf /etc/letsencrypt/archive/$domain && \
    rm -Rf /etc/letsencrypt/renewal/$domain.conf" certbot
echo

# --- REQUEST REAL CERTIFICATES ---
echo "### Requesting Let's Encrypt certificate for $domain using DNS-01 challenge ..."

# Select appropriate email arg
case "$email" in
    "") email_arg="--register-unsafely-without-email" ;;
    *) email_arg="--email $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then
    staging_arg="--staging"
    echo "### STAGING MODE ENABLED - Testing with Let's Encrypt staging environment"
else
    staging_arg=""
fi

# Create DuckDNS credentials file
echo "dns_duckdns_token = $duckdns_token" > "$data_path/duckdns_credentials.ini"
chmod 600 "$data_path/duckdns_credentials.ini"

# Request certificate using DNS-01 challenge
docker compose --profile Secured run --rm --entrypoint "\
    certbot certonly \
    --authenticator dns-duckdns \
    --dns-duckdns-credentials /etc/letsencrypt/duckdns_credentials.ini \
    --dns-duckdns-propagation-seconds 120 \
    $staging_arg \
    $email_arg \
    -d $domain \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal \
    --non-interactive" \
    -v "$PWD/$data_path/duckdns_credentials.ini:/etc/letsencrypt/duckdns_credentials.ini:ro" \
    certbot

if [ $? -eq 0 ]; then
    echo "### Certificate obtained successfully!"

    # Clean up credentials file for security
    rm -f "$data_path/duckdns_credentials.ini"

    # --- RELOAD NGINX ---
    echo "### Reloading nginx with new certificates ..."
    docker compose exec nginx nginx -s reload

    echo ""
    echo "### SSL setup complete! ###"
    echo "Your site should now be accessible at: https://$domain"
    echo ""
    echo "Certificate will auto-renew. To manually renew:"
    echo "  docker compose run --rm certbot renew"
    echo ""

    # Verify certificate
    echo "### Certificate information:"
    docker compose run --rm --entrypoint "\
        openssl x509 -in /etc/letsencrypt/live/$domain/fullchain.pem -text -noout | grep -A 2 'Validity'" certbot

else
    echo "### Certificate request failed!"
    echo "Check the logs above for errors."
    echo "Common issues:"
    echo "  - DuckDNS token is incorrect"
    echo "  - Domain doesn't exist or isn't pointing to your server"
    echo "  - Rate limiting (try staging mode first)"
    rm -f "$data_path/duckdns_credentials.ini"
    exit 1
fi