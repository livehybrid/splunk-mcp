# Splunk MCP (Model Context Protocol) Tool

A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language. This tool provides a set of capabilities for searching Splunk data, managing KV stores, and accessing Splunk resources through an intuitive interface.

## Operating Modes

The tool operates in three modes:

1. **SSE Mode** (Default)
   - Server-Sent Events based communication
   - Real-time bidirectional interaction
   - Suitable for web-based MCP clients
   - Default mode when no arguments provided
   - Access via `/sse` endpoint

2. **API Mode**
   - RESTful API endpoints
   - Access via `/api/v1` endpoint prefix
   - Start with `python splunk_mcp.py api`

3. **STDIO Mode**
   - Standard input/output based communication
   - Compatible with Claude Desktop and other MCP clients
   - Ideal for direct integration with AI assistants
   - Start with `python splunk_mcp.py stdio`

## Features

- **Splunk Search**: Execute Splunk searches with natural language queries
- **Index Management**: List and inspect Splunk indexes
- **User Management**: View and manage Splunk users
- **KV Store Operations**: Create, list, and manage KV store collections
- **Async Support**: Built with async/await patterns for better performance
- **Detailed Logging**: Comprehensive logging with emoji indicators for better visibility
- **SSL Configuration**: Flexible SSL verification options for different security requirements
- **Enhanced Debugging**: Detailed connection and error logging for troubleshooting
- **Comprehensive Testing**: Unit tests covering all major functionality
- **Error Handling**: Robust error handling with appropriate status codes
- **SSE Compliance**: Fully compliant with MCP SSE specification

## Available MCP Tools

The following tools are available via the MCP interface:

### Tools Management
- **list_tools**
  - Lists all available MCP tools with their descriptions and parameters

### Health Check
- **health_check**
  - Returns a list of available Splunk apps to verify connectivity
- **ping**
  - Simple ping endpoint to verify MCP server is alive

### User Management
- **current_user**
  - Returns information about the currently authenticated user
- **list_users**
  - Returns a list of all users and their roles

### Index Management
- **list_indexes**
  - Returns a list of all accessible Splunk indexes
- **get_index_info**
  - Returns detailed information about a specific index
  - Parameters: index_name (string)
- **indexes_and_sourcetypes**
  - Returns a comprehensive list of indexes and their sourcetypes

### Search
- **search_splunk**
  - Executes a Splunk search query
  - Parameters: 
    - search_query (string): Splunk search string
    - earliest_time (string, optional): Start time for search window
    - latest_time (string, optional): End time for search window
    - max_results (integer, optional): Maximum number of results to return
- **list_saved_searches**
  - Returns a list of saved searches in the Splunk instance

### KV Store
- **list_kvstore_collections**
  - Lists all KV store collections
- **create_kvstore_collection**
  - Creates a new KV store collection
  - Parameters: collection_name (string)
- **delete_kvstore_collection**
  - Deletes an existing KV store collection
  - Parameters: collection_name (string)

## SSE Endpoints

When running in SSE mode, the following endpoints are available:

- **/sse**: Returns SSE connection information in text/event-stream format
  - Provides metadata about the SSE connection
  - Includes URL for the messages endpoint
  - Provides protocol and capability information

- **/sse/messages**: The main SSE stream endpoint
  - Streams system events like heartbeats
  - Maintains persistent connection
  - Sends properly formatted SSE events

- **/sse/health**: Health check endpoint for SSE mode
  - Returns status and version information in SSE format

## Error Handling

The MCP implementation includes consistent error handling:

- Invalid search commands or malformed requests
- Insufficient permissions
- Resource not found
- Invalid input validation
- Unexpected server errors
- Connection issues with Splunk server

All error responses include a detailed message explaining the error.

## Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Splunk Enterprise/Cloud instance
- Appropriate Splunk credentials with necessary permissions

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd splunk-mcp
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

4. Update the `.env` file with your Splunk credentials:
```env
SPLUNK_HOST=your_splunk_host
SPLUNK_PORT=8089
SPLUNK_USERNAME=your_username
SPLUNK_PASSWORD=your_password
SPLUNK_SCHEME=https
VERIFY_SSL=true
FASTMCP_LOG_LEVEL=INFO
```

### Option 2: Docker Installation

1. Pull the latest image:
```bash
docker pull livehybrid/splunk-mcp:latest
```

2. Create your `.env` file as above or use environment variables directly.

3. Run using Docker Compose:
```bash
docker-compose up -d
```

Or using Docker directly:
```bash
docker run -i \
  --env-file .env \
  livehybrid/splunk-mcp
```

## Usage

### Local Usage

The tool can run in three modes:

1. SSE mode (default for MCP clients):
```bash
# Start in SSE mode (default)
poetry run python splunk_mcp.py
# or explicitly:
poetry run python splunk_mcp.py sse

# Use uvicorn directly:
SERVER_MODE=api poetry run uvicorn splunk_mcp:app --host 0.0.0.0 --port 8000 --reload
```

3. STDIO mode:
```bash
poetry run python splunk_mcp.py stdio
```

### Docker Usage

The project supports both the new `docker compose` (V2) and legacy `docker-compose` (V1) commands. The examples below use V2 syntax, but both are supported.

1. SSE Mode (Default):
```bash
docker compose up -d mcp
```

2. API Mode:
```bash
docker compose run --rm mcp python splunk_mcp.py api
```

3. STDIO Mode:
```bash
docker compose run -i --rm mcp python splunk_mcp.py stdio
```

### Testing with Docker

The project includes a dedicated test environment in Docker:

1. Run all tests:
```bash
./run_tests.sh --docker
```

2. Run specific test components:
```bash
# Run only the MCP server
docker compose up -d mcp

# Run only the test container
docker compose up test

# Run both with test results
docker compose up --abort-on-container-exit
```

Test results will be available in the `./test-results` directory.

### Docker Development Tips

1. **Building Images**:
```bash
# Build both images
docker compose build

# Build specific service
docker compose build mcp
docker compose build test
```

2. **Viewing Logs**:
```bash
# View all logs
docker compose logs

# Follow specific service logs
docker compose logs -f mcp
```

3. **Debugging**:
```bash
# Run with debug mode
DEBUG=true docker compose up mcp

# Access container shell
docker compose exec mcp /bin/bash
```

Note: If you're using Docker Compose V1, replace `docker compose` with `docker-compose` in the above commands.

### Security Notes

1. **Environment Variables**:
- Never commit `.env` files
- Use `.env.example` as a template
- Consider using Docker secrets for production

2. **SSL Verification**:
- `VERIFY_SSL=true` recommended for production
- Can be disabled for development/testing
- Configure through environment variables

3. **Port Exposure**:
- Only expose necessary ports
- Use internal Docker network when possible
- Consider network security in production

## Environment Variables

Configure the following environment variables:
- `SPLUNK_HOST`: Your Splunk host address
- `SPLUNK_PORT`: Splunk management port (default: 8089)
- `SPLUNK_USERNAME`: Your Splunk username
- `SPLUNK_PASSWORD`: Your Splunk password
- `SPLUNK_SCHEME`: Connection scheme (default: https)
- `VERIFY_SSL`: Enable/disable SSL verification (default: true)
- `FASTMCP_LOG_LEVEL`: Logging level (default: INFO)
- `SERVER_MODE`: Server mode (sse, api, stdio) when using uvicorn

### SSL Configuration

The tool provides flexible SSL verification options:

1. **Default (Secure) Mode**:
```env
VERIFY_SSL=true
```
- Full SSL certificate verification
- Hostname verification enabled
- Recommended for production environments

2. **Relaxed Mode**:
```env
VERIFY_SSL=false
```
- SSL certificate verification disabled
- Hostname verification disabled
- Useful for testing or self-signed certificates

## Testing

The project includes comprehensive test coverage using pytest and end-to-end testing with a custom MCP client:

### Running Tests

Basic test execution:
```bash
poetry run pytest
```

With coverage reporting:
```bash
poetry run pytest --cov=splunk_mcp
```

With verbose output:
```bash
poetry run pytest -v
```

### End-to-End SSE Testing

The project includes a custom MCP client test script that connects to the live SSE endpoint and tests all tools:

```bash
# Test all tools
python test_endpoints.py

# Test specific tools
python test_endpoints.py health_check list_indexes

# List all available tools
python test_endpoints.py --list
```

This script acts as an MCP client by:
1. Connecting to the `/sse` endpoint to get the messages URL
2. Sending tool invocations to the messages endpoint
3. Processing the SSE events to extract tool results
4. Validating the results against expected formats

This provides real-world testing of the SSE interface as it would be used by an actual MCP client.

### Test Structure

The project uses three complementary testing approaches:

1. **MCP Integration Tests** (`tests/test_api.py`)**:**
   - Tests the MCP tools interface through `mcp.call_tool()`
   - Verifies proper tool registration with FastMCP
   - Ensures correct response format and data structure
   - Validates error handling at the MCP interface level
   - **Note:** This file should ideally be renamed to `test_mcp.py` to better reflect its purpose

2. **Direct Function Tests** (`tests/test_endpoints_pytest.py`)**:**
   - Tests Splunk functions directly (bypassing the MCP layer)
   - Provides more comprehensive coverage of function implementation details
   - Tests edge cases, parameter variations, and error handling
   - Includes tests for SSL configuration, connection parameters, and timeouts
   - Uses parameterized testing for efficient test coverage

3. **End-to-End MCP Client Tests** (`test_endpoints.py`)**:**
   - Behaves like a real MCP client connecting to the SSE endpoint
   - Tests the complete flow from connection to tool invocation to response parsing
   - Validates the actual SSE protocol implementation
   - Tests tools with real parameters against the live server

4. **Configuration Tests** (`tests/test_config.py`)**:**
   - Tests for environment variable parsing
   - SSL verification settings
   - Connection parameter validation

### Testing Tools

The tests support:
- Async testing with pytest-asyncio
- Coverage reporting with pytest-cov
- Mocking with pytest-mock
- Parameterized testing
- Connection timeout testing

### Troubleshooting

#### Connection Issues

1. **Basic Connectivity**:
- The tool now performs a basic TCP connectivity test
- Check if port 8089 is accessible
- Verify network routing and firewalls

2. **SSL Issues**:
- If seeing SSL errors, try setting `VERIFY_SSL=false`
- Check certificate validity and trust chain
- Verify hostname matches certificate

3. **Authentication Issues**:
- Verify Splunk credentials
- Check user permissions
- Ensure account is not locked

4. **Debugging**:
- Set `FASTMCP_LOG_LEVEL=DEBUG` for detailed logs
- Check connection logs for specific error messages
- Review SSL configuration messages

5. **SSE Connection Issues**:
- Verify SSE endpoint is accessible via `/sse`
- Check for proper content-type headers
- Use browser developer tools to inspect SSE connections

## Claude Integration

### Claude Desktop Configuration

You can integrate Splunk MCP with Claude Desktop by configuring it to use either SSE or STDIO mode. Add the following configuration to your `claude_desktop_config.json`:

#### STDIO Mode (Recommended for Desktop)
```json
{
  "mcpServers": {
    "splunk": {
      "command": "poetry",
      "env": {
        "SPLUNK_HOST": "your_splunk_host",
        "SPLUNK_PORT": "8089",
        "SPLUNK_USERNAME": "your_username",
        "SPLUNK_PASSWORD": "your_password",
        "SPLUNK_SCHEME": "https",
        "VERIFY_SSL": "false"
      },
      "args": [
          "--directory",
          "/path/to/splunk-mcp",
          "run",
          "python",
          "splunk_mcp.py",
          "stdio"
      ]
    }
  }
}
```

#### SSE Mode
```json
{
  "mcpServers": {
    "splunk": {
      "command": "poetry",
      "env": {
        "SPLUNK_HOST": "your_splunk_host",
        "SPLUNK_PORT": "8089",
        "SPLUNK_USERNAME": "your_username",
        "SPLUNK_PASSWORD": "your_password",
        "SPLUNK_SCHEME": "https",
        "VERIFY_SSL": "false",
        "FASTMCP_PORT": "8001",
        "DEBUG": "true"
      },
      "args": [
          "--directory",
          "/path/to/splunk-mcp",
          "run",
          "python",
          "splunk_mcp.py",
          "sse"
      ]
    }
  }
}
```

### Usage with Claude

Once configured, you can use natural language to interact with Splunk through Claude. Examples:

1. List available indexes:
```
What Splunk indexes are available?
```

2. Search Splunk data:
```
Search Splunk for failed login attempts in the last 24 hours
```

3. Get system health:
```
Check the health of the Splunk system
```

4. Manage KV stores:
```
List all KV store collections
```

The MCP tools will be automatically available to Claude, allowing it to execute these operations through natural language commands.

## License

[Your License Here]

## Acknowledgments

- FastMCP framework
- Splunk SDK for Python
- Python-decouple for configuration management
- SSE Starlette for SSE implementation
