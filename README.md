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

## Installation

### Using UV (Recommended)

UV is a fast Python package installer and resolver, written in Rust. It's significantly faster than pip and provides better dependency resolution.

#### Prerequisites
- Python 3.10 or higher
- UV installed (see [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/))

#### Quick Start with UV

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd splunk-mcp
   ```

2. **Install dependencies with UV:**
   ```bash
   # Install main dependencies
   uv sync
   
   # Or install with development dependencies
   uv sync --extra dev
   ```

3. **Run the application:**
   ```bash
   # SSE mode (default)
   uv run python splunk_mcp.py
   
   # STDIO mode
   uv run python splunk_mcp.py stdio
   
   # API mode
   uv run python splunk_mcp.py api
   ```

#### UV Commands Reference

```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --extra dev

# Run the application
uv run python splunk_mcp.py

# Run tests
uv run pytest

# Run with specific Python version
uv run --python 3.11 python splunk_mcp.py

# Add a new dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade

# Generate requirements.txt
uv pip compile pyproject.toml -o requirements.txt
```

### Using Poetry (Alternative)

If you prefer Poetry, you can still use it:

```bash
# Install dependencies
poetry install

# Run the application
poetry run python splunk_mcp.py
```

### Using pip (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python splunk_mcp.py
```

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
- `SPLUNK_TOKEN`: (Optional) Splunk authentication token. If set, this will be used instead of username/password.
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