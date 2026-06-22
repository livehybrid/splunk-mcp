# Upgrade to FastMCP 2.x and MCP 1.25.0

**Date:** January 20, 2026  
**Status:** ✅ Complete

## Overview

This document describes the upgrade from FastMCP 0.4.x and MCP 1.5.0 to FastMCP 2.14.3 and MCP 1.25.0, including all dependency updates and required code changes.

## Dependency Updates

### Core Dependencies

All dependencies updated in [`pyproject.toml`](pyproject.toml):

| Package | Previous Version | Updated Version | Notes |
|---------|-----------------|-----------------|-------|
| `mcp` | 1.5.0 | **1.25.0** | Primary upgrade target |
| `fastmcp` | 0.4.0 | **2.14.3** | Major version upgrade with breaking changes |
| `fastapi` | 0.104.0 | **0.128.0** | |
| `starlette` | 0.27.0 | **0.50.0** | Constrained by FastAPI |
| `pydantic` | 2.0.0 | **2.12.5** | |
| `pydantic-settings` | 2.0.0 | **2.12.0** | |
| `uvicorn` | 0.23.1 | **0.40.0** | |
| `aiohttp` | 3.11.14 | **3.13.3** | |

### Dev Dependencies

| Package | Previous Version | Updated Version |
|---------|-----------------|-----------------|
| `pytest` | 8.3.0 | **9.0.2** |
| `pytest-asyncio` | 0.21.0 | **1.3.0** |
| `black` | 25.1.0 | **26.1.0** |

## Breaking Changes in FastMCP 2.x

### 1. Import Path Changed

**Before:**
```python
from mcp.server.fastmcp import FastMCP
```

**After:**
```python
from fastmcp import FastMCP
```

### 2. Constructor Parameters Changed

**Before:**
```python
mcp = FastMCP(
    "splunk",
    description="Description text",
    version="0.3.0",
    host="0.0.0.0",
    port=8000
)
```

**After:**
```python
mcp = FastMCP(
    name="splunk",
    instructions="Description text",  # Changed from 'description'
    version="0.3.0"
    # host and port removed - now passed to run() method
)
```

Key changes:
- `description` parameter renamed to `instructions`
- `host` and `port` are deprecated in constructor (pass to `run()` instead)
- All keyword arguments after `instructions` must be keyword-only

### 3. Tool Registration Unchanged

The `@mcp.tool()` decorator still works the same way - no changes needed to tool functions themselves.

### 4. Testing API Changed

**Before:**
```python
result = await mcp.call_tool("tool_name", {"param": "value"})
```

**After:**
```python
# Tools are wrapped in FunctionTool objects
# Access the underlying function via .fn attribute
from splunk_mcp import list_indexes
actual_function = list_indexes.fn
result = await actual_function()
```

## Code Changes

### File: `splunk_mcp.py`

**Line 12 - Import statement:**
```python
# Before
from mcp.server.fastmcp import FastMCP

# After
from fastmcp import FastMCP
```

**Lines 46-51 - FastMCP initialization:**
```python
# Before
mcp = FastMCP(
    "splunk",
    description="A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language",
    version="0.3.0",
    host="0.0.0.0",
    port=FASTMCP_PORT
)

# After
mcp = FastMCP(
    name="splunk",
    instructions="A FastMCP-based tool for interacting with Splunk Enterprise/Cloud through natural language",
    version="0.3.0"
)
```

## Test Updates

### File: `tests/test_mcp.py`

**Key Changes:**

1. **Updated imports to access underlying functions:**
```python
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
```

2. **Updated all test calls to use direct function invocation:**
```python
# Before
result = await mcp.call_tool("list_indexes", {})

# After
result = await list_indexes()
```

3. **Updated test_list_tools to use FastMCP 2.x API:**
```python
# Before
result = await mcp.call_tool("list_tools", {})

# After
tools_dict = await mcp.get_tools()
tools = list(tools_dict.values())
```

4. **Fixed exception type expectations:**
```python
# test_search_splunk_invalid_query now expects ValueError instead of Exception
with pytest.raises(ValueError, match="Search query cannot be empty"):
    await search_splunk(...)

# test_get_index_info_not_found now expects ValueError
with pytest.raises(ValueError, match="Index not found: nonexistent"):
    await get_index_info(index_name="nonexistent")
```

### File: `tests/test_endpoints_pytest.py`

**Key Changes:**

1. **Added function unwrapping imports:**
```python
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
```

2. **Updated TEST_FUNCTIONS to use function objects:**
```python
# Before
TEST_FUNCTIONS = [
    "list_indexes",
    "list_saved_searches",
    ...
]

# After
TEST_FUNCTIONS = [
    list_indexes,
    list_saved_searches,
    ...
]
```

3. **Updated test_function_directly to handle function objects:**
```python
# Now extracts function name from the function object itself
function_name = function.__name__
```

4. **Updated test_tools_registration:**
```python
# Before
assert hasattr(mcp, "call_tool")

# After
assert hasattr(mcp, "get_tools")
assert hasattr(mcp, "_tool_manager")
```

5. **Updated test_ping to use direct function call:**
```python
# Before
result = await mcp.call_tool("ping", {})
result_dict = json.loads(result[0].text)

# After
result = await ping()
# Result is now a dict directly, no need to parse
```

## Installation

To install the updated dependencies:

```bash
uv sync --extra dev
```

## Testing

All tests pass successfully:

```bash
uv run python -m pytest tests/ -v
```

**Results:** ✅ 34/34 tests passing

- `tests/test_mcp.py`: 13/13 passing
- `tests/test_endpoints_pytest.py`: 21/21 passing

## Verification

To verify the application still works correctly:

```bash
# Run in SSE mode (default)
uv run python splunk_mcp.py

# Run in STDIO mode (for Claude Desktop)
uv run python splunk_mcp.py stdio

# Run in HTTP mode
uv run python splunk_mcp.py http
```

## Migration Checklist

- [x] Update `pyproject.toml` with new dependency versions
- [x] Run `uv sync --extra dev` to install dependencies
- [x] Update import statement in `splunk_mcp.py`
- [x] Update FastMCP constructor parameters
- [x] Update test files to use new testing patterns
- [x] Run full test suite to verify compatibility
- [x] Test application startup in all modes

## Notes

1. **FastMCP 2.x Deprecation Warnings:**
   - Passing `host` and `port` to the FastMCP constructor triggers deprecation warnings
   - These parameters should be passed to the `run()` method instead
   - We removed them from the constructor to avoid warnings

2. **FunctionTool Wrapper:**
   - In FastMCP 2.x, decorated functions are wrapped in `FunctionTool` objects
   - Access the underlying function via the `.fn` attribute for direct testing
   - The wrapper provides additional metadata and validation

3. **Testing Pattern:**
   - Direct function invocation is now preferred over `mcp.call_tool()`
   - This provides cleaner test code and better type checking
   - The `.fn` attribute gives access to the original async function

4. **Starlette Version:**
   - Starlette 0.52.1 was initially attempted but FastAPI 0.128.0 requires `<0.51.0`
   - Final version settled on 0.50.0 to satisfy FastAPI's constraint

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://github.com/anthropics/mcp)
- Project: `splunk-mcp` v0.4.0
