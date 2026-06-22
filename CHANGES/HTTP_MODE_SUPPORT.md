# HTTP Transport Mode Support

**Date:** January 20, 2026  
**Status:** ✅ Complete

## Overview

This document describes the addition of HTTP transport mode to the Splunk MCP server. HTTP transport is the current standard in the MCP protocol specification, superseding the Server-Sent Events (SSE) transport that was previously the primary mode.

## Background

### MCP Protocol Evolution

The Model Context Protocol (MCP) specification has evolved to standardize on HTTP transport for client-server communication:

- **SSE Transport**: Original implementation, still supported but considered legacy
- **HTTP Transport**: Current standard as of MCP 1.25.0, recommended for all new implementations
- **STDIO Transport**: Remains the standard for desktop integrations like Claude Desktop

### Design Decision: SSE as Default

While HTTP is the current MCP standard, we maintained **SSE as the default** transport mode for backward compatibility:

- Existing users and integrations continue to work without changes
- No breaking changes to deployment scripts or configurations
- Users can explicitly opt into HTTP mode when ready
- Clear documentation guides users toward HTTP as the recommended mode

## Changes Implemented

### 1. Command-Line Interface Update

**File:** [`splunk_mcp.py`](splunk_mcp.py)

**Lines 970-1000:**

Added `http` as a valid transport mode alongside `stdio` and `sse`:

```python
# Get the mode from command line arguments
mode = sys.argv[1] if len(sys.argv) > 1 else "sse"

if mode not in ["stdio", "sse", "http"]:
    logger.error(f"❌ Invalid mode: {mode}. Must be one of: stdio, http, sse")
    sys.exit(1)
```

### 2. HTTP Transport Initialization

**File:** [`splunk_mcp.py`](splunk_mcp.py)

**Lines 993-996:**

Added HTTP mode handling using FastMCP's native HTTP transport:

```python
elif mode == "http":
    # FastMCP Server with HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=FASTMCP_PORT)
```

This leverages FastMCP 2.14's built-in HTTP transport support, which implements the MCP 1.25 specification.

### 3. Documentation Updates

**File:** [`README.md`](README.md)

Multiple sections updated to document HTTP mode:

1. **Introduction**: Added note about FastMCP 2.14 and MCP 1.25 alignment
2. **Operating Modes**: Expanded from 3 to 4 modes, added HTTP as recommended
3. **Quick Start**: Added `uv run python splunk_mcp.py http` example
4. **Local Usage**: Added HTTP mode with `poetry run python splunk_mcp.py http`
5. **Docker Usage**: Added `docker compose run --rm mcp python splunk_mcp.py http`
6. **Environment Variables**: Added `http` to valid `SERVER_MODE` values

## Usage

### Starting in HTTP Mode

**Local Development:**
```bash
# Using UV (recommended)
uv run python splunk_mcp.py http

# Using Poetry
poetry run python splunk_mcp.py http

# Direct Python
python splunk_mcp.py http
```

**Docker:**
```bash
# Run HTTP mode in Docker
docker compose run --rm mcp python splunk_mcp.py http

# Or with port mapping
docker compose run --rm -p 8000:8000 mcp python splunk_mcp.py http
```

### HTTP Endpoint

When running in HTTP mode, the MCP server exposes the standard HTTP transport endpoint:

- **Endpoint**: `/mcp` (standard MCP HTTP path)
- **Protocol**: HTTP POST with JSON-RPC style messages
- **Port**: `8000` (default, configurable via `FASTMCP_PORT`)

### Comparison with SSE Mode

| Feature | HTTP Mode | SSE Mode |
|---------|-----------|----------|
| **Standard** | ✅ Current MCP spec | ⚠️ Legacy (still supported) |
| **Endpoint** | `/mcp` | `/sse` |
| **Protocol** | HTTP request/response | Server-Sent Events |
| **Default** | No (explicit opt-in) | Yes (backward compatibility) |
| **Recommended** | Yes | No (migrate when ready) |

## FastMCP 2.14 HTTP Transport

The HTTP mode implementation uses FastMCP 2.14's built-in HTTP transport, which provides:

- **Standards Compliance**: Full MCP 1.25 HTTP transport specification
- **Automatic Routing**: FastMCP handles endpoint setup and message routing
- **Error Handling**: Proper HTTP status codes and error responses
- **Documentation**: OpenAPI/Swagger docs available at `/docs`

### Key Implementation Details

FastMCP 2.14 abstracts the HTTP transport complexity:

```python
# Simple one-line call to enable HTTP transport
mcp.run(transport="http", host="0.0.0.0", port=FASTMCP_PORT)
```

Behind the scenes, FastMCP:
1. Creates HTTP POST handler at `/mcp`
2. Implements JSON-RPC style message handling
3. Maps MCP protocol messages to HTTP requests/responses
4. Provides proper content negotiation and error handling

## Migration Path

### For New Deployments

New deployments should use HTTP mode:

```bash
# Start with HTTP mode
uv run python splunk_mcp.py http
```

### For Existing Deployments

Existing deployments can continue using SSE (default) and migrate when ready:

```bash
# Current behavior - continues to work
uv run python splunk_mcp.py

# Explicit SSE mode
uv run python splunk_mcp.py sse

# Migrate to HTTP when ready
uv run python splunk_mcp.py http
```

## Testing

### Manual Testing

Test HTTP mode is working correctly:

```bash
# Start server in HTTP mode
uv run python splunk_mcp.py http

# In another terminal, verify endpoint is accessible
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

### Automated Testing

All existing tests continue to pass with HTTP mode available:

```bash
uv run python -m pytest tests/ -v
```

**Results:** ✅ 34/34 tests passing

- Tests primarily focus on tool functionality, not transport layer
- Transport mode selection doesn't affect tool behavior
- HTTP mode uses same tool implementations as SSE and STDIO modes

## Verification Checklist

- [x] HTTP mode recognized as valid command-line argument
- [x] HTTP transport properly initialized via FastMCP
- [x] Server starts successfully in HTTP mode
- [x] MCP endpoint accessible at expected path
- [x] Existing modes (SSE, STDIO) continue to work
- [x] Default behavior (SSE) unchanged for backward compatibility
- [x] Documentation updated across all relevant sections
- [x] Error messages include HTTP in valid mode list

## Configuration

### Environment Variables

No new environment variables required. Existing variables work with HTTP mode:

```env
# Standard Splunk connection settings
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_SCHEME=https
VERIFY_SSL=false

# Server configuration (applies to all modes)
FASTMCP_PORT=8000
DEBUG=false
```

### Docker Configuration

The [`docker-compose.yml`](docker-compose.yml) works with HTTP mode without modifications:

```bash
# HTTP mode via docker-compose
docker compose run --rm mcp python splunk_mcp.py http
```

## Notes

1. **No Breaking Changes**: Default behavior remains SSE mode to avoid disrupting existing deployments

2. **Standards Alignment**: HTTP mode brings the project in line with current MCP 1.25 specification

3. **FastMCP Abstraction**: FastMCP 2.14 handles all HTTP transport complexity internally

4. **Future Default**: Consider making HTTP the default in a future major version (v1.0.0)

5. **Deprecation Timeline**: SSE mode will remain supported indefinitely, but HTTP is recommended for new work

6. **Client Compatibility**: Ensure MCP clients support HTTP transport (most modern clients do as of MCP 1.25)

## Related Documentation

- [UPGRADE_TO_FASTMCP_2.md](UPGRADE_TO_FASTMCP_2.md) - FastMCP 2.14 and MCP 1.25 upgrade details
- [README.md](README.md) - Full usage documentation with HTTP mode examples
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Official MCP protocol docs
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - FastMCP library docs

## References

- **Project**: splunk-mcp v0.3.0
- **FastMCP Version**: 2.14.3
- **MCP Version**: 1.25.0
- **Python**: 3.10+

---

**Summary**: HTTP transport mode is now available as the recommended, standards-compliant option for new deployments, while SSE remains the default for backward compatibility. The implementation leverages FastMCP 2.14's native HTTP support for clean, maintainable code.
