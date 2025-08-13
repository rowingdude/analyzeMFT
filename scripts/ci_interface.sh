#!/bin/bash
# CI Interface Script - Direct interface with GitHub Actions

set -e

# Configuration
REPO="rowingdude/analyzeMFT"
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}GitHub Actions CI Interface${NC}"
echo "Repository: $REPO"
echo "Branch: $BRANCH"
echo ""

# Function to setup GitHub CLI
setup_gh() {
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
        
        # Detect OS and install
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install gh
        else
            echo -e "${RED}Please install GitHub CLI manually: https://cli.github.com${NC}"
            exit 1
        fi
    fi
    
    # Check authentication
    if ! gh auth status &> /dev/null; then
        echo -e "${YELLOW}Please authenticate with GitHub:${NC}"
        gh auth login
    fi
}

# Function to push and monitor
push_and_monitor() {
    echo -e "${YELLOW}Pushing current branch to GitHub...${NC}"
    git push origin $BRANCH
    
    echo -e "${YELLOW}Waiting for workflow to start...${NC}"
    sleep 5
    
    # Get the latest run for this branch
    run_id=$(gh run list --branch $BRANCH --limit 1 --json databaseId --jq '.[0].databaseId' -R $REPO)
    
    if [ -z "$run_id" ]; then
        echo -e "${RED}No workflow run found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Monitoring run $run_id...${NC}"
    gh run watch $run_id -R $REPO
    
    # Get conclusion
    conclusion=$(gh run view $run_id --json conclusion --jq '.conclusion' -R $REPO)
    
    if [ "$conclusion" = "failure" ]; then
        echo -e "${RED}Run failed! Getting error details...${NC}"
        gh run view $run_id --log-failed -R $REPO | head -100
        
        # Parse and show test failures
        echo -e "\n${YELLOW}Test Failures Summary:${NC}"
        gh run view $run_id --log-failed -R $REPO | grep -E "FAILED|ERROR" | head -20
        
        return 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    fi
}

# Function to run tests locally first
local_test() {
    echo -e "${BLUE}Running local tests first...${NC}"
    
    if [ -f "run_tests.sh" ]; then
        bash run_tests.sh
    else
        python -m pytest tests/ -q --tb=no --maxfail=5
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Local tests failed. Fix them before pushing.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Local tests passed!${NC}"
    return 0
}

# Function to get real-time logs
stream_logs() {
    local run_id=$1
    if [ -z "$run_id" ]; then
        run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId' -R $REPO)
    fi
    
    echo -e "${BLUE}Streaming logs for run $run_id...${NC}"
    
    # Stream logs in real-time
    while true; do
        status=$(gh run view $run_id --json status --jq '.status' -R $REPO)
        
        if [ "$status" = "completed" ]; then
            break
        fi
        
        # Get current logs
        gh run view $run_id --log -R $REPO | tail -50
        
        sleep 5
    done
    
    conclusion=$(gh run view $run_id --json conclusion --jq '.conclusion' -R $REPO)
    echo -e "\nRun completed: $conclusion"
}

# Function to fetch errors as JSON
get_errors_json() {
    local run_id=$1
    if [ -z "$run_id" ]; then
        run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId' -R $REPO)
    fi
    
    # Create JSON output
    echo "{"
    echo "  \"run_id\": $run_id,"
    echo "  \"errors\": ["
    
    gh run view $run_id --log-failed -R $REPO | grep -E "FAILED|ERROR" | while read -r line; do
        escaped=$(echo "$line" | sed 's/"/\\"/g')
        echo "    \"$escaped\","
    done | sed '$ s/,$//'
    
    echo "  ]"
    echo "}"
}

# Main menu
case "${1:-}" in
    setup)
        setup_gh
        ;;
    test)
        local_test
        ;;
    push)
        local_test && push_and_monitor
        ;;
    monitor)
        push_and_monitor
        ;;
    stream)
        stream_logs $2
        ;;
    errors)
        get_errors_json $2
        ;;
    status)
        gh run list --limit 5 -R $REPO
        ;;
    *)
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  setup    - Setup GitHub CLI"
        echo "  test     - Run local tests"
        echo "  push     - Run tests locally, then push and monitor"
        echo "  monitor  - Push and monitor GitHub Actions"
        echo "  stream   - Stream logs from a run"
        echo "  errors   - Get errors as JSON"
        echo "  status   - Show recent runs"
        echo ""
        echo "Examples:"
        echo "  $0 setup"
        echo "  $0 test"
        echo "  $0 push"
        echo "  $0 errors"
        ;;
esac