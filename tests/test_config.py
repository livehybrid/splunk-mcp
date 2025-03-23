"""
Configuration for test_endpoints.py.
This file contains settings used by the endpoint testing script.
"""

# Server configuration
SSE_BASE_URL = "http://localhost:8000"        # SSE mode base URL

# Connection timeouts (seconds)
CONNECTION_TIMEOUT = 5                        # Timeout for basic connection check
REQUEST_TIMEOUT = 30                          # Timeout for API requests

# Search test configuration
TEST_SEARCH_QUERY = "index=_internal | head 5"
SEARCH_EARLIEST_TIME = "-10m"
SEARCH_LATEST_TIME = "now"
SEARCH_MAX_RESULTS = 5

# Default index for testing (leave empty to auto-select)
DEFAULT_TEST_INDEX = "_internal"

# Output settings
VERBOSE_OUTPUT = True                         # Show detailed output 