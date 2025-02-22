import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from datetime import datetime
from splunk_mcp import (
    get_splunk_connection,
    search_splunk,
    list_indexes,
    list_users,
    list_kvstore_collections,
    create_kvstore_collection,
    delete_kvstore_collection,
)

# Mock data for testing
MOCK_SEARCH_RESULTS = {
    "results": [
        {"field1": "value1", "field2": "value2"},
        {"field1": "value3", "field2": "value4"},
    ]
}

MOCK_INDEXES = [
    {
        "name": "main",
        "totalEventCount": "1000",
        "currentDBSizeMB": "100",
        "maxTotalDataSizeMB": "500",
        "earliestTime": "0",
        "latestTime": "1615430400",
    }
]

MOCK_USERS = [
    {
        "name": "admin",
        "realname": "Administrator",
        "email": "admin@example.com",
        "defaultApp": "search",
        "type": "admin",
    }
]

MOCK_KVSTORE_COLLECTIONS = [
    {
        "name": "test_collection",
        "app": "search",
        "fields": {"field1": "string", "field2": "number"},
        "accelerated_fields": {},
        "record_count": 10,
    }
]

@pytest.fixture
def mock_splunk_service():
    """Fixture to create a mock Splunk service"""
    mock_service = Mock()
    
    # Mock search job
    mock_job = Mock()
    mock_results = Mock()
    mock_results.read.return_value = json.dumps(MOCK_SEARCH_RESULTS).encode('utf-8')
    mock_job.results.return_value = mock_results
    mock_service.jobs.create.return_value = mock_job
    
    # Mock indexes
    mock_index = MagicMock()  # Use MagicMock for __getitem__ support
    mock_index.name = MOCK_INDEXES[0]["name"]
    mock_index.__getitem__.side_effect = lambda x: MOCK_INDEXES[0][x]
    mock_service.indexes = [mock_index]
    
    # Mock users
    mock_user = MagicMock()  # Use MagicMock for __getitem__ support
    mock_user.name = MOCK_USERS[0]["name"]
    mock_user.__getitem__.side_effect = lambda x: MOCK_USERS[0][x]
    mock_user.role_entities.return_value = ["admin"]
    mock_service.users = [mock_user]
    
    # Mock KV store
    mock_collection = MagicMock()  # Use MagicMock for attribute access
    mock_collection.name = MOCK_KVSTORE_COLLECTIONS[0]["name"]
    mock_collection.fields = MOCK_KVSTORE_COLLECTIONS[0]["fields"]
    mock_collection.accelerated_fields = MOCK_KVSTORE_COLLECTIONS[0]["accelerated_fields"]
    mock_collection.data = range(10)
    
    mock_app = MagicMock()  # Use MagicMock for attribute access
    mock_app.name = "search"
    mock_app.kvstore = [mock_collection]
    mock_service.apps = [mock_app]
    
    return mock_service

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_search_splunk(mock_get_conn, mock_splunk_service):
    """Test the search_splunk function"""
    mock_get_conn.return_value = mock_splunk_service
    
    results = await search_splunk(
        search_query="search index=main",
        earliest_time="-1h",
        latest_time="now",
        max_results=10
    )
    
    assert results == MOCK_SEARCH_RESULTS["results"]
    mock_splunk_service.jobs.create.assert_called_once()
    search_args = mock_splunk_service.jobs.create.call_args[0][0]
    assert search_args == "search index=main"

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_list_indexes(mock_get_conn, mock_splunk_service):
    """Test the list_indexes function"""
    mock_get_conn.return_value = mock_splunk_service
    
    indexes = await list_indexes()
    
    assert len(indexes) == 1
    assert indexes[0]["name"] == MOCK_INDEXES[0]["name"]
    assert indexes[0]["total_event_count"] == MOCK_INDEXES[0]["totalEventCount"]

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_list_users(mock_get_conn, mock_splunk_service):
    """Test the list_users function"""
    mock_get_conn.return_value = mock_splunk_service
    
    users = await list_users()
    
    assert len(users) == 1
    assert users[0]["username"] == MOCK_USERS[0]["name"]
    assert users[0]["real_name"] == MOCK_USERS[0]["realname"]
    assert users[0]["roles"] == ["admin"]

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_list_kvstore_collections(mock_get_conn, mock_splunk_service):
    """Test the list_kvstore_collections function"""
    mock_get_conn.return_value = mock_splunk_service
    
    collections = await list_kvstore_collections()
    
    assert len(collections) == 1
    assert collections[0]["name"] == MOCK_KVSTORE_COLLECTIONS[0]["name"]
    assert collections[0]["app"] == MOCK_KVSTORE_COLLECTIONS[0]["app"]
    assert collections[0]["fields"] == MOCK_KVSTORE_COLLECTIONS[0]["fields"]

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_create_kvstore_collection(mock_get_conn, mock_splunk_service):
    """Test the create_kvstore_collection function"""
    mock_get_conn.return_value = mock_splunk_service
    
    fields = {"field1": "string", "field2": "number"}
    result = await create_kvstore_collection(
        collection_name="test_collection",
        app_name="search",
        fields=fields
    )
    
    assert result["name"] == MOCK_KVSTORE_COLLECTIONS[0]["name"]
    assert result["app"] == MOCK_KVSTORE_COLLECTIONS[0]["app"]
    assert result["fields"] == fields

@pytest.mark.asyncio
@patch('splunk_mcp.get_splunk_connection')
async def test_delete_kvstore_collection(mock_get_conn, mock_splunk_service):
    """Test the delete_kvstore_collection function"""
    mock_get_conn.return_value = mock_splunk_service
    
    result = await delete_kvstore_collection(
        collection_name="test_collection",
        app_name="search"
    )
    
    assert result is True 