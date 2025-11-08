#!/bin/bash
#
# OpenCode Wrapper Script with Automatic Context Filter Proxy
#
# This wrapper automatically starts the Ollama Context Filter Proxy
# before launching OpenCode, ensuring minimal context for small models.
#
# Installation:
#   1. Make executable: chmod +x opencode-wrapper.sh
#   2. Add to PATH or create alias in ~/.bashrc:
#      alias opencode='/home/gunnar/github/architecture_as_code/opencode-wrapper.sh'
#

set -e

# Configuration
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

PROXY_SCRIPT="$REPO_ROOT/src/ollama_context_filter_proxy.py"
PROXY_PORT=11435
PROXY_PID_FILE="/tmp/ollama_context_filter.pid"
PROXY_LOG_FILE="/tmp/ollama_context_filter.log"
OPENCODE_BIN="/home/gunnar/.opencode/bin/opencode"

# Colours for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

# Function to check if proxy is running
is_proxy_running() {
    if [ -f "$PROXY_PID_FILE" ]; then
        local pid=$(cat "$PROXY_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to check if port is in use
is_port_in_use() {
    lsof -i :$PROXY_PORT > /dev/null 2>&1
}

# Function to start proxy
start_proxy() {
    if is_proxy_running; then
        echo -e "${GREEN}✓${NC} Context filter proxy already running (PID: $(cat $PROXY_PID_FILE))"
        return 0
    fi
    
    if is_port_in_use; then
        echo -e "${YELLOW}⚠${NC} Port $PROXY_PORT in use, attempting to reclaim..."
        lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    echo -e "${YELLOW}→${NC} Starting Ollama context filter proxy..."
    
    # Start proxy in background
    nohup python3 -u "$PROXY_SCRIPT" > "$PROXY_LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PROXY_PID_FILE"
    
    # Wait for proxy to start
    local retries=0
    while ! is_port_in_use && [ $retries -lt 10 ]; do
        sleep 0.5
        retries=$((retries + 1))
    done
    
    if is_port_in_use; then
        echo -e "${GREEN}✓${NC} Context filter proxy started successfully (PID: $pid)"
        echo -e "${GREEN}✓${NC} Filtering context for: llama3.2:1b, qwen2.5:1.5b"
        echo -e "${GREEN}✓${NC} Proxy logs: $PROXY_LOG_FILE"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start proxy"
        return 1
    fi
}

# Function to stop proxy on exit
cleanup() {
    # Don't stop proxy on exit - keep it running for next session
    :
}

# Register cleanup function
trap cleanup EXIT

# Main execution
echo "================================================================================"
echo "OpenCode with Context Filter Proxy"
echo "================================================================================"
echo ""

# Check if proxy script exists
if [ ! -f "$PROXY_SCRIPT" ]; then
    echo -e "${RED}✗${NC} Proxy script not found: $PROXY_SCRIPT"
    echo -e "${YELLOW}→${NC} Running OpenCode without context filtering..."
    echo ""
    exec "$OPENCODE_BIN" "$@"
fi

# Check if OpenCode binary exists
if [ ! -f "$OPENCODE_BIN" ]; then
    echo -e "${RED}✗${NC} OpenCode not found: $OPENCODE_BIN"
    echo -e "${YELLOW}→${NC} Please install OpenCode first: curl -fsSL https://opencode.ai/install | bash"
    exit 1
fi

# Start proxy if needed
if ! start_proxy; then
    echo -e "${YELLOW}→${NC} Running OpenCode without context filtering..."
fi

echo ""
echo -e "${GREEN}→${NC} Launching OpenCode..."
echo "================================================================================"
echo ""

# Launch OpenCode with all arguments passed through
exec "$OPENCODE_BIN" "$@"
