#!/bin/bash
# daily_sync.sh
# Dynamic ETL: Extracts last 24h Gravity Forms data, enriches via CartoCiudad, and loads to PostgreSQL.
# Include as crontab -e: 0 2 * * * $HOME/github/prod/tenantsUnion/utils/cron/daily_sync.sh >> $HOME/github/prod/tenantsUnion/utils/cron/cron_errors.log 2>&1

set -e # Exit immediately if a command exits with a non-zero status

: "${HOME:?HOME is not set — aborting}"
PROJECT_DIR="${HOME}/github/prod/tenantsUnion"
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
GEOLINK_SCRIPT_PATH="${PROJECT_DIR}/ETL/02-geolink.py"
PG_IMPORT_SCRIPT="${PROJECT_DIR}/ETL/03-load-from-csv.sql"
CSV_DEST_PATH="${PROJECT_DIR}/dev/back/SI_MAD/db_fork/mariadb_export.csv" 
CSV_TMP_PATH="${CSV_DEST_PATH}.tmp"

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
    if [ -f "$CSV_TMP_PATH" ]; then
        rm -f "$CSV_TMP_PATH"
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
echo "[$TIMESTAMP] Executing SQL extraction from target engine..." >> "$LOG_FILE"
mysql -h "$TARGET_MYSQL_HOST" -P "$TARGET_MYSQL_PORT" -u "$WP_DB_USER" -p"$WP_DB_PASS" "$WP_DB_NAME" < "$SQL_QUERY_PATH" | sed "s/'/\'/;s/\t/\",\"/g;s/^/\"/;s/$/\"/;s/\n//g" > "$CSV_DEST_PATH"

# 3. Check if CSV has data (more than just the header row) before running enrichment
if [ $(wc -l < "$CSV_DEST_PATH") -le 1 ]; then
    echo "[$TIMESTAMP] No new records found in the last 24 hours. Aborting pipeline." >> "$LOG_FILE"
    exit 0
fi

# ==============================================================================
# 2b. ENRICHMENT PHASE (GEO-LINKING & SANITIZATION)
# ==============================================================================
echo "[$TIMESTAMP] Injecting Geo-Link enrichment & address sanitation..." >> "$LOG_FILE"
# Activate virtual environment if needed (e.g., source ${PROJECT_DIR}/.venv/bin/activate)
if [ -d "${PROJECT_DIR}/.venv" ]; then
    source "${PROJECT_DIR}/.venv/bin/activate"
fi

# Process the CSV file using the temporary track
python3 "$GEOLINK_SCRIPT_PATH" "$CSV_DEST_PATH" "$CSV_TMP_PATH" >> "$LOG_FILE" 2>&1

# Atomically overwrite original file path with the enriched dataset
mv "$CSV_TMP_PATH" "$CSV_DEST_PATH"

# Deactivate virtual environment if it was opened
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# ==============================================================================
# 4. TRIGGER POSTGRESQL DATA INTEGRATION
# ==============================================================================
echo "[$TIMESTAMP] Triggering PostgreSQL Import Script..." >> "$LOG_FILE"
docker exec -i "$DB_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$PG_IMPORT_SCRIPT" >> "$LOG_FILE" 2>&1

echo "[$TIMESTAMP] ETL pipeline completed successfully." >> "$LOG_FILE"