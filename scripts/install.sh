#!/bin/bash
#
# Installation Script for OpenCode Context Filter Proxy
#
# This script sets up the OpenCode wrapper to automatically start
# the context filter proxy whenever you run OpenCode.
#

set -e

# Colours
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

WRAPPER_SCRIPT="$SCRIPT_DIR/opencode-wrapper.sh"
BASHRC="$HOME/.bashrc"

echo "================================================================================"
echo "OpenCode Context Filter Proxy - Installation"
echo "================================================================================"
echo ""

# Check if wrapper script exists
if [ ! -f "$WRAPPER_SCRIPT" ]; then
    echo -e "${RED}✗${NC} Wrapper script not found: $WRAPPER_SCRIPT"
    exit 1
fi

# Make wrapper executable
chmod +x "$WRAPPER_SCRIPT"
echo -e "${GREEN}✓${NC} Wrapper script is executable"

# Check if alias already exists
if grep -q "alias opencode=" "$BASHRC" 2>/dev/null; then
    echo ""
    echo -e "${YELLOW}⚠${NC} OpenCode alias already exists in $BASHRC"
    echo ""
    echo "Current alias:"
    grep "alias opencode=" "$BASHRC"
    echo ""
    read -p "Replace with new wrapper? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}→${NC} Installation cancelled"
        exit 0
    fi
    
    # Remove old alias
    sed -i '/alias opencode=/d' "$BASHRC"
    echo -e "${GREEN}✓${NC} Old alias removed"
fi

# Add new alias
echo "" >> "$BASHRC"
echo "# OpenCode with automatic context filter proxy" >> "$BASHRC"
echo "alias opencode='$WRAPPER_SCRIPT'" >> "$BASHRC"

echo ""
echo -e "${GREEN}✓${NC} Alias added to $BASHRC"
echo ""
echo "================================================================================"
echo "Installation Complete!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo -e "  1. ${BLUE}Reload your shell:${NC}"
echo "     source ~/.bashrc"
echo ""
echo -e "  2. ${BLUE}Update OpenCode configuration:${NC}"
echo "     Edit ~/.config/opencode/opencode.json"
echo "     Change baseURL to: http://localhost:11435/v1"
echo ""
echo -e "  3. ${BLUE}Run OpenCode:${NC}"
echo "     opencode"
echo ""
echo "The proxy will start automatically when you run OpenCode!"
echo ""
echo "To view proxy logs:"
echo "  tail -f /tmp/ollama_context_filter.log"
echo ""
echo "To stop the proxy:"
echo "  kill \$(cat /tmp/ollama_context_filter.pid)"
echo ""
echo "================================================================================"
