# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-01-20

### Changed
- Upgraded `mcp` from 1.5.0 to 1.25.0
- Upgraded `fastmcp` from 0.4.0 to 2.14.3 (major version with breaking changes)
- Upgraded `fastapi` from 0.104.0 to 0.128.0
- Upgraded `pydantic` from 2.0.0 to 2.12.5
- Upgraded `pydantic-settings` from 2.0.0 to 2.12.0
- Upgraded `uvicorn` from 0.23.1 to 0.40.0
- Upgraded `aiohttp` from 3.11.14 to 3.13.3
- Upgraded `starlette` from 0.27.0 to 0.50.0
- Upgraded `pytest` from 8.3.0 to 9.0.2
- Upgraded `pytest-asyncio` from 0.21.0 to 1.3.0
- Upgraded `black` from 25.1.0 to 26.1.0
- Updated FastMCP import from `mcp.server.fastmcp` to `fastmcp`
- Changed FastMCP constructor parameter `description` to `instructions`
- Removed deprecated `host` and `port` from FastMCP constructor
- Updated all tests to use FastMCP 2.x API patterns

### Fixed
- Test suite compatibility with FastMCP 2.x (all 34 tests passing)
- Exception handling in tests to match correct error types

### Documentation
- Added [CHANGES/UPGRADE_TO_FASTMCP_2.md](CHANGES/UPGRADE_TO_FASTMCP_2.md) with detailed upgrade guide

## [0.3.0] - Previous Release

### Added
- FastMCP-based MCP server for Splunk Enterprise/Cloud
- Support for STDIO, SSE, and HTTP transport modes
- 12 MCP tools for Splunk operations:
  - `search_splunk` - Execute Splunk searches
  - `list_indexes` - List available indexes
  - `get_index_info` - Get index metadata
  - `get_indexes_and_sourcetypes` - List indexes with sourcetypes
  - `list_saved_searches` - List saved searches
  - `run_saved_search` - Execute saved searches
  - `list_users` - List Splunk users
  - `current_user` - Get current user info
  - `list_apps` - List installed apps
  - `list_kvstore_collections` - List KV store collections
  - `health_check` - Check Splunk connection health
  - `list_tools` - List available MCP tools
  - `ping` - Server health check
- Token-based and username/password authentication
- Comprehensive test suite with mocked Splunk services
- Docker support for development and testing
- OpenAPI documentation at `/openapi.json`

[Unreleased]: https://github.com/yourusername/splunk-mcp/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/yourusername/splunk-mcp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yourusername/splunk-mcp/releases/tag/v0.3.0
