"""
Configuration settings for the Splunk MCP API test script.
Override these values as needed for your environment.
"""

import os

# SSE mode base URL (without /sse path, which will be appended by the client)
SSE_BASE_URL = os.environ.get("SPLUNK_MCP_SSE_URL", "http://localhost:8001")


# Server connection timeout in seconds
CONNECTION_TIMEOUT = int(os.environ.get("SPLUNK_MCP_CONNECTION_TIMEOUT", "30"))

# Request timeout in seconds
REQUEST_TIMEOUT = int(os.environ.get("SPLUNK_MCP_TIMEOUT", "30"))

# Verbose output (set to "false" to disable)
VERBOSE_OUTPUT = os.environ.get("SPLUNK_MCP_VERBOSE", "true").lower() == "true"

# Test search query (for testing the search endpoint)
TEST_SEARCH_QUERY = os.environ.get("SPLUNK_MCP_TEST_QUERY", "index=_internal | head 5")

# Time range for search (can be adjusted for different Splunk instances)
SEARCH_EARLIEST_TIME = os.environ.get("SPLUNK_MCP_EARLIEST_TIME", "-1h")
SEARCH_LATEST_TIME = os.environ.get("SPLUNK_MCP_LATEST_TIME", "now")

# Maximum number of results to fetch in searches
SEARCH_MAX_RESULTS = int(os.environ.get("SPLUNK_MCP_MAX_RESULTS", "5"))

# Default index to use for tests if _internal is not available
DEFAULT_TEST_INDEX = os.environ.get("SPLUNK_MCP_TEST_INDEX", "") 