# Import packages
import json
import logging
import os
import ssl
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import splunklib.client
from decouple import config
from mcp.server.fastmcp import FastMCP
from splunklib import results
import sys
import socket
from fastapi import FastAPI, APIRouter, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("splunk_mcp.log")
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
FASTMCP_PORT = int(os.environ.get("FASTMCP_PORT", "8000"))
os.environ["FASTMCP_PORT"] = str(FASTMCP_PORT)

# Create FastAPI application with metadata
app = FastAPI(
    title="Splunk MCP API",
    description="A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language",
    version="0.3.0",
)

# Initialize the MCP server
mcp = FastMCP(
    "splunk",
    description="A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language",
    version="0.3.0",
    host="0.0.0.0",  # Listen on all interfaces
    port=FASTMCP_PORT
)

# Create SSE transport instance for handling server-sent events
sse = SseServerTransport("/messages/")

# Mount the /messages path to handle SSE message posting
app.router.routes.append(Mount("/messages", app=sse.handle_post_message))

# Add documentation for the /messages endpoint
@app.get("/messages", tags=["MCP"], include_in_schema=True)
def messages_docs():
    """
    Messages endpoint for SSE communication

    This endpoint is used for posting messages to SSE clients.
    Note: This route is for documentation purposes only.
    The actual implementation is handled by the SSE transport.
    """
    pass

@app.get("/sse", tags=["MCP"])
async def handle_sse(request: Request):
    """
    SSE endpoint that connects to the MCP server

    This endpoint establishes a Server-Sent Events connection with the client
    and forwards communication to the Model Context Protocol server.
    """
    # Use sse.connect_sse to establish an SSE connection with the MCP server
    async with sse.connect_sse(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        # Run the MCP server with the established streams
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options(),
        )

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{mcp.name} - Swagger UI"
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{mcp.name} - ReDoc"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """Generate OpenAPI schema that documents MCP tools as operations"""
    # Get the OpenAPI schema from MCP tools
    tools = await list_tools()
    
    # Define the tool request/response schemas
    tool_schemas = {
        "ToolRequest": {
            "type": "object",
            "required": ["tool", "parameters"],
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "The name of the tool to execute"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the tool execution"
                }
            }
        },
        "ToolResponse": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "The result of the tool execution"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if the execution failed"
                }
            }
        }
    }
    
    # Convert MCP tools to OpenAPI operations
    tool_operations = {}
    for tool in tools:
        tool_name = tool["name"]
        tool_desc = tool["description"]
        tool_params = tool.get("parameters", {}).get("properties", {})
        
        # Create parameter schema for this specific tool
        param_schema = {
            "type": "object",
            "required": tool.get("parameters", {}).get("required", []),
            "properties": {}
        }
        
        # Add each parameter's properties
        for param_name, param_info in tool_params.items():
            param_schema["properties"][param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
                "default": param_info.get("default", None)
            }
        
        # Add operation for this tool
        operation_id = f"execute_{tool_name}"
        tool_operations[operation_id] = {
            "summary": tool_desc.split("\n")[0] if tool_desc else tool_name,
            "description": tool_desc,
            "tags": ["MCP Tools"],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["parameters"],
                            "properties": {
                                "parameters": param_schema
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Successful tool execution",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ToolResponse"}
                        }
                    }
                },
                "400": {
                    "description": "Invalid parameters",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    # Build OpenAPI schema
    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "Splunk MCP API",
            "description": "A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language",
            "version": VERSION
        },
        "paths": {
            "/sse": {
                "get": {
                    "summary": "SSE Connection",
                    "description": "Establishes a Server-Sent Events connection for real-time communication",
                    "tags": ["MCP Core"],
                    "responses": {
                        "200": {
                            "description": "SSE connection established"
                        }
                    }
                }
            },
            "/messages": {
                "get": {
                    "summary": "Messages Endpoint",
                    "description": "Endpoint for SSE message communication",
                    "tags": ["MCP Core"],
                    "responses": {
                        "200": {
                            "description": "Message endpoint ready"
                        }
                    }
                }
            },
            "/execute": {
                "post": {
                    "summary": "Execute MCP Tool",
                    "description": "Execute any available MCP tool with the specified parameters",
                    "tags": ["MCP Tools"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ToolRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tool executed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ToolResponse"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                **tool_schemas,
                **{f"{tool['name']}Parameters": {
                    "type": "object",
                    "properties": tool.get("parameters", {}).get("properties", {}),
                    "required": tool.get("parameters", {}).get("required", [])
                } for tool in tools}
            }
        },
        "tags": [
            {"name": "MCP Core", "description": "Core MCP server endpoints"},
            {"name": "MCP Tools", "description": "Available MCP tools and operations"}
        ],
        "x-mcp-tools": tool_operations
    }
    
    return JSONResponse(content=openapi_schema)

# Global variables
VERSION = "0.3.0"
SPLUNK_HOST = os.environ.get("SPLUNK_HOST", "localhost")
SPLUNK_PORT = int(os.environ.get("SPLUNK_PORT", "8089"))
SPLUNK_SCHEME = os.environ.get("SPLUNK_SCHEME", "https")
SPLUNK_PASSWORD = os.environ.get("SPLUNK_PASSWORD", "admin")
VERIFY_SSL = config("VERIFY_SSL", default="true", cast=bool)

def get_splunk_connection() -> splunklib.client.Service:
    """
    Get a connection to the Splunk service.
    
    Returns:
        splunklib.client.Service: Connected Splunk service
    """
    try:
        username = os.environ.get("SPLUNK_USERNAME", "admin")
        
        logger.debug(f"🔌 Connecting to Splunk at {SPLUNK_SCHEME}://{SPLUNK_HOST}:{SPLUNK_PORT} as {username}")
        
        # Connect to Splunk
        service = splunklib.client.connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            username=username,
            password=SPLUNK_PASSWORD,
            scheme=SPLUNK_SCHEME,
            verify=VERIFY_SSL
        )
        
        logger.debug(f"✅ Connected to Splunk successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to connect to Splunk: {str(e)}")
        raise

@mcp.tool()
async def search_splunk(search_query: str, earliest_time: str = "-24h", latest_time: str = "now", max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Execute a Splunk search query and return the results.
    
    Args:
        search_query: The search query to execute
        earliest_time: Start time for the search (default: 24 hours ago)
        latest_time: End time for the search (default: now)
        max_results: Maximum number of results to return (default: 100)
        
    Returns:
        List of search results
    """
    if not search_query:
        raise ValueError("Search query cannot be empty")
        
    try:
        service = get_splunk_connection()
        logger.info(f"🔍 Executing search: {search_query}")
        
        # Create the search job
        kwargs_search = {
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "preview": False,
            "exec_mode": "blocking"
        }
        
        job = service.jobs.create(search_query, **kwargs_search)
        
        # Get the results
        result_stream = job.results(output_mode='json', count=max_results)
        results_data = json.loads(result_stream.read().decode('utf-8'))
        
        return results_data.get("results", [])
        
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}")
        raise

@mcp.tool()
async def list_indexes() -> Dict[str, List[str]]:
    """
    Get a list of all available Splunk indexes.
    
    Returns:
        Dictionary containing list of indexes
    """
    try:
        service = get_splunk_connection()
        indexes = [index.name for index in service.indexes]
        logger.info(f"📊 Found {len(indexes)} indexes")
        return {"indexes": indexes}
    except Exception as e:
        logger.error(f"❌ Failed to list indexes: {str(e)}")
        raise

@mcp.tool()
async def get_index_info(index_name: str) -> Dict[str, Any]:
    """
    Get metadata for a specific Splunk index.
    
    Args:
        index_name: Name of the index to get metadata for
        
    Returns:
        Dictionary containing index metadata
    """
    try:
        service = get_splunk_connection()
        index = service.indexes[index_name]
        
        return {
            "name": index_name,
            "total_event_count": str(index["totalEventCount"]),
            "current_size": str(index["currentDBSizeMB"]),
            "max_size": str(index["maxTotalDataSizeMB"]),
            "min_time": str(index["minTime"]),
            "max_time": str(index["maxTime"])
        }
    except KeyError:
        logger.error(f"❌ Index not found: {index_name}")
        raise ValueError(f"Index not found: {index_name}")
    except Exception as e:
        logger.error(f"❌ Failed to get index info: {str(e)}")
        raise

@mcp.tool()
async def list_saved_searches() -> List[Dict[str, Any]]:
    """
    List all saved searches in Splunk
    
    Returns:
        List of saved searches with their names, descriptions, and search queries
    """
    try:
        service = get_splunk_connection()
        saved_searches = []
        
        for saved_search in service.saved_searches:
            try:
                saved_searches.append({
                    "name": saved_search.name,
                    "description": saved_search.description or "",
                    "search": saved_search.search
                })
            except Exception as e:
                logger.warning(f"⚠️ Error processing saved search: {str(e)}")
                continue
            
        return saved_searches
        
    except Exception as e:
        logger.error(f"❌ Failed to list saved searches: {str(e)}")
        raise

@mcp.tool()
async def current_user() -> Dict[str, Any]:
    """
    Get information about the currently authenticated user.
    
    This endpoint retrieves:
    - Basic user information (username, real name, email)
    - Assigned roles
    - Default app settings
    - User type
    
    Returns:
        Dict[str, Any]: Dictionary containing user information
    """
    try:
        service = get_splunk_connection()
        logger.info("👤 Fetching current user information...")
        
        # First try to get username from environment variable
        current_username = os.environ.get("SPLUNK_USERNAME", "admin")
        logger.debug(f"Using username from environment: {current_username}")
        
        # Try to get additional context information
        try:
            # Get the current username from the /services/authentication/current-context endpoint
            current_context_resp = service.get("/services/authentication/current-context", **{"output_mode":"json"}).body.read()
            current_context_obj = json.loads(current_context_resp)
            if "entry" in current_context_obj and len(current_context_obj["entry"]) > 0:
                context_username = current_context_obj["entry"][0]["content"].get("username")
                if context_username:
                    current_username = context_username
                    logger.debug(f"Using username from current-context: {current_username}")
        except Exception as context_error:
            logger.warning(f"⚠️ Could not get username from current-context: {str(context_error)}")
        
        try:
            # Get the current user by username
            current_user = service.users[current_username]
            
            # Ensure roles is a list
            roles = []
            if hasattr(current_user, 'roles') and current_user.roles:
                roles = list(current_user.roles)
            else:
                # Try to get from content
                if hasattr(current_user, 'content'):
                    roles = current_user.content.get("roles", [])
                else:
                    roles = current_user.get("roles", [])
                
                if roles is None:
                    roles = []
                elif isinstance(roles, str):
                    roles = [roles]
            
            # Determine how to access user properties
            if hasattr(current_user, 'content') and isinstance(current_user.content, dict):
                user_info = {
                    "username": current_user.name,
                    "real_name": current_user.content.get('realname', "N/A") or "N/A",
                    "email": current_user.content.get('email', "N/A") or "N/A",
                    "roles": roles,
                    "capabilities": current_user.content.get('capabilities', []) or [],
                    "default_app": current_user.content.get('defaultApp', "search") or "search",
                    "type": current_user.content.get('type', "user") or "user"
                }
            else:
                user_info = {
                    "username": current_user.name,
                    "real_name": current_user.get("realname", "N/A") or "N/A",
                    "email": current_user.get("email", "N/A") or "N/A",
                    "roles": roles,
                    "capabilities": current_user.get("capabilities", []) or [],
                    "default_app": current_user.get("defaultApp", "search") or "search",
                    "type": current_user.get("type", "user") or "user"
                }
            
            logger.info(f"✅ Successfully retrieved current user information: {current_user.name}")
            return user_info
            
        except KeyError:
            logger.error(f"❌ User not found: {current_username}")
            raise ValueError(f"User not found: {current_username}")
            
    except Exception as e:
        logger.error(f"❌ Error getting current user: {str(e)}")
        raise

@mcp.tool()
async def list_users() -> List[Dict[str, Any]]:
    """List all Splunk users (requires admin privileges)"""
    try:
        service = get_splunk_connection()
        logger.info("👥 Fetching Splunk users...")
                
        users = []
        for user in service.users:
            try:
                if hasattr(user, 'content'):
                    # Ensure roles is a list
                    roles = user.content.get('roles', [])
                    if roles is None:
                        roles = []
                    elif isinstance(roles, str):
                        roles = [roles]
                    
                    # Ensure capabilities is a list
                    capabilities = user.content.get('capabilities', [])
                    if capabilities is None:
                        capabilities = []
                    elif isinstance(capabilities, str):
                        capabilities = [capabilities]
                    
                    user_info = {
                        "username": user.name,
                        "real_name": user.content.get('realname', "N/A") or "N/A",
                        "email": user.content.get('email', "N/A") or "N/A",
                        "roles": roles,
                        "capabilities": capabilities,
                        "default_app": user.content.get('defaultApp', "search") or "search",
                        "type": user.content.get('type', "user") or "user"
                    }
                    users.append(user_info)
                    logger.debug(f"✅ Successfully processed user: {user.name}")
                else:
                    # Handle users without content
                    user_info = {
                        "username": user.name,
                        "real_name": "N/A",
                        "email": "N/A",
                        "roles": [],
                        "capabilities": [],
                        "default_app": "search",
                        "type": "user"
                    }
                    users.append(user_info)
                    logger.warning(f"⚠️ User {user.name} has no content, using default values")
            except Exception as e:
                logger.warning(f"⚠️ Error processing user {user.name}: {str(e)}")
                continue
            
        logger.info(f"✅ Found {len(users)} users")
        return users
        
    except Exception as e:
        logger.error(f"❌ Error listing users: {str(e)}")
        raise

@mcp.tool()
async def list_kvstore_collections() -> List[Dict[str, Any]]:
    """
    List all KV store collections across apps.
    
    Returns:
        List of KV store collections with metadata including app, fields, and accelerated fields
    """
    try:
        service = get_splunk_connection()
        logger.info("📚 Fetching KV store collections...")
        
        collections = []
        app_count = 0
        collections_found = 0
        
        # Get KV store collection stats to retrieve record counts
        collection_stats = {}
        try:
            stats_response = service.get("/services/server/introspection/kvstore/collectionstats", output_mode="json")
            stats_data = json.loads(stats_response.body.read())
            if "entry" in stats_data and len(stats_data["entry"]) > 0:
                entry = stats_data["entry"][0]
                content = entry.get("content", {})
                data = content.get("data", {})
                for kvstore in data:
                    kvstore = json.loads(kvstore)
                    if "ns" in kvstore and "count" in kvstore:
                        collection_stats[kvstore["ns"]] = kvstore["count"]
                logger.debug(f"✅ Retrieved stats for {len(collection_stats)} KV store collections")
        except Exception as e:
            logger.warning(f"⚠️ Error retrieving KV store collection stats: {str(e)}")
            
        try:
            for entry in service.kvstore:
                try:
                    collection_name = entry['name']
                    fieldsList = [f.replace('field.', '') for f in entry['content'] if f.startswith('field.')]
                    accelFields = [f.replace('accelerated_field.', '') for f in entry['content'] if f.startswith('accelerated_field.')]
                    app_name = entry['access']['app']
                    collection_data = {
                        "name": collection_name,
                        "app": app_name,
                        "fields": fieldsList,
                        "accelerated_fields": accelFields,
                        "record_count": collection_stats.get(f"{app_name}.{collection_name}", 0)
                    }
                    collections.append(collection_data)
                    collections_found += 1
                    logger.debug(f"✅ Added collection: {collection_name} from app: {app_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Error processing collection entry: {str(e)}")
                    continue
            
            logger.info(f"✅ Found {collections_found} KV store collections")
            return collections
            
        except Exception as e:
            logger.error(f"❌ Error accessing KV store collections: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"❌ Error listing KV store collections: {str(e)}")
        raise

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Get basic Splunk connection information and list available apps"""
    try:
        service = get_splunk_connection()
        logger.info("🏥 Performing health check...")
        
        # List available apps
        apps = []
        for app in service.apps:
            try:
                app_info = {
                    "name": app['name'],
                    "label": app['label'],
                    "version": app['version']
                }
                apps.append(app_info)
            except Exception as e:
                logger.warning(f"⚠️ Error getting info for app {app['name']}: {str(e)}")
                continue
        
        response = {
            "status": "healthy",
            "connection": {
                "host": SPLUNK_HOST,
                "port": SPLUNK_PORT,
                "scheme": SPLUNK_SCHEME,
                "username": os.environ.get("SPLUNK_USERNAME", "admin"),
                "ssl_verify": VERIFY_SSL
            },
            "apps_count": len(apps),
            "apps": apps
        }
        
        logger.info(f"✅ Health check successful. Found {len(apps)} apps")
        return response
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        raise

@mcp.tool()
async def get_indexes_and_sourcetypes() -> Dict[str, Any]:
    """
    Get a list of all indexes and their sourcetypes.
    
    This endpoint performs a search to gather:
    - All available indexes
    - All sourcetypes within each index
    - Event counts for each sourcetype
    - Time range information
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - indexes: List of all accessible indexes
            - sourcetypes: Dictionary mapping indexes to their sourcetypes
            - metadata: Additional information about the search
    """
    try:
        service = get_splunk_connection()
        logger.info("📊 Fetching indexes and sourcetypes...")
        
        # Get list of indexes
        indexes = [index.name for index in service.indexes]
        logger.info(f"Found {len(indexes)} indexes")
        
        # Search for sourcetypes across all indexes
        search_query = """
        | tstats count WHERE index=* BY index, sourcetype
        | stats count BY index, sourcetype
        | sort - count
        """
        
        kwargs_search = {
            "earliest_time": "-24h",
            "latest_time": "now",
            "preview": False,
            "exec_mode": "blocking"
        }
        
        logger.info("🔍 Executing search for sourcetypes...")
        job = service.jobs.create(search_query, **kwargs_search)
        
        # Get the results
        result_stream = job.results(output_mode='json')
        results_data = json.loads(result_stream.read().decode('utf-8'))
        
        # Process results
        sourcetypes_by_index = {}
        for result in results_data.get('results', []):
            index = result.get('index', '')
            sourcetype = result.get('sourcetype', '')
            count = result.get('count', '0')
            
            if index not in sourcetypes_by_index:
                sourcetypes_by_index[index] = []
            
            sourcetypes_by_index[index].append({
                'sourcetype': sourcetype,
                'count': count
            })
        
        response = {
            'indexes': indexes,
            'sourcetypes': sourcetypes_by_index,
            'metadata': {
                'total_indexes': len(indexes),
                'total_sourcetypes': sum(len(st) for st in sourcetypes_by_index.values()),
                'search_time_range': '24 hours'
            }
        }
        
        logger.info(f"✅ Successfully retrieved indexes and sourcetypes")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting indexes and sourcetypes: {str(e)}")
        raise

@mcp.tool()
async def list_tools() -> List[Dict[str, Any]]:
    """
    List all available MCP tools.
    
    Returns:
        List of all available tools with their name, description, and parameters.
    """
    try:
        logger.info("🧰 Listing available MCP tools...")
        tools_list = []
        
        # Try to access tools from different potential attributes
        if hasattr(mcp, '_tools') and isinstance(mcp._tools, dict):
            # Direct access to the tools dictionary
            for name, tool_info in mcp._tools.items():
                try:
                    tool_data = {
                        "name": name,
                        "description": tool_info.get("description", "No description available"),
                        "parameters": tool_info.get("parameters", {})
                    }
                    tools_list.append(tool_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing tool {name}: {str(e)}")
                    continue
                    
        elif hasattr(mcp, 'tools') and callable(getattr(mcp, 'tools', None)):
            # Tools accessed as a method
            for name, tool_info in mcp.tools().items():
                try:
                    tool_data = {
                        "name": name,
                        "description": tool_info.get("description", "No description available"),
                        "parameters": tool_info.get("parameters", {})
                    }
                    tools_list.append(tool_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing tool {name}: {str(e)}")
                    continue
                    
        elif hasattr(mcp, 'registered_tools') and isinstance(mcp.registered_tools, dict):
            # Access through registered_tools attribute
            for name, tool_info in mcp.registered_tools.items():
                try:
                    description = (
                        tool_info.get("description", None) or 
                        getattr(tool_info, "description", None) or
                        "No description available"
                    )
                    
                    parameters = (
                        tool_info.get("parameters", None) or 
                        getattr(tool_info, "parameters", None) or
                        {}
                    )
                    
                    tool_data = {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                    tools_list.append(tool_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing tool {name}: {str(e)}")
                    continue
        
        # Sort tools by name for consistent ordering
        tools_list.sort(key=lambda x: x["name"])
        
        logger.info(f"✅ Found {len(tools_list)} tools")
        return tools_list
        
    except Exception as e:
        logger.error(f"❌ Error listing tools: {str(e)}")
        raise

@mcp.tool()
async def health() -> Dict[str, Any]:
    """Get basic Splunk connection information and list available apps (same as health_check but for endpoint consistency)"""
    return await health_check()

@mcp.tool()
async def ping() -> Dict[str, Any]:
    """
    Simple ping endpoint to check server availability and get basic server information.
    
    This endpoint provides a lightweight way to:
    - Verify the server is running and responsive
    - Get basic server information including version and server time
    - Check connectivity without making complex API calls
    
    Returns:
        Dict[str, Any]: Dictionary containing status and basic server information
    """
    try:
        return {
            "status": "ok",
            "server": "splunk-mcp",
            "version": VERSION,
            "timestamp": datetime.now().isoformat(),
            "protocol": "mcp",
            "capabilities": ["splunk"]
        }
    except Exception as e:
        logger.error(f"❌ Error in ping endpoint: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import sys
    
    # Get the mode from command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "sse"
    
    if mode not in ["stdio", "sse"]:
        logger.error(f"❌ Invalid mode: {mode}. Must be one of: stdio, sse")
        sys.exit(1)
    
    # Set logger level to debug if DEBUG environment variable is set
    if os.environ.get("DEBUG", "false").lower() == "true":
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Logger level set to DEBUG, server will run on port {FASTMCP_PORT}")
    
    # Start the server
    logger.info(f"🚀 Starting Splunk MCP server in {mode.upper()} mode")
    
    if mode == "stdio":
        # Run in stdio mode
        mcp.run(transport=mode)
    else:
        # Run in SSE mode with documentation
        uvicorn.run(app, host="0.0.0.0", port=FASTMCP_PORT) 
