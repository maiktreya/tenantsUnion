#!/bin/bash
# daily_sync.sh
# Extracts last 24h Gravity Forms data over SSH tunnel and pipes into Sindicato PostgreSQL.
# include as crontab -e: 0 2 * * * /home/other/github/prod/tenantsUnion/utils/cron/daily_sync.sh >> /home/other/github/prod/tenantsUnion/utils/cron/cron_errors.log 2>&1

set -e # Exit immediately if a command exits with a non-zero status

PROJECT_DIR="/home/other/github/prod/tenantsUnion"
LOG_FILE="${PROJECT_DIR}/utils/cron/tenants_sync.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# ==============================================================================
# SECURE CREDENTIAL INJECTION
# ==============================================================================
# Load environment variables from the project .env file safely
ENV_FILE="${PROJECT_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
else
    echo "[$TIMESTAMP] ERROR: .env file not found at $ENV_FILE" >> "$LOG_FILE"
    exit 1
fi

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# SSH Tunnel Configuration (Variables injected from .env)
SSH_KEY="/home/other/.ssh/id_rsa"
TUNNEL_SOCKET="/tmp/mariadb_tunnel_socket"
LOCAL_DB_PORT="33306"
REMOTE_DB_HOST="127.0.0.1"
REMOTE_DB_PORT="3306"

# PostgreSQL (Sindicato) Docker Config
DB_CONTAINER_NAME="tenantsunion-db-1" # Confirm this matches: docker ps
# Note: POSTGRES_USER and POSTGRES_DB are now injected directly from your .env file!

# File Paths
SQL_QUERY_PATH="${PROJECT_DIR}/utils/cron/01-extract_24h.sql"
PG_IMPORT_SCRIPT="${PROJECT_DIR}/utils/cron/02-migrate-from-mariadb-csv.sql"
CSV_DEST_PATH="${PROJECT_DIR}/dev/back/SI_MAD/db_fork/mariadb_export.csv" 

# ==============================================================================
# CLEANUP TRAP (Ensures tunnel closes and CSV is deleted)
# ==============================================================================
cleanup() {
    echo "[$TIMESTAMP] Running cleanup procedures..." >> "$LOG_FILE"
    
    if [ -S "$TUNNEL_SOCKET" ]; then
        echo "[$TIMESTAMP] Closing SSH tunnel..." >> "$LOG_FILE"
        ssh -S "$TUNNEL_SOCKET" -O exit "${SSH_USER}@${SSH_HOST}" 2>/dev/null || true
    fi

    if [ -f "$CSV_DEST_PATH" ]; then
        rm -f "$CSV_DEST_PATH"
    fi
}
trap cleanup EXIT

# ==============================================================================
# PIPELINE EXECUTION
# ==============================================================================
echo "[$TIMESTAMP] Starting daily ETL pipeline..." >> "$LOG_FILE"

# 1. Establish SSH Tunnel
echo "[$TIMESTAMP] Establishing SSH tunnel to MariaDB on port $SSH_PORT..." >> "$LOG_FILE"
ssh -M -S "$TUNNEL_SOCKET" -fnNT -L "${LOCAL_DB_PORT}:${REMOTE_DB_HOST}:${REMOTE_DB_PORT}" -i "$SSH_KEY" -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}"

sleep 3 # Wait briefly to ensure the tunnel is ready

# 2. Extract from MariaDB to CSV
echo "[$TIMESTAMP] Extracting from MariaDB via tunnel..." >> "$LOG_FILE"
mysql -h 127.0.0.1 -P "$LOCAL_DB_PORT" -u "$WP_DB_USER" -p"$WP_DB_PASS" "$WP_DB_NAME" < "$SQL_QUERY_PATH" | sed "s/'/\'/;s/\t/\",\"/g;s/^/\"/;s/$/\"/;s/\n//g" > "$CSV_DEST_PATH"

# 3. Check if CSV has data (more than just the header row)
if [ $(wc -l < "$CSV_DEST_PATH") -le 1 ]; then
    echo "[$TIMESTAMP] No new records found in the last 24 hours. Aborting DB import." >> "$LOG_FILE"
    exit 0
fi

# 4. Trigger PostgreSQL ETL Script
echo "[$TIMESTAMP] Triggering PostgreSQL Import Script..." >> "$LOG_FILE"
docker exec -i "$DB_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$PG_IMPORT_SCRIPT" >> "$LOG_FILE" 2>&1

echo "[$TIMESTAMP] ETL pipeline completed successfully." >> "$LOG_FILE"