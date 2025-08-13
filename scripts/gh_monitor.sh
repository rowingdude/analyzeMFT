#!/bin/bash
# GitHub Actions Monitoring Script
# This script interfaces with GitHub to monitor test runs in real-time

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed."
    echo "Install it with: brew install gh (macOS) or apt install gh (Linux)"
    echo "Then authenticate with: gh auth login"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to list recent workflow runs
list_runs() {
    echo -e "${BLUE}Recent workflow runs:${NC}"
    gh run list --limit 10
}

# Function to watch a specific run
watch_run() {
    local run_id=$1
    if [ -z "$run_id" ]; then
        echo "Getting latest run..."
        run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
    fi
    
    echo -e "${YELLOW}Watching run $run_id...${NC}"
    gh run watch $run_id
}

# Function to get logs from failed jobs
get_failed_logs() {
    local run_id=$1
    if [ -z "$run_id" ]; then
        run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
    fi
    
    echo -e "${RED}Getting failed job logs for run $run_id...${NC}"
    gh run view $run_id --log-failed
}

# Function to download all logs
download_logs() {
    local run_id=$1
    if [ -z "$run_id" ]; then
        run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
    fi
    
    echo "Downloading logs for run $run_id..."
    gh run download $run_id
}

# Function to trigger a workflow manually
trigger_workflow() {
    local workflow=$1
    if [ -z "$workflow" ]; then
        workflow="test.yml"
    fi
    
    echo -e "${GREEN}Triggering workflow: $workflow${NC}"
    gh workflow run $workflow
}

# Function to get real-time status
monitor_latest() {
    echo -e "${BLUE}Monitoring latest workflow run...${NC}"
    
    # Get the latest run
    run_info=$(gh run list --limit 1 --json databaseId,status,conclusion,name)
    run_id=$(echo $run_info | jq -r '.[0].databaseId')
    status=$(echo $run_info | jq -r '.[0].status')
    name=$(echo $run_info | jq -r '.[0].name')
    
    echo "Workflow: $name (ID: $run_id)"
    echo "Status: $status"
    
    if [ "$status" = "in_progress" ]; then
        echo "Run is in progress. Watching..."
        gh run watch $run_id
    else
        conclusion=$(echo $run_info | jq -r '.[0].conclusion')
        echo "Run completed with: $conclusion"
        
        if [ "$conclusion" = "failure" ]; then
            echo -e "${RED}Run failed. Getting error logs...${NC}"
            gh run view $run_id --log-failed
        fi
    fi
}

# Main menu
case "${1:-}" in
    list)
        list_runs
        ;;
    watch)
        watch_run $2
        ;;
    logs)
        get_failed_logs $2
        ;;
    download)
        download_logs $2
        ;;
    trigger)
        trigger_workflow $2
        ;;
    monitor)
        monitor_latest
        ;;
    *)
        echo "GitHub Actions Monitor for analyzeMFT"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  list              List recent workflow runs"
        echo "  watch [run_id]    Watch a specific run (or latest)"
        echo "  logs [run_id]     Get failed job logs"
        echo "  download [run_id] Download all logs"
        echo "  trigger [workflow] Trigger a workflow"
        echo "  monitor           Monitor latest run"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 watch 123456789"
        echo "  $0 monitor"
        ;;
esac