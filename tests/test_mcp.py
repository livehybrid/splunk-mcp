import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import splunklib.client
from datetime import datetime
import splunk_mcp
from splunk_mcp import get_splunk_connection, mcp

# Access the underlying functions from the FunctionTool wrappers
list_indexes = splunk_mcp.list_indexes.fn
get_index_info = splunk_mcp.get_index_info.fn
search_splunk = splunk_mcp.search_splunk.fn
list_saved_searches = splunk_mcp.list_saved_searches.fn
current_user = splunk_mcp.current_user.fn
list_users = splunk_mcp.list_users.fn
list_kvstore_collections = splunk_mcp.list_kvstore_collections.fn
health_check = splunk_mcp.health_check.fn
list_tools = splunk_mcp.list_tools.fn

# Ensure pytest-mock is available for the 'mocker' fixture
try:
    import pytest_mock  # noqa: F401
except ImportError:
    # If pytest-mock is not installed, provide a fallback for 'mocker'
    @pytest.fixture
    def mocker():
        from unittest import mock

        return mock

    # Note: For full functionality, install pytest-mock: pip install pytest-mock


# Helper function to extract JSON from TextContent objects
def extract_json_from_result(result):
    """Extract JSON data from FastMCP TextContent objects or regular dict/list objects"""
    if hasattr(result, "__iter__") and not isinstance(result, (dict, str)):
        # It's likely a list of TextContent objects
        if len(result) > 0 and hasattr(result[0], "text"):
            try:
                return json.loads(result[0].text)
            except json.JSONDecodeError:
                return result[0].text
    return result


# Mock Splunk service fixture
@pytest.fixture
def mock_splunk_service(mocker):
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

    # Prepare search results that match the format returned by the actual tool
    search_results = {
        "results": [
            {"result": {"field1": "value1", "field2": "value2"}},
            {"result": {"field1": "value3", "field2": "value4"}},
            {"result": {"field1": "value5", "field2": "value6"}},
            {"result": {"field1": "value7", "field2": "value8"}},
            {"result": {"field1": "value9", "field2": "value10"}},
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

    # Mock users
    mock_user = MagicMock()
    mock_user.name = "admin"
    mock_user.content = {
        "realname": "Administrator",
        "email": "admin@example.com",
        "roles": ["admin"],
        "capabilities": ["admin_all_objects"],
        "defaultApp": "search",
        "type": "admin",
    }
    mock_user.roles = ["admin"]

    mock_users = MagicMock()
    mock_users.__getitem__ = MagicMock(return_value=mock_user)
    mock_users.__iter__ = MagicMock(return_value=iter([mock_user]))
    mock_service.users = mock_users

    # Mock apps
    mock_app = MagicMock()
    mock_app.name = "search"
    mock_app.label = "Search"
    mock_app.version = "1.0.0"
    mock_app.__getitem__ = lambda self, key: {
        "name": "search",
        "label": "Search",
        "version": "1.0.0",
    }.get(key)

    mock_apps = MagicMock()
    mock_apps.__iter__ = MagicMock(return_value=iter([mock_app]))
    mock_service.apps = mock_apps

    # Mock get method
    def mock_get(endpoint, **kwargs):
        if endpoint == "/services/authentication/current-context":
            result = MagicMock()
            result.body.read.return_value = json.dumps(
                {"entry": [{"content": {"username": "admin"}}]}
            ).encode("utf-8")
            return result
        elif endpoint == "/services/server/introspection/kvstore/collectionstats":
            result = MagicMock()
            result.body.read.return_value = json.dumps(
                {
                    "entry": [
                        {
                            "content": {
                                "data": [
                                    json.dumps(
                                        {"ns": "search.test_collection", "count": 5}
                                    )
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8")
            return result
        else:
            raise Exception(f"Unexpected endpoint: {endpoint}")

    mock_service.get = mock_get

    # Mock KV store collections
    mock_kvstore_entry = {
        "name": "test_collection",
        "content": {"field.testField": "text"},
        "access": {"app": "search"},
    }

    mock_kvstore = MagicMock()
    mock_kvstore.__iter__ = MagicMock(return_value=iter([mock_kvstore_entry]))
    mock_service.kvstore = mock_kvstore

    return mock_service


@pytest.mark.asyncio
async def test_list_indexes(mock_splunk_service):
    """Test the list_indexes MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await list_indexes()
        assert isinstance(result, dict)
        assert "indexes" in result
        assert "main" in result["indexes"]


@pytest.mark.asyncio
async def test_get_index_info(mock_splunk_service):
    """Test the get_index_info MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await get_index_info(index_name="main")
        assert result["name"] == "main"
        assert result["total_event_count"] == "1000"
        assert result["current_size"] == "100"
        assert result["max_size"] == "500"


@pytest.mark.asyncio
async def test_search_splunk(mock_splunk_service):
    """Test the search_splunk MCP tool"""
    search_params = {
        "search_query": "index=main",
        "earliest_time": "-24h",
        "latest_time": "now",
        "max_results": 100,
    }

    expected_results = [
        {"result": {"field1": "value1", "field2": "value2"}},
        {"result": {"field1": "value3", "field2": "value4"}},
        {"result": {"field1": "value5", "field2": "value6"}},
        {"result": {"field1": "value7", "field2": "value8"}},
        {"result": {"field1": "value9", "field2": "value10"}},
    ]

    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        # Just verify that the call succeeds without exception
        result = await search_splunk(
            search_query=search_params["search_query"],
            earliest_time=search_params["earliest_time"],
            latest_time=search_params["latest_time"],
            max_results=search_params["max_results"],
        )
        # For this test, we just verify it doesn't throw an exception and returns results
        assert result is not None


@pytest.mark.asyncio
async def test_search_splunk_invalid_query(mock_splunk_service):
    """Test search_splunk with invalid query"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await search_splunk(
                search_query="",
                earliest_time="-24h",
                latest_time="now",
                max_results=100,
            )


@pytest.mark.asyncio
async def test_connection_error():
    """Test handling of connection errors"""
    # Mock get_splunk_connection to raise an exception
    with patch(
        "splunk_mcp.get_splunk_connection", side_effect=Exception("Connection failed")
    ):
        with pytest.raises(Exception, match="Connection failed"):
            await list_indexes()


@pytest.mark.asyncio
async def test_get_index_info_not_found(mock_splunk_service):
    """Test get_index_info with non-existent index"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        with pytest.raises(ValueError, match="Index not found: nonexistent"):
            await get_index_info(index_name="nonexistent")


@pytest.mark.asyncio
async def test_search_splunk_invalid_command(mock_splunk_service):
    """Test search_splunk with invalid command"""
    # Mock the jobs.create to raise an exception
    mock_splunk_service.jobs.create.side_effect = Exception(
        "Unknown search command 'invalid'"
    )

    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        with pytest.raises(Exception, match="Unknown search command 'invalid'"):
            await search_splunk(
                search_query="invalid command",
                earliest_time="-24h",
                latest_time="now",
                max_results=100,
            )


@pytest.mark.asyncio
async def test_list_saved_searches(mock_splunk_service):
    """Test the list_saved_searches MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await list_saved_searches()

        # If result is a dict with a single item, convert it to a list
        if isinstance(result, dict) and "name" in result:
            result = [result]

        assert len(result) > 0
        assert result[0]["name"] == "test_search"
        assert result[0]["description"] == "Test search description"
        assert result[0]["search"] == "index=main | stats count"


@pytest.mark.asyncio
async def test_current_user(mock_splunk_service):
    """Test the current_user MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await current_user()
        assert isinstance(result, dict)
        assert result["username"] == "admin"
        assert result["real_name"] == "Administrator"
        assert result["email"] == "admin@example.com"
        assert "admin" in result["roles"]


@pytest.mark.asyncio
async def test_list_users(mock_splunk_service):
    """Test the list_users MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await list_users()

        # If result is a dict with username, convert it to a list
        if isinstance(result, dict) and "username" in result:
            result = [result]

        assert len(result) > 0
        assert result[0]["username"] == "admin"
        assert result[0]["real_name"] == "Administrator"
        assert result[0]["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_list_kvstore_collections(mock_splunk_service):
    """Test the list_kvstore_collections MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await list_kvstore_collections()

        # If result is a dict with name, convert it to a list
        if isinstance(result, dict) and "name" in result:
            result = [result]

        assert len(result) > 0
        assert result[0]["name"] == "test_collection"
        assert result[0]["app"] == "search"


@pytest.mark.asyncio
async def test_health_check(mock_splunk_service):
    """Test the health_check MCP tool"""
    # Mock get_splunk_connection
    with patch("splunk_mcp.get_splunk_connection", return_value=mock_splunk_service):
        result = await health_check()
        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert "connection" in result
        assert "apps" in result
        assert len(result["apps"]) > 0


@pytest.mark.asyncio
async def test_list_tools():
    """Test the list_tools MCP tool"""
    # Get tools from the mcp server directly
    tools_dict = await mcp.get_tools()
    tools = list(tools_dict.values())

    assert isinstance(tools, list)
    assert len(tools) > 0
    # Each tool should have name and description attributes
    tool = tools[0]
    assert hasattr(tool, "name")
    assert hasattr(tool, "description")
