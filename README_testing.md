# Splunk MCP API Testing

This directory contains scripts for testing the Splunk MCP API endpoints against a live Splunk instance.

## Overview

The test suite includes:

- `test_endpoints.py`: Main test script that tests all API endpoints against a running Splunk MCP server
- `test_config.py`: Configuration settings for the test script
- `run_tests.sh`: Shell script to run all tests and generate a report

## Testing Approaches

This project has two different testing approaches, each with a different purpose:

### 1. Live Server Testing (this tool)

This test script (`test_endpoints.py`) is designed to:

- Test a **running instance** of the Splunk MCP server connected to a live Splunk deployment
- Validate that all endpoints are working correctly in a real environment
- Provide a quick way to check if the server is responding properly
- Test both API mode and SSE (Server-Sent Events) mode
- Generate reports about the health of the API

Use this approach for:
- Integration testing with a real Splunk instance
- Verifying deployment in production or staging environments
- Troubleshooting connectivity issues
- Checking if all endpoints are accessible

### 2. Pytest Testing (in `/tests` directory)

The pytest tests are designed to:

- Unit test the code without requiring a real Splunk instance
- Mock Splunk's responses to test error handling
- Verify code coverage and edge cases
- Run in CI/CD pipelines without external dependencies
- Test internal code logic and functions

Use this approach for:
- Development and debugging
- Verifying code changes don't break functionality
- Ensuring proper error handling
- Automated testing in CI/CD pipelines

## Requirements

- Python 3.6+
- Required packages: `requests`

You can install the required packages using:

```bash
pip install requests
```

## Configuration

The `test_config.py` file contains default settings that can be overridden using environment variables:

| Environment Variable       | Description                      | Default Value             |
|----------------------------|----------------------------------|---------------------------|
| `SPLUNK_MCP_API_URL`       | Base URL for API mode            | http://localhost:8000/api/v1 |
| `SPLUNK_MCP_SSE_URL`       | Base URL for SSE mode            | http://localhost:8000/sse/v1 |
| `SPLUNK_MCP_AUTO_DETECT`   | Auto-detect server mode (true/false) | true                 |
| `SPLUNK_MCP_CONNECTION_TIMEOUT` | Connection timeout in seconds | 5                     |
| `SPLUNK_MCP_TIMEOUT`       | Request timeout in seconds       | 30                        |
| `SPLUNK_MCP_VERBOSE`       | Enable verbose output (true/false) | true                    |
| `SPLUNK_MCP_TEST_QUERY`    | Search query to test             | index=_internal \| head 5 |
| `SPLUNK_MCP_EARLIEST_TIME` | Earliest time for search         | -1h                       |
| `SPLUNK_MCP_LATEST_TIME`   | Latest time for search           | now                       |
| `SPLUNK_MCP_MAX_RESULTS`   | Max results for search           | 5                         |
| `SPLUNK_MCP_TEST_INDEX`    | Default index to use for tests   | (empty)                   |

## Server Modes

The Splunk MCP server can run in two different modes:

1. **API Mode**: Standard REST API endpoints (default)
2. **SSE Mode**: Server-Sent Events for streaming updates

The test script can detect which mode the server is running in and adjust accordingly. You can also force a specific mode using the `--mode` command-line option.

## Running the Tests

1. Ensure the Splunk MCP API server is running and connected to a Splunk instance.

2. Run the test script:

```bash
# Test all endpoints with automatic mode detection
./test_endpoints.py

# List available endpoints
./test_endpoints.py --list

# Test specific endpoints
./test_endpoints.py health list_indexes

# Test in specific server mode
./test_endpoints.py --mode api
./test_endpoints.py --mode sse

# Generate a full test report
./run_tests.sh
```

### Command-line Arguments

The test script supports the following command-line arguments:

- **Positional arguments**: Names of endpoints to test (if not specified, all suitable endpoints will be tested)
- `--list`: List all available endpoints and exit
- `--mode {api,sse}`: Force a specific server mode instead of auto-detecting

### Customizing Tests

You can customize tests by setting environment variables:

```bash
# Example: Test against a different server
export SPLUNK_MCP_API_URL="http://my-splunk-server:8000/api/v1"
export SPLUNK_MCP_SSE_URL="http://my-splunk-server:8000/sse/v1"

# Example: Use a different search query
export SPLUNK_MCP_TEST_QUERY="index=main | head 10"

# Example: Set a specific index to test
export SPLUNK_MCP_TEST_INDEX="main"

# Run with customized settings
./test_endpoints.py
```

## Test Results

The script will output results for each endpoint test and a summary at the end:

- ✅ Successful tests
- ❌ Failed tests with error details

If any test fails, the script will exit with a non-zero status code, which is useful for CI/CD environments.

When using `run_tests.sh`, a Markdown report file will be generated with details of all test results.

## Adding New Tests

To add new tests, modify the `ALL_ENDPOINTS` dictionary in `test_endpoints.py`. Each endpoint should have:

- `method`: HTTP method (GET, POST, etc.)
- `path`: API endpoint path
- `description`: Short description of the endpoint
- `validation`: Function to validate the response
- `available_in`: List of modes where this endpoint is available (`["api"]`, `["sse"]`, or `["api", "sse"]`)
- `data`: (Optional) Request data for POST/PUT requests
- `requires_parameters`: (Optional) Set to True if the endpoint requires parameters

Example:

```python
"new_endpoint": {
    "method": "GET",
    "path": "/new_endpoint",
    "description": "Example new endpoint",
    "validation": lambda data: assert_dict_keys(data, ["required_field1", "required_field2"]),
    "available_in": ["api", "sse"]
}
``` 