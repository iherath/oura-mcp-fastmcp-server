#!/usr/bin/env python3
"""
Simple test client for the datetime MCP server.
"""

import asyncio
import httpx
import json

async def test_datetime_server():
    """Test the datetime server."""
    
    # Server URL
    url = "http://localhost:8000/mcp/"
    
    # Headers that the server expects
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Test 1: Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Test 2: List tools
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    # Test 3: Call current_datetime tool
    call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "current_datetime",
            "arguments": {
                "timezone": "UTC"
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        print("Testing datetime server...")
        
        # Test initialization
        print("\n1. Testing initialization...")
        try:
            response = await client.post(url, json=init_request, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test tools list
        print("\n2. Testing tools list...")
        try:
            response = await client.post(url, json=tools_request, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test tool call
        print("\n3. Testing current_datetime tool...")
        try:
            response = await client.post(url, json=call_request, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_datetime_server()) 