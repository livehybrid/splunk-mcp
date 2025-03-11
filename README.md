# Splunk MCP (Model Context Protocol) Tool

A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language. This tool provides a set of capabilities for searching Splunk data, managing KV stores, and accessing Splunk resources through an intuitive interface.

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

The tool can run in two modes:

1. STDIO mode (default) - for command-line integration:
```bash
poetry run python splunk_mcp.py
```

2. SSE mode - for web server integration:
```bash
poetry run python splunk_mcp.py sse
```

### Docker Usage

If using Docker Compose:
```bash
# Start the service in STDIO mode (default)
docker-compose up -d

# Start in SSE mode
docker-compose run --rm splunk-mcp python splunk_mcp.py sse
```

If using Docker directly:
```bash
# Start in STDIO mode (default)
docker run -i \
  --env-file .env \
  livehybrid/splunk-mcp

# Start in SSE mode
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  livehybrid/splunk-mcp python splunk_mcp.py sse
```

### Environment Variables

Configure the following environment variables:
- `SPLUNK_HOST`: Your Splunk host address
- `SPLUNK_PORT`: Splunk management port (default: 8089)
- `SPLUNK_USERNAME`: Your Splunk username
- `SPLUNK_PASSWORD`: Your Splunk password
- `SPLUNK_SCHEME`: Connection scheme (default: https)
- `VERIFY_SSL`: Enable/disable SSL verification (default: true)
- `FASTMCP_LOG_LEVEL`: Logging level (default: INFO)

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

### Available Tools

1. **search_splunk**
   - Execute Splunk searches with customizable time ranges
   - Example: Search for events in the last hour
   ```python
   search_query="index=* | stats count by host"
   ```

2. **list_indexes**
   - List all available Splunk indexes with metadata
   - Shows event counts, sizes, and time ranges

3. **list_users**
   - Display all Splunk users and their roles
   - Includes user metadata and permissions

4. **KV Store Operations**
   - list_kvstore_collections: View all KV store collections
   - create_kvstore_collection: Create new collections
   - delete_kvstore_collection: Remove existing collections

## Development

### Running Tests

```bash
poetry run pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Claude Desktop Integration

You can integrate Splunk MCP directly with Claude Desktop by adding configuration to your `claude_desktop_config.json` file (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS).

### Configuration Example

Add the following to your `claude_desktop_config.json`:

```json
{
  "tools": {
    "splunk": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "SPLUNK_HOST",
        "-e",
        "SPLUNK_USERNAME",
        "-e",
        "SPLUNK_PASSWORD",
        "-e",
        "SPLUNK_PORT",
        "livehybrid/splunk-mcp",
        "python", 
        "splunk_mcp.py", 
        "stdio"
      ],
      "env": {
        "SPLUNK_HOST": "yourSplunkInstance.splunkcloud.com",
        "SPLUNK_USERNAME": "admin",
        "SPLUNK_PASSWORD": "yourPassword",
        "SPLUNK_PORT": "8089"
      }
    }
  }
}
```

### Configuration Parameters

1. **Docker Configuration**:
   - Uses the official `livehybrid/splunk-mcp` image
   - Runs in interactive mode (`-i`)
   - Automatically removes container after execution (`--rm`)
   - Uses STDIO mode for Claude integration

2. **Environment Variables**:
   - `SPLUNK_HOST`: Your Splunk instance URL
   - `SPLUNK_USERNAME`: Your Splunk username
   - `SPLUNK_PORT`: Splunk management port (typically 8089)
   - `SPLUNK_PASSWORD`: Your Splunk password

### Security Note

When configuring the tool with Claude Desktop:
- Store your `claude_desktop_config.json` in a secure location
- Use appropriate file permissions
- Consider using environment variables or a credential manager for sensitive values
- Never share your configuration file containing credentials

## License

[Your License Here]

## Acknowledgments

- FastMCP framework
- Splunk SDK for Python
- Python-decouple for configuration management
