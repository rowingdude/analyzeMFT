#!/bin/bash
# Test runner script for analyzeMFT

set -e

echo "========================================="
echo "analyzeMFT Test Suite"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run tests with timeout
run_test_group() {
    local name=$1
    local command=$2
    
    echo -e "\n${YELLOW}Running: $name${NC}"
    if timeout 30s bash -c "$command"; then
        echo -e "${GREEN}✓ $name passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}"
        return 1
    fi
}

# Track failures
FAILED=0

# 1. Quick syntax check
echo -e "\n${YELLOW}1. Syntax Check${NC}"
python -m py_compile analyzeMFT.py 2>/dev/null && echo -e "${GREEN}✓ Main entry point OK${NC}" || FAILED=$((FAILED+1))

# 2. Fast unit tests
if run_test_group "Fast Unit Tests" "python -m pytest tests/test_constants.py tests/test_config.py -q"; then
    :
else
    FAILED=$((FAILED+1))
fi

# 3. File writer tests
if run_test_group "File Writer Tests" "python -m pytest tests/test_file_writers.py -q"; then
    :
else
    FAILED=$((FAILED+1))
fi

# 4. Test the test generator
echo -e "\n${YELLOW}4. Test Generator${NC}"
if python -c "from src.analyzeMFT.test_generator import create_test_mft; create_test_mft('test_sample.mft', 10)" 2>/dev/null; then
    echo -e "${GREEN}✓ Test generator works${NC}"
    rm -f test_sample.mft
else
    echo -e "${RED}✗ Test generator failed${NC}"
    FAILED=$((FAILED+1))
fi

# 5. CLI test
echo -e "\n${YELLOW}5. CLI Test${NC}"
python -c "from src.analyzeMFT.test_generator import create_test_mft; create_test_mft('test.mft', 10)" 2>/dev/null
if python analyzeMFT.py -f test.mft -o test_output.csv --csv 2>/dev/null; then
    if [ -f test_output.csv ]; then
        lines=$(wc -l < test_output.csv)
        if [ $lines -gt 1 ]; then
            echo -e "${GREEN}✓ CLI works (generated $lines lines)${NC}"
        else
            echo -e "${RED}✗ Output file empty${NC}"
            FAILED=$((FAILED+1))
        fi
    else
        echo -e "${RED}✗ Output file not created${NC}"
        FAILED=$((FAILED+1))
    fi
else
    echo -e "${RED}✗ CLI failed${NC}"
    FAILED=$((FAILED+1))
fi
rm -f test.mft test_output.csv

# 6. Coverage check (optional)
echo -e "\n${YELLOW}6. Coverage Report (Quick)${NC}"
if command -v coverage &> /dev/null; then
    coverage run -m pytest tests/test_constants.py -q 2>/dev/null
    coverage report --include="src/*" | grep -E "TOTAL|src/analyzeMFT" || true
else
    echo "Coverage tool not installed (pip install coverage)"
fi

# Summary
echo -e "\n========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo "Ready for GitHub Actions CI/CD"
else
    echo -e "${RED}$FAILED test groups failed${NC}"
    echo "Please fix issues before pushing"
    exit 1
fi