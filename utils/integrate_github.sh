#!/bin/bash

# GitHub SSH Key Setup Script for Ubuntu
# This script automates SSH key generation and setup for GitHub access

set -e  # Exit on any error

echo "🔐 GitHub SSH Key Setup Script"
echo "================================"

# Check if running on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Ubuntu. Proceeding anyway..."
fi

# Function to prompt for user input
prompt_user() {
    read -p "$1: " input
    echo "$input"
}

# Get user information
echo
echo "📝 Setting up Git configuration..."
GIT_NAME=$(prompt_user "Enter your full name for Git")
GIT_EMAIL=$(prompt_user "Enter your email address")
KEY_COMMENT=$(prompt_user "Enter a comment for the SSH key (e.g., 'Hetzner Server')" || echo "$GIT_EMAIL")

# Set Git global configuration
echo "🔧 Configuring Git..."
git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
echo "✅ Git configured successfully"

# Check if SSH key already exists
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"
if [ -f "$SSH_KEY_PATH" ]; then
    echo
    read -p "🔑 SSH key already exists at $SSH_KEY_PATH. Overwrite? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "📋 Using existing SSH key..."
        echo "Public key content:"
        echo "===================="
        cat "$SSH_KEY_PATH.pub"
        echo "===================="
        echo
        echo "🌐 Next steps:"
        echo "1. Copy the public key above"
        echo "2. Go to: https://github.com/settings/ssh"
        echo "3. Click 'New SSH key'"
        echo "4. Paste the key and save"
        echo "5. Test with: ssh -T git@github.com"
        exit 0
    fi
fi

# Generate SSH key
echo
echo "🔑 Generating SSH key..."
ssh-keygen -t ed25519 -C "$KEY_COMMENT" -f "$SSH_KEY_PATH" -N ""
echo "✅ SSH key generated successfully"

# Start SSH agent and add key
echo
echo "🔄 Starting SSH agent and adding key..."
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"
echo "✅ SSH key added to agent"

# Display the public key
echo
echo "📋 Your SSH public key:"
echo "======================="
cat "$SSH_KEY_PATH.pub"
echo "======================="

# Copy to clipboard if possible
if command -v xclip &> /dev/null; then
    cat "$SSH_KEY_PATH.pub" | xclip -selection clipboard
    echo "📎 Public key copied to clipboard!"
elif command -v pbcopy &> /dev/null; then
    cat "$SSH_KEY_PATH.pub" | pbcopy
    echo "📎 Public key copied to clipboard!"
fi

# Final instructions
echo
echo "🌐 Next steps:"
echo "1. Copy the public key above (if not automatically copied)"
echo "2. Go to: https://github.com/settings/ssh"
echo "3. Click 'New SSH key'"
echo "4. Give it a title (e.g., '$KEY_COMMENT')"
echo "5. Paste the key and click 'Add SSH key'"
echo
echo "🧪 After adding the key to GitHub, test the connection with:"
echo "   ssh -T git@github.com"
echo
echo "🎉 Setup complete! You can now clone private repositories using SSH URLs."
echo "   Example: git clone git@github.com:username/repo.git"