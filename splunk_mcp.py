import logging
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP  # Updated import path
from decouple import config
import splunklib.client as client
from splunklib import results
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("splunk")

# Splunk connection configuration
SPLUNK_HOST = config("SPLUNK_HOST", default="localhost")
SPLUNK_PORT = config("SPLUNK_PORT", default=8089)
SPLUNK_USERNAME = config("SPLUNK_USERNAME", default="admin")
SPLUNK_PASSWORD = config("SPLUNK_PASSWORD")
SPLUNK_SCHEME = config("SPLUNK_SCHEME", default="https")

def get_splunk_connection():
    """Helper function to establish Splunk connection"""
    try:
        service = client.connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            username=SPLUNK_USERNAME,
            password=SPLUNK_PASSWORD,
            scheme=SPLUNK_SCHEME
        )
        return service
    except Exception as e:
        logger.error(f"Failed to connect to Splunk: {str(e)}")
        raise

@mcp.tool()
async def search_splunk(
    search_query: str,
    earliest_time: Optional[str] = "-24h",
    latest_time: Optional[str] = "now",
    max_results: Optional[int] = 100
) -> List[Dict[str, Any]]:
    """
    Execute a Splunk search query and return results
    
    Args:
        search_query: The Splunk search query to execute
        earliest_time: Start time for the search (default: 24 hours ago)
        latest_time: End time for the search (default: now)
        max_results: Maximum number of results to return (default: 100)
    
    Returns:
        List of search results as dictionaries
    """
    try:
        service = get_splunk_connection()
        logger.info(f"🔍 Executing Splunk search: {search_query}")
        
        # Create the search job
        kwargs_search = {
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "preview": False,
            "exec_mode": "blocking"  # Make the search synchronous
        }
        
        # Remove 'search' if it's already in the query
        if not search_query.lower().startswith('search '):
            search_query = f"search {search_query}"
            
        job = service.jobs.create(search_query, **kwargs_search)
        
        # Get the results
        results_list = []
        
        # Get all results at once in JSON format
        result_stream = job.results(output_mode='json', count=max_results)
        
        # Parse the JSON response
        import json
        response_data = json.loads(result_stream.read().decode('utf-8'))
        
        if 'results' in response_data:
            results_list = response_data['results']
            
        logger.info(f"✅ Search completed. Found {len(results_list)} results")
        return results_list[:max_results]
        
    except Exception as e:
        logger.error(f"❌ Error executing Splunk search: {str(e)}")
        raise

@mcp.tool()
async def list_indexes() -> List[Dict[str, Any]]:  # Made async
    """
    List all available Splunk indexes
    
    Returns:
        List of dictionaries containing index information
    """
    try:
        service = get_splunk_connection()
        logger.info("📊 Fetching Splunk indexes...")
        indexes = []
        
        for index in service.indexes:
            index_info = {
                "name": index.name,
                "total_event_count": index["totalEventCount"],
                "current_size": index["currentDBSizeMB"],
                "max_size": index["maxTotalDataSizeMB"],
                "earliest_time": index["earliestTime"],
                "latest_time": index["latestTime"]
            }
            indexes.append(index_info)
            
        logger.info(f"✅ Found {len(indexes)} indexes")
        return indexes
        
    except Exception as e:
        logger.error(f"❌ Error listing indexes: {str(e)}")
        raise

@mcp.tool()
async def list_users() -> List[Dict[str, Any]]:  # Made async
    """
    List all Splunk users
    
    Returns:
        List of dictionaries containing user information
    """
    try:
        service = get_splunk_connection()
        logger.info("👥 Fetching Splunk users...")
        users = []
        
        for user in service.users:
            user_info = {
                "username": user.name,
                "real_name": user["realname"],
                "email": user["email"],
                "roles": [role for role in user.role_entities()],
                "default_app": user["defaultApp"],
                "type": user["type"]
            }
            users.append(user_info)
            
        logger.info(f"✅ Found {len(users)} users")
        return users
        
    except Exception as e:
        logger.error(f"❌ Error listing users: {str(e)}")
        raise

@mcp.tool()
async def list_kvstore_collections() -> List[Dict[str, Any]]:  # Made async
    """
    List all KV store collections
    
    Returns:
        List of dictionaries containing collection information
    """
    try:
        service = get_splunk_connection()
        logger.info("📦 Fetching KV store collections...")
        collections = []
        
        for app in service.apps:
            try:
                kvstore = app.kvstore
                for collection in kvstore:
                    collection_info = {
                        "name": collection.name,
                        "app": app.name,
                        "fields": collection.fields,
                        "accelerated_fields": collection.accelerated_fields,
                        "record_count": len(collection.data)
                    }
                    collections.append(collection_info)
            except Exception as e:
                logger.warning(f"⚠️ Error accessing KV store for app {app.name}: {str(e)}")
                continue
                
        logger.info(f"✅ Found {len(collections)} KV store collections")
        return collections
        
    except Exception as e:
        logger.error(f"❌ Error listing KV store collections: {str(e)}")
        raise

@mcp.tool()
async def create_kvstore_collection(  # Made async
    collection_name: str,
    app_name: str,
    fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new KV store collection
    
    Args:
        collection_name: Name of the collection to create
        app_name: Name of the app to create the collection in
        fields: Dictionary defining the collection schema
        
    Returns:
        Dictionary containing the created collection information
    """
    try:
        service = get_splunk_connection()
        logger.info(f"📝 Creating KV store collection: {collection_name} in app: {app_name}")
        app = service.apps[app_name]
        
        # Create the collection
        collection = app.kvstore.create(collection_name, fields)
        
        result = {
            "name": collection.name,
            "app": app_name,
            "fields": collection.fields,
            "accelerated_fields": collection.accelerated_fields
        }
        
        logger.info("✅ KV store collection created successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating KV store collection: {str(e)}")
        raise

@mcp.tool()
async def delete_kvstore_collection(  # Made async
    collection_name: str,
    app_name: str
) -> bool:
    """
    Delete a KV store collection
    
    Args:
        collection_name: Name of the collection to delete
        app_name: Name of the app containing the collection
        
    Returns:
        True if deletion was successful
    """
    try:
        service = get_splunk_connection()
        logger.info(f"🗑️ Deleting KV store collection: {collection_name} from app: {app_name}")
        app = service.apps[app_name]
        
        # Delete the collection
        app.kvstore[collection_name].delete()
        logger.info("✅ KV store collection deleted successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting KV store collection: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("🚀 Starting Splunk MCP server")
    mcp.run(transport="sse")  # Added SSE transport 