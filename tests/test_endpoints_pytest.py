#!/usr/bin/env python3
"""
Test module for Splunk MCP endpoints using pytest.
"""

import json
import os
import pytest
import requests
import time
import uuid
import ssl
import importlib
import asyncio
import sys
from typing import Dict, List, Any, Optional, Union, Tuple
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Import configuration
import test_config as config

# Import directly from splunk_mcp for direct function testing
import splunk_mcp
from splunk_mcp import mcp, get_splunk_connection

# Access the underlying functions from the FunctionTool wrappers
list_indexes = splunk_mcp.list_indexes.fn
get_index_info = splunk_mcp.get_index_info.fn
search_splunk = splunk_mcp.search_splunk.fn
list_saved_searches = splunk_mcp.list_saved_searches.fn
current_user = splunk_mcp.current_user.fn
list_users = splunk_mcp.list_users.fn
list_kvstore_collections = splunk_mcp.list_kvstore_collections.fn
health_check = splunk_mcp.health_check.fn
get_indexes_and_sourcetypes = splunk_mcp.get_indexes_and_sourcetypes.fn
ping = splunk_mcp.ping.fn

# Configuration
BASE_URL = config.SSE_BASE_URL
TIMEOUT = config.REQUEST_TIMEOUT
VERBOSE = config.VERBOSE_OUTPUT

# Functions to test directly
# This provides better coverage than going through MCP's call_tool
TEST_FUNCTIONS = [
    list_indexes,
    list_saved_searches,
    current_user,
    list_users,
    list_kvstore_collections,
    health_check,
]


def log(message: str, level: str = "INFO") -> None:
    """Print log messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


# Fixture for function parameters
@pytest.fixture
def function_params():
    """Return parameters for different functions"""
    return {
        "search_splunk": {
            "search_query": config.TEST_SEARCH_QUERY,
            "earliest_time": config.SEARCH_EARLIEST_TIME,
            "latest_time": config.SEARCH_LATEST_TIME,
            "max_results": config.SEARCH_MAX_RESULTS,
        },
        "get_index_info": {"index_name": "main"},
        "create_kvstore_collection": {"collection_name": "test_collection"},
        "delete_kvstore_collection": {"collection_name": "test_collection"},
    }


# Fixture for mock Splunk service
@pytest.fixture
def mock_splunk_service():
    """Create a mock Splunk service for testing"""
    mock_service = MagicMock()

    # Mock index
    mock_index = MagicMock()
    mock_index.name = "main"
    mock_index.get = lambda key, default=None: {
        "totalEventCount": "1000",
        "currentDBSizeMB": "100",
        "maxTotalDataSizeMB": "500",
        "minTime": "1609459200",
        "maxTime": "1640995200",
    }.get(key, default)
    mock_index.__getitem__ = lambda self, key: {
        "totalEventCount": "1000",
        "currentDBSizeMB": "100",
        "maxTotalDataSizeMB": "500",
        "minTime": "1609459200",
        "maxTime": "1640995200",
    }.get(key)

    # Create a mock collection for indexes
    mock_indexes = MagicMock()
    mock_indexes.__getitem__ = MagicMock(
        side_effect=lambda key: (
            mock_index
            if key == "main"
            else (_ for _ in ()).throw(KeyError(f"Index not found: {key}"))
        )
    )
    mock_indexes.__iter__ = MagicMock(return_value=iter([mock_index]))
    mock_indexes.keys = MagicMock(return_value=["main"])
    mock_service.indexes = mock_indexes

    # Mock job
    mock_job = MagicMock()
    mock_job.sid = "search_1"
    mock_job.state = "DONE"
    mock_job.content = {"resultCount": 5, "doneProgress": 100}

    # Prepare search results
    search_results = {
        "results": [
            {"result": {"field1": "value1", "field2": "value2"}},
            {"result": {"field1": "value3", "field2": "value4"}},
            {"result": {"field1": "value5", "field2": "value6"}},
        ]
    }

    mock_job.results = lambda output_mode="json", count=None: type(
        "MockResultStream",
        (),
        {"read": lambda self: json.dumps(search_results).encode("utf-8")},
    )()
    mock_job.is_done.return_value = True

    # Create a mock collection for jobs
    mock_jobs = MagicMock()
    mock_jobs.__getitem__ = MagicMock(return_value=mock_job)
    mock_jobs.__iter__ = MagicMock(return_value=iter([mock_job]))
    mock_jobs.create = MagicMock(return_value=mock_job)
    mock_service.jobs = mock_jobs

    # Mock saved searches
    mock_saved_search = MagicMock()
    mock_saved_search.name = "test_search"
    mock_saved_search.description = "Test search description"
    mock_saved_search.search = "index=main | stats count"

    mock_saved_searches = MagicMock()
    mock_saved_searches.__iter__ = MagicMock(return_value=iter([mock_saved_search]))
    mock_service.saved_searches = mock_saved_searches

    # Mock users for list_users
    mock_user = MagicMock()
    mock_user.name = "admin"
    mock_user.roles = ["admin", "power"]
    mock_user.email = "admin@example.com"

    mock_users = MagicMock()
    mock_users.__iter__ = MagicMock(return_value=iter([mock_user]))
    mock_service.users = mock_users

    # Mock kvstore collections
    mock_collection = MagicMock()
    mock_collection.name = "test_collection"

    mock_kvstore = MagicMock()
    mock_kvstore.__iter__ = MagicMock(return_value=iter([mock_collection]))
    mock_kvstore.create = MagicMock(return_value=True)
    mock_kvstore.delete = MagicMock(return_value=True)
    mock_service.kvstore = mock_kvstore

    # Mock sourcetypes
    mock_sourcetypes_job = MagicMock()
    mock_sourcetypes_job.results = lambda output_mode="json": type(
        "MockResultStream",
        (),
        {
            "read": lambda self: json.dumps(
                {
                    "results": [
                        {
                            "index": "main",
                            "sourcetype": "access_combined",
                            "count": "500",
                        },
                        {"index": "main", "sourcetype": "apache_error", "count": "300"},
                    ]
                }
            ).encode("utf-8")
        },
    )()
    mock_sourcetypes_job.is_done.return_value = True

    # Update the jobs.create to handle different search patterns
    def create_mock_job(search, **kwargs):
        if "sourcetype by index" in search:
            return mock_sourcetypes_job
        return mock_job

    mock_service.jobs.create = MagicMock(side_effect=create_mock_job)

    # Mock apps for health_check
    mock_app = MagicMock()
    mock_app.name = "search"
    mock_app.label = "Search"
    mock_app.version = "8.0.0"

    mock_apps = MagicMock()
    mock_apps.__iter__ = MagicMock(return_value=iter([mock_app]))
    mock_service.apps = mock_apps

    return mock_service


@pytest.mark.parametrize("function", TEST_FUNCTIONS)
@pytest.mark.asyncio
async def test_function_directly(function, function_params, mock_splunk_service):
    """
    Test functions in splunk_mcp directly (not via MCP)

    Args:
        function: The function to test
        function_params: Fixture with parameters for functions
        mock_splunk_service: Mock Splunk service
    """
    # Get function name for logging and parameter lookup
    function_name = function.__name__

    # Get parameters for this function if needed
    params = function_params.get(function_name, {})

    log(f"Testing function: {function_name} with params: {params}", "INFO")

    # Use patch to mock Splunk connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        try:
            # Call the function with parameters
            result = await function(**params)

            # For better test output, print the result
            if VERBOSE:
                log(
                    f"Function result: {str(result)[:200]}...", "DEBUG"
                )  # Limit output size

            # The test passes if we get a result without exception
            assert result is not None
            log(f"✅ {function_name} - SUCCESS", "SUCCESS")

        except Exception as e:
            log(f"❌ {function_name} - FAILED: {str(e)}", "ERROR")
            raise  # Re-raise the exception to fail the test


# Test get_index_info specifically
@pytest.mark.asyncio
async def test_get_index_info(mock_splunk_service):
    """Test get_index_info function directly"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await get_index_info(index_name="main")
        assert result is not None
        assert result["name"] == "main"


# Test search_splunk specifically
@pytest.mark.asyncio
async def test_search_splunk(mock_splunk_service):
    """Test search_splunk function directly"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await search_splunk(
            search_query="index=main | head 3",
            earliest_time="-5m",
            latest_time="now",
            max_results=3,
        )
        assert result is not None
        assert isinstance(result, list)


# Test indexes_and_sourcetypes
@pytest.mark.asyncio
async def test_indexes_and_sourcetypes(mock_splunk_service):
    """Test get_indexes_and_sourcetypes function directly"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await get_indexes_and_sourcetypes()
        assert result is not None
        assert "indexes" in result
        assert "sourcetypes" in result
        assert "metadata" in result
        assert "total_indexes" in result["metadata"]


# Test KV store operations
@pytest.mark.asyncio
async def test_kvstore_operations(mock_splunk_service):
    """Test KV store operations directly"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        # Test list collections
        list_result = await list_kvstore_collections()
        assert list_result is not None
        assert isinstance(list_result, list)


# Test error handling for missing parameters
@pytest.mark.asyncio
async def test_missing_required_parameters(mock_splunk_service):
    """Test error handling for missing required parameters"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        with pytest.raises(
            TypeError
        ):  # Missing required parameter will raise TypeError
            await get_index_info()  # Missing index_name


# Test error handling for index not found
@pytest.mark.asyncio
async def test_index_not_found(mock_splunk_service):
    """Test error handling for index not found"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        with pytest.raises(Exception):
            await get_index_info(index_name="non_existent_index")


# Test connection error handling
@pytest.mark.asyncio
async def test_connection_error():
    """Test handling of Splunk connection errors"""
    with patch(
        "splunk_mcp.get_splunk_connection", side_effect=Exception("Connection error")
    ):
        with pytest.raises(Exception):
            await list_indexes()


# Test general utility functions
@pytest.mark.asyncio
async def test_health_check(mock_splunk_service):
    """Test health_check function directly"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await health_check()
        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result


# Test FastMCP registration
def test_tools_registration():
    """Test that tools are properly registered with FastMCP"""
    # Check that the MCP instance is properly initialized
    assert mcp is not None
    # In FastMCP 2.x, check for get_tools method instead of call_tool
    assert hasattr(mcp, "get_tools")
    # Verify that we can also access the tool manager
    assert hasattr(mcp, "_tool_manager")


# Test search_splunk with different parameters
@pytest.mark.asyncio
async def test_search_splunk_params(mock_splunk_service):
    """Test search_splunk with different parameter variations"""
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        # Test with minimal parameters
        result1 = await search_splunk(search_query="index=main")
        assert result1 is not None

        # Test with different time ranges
        result2 = await search_splunk(
            search_query="index=main", earliest_time="-1h", latest_time="now"
        )
        assert result2 is not None

        # Test with max_results
        result3 = await search_splunk(search_query="index=main", max_results=10)
        assert result3 is not None


# Test SSL verification
def test_ssl_verification():
    """Test the SSL verification setting"""
    # Instead of testing a non-existent get_ssl_context function,
    # we'll test the VERIFY_SSL configuration
    original_env = os.environ.copy()

    try:
        # Test with VERIFY_SSL=true
        os.environ["VERIFY_SSL"] = "true"
        # Reload the module to refresh the VERIFY_SSL value
        importlib.reload(splunk_mcp)
        assert splunk_mcp.VERIFY_SSL is True

        # Test with VERIFY_SSL=false
        os.environ["VERIFY_SSL"] = "false"
        # Reload the module to refresh the VERIFY_SSL value
        importlib.reload(splunk_mcp)
        assert splunk_mcp.VERIFY_SSL is False

    finally:
        # Restore the environment
        os.environ.clear()
        os.environ.update(original_env)
        # Reload the module to restore the original state
        importlib.reload(splunk_mcp)


# Test service connection with different parameters
@pytest.mark.asyncio
async def test_splunk_connection_params():
    """Test Splunk connection with different parameters"""
    with patch("splunklib.client.connect") as mock_connect:
        mock_service = MagicMock()
        mock_connect.return_value = mock_service

        # Normal connection - get_splunk_connection is not async in splunk_mcp.py
        splunk_mcp.get_splunk_connection()
        mock_connect.assert_called_once()

        # Reset mock
        mock_connect.reset_mock()

        # Connection with custom parameters
        with patch.dict(
            "os.environ",
            {
                "SPLUNK_HOST": "custom-host",
                "SPLUNK_PORT": "8888",
                "SPLUNK_USERNAME": "custom-user",
                "SPLUNK_PASSWORD": "custom-pass",
            },
        ):
            # Reload module to refresh environment variables
            importlib.reload(splunk_mcp)
            splunk_mcp.get_splunk_connection()
            # Check if connect was called with the proper parameters
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs["host"] == "custom-host"
            # Port might be converted to int by the function
            assert str(call_kwargs["port"]) == "8888"
            assert call_kwargs["username"] == "custom-user"
            assert call_kwargs["password"] == "custom-pass"


# Test job waiting with timeout
@pytest.mark.asyncio
async def test_search_job_timeout():
    """Test handling of Splunk job timeout"""
    # Create a job that never finishes
    mock_timeout_job = MagicMock()
    mock_timeout_job.is_done = MagicMock(return_value=False)
    mock_timeout_job.sid = "timeout_job"

    timeout_service = MagicMock()
    timeout_service.jobs.create = MagicMock(return_value=mock_timeout_job)

    # Patch time.sleep to speed up the test
    with (
        patch("splunk_mcp.get_splunk_connection", return_value=timeout_service),
        patch("asyncio.sleep", return_value=None),
        patch("time.time", side_effect=[0, 15, 30, 60, 120]),
    ):  # Simulate timeout

        # Make a custom search function with a timeout - not using await since get_splunk_connection is not async
        async def test_search_with_timeout():
            service = splunk_mcp.get_splunk_connection()
            job = service.jobs.create(
                "search index=main", earliest_time="-24h", latest_time="now"
            )
            # Wait for job completion with a timeout
            max_wait = 100  # seconds
            start_time = time.time()
            while not job.is_done() and time.time() - start_time < max_wait:
                await asyncio.sleep(1)

            if not job.is_done():
                raise Exception(f"Search timed out after {max_wait} seconds")
            return []

        with pytest.raises(Exception) as excinfo:
            await test_search_with_timeout()

        assert "timed out" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_ping():
    """Test the ping endpoint for server health check"""
    result = await ping()

    assert result["status"] == "ok"
    assert result["server"] == "splunk-mcp"
    assert result["version"] == splunk_mcp.VERSION
    assert "timestamp" in result
    assert result["protocol"] == "mcp"
    assert "splunk" in result["capabilities"]

    # Test that the timestamp is in a valid format
    try:
        datetime.fromisoformat(result["timestamp"])
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False

    assert timestamp_valid, "Timestamp is not in a valid ISO format"


@pytest.mark.asyncio
async def test_splunk_token_auth():
    """Test Splunk connection with token-based authentication"""
    with patch("splunklib.client.connect") as mock_connect:
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        with patch.dict(
            "os.environ",
            {
                "SPLUNK_HOST": "token-host",
                "SPLUNK_PORT": "9999",
                "SPLUNK_TOKEN": "test-token",
                "SPLUNK_USERNAME": "should-not-be-used",
                "SPLUNK_PASSWORD": "should-not-be-used",
            },
        ):
            importlib.reload(splunk_mcp)
            splunk_mcp.get_splunk_connection()
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs["host"] == "token-host"
            assert str(call_kwargs["port"]) == "9999"
            assert call_kwargs["token"] == "Bearer test-token"
            assert "username" not in call_kwargs
            assert "password" not in call_kwargs
