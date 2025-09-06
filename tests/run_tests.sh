#!/bin/bash

# ==============================================================================
# Test Runner Script for Sindicato App
# ==============================================================================
# This script provides a single command to run the entire test suite.
# It ensures that:
# 1. The script is run from the project's root directory.
# 2. Necessary Docker containers for integration tests are started.
# 3. Pytest is executed.
# 4. Docker containers are stopped, even if tests fail.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Get the directory of this script ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# --- Change to the project root directory ---
cd "$PROJECT_ROOT"
echo "✅ Changed directory to project root: $(pwd)"

# --- Define Docker Compose files and profile ---
# We use the dev override to expose ports for the integration tests
COMPOSE_FILES="-f docker-compose.yaml -f docker-compose-dev.yaml"
# This profile only starts the database and API, which is all we need for tests.
TEST_PROFILE="Frontend"

# --- Function to clean up Docker containers ---
cleanup() {
    echo "---"
    echo "🛑 Stopping Docker containers..."
    docker-compose $COMPOSE_FILES down --remove-orphans
    echo "✅ Cleanup complete."
}

# --- Trap to ensure cleanup runs on exit ---
# This makes sure that even if tests fail (non-zero exit code), the containers are stopped.
trap cleanup EXIT

# --- Start required services for integration tests ---
echo "---"
echo "🚀 Starting required Docker containers for integration tests (db, server)..."
# We build to ensure we have the latest changes
docker-compose $COMPOSE_FILES --profile $TEST_PROFILE build
# Start in detached mode
docker-compose $COMPOSE_FILES --profile $TEST_PROFILE up -d

echo "✅ Containers are starting in the background. Waiting for them to be healthy..."
# A simple sleep is often sufficient here, but a more robust script might poll the health checks.
sleep 15

# --- Run the tests ---
echo "---"
echo "▶️ Running pytest..."
# We need to add the project root to PYTHONPATH so that `build` is importable
export PYTHONPATH="$PROJECT_ROOT"
pytest

echo "---"
echo "🎉 All tests passed successfully!"

# The 'trap' will handle the cleanup automatically.
exit 0
