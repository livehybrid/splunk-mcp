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
USE_UV=false

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
        --uv) USE_UV=true ;;
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
        
        # Check for UV first
        if command -v uv &> /dev/null; then
            echo -e "${GREEN}Using UV for dependency installation...${NC}"
            uv sync --extra dev
            USE_UV=true
        elif command -v poetry &> /dev/null; then
            echo -e "${YELLOW}UV not found, using Poetry...${NC}"
            poetry install
        else
            echo -e "${RED}Neither UV nor Poetry found. Please install one of them.${NC}"
            exit 1
        fi
        echo ""
    fi

    # Run standalone test script
    echo -e "${YELLOW}Running standalone tests...${NC}"
    if [ "$USE_UV" = true ]; then
        uv run python test_endpoints.py
    else
        DEBUG=true python test_endpoints.py
    fi
    
    # Run pytest tests
    echo -e "${YELLOW}Running pytest tests...${NC}"
    if [ "$USE_UV" = true ]; then
        uv run pytest tests/test_endpoints_pytest.py --cov=splunk_mcp -v
    else
        pytest tests/test_endpoints_pytest.py --cov=splunk_mcp -v
    fi
    
    # Generate coverage report
    echo -e "${YELLOW}Generating HTML coverage report...${NC}"
    if [ "$USE_UV" = true ]; then
        uv run pytest tests/test_endpoints_pytest.py --cov=splunk_mcp --cov-report=html
    else
        pytest tests/test_endpoints_pytest.py --cov=splunk_mcp --cov-report=html
    fi
fi

echo ""
echo -e "${GREEN}Tests completed!${NC}"
if [ "$USE_DOCKER" = false ]; then
    echo -e "${GREEN}Coverage report is in htmlcov/index.html${NC}"
fi 