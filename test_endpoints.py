#!/usr/bin/env python3
"""
Test script for Splunk MCP SSE endpoints.
This script tests the SSE endpoint by connecting to it as an MCP client would, 
sending tool invocations, and validating responses.

Usage:
    python test_endpoints.py [tool1] [tool2] ...
    
    If no tools are specified, all tools will be tested.
    
Examples:
    python test_endpoints.py                        # Test all available tools
    python test_endpoints.py health_check list_indexes    # Test only health_check and list_indexes
"""

import json
import sys
import time
import os
import argparse
import asyncio
import uuid
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
import mcp.types as types

# Import configuration
import test_config as config

def log(message: str, level: str = "INFO") -> None:
    """Print log messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def run_tests(tool_names: List[str] = None) -> Dict[str, Any]:
    """Run tool tests"""
    results = {
        "total": 0,
        "success": 0,
        "failure": 0,
        "tests": []
    }
    
    log("Starting Splunk MCP SSE endpoint tests")
    log(f"Using SSE endpoint: {config.SSE_BASE_URL}/sse")
    
    try:
        async with sse_client(url=f"{config.SSE_BASE_URL}/sse") as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                log("Session initialized, starting tests")
                
                # Get list of available tools
                tools_response = await session.list_tools()
                tools = tools_response.tools
                log(f"Available tools: {len(tools)} total")
                
                # If no specific tools requested, test all tools
                if not tool_names:
                    tool_names = [tool.name for tool in tools]
                else:
                    # Validate requested tools exist
                    available_tools = {tool.name for tool in tools}
                    valid_tools = []
                    for name in tool_names:
                        if name not in available_tools:
                            log(f"⚠️ Unknown tool: {name}. Skipping.", "WARNING")
                        else:
                            valid_tools.append(name)
                    tool_names = valid_tools
                
                log(f"Testing tools: {tool_names}")
                
                # Test each tool
                for tool_name in tool_names:
                    try:
                        log(f"Testing tool: {tool_name}")
                        result = await session.call_tool(tool_name, {})
                        log(f"✅ {tool_name} - SUCCESS")
                        results["tests"].append({
                            "tool": tool_name,
                            "success": True,
                            "response": result
                        })
                    except Exception as e:
                        log(f"❌ {tool_name} - FAILED: {str(e)}", "ERROR")
                        results["tests"].append({
                            "tool": tool_name,
                            "success": False,
                            "error": str(e)
                        })
                
                # Calculate summary statistics
                results["total"] = len(results["tests"])
                results["success"] = sum(1 for test in results["tests"] if test["success"])
                results["failure"] = results["total"] - results["success"]
                
    except Exception as e:
        log(f"Error during test execution: {str(e)}", "ERROR")
        if config.VERBOSE_OUTPUT:
            log(f"Stacktrace: {traceback.format_exc()}")
    
    return results

def print_summary(results: Dict[str, Any]) -> None:
    """Print summary of test results"""
    success_rate = (results["success"] / results["total"]) * 100 if results["total"] > 0 else 0
    
    log("\n----- TEST SUMMARY -----")
    log(f"Total tests: {results['total']}")
    log(f"Successful: {results['success']} ({success_rate:.1f}%)")
    log(f"Failed: {results['failure']}")
    
    if results["failure"] > 0:
        log("\nFailed tests:")
        for test in results["tests"]:
            if not test["success"]:
                log(f"  - {test['tool']}: {test['error']}", "ERROR")

async def main_async():
    """Async main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(
        description="Test Splunk MCP tools via SSE endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_endpoints.py                          # Test all tools
  python test_endpoints.py health_check list_indexes      # Test only health_check and list_indexes
  python test_endpoints.py --list                   # List available tools
"""
    )
    parser.add_argument(
        "tools", 
        nargs="*", 
        help="Tools to test (if not specified, all tools will be tested)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available tools and exit"
    )
    
    args = parser.parse_args()
    
    # Run tests
    start_time = time.time()
    results = await run_tests(args.tools)
    end_time = time.time()
    
    # Print summary
    print_summary(results)
    log(f"Tests completed in {end_time - start_time:.2f} seconds")
    
    # Return non-zero code if any test failed
    return 1 if results["failure"] > 0 else 0

def main():
    """Main entry point that runs the async main function"""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        log("Tests interrupted by user", "WARNING")
        return 1

if __name__ == "__main__":
    sys.exit(main())