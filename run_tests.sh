#!/bin/bash
# Run tests with coverage and generate HTML report

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
USE_DOCKER=false
INSTALL_DEPS=false

# Determine which docker compose command to use
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --docker) USE_DOCKER=true ;;
        --install) INSTALL_DEPS=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${YELLOW}==========================${NC}"
echo -e "${YELLOW}= Running Splunk MCP Tests =${NC}"
echo -e "${YELLOW}==========================${NC}"
echo ""

if [ "$USE_DOCKER" = true ]; then
    echo -e "${YELLOW}Running tests in Docker...${NC}"
    
    # Clean up any existing containers
    $DOCKER_COMPOSE down
    
    # Build and run tests
    $DOCKER_COMPOSE up --build --abort-on-container-exit test
    
    # Copy test results from container
    docker cp $($DOCKER_COMPOSE ps -q test):/app/test-results ./
    
    # Cleanup
    $DOCKER_COMPOSE down
else
    # Local testing
    if [ "$INSTALL_DEPS" = true ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        if command -v uv &> /dev/null; then
            echo "Using uv for dependency installation..."
            uv pip compile pyproject.toml --extra test -o requirements-test.txt
            uv pip sync requirements-test.txt
            uv pip install -e ".[test]"
        else
            echo "uv not found, falling back to poetry..."
            poetry install
        fi
        echo ""
    fi

    # Run standalone test script
    echo -e "${YELLOW}Running standalone tests...${NC}"
    DEBUG=true python test_endpoints.py
    
    # Run pytest tests
    echo -e "${YELLOW}Running pytest tests...${NC}"
    pytest tests/test_endpoints_pytest.py --cov=splunk_mcp -v
    
    # Generate coverage report
    echo -e "${YELLOW}Generating HTML coverage report...${NC}"
    pytest tests/test_endpoints_pytest.py --cov=splunk_mcp --cov-report=html
fi

echo ""
echo -e "${GREEN}Tests completed!${NC}"
if [ "$USE_DOCKER" = false ]; then
    echo -e "${GREEN}Coverage report is in htmlcov/index.html${NC}"
fi 