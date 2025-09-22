#!/bin/bash

# prepare-storage.sh - Auto prepare storage folder for PostgreSQL Docker container
# Usage: ./prepare-storage.sh

set -e  # Exit on any error

# Configuration
STORAGE_DIR="./storage"
POSTGRES_USER_ID=999
POSTGRES_GROUP_ID=999

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is not recommended for development."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted by user."
            exit 1
        fi
    fi
}

# Function to create storage directory
create_storage_dir() {
    print_info "Creating storage directory: ${STORAGE_DIR}"

    if [[ -d "$STORAGE_DIR" ]]; then
        print_warning "Storage directory already exists."

        # Check if directory is empty
        if [[ "$(ls -A $STORAGE_DIR 2>/dev/null)" ]]; then
            print_warning "Storage directory is not empty. Contents:"
            ls -la "$STORAGE_DIR"
            echo
            read -p "Do you want to continue? This may affect existing data (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Aborted by user."
                exit 1
            fi
        fi
    else
        mkdir -p "$STORAGE_DIR"
        print_success "Storage directory created: ${STORAGE_DIR}"
    fi
}

# Function to set proper permissions
set_permissions() {
    print_info "Setting proper permissions for PostgreSQL container..."

    # Check if we can change ownership (requires sudo for non-root users)
    if [[ $EUID -ne 0 ]]; then
        print_info "Setting ownership requires sudo privileges..."
        if command -v sudo >/dev/null 2>&1; then
            sudo chown -R ${POSTGRES_USER_ID}:${POSTGRES_GROUP_ID} "$STORAGE_DIR"
            print_success "Ownership set to postgres user (${POSTGRES_USER_ID}:${POSTGRES_GROUP_ID})"
        else
            print_warning "sudo not available. Setting permissions to 777 as fallback."
            chmod 777 "$STORAGE_DIR"
        fi
    else
        chown -R ${POSTGRES_USER_ID}:${POSTGRES_GROUP_ID} "$STORAGE_DIR"
        print_success "Ownership set to postgres user (${POSTGRES_USER_ID}:${POSTGRES_GROUP_ID})"
    fi

    # Set appropriate permissions
    chmod 755 "$STORAGE_DIR"
    print_success "Permissions set to 755"
}

# Function to create .gitignore entry
update_gitignore() {
    local gitignore_file=".gitignore"

    if [[ -f "$gitignore_file" ]]; then
        # Check if storage/ is already in .gitignore
        if ! grep -q "^storage/$" "$gitignore_file"; then
            print_info "Adding storage/ to .gitignore"
            echo "" >> "$gitignore_file"
            echo "# PostgreSQL data directory" >> "$gitignore_file"
            echo "storage/" >> "$gitignore_file"
            print_success "Added storage/ to .gitignore"
        else
            print_info "storage/ already exists in .gitignore"
        fi
    else
        print_info "Creating .gitignore with storage/ entry"
        cat > "$gitignore_file" << EOF
# PostgreSQL data directory
storage/
EOF
        print_success "Created .gitignore with storage/ entry"
    fi
}

# Function to verify setup
verify_setup() {
    print_info "Verifying setup..."

    if [[ -d "$STORAGE_DIR" ]]; then
        print_success "✓ Storage directory exists: ${STORAGE_DIR}"

        # Check permissions
        local perms=$(stat -f "%Mp%Lp" "$STORAGE_DIR" 2>/dev/null || stat -c "%a" "$STORAGE_DIR" 2>/dev/null)
        print_info "Directory permissions: ${perms}"

        # Check ownership
        local owner=$(stat -f "%Su:%Sg" "$STORAGE_DIR" 2>/dev/null || stat -c "%U:%G" "$STORAGE_DIR" 2>/dev/null)
        print_info "Directory ownership: ${owner}"

        print_success "✓ Setup verification complete"
    else
        print_error "✗ Storage directory was not created properly"
        exit 1
    fi
}

# Function to show next steps
show_next_steps() {
    print_success "Storage folder preparation complete!"
    echo
    print_info "Next steps:"
    echo "1. Make sure your do
    cker-compose.yml uses the bind mount:"
    echo "   volumes:"
    echo "     - ./storage:/var/lib/postgresql/data"
    echo
    echo "2. Start your PostgreSQL container:"
    echo "   docker-compose up -d db"
    echo
    echo "3. Your PostgreSQL data will now persist in the './storage' directory"
    echo
}

# Main execution
main() {
    print_info "PostgreSQL Storage Folder Preparation Script"
    print_info "==========================================="
    echo

    check_root
    create_storage_dir
    set_permissions
    update_gitignore
    verify_setup
    show_next_steps
}

# Run main function
main "$@"