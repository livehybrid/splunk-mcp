# Splunk MCP (Model Context Protocol) Tool

A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language. This tool provides a set of capabilities for searching Splunk data, managing KV stores, and accessing Splunk resources through an intuitive interface.

## Features

- **Splunk Search**: Execute Splunk searches with natural language queries
- **Index Management**: List and inspect Splunk indexes
- **User Management**: View and manage Splunk users
- **KV Store Operations**: Create, list, and manage KV store collections
- **Async Support**: Built with async/await patterns for better performance
- **Detailed Logging**: Comprehensive logging with emoji indicators for better visibility
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
FASTMCP_LOG_LEVEL=INFO
```

### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd splunk-mcp
```

2. Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

3. Update the `.env` file with your Splunk credentials (same as above).

4. Build and run using Docker Compose:
```bash
docker-compose up -d
```

Or using Docker directly:
```bash
# Build the image
docker build -t splunk-mcp .

# Run the container
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  --name splunk-mcp \
  splunk-mcp
```

## Usage

### Local Usage

1. Start the MCP server:
```bash
poetry run python splunk_mcp.py
```

### Docker Usage

If using Docker Compose:
```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

If using Docker directly:
```bash
# Start the container
docker start splunk-mcp

# View logs
docker logs -f splunk-mcp

# Stop the container
docker stop splunk-mcp
```

The server will start and listen for connections on port 3000 in both local and Docker installations.

### Docker Environment Variables

When running with Docker, you can configure the following environment variables:
- `SPLUNK_HOST`: Your Splunk host address
- `SPLUNK_PORT`: Splunk management port (default: 8089)
- `SPLUNK_USERNAME`: Your Splunk username
- `SPLUNK_PASSWORD`: Your Splunk password
- `SPLUNK_SCHEME`: Connection scheme (default: https)
- `FASTMCP_LOG_LEVEL`: Logging level (default: INFO)

These can be set either in the `.env` file or passed directly to Docker using the `-e` flag.

### Available Tools

1. **search_splunk**
   - Execute Splunk searches with customizable time ranges
   - Example: Search for hosts sending data in the last hour
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

## Example Queries

1. Search for temperature data:
```python
search_query="index=main sourcetype=httpevent *temperature* | stats avg(value) by location"
```

2. List all indexes:
```python
await list_indexes()
```

3. View user information:
```python
await list_users()
```

## Development

### Project Structure

- `splunk_mcp.py`: Main implementation file
- `pyproject.toml`: Poetry project configuration
- `.env`: Environment configuration
- `README.md`: Documentation
- `tests/`: Unit tests directory
  - `test_splunk_mcp.py`: Test suite for Splunk MCP functionality

### Running Tests

The project uses pytest for testing. All tests are written to work without requiring an actual Splunk connection, using mocks to simulate Splunk's behavior.

1. Run all tests:
```bash
poetry run pytest
```

2. Run tests with coverage:
```bash
poetry run pytest --cov=splunk_mcp tests/
```

3. Run specific test file:
```bash
poetry run pytest tests/test_splunk_mcp.py
```

4. Run tests with verbose output:
```bash
poetry run pytest -v
```

The test suite includes:
- Unit tests for all Splunk operations (search, index listing, user management)
- KV store operation tests
- Connection handling tests
- Error case testing

### Adding New Tests

When adding new features:
1. Create corresponding test cases in `tests/test_splunk_mcp.py`
2. Use the provided mock fixtures for Splunk service simulation
3. Add appropriate assertions to verify functionality
4. Ensure both success and error cases are covered

## Troubleshooting

Common issues and solutions:

1. Connection Issues
   - Verify Splunk credentials in `.env`
   - Check network connectivity
   - Ensure Splunk management port (8089) is accessible
   - If using Docker, ensure the container has network access to your Splunk instance

2. Docker Issues
   - Check container logs: `docker logs splunk-mcp`
   - Verify environment variables are properly set
   - Ensure port 3000 is not in use by another service
   - Check container status: `docker ps -a`

2. Permission Issues
   - Verify user has appropriate Splunk roles
   - Check app/collection access permissions

3. Search Issues
   - Validate search syntax
   - Check time ranges
   - Verify index access permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- FastMCP framework
- Splunk SDK for Python
- Python-decouple for configuration management
