#!/bin/bash
# daily_sync.sh
# Dynamic ETL: Extracts last 24h Gravity Forms data over an SSH tunnel OR a direct IP link.
# Include as crontab -e: 0 2 * * * /home/other/github/prod/tenantsUnion/utils/cron/daily_sync.sh >> /home/other/github/prod/tenantsUnion/utils/cron/cron_errors.log 2>&1

set -e # Exit immediately if a command exits with a non-zero status

PROJECT_DIR="/home/other/github/prod/tenantsUnion"
LOG_FILE="${PROJECT_DIR}/utils/cron/tenants_sync.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# ==============================================================================
# SECURE CREDENTIAL INJECTION
# ==============================================================================
ENV_FILE="${PROJECT_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source <(grep -vE '^(UID|EUID|PPID)=' "$ENV_FILE")
    set +o allexport
else
    echo "[$TIMESTAMP] ERROR: .env file not found at $ENV_FILE" >> "$LOG_FILE"
    exit 1
fi

# Set a fallback connection mode if it's missing from the .env file
CONNECTION_MODE="${GF_CONNECTION_MODE:-tunnel}"

# ==============================================================================
# NETWORKING TARGET SETUP
# ==============================================================================
TUNNEL_SOCKET="/tmp/mariadb_tunnel_socket"
LOCAL_DB_PORT="33306"
REMOTE_DB_HOST="127.0.0.1"
REMOTE_DB_PORT="3306"

if [ "$CONNECTION_MODE" = "direct" ]; then
    TARGET_MYSQL_HOST="$WP_DB_HOST"
    TARGET_MYSQL_PORT="${WP_DB_PORT:-3306}"
    echo "[$TIMESTAMP] Pipeline configured for DIRECT network connection to ${TARGET_MYSQL_HOST}:${TARGET_MYSQL_PORT}." >> "$LOG_FILE"
else
    TARGET_MYSQL_HOST="127.0.0.1"
    TARGET_MYSQL_PORT="$LOCAL_DB_PORT"
    echo "[$TIMESTAMP] Pipeline configured for SECURE SSH TUNNEL transport mapping." >> "$LOG_FILE"
fi

# Execution Paths
SQL_QUERY_PATH="${PROJECT_DIR}/${ETL_EXTRACT_PATH#./}"
PG_IMPORT_SCRIPT="${PROJECT_DIR}/ETL/03-load-from-csv.sql"
CSV_DEST_PATH="${PROJECT_DIR}/dev/back/SI_MAD/db_fork/mariadb_export.csv" 

# ==============================================================================
# CLEANUP TRAP
# ==============================================================================
cleanup() {
    echo "[$TIMESTAMP] Running cleanup procedures..." >> "$LOG_FILE"
    
    # Only try to close the tunnel if we're in tunnel mode and the socket exists
    if [ "$CONNECTION_MODE" = "tunnel" ] && [ -S "$TUNNEL_SOCKET" ]; then
        echo "[$TIMESTAMP] Closing active SSH tunnel instance..." >> "$LOG_FILE"
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
echo "[$TIMESTAMP] Starting daily ETL pipeline orchestration..." >> "$LOG_FILE"

# 1. Network Initialization (Conditional on mode)
if [ "$CONNECTION_MODE" = "tunnel" ]; then
    echo "[$TIMESTAMP] Establishing SSH tunnel to remote instance on port $SSH_PORT..." >> "$LOG_FILE"
    ssh -M -S "$TUNNEL_SOCKET" -fnNT -L "${LOCAL_DB_PORT}:${REMOTE_DB_HOST}:${REMOTE_DB_PORT}" -i "$SSH_KEY" -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}"
    sleep 3 # Wait for the socket to stabilize
fi

# 2. Extract Data via MySQL CLI Client Tools
# Note: The 'mysql' client safely handles communication with both MariaDB and standard MySQL servers seamlessly.
echo "[$TIMESTAMP] Executing SQL extraction from target engine..." >> "$LOG_FILE"
mysql -h "$TARGET_MYSQL_HOST" -P "$TARGET_MYSQL_PORT" -u "$WP_DB_USER" -p"$WP_DB_PASS" "$WP_DB_NAME" < "$SQL_QUERY_PATH" | sed "s/'/\'/;s/\t/\",\"/g;s/^/\"/;s/$/\"/;s/\n//g" > "$CSV_DEST_PATH"

# 3. Check if CSV has data (more than just the header row)
if [ $(wc -l < "$CSV_DEST_PATH") -le 1 ]; then
    echo "[$TIMESTAMP] No new records found in the last 24 hours. Aborting DB import." >> "$LOG_FILE"
    exit 0
fi

# 4. Trigger PostgreSQL Data Integration
echo "[$TIMESTAMP] Triggering PostgreSQL Import Script..." >> "$LOG_FILE"
docker exec -i "$DB_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$PG_IMPORT_SCRIPT" >> "$LOG_FILE" 2>&1

echo "[$TIMESTAMP] ETL pipeline completed successfully." >> "$LOG_FILE"