#!/usr/bin/env python3
"""
MCP server for Oura API integration.
This server exposes methods to query the Oura API for sleep, readiness, and resilience data.
Users provide their Oura API token dynamically through Letta's interface.
"""

import os
from datetime import date, datetime
from typing import Any, Optional

import httpx
from fastmcp.server.fastmcp import FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.client import Client


class OuraClient:
    """Client for interacting with the Oura API."""

    BASE_URL = "https://api.ouraring.com/v2/usercollection"

    def __init__(self, access_token: str):
        """
        Initialize the Oura API client.

        Args:
            access_token: Personal access token for Oura API
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.client = httpx.Client(timeout=30.0)

    def get_sleep_data(
        self, start_date: date, end_date: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Get sleep data for a specific date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (optional, defaults to start_date)

        Returns:
            Dictionary containing sleep data
        """
        if end_date is None:
            end_date = start_date

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        url = f"{self.BASE_URL}/sleep"
        response = self.client.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        # Get the raw response
        raw_data = response.json()

        # Transform the data
        transformed_data = []

        for item in raw_data.get("data", []):
            # Format time durations
            awake_time = self._format_duration(item.get("awake_time", 0))
            deep_sleep_duration = self._format_duration(
                item.get("deep_sleep_duration", 0)
            )
            light_sleep_duration = self._format_duration(
                item.get("light_sleep_duration", 0)
            )
            rem_sleep_duration = self._format_duration(
                item.get("rem_sleep_duration", 0)
            )
            total_sleep_duration = self._format_duration(
                item.get("total_sleep_duration", 0)
            )
            time_in_bed = self._format_duration(item.get("time_in_bed", 0))

            # Format bedtime timestamps
            bedtime_start = self._format_time(item.get("bedtime_start", ""))
            bedtime_end = self._format_time(item.get("bedtime_end", ""))

            # Extract readiness data if available
            readiness = item.get("readiness", {})
            readiness_score = readiness.get("score") if readiness else None
            readiness_contributors = (
                readiness.get("contributors", {}) if readiness else {}
            )

            # Create transformed item
            transformed_item = {
                "day": item.get("day"),
                "bedtime_start": bedtime_start,
                "bedtime_end": bedtime_end,
                "awake_time": awake_time,
                "deep_sleep_duration": deep_sleep_duration,
                "light_sleep_duration": light_sleep_duration,
                "rem_sleep_duration": rem_sleep_duration,
                "total_sleep_duration": total_sleep_duration,
                "time_in_bed": time_in_bed,
                "efficiency": item.get("efficiency"),
                "latency": item.get("latency"),
                "restless_periods": item.get("restless_periods"),
                "average_breath": item.get("average_breath"),
                "average_heart_rate": item.get("average_heart_rate"),
                "average_hrv": item.get("average_hrv"),
                "lowest_heart_rate": item.get("lowest_heart_rate"),
            }

            # Add readiness data if available
            if readiness_score is not None:
                transformed_item["readiness_score"] = readiness_score
                transformed_item["readiness_contributors"] = readiness_contributors

            transformed_data.append(transformed_item)

        # Return with the original structure but with transformed data
        return {"data": transformed_data}

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to a human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "7 hours, 30 minutes, 15 seconds")
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        if not parts:
            return "0 seconds"

        return ", ".join(parts)

    def _format_time(self, timestamp: str) -> str:
        """
        Format ISO timestamp to a time-only string.

        Args:
            timestamp: ISO timestamp string

        Returns:
            Formatted time string (e.g., "10:30 PM")
        """
        if not timestamp:
            return ""

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%I:%M %p")
        except (ValueError, TypeError):
            return timestamp

    def get_daily_sleep_data(
        self, start_date: date, end_date: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Get daily sleep data for a specific date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (optional, defaults to start_date)

        Returns:
            Dictionary containing daily sleep data
        """
        if end_date is None:
            end_date = start_date

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        url = f"{self.BASE_URL}/daily_sleep"
        response = self.client.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        # Get the raw response
        raw_data = response.json()

        # Transform the data - just return the data array directly
        transformed_data = []

        for item in raw_data.get("data", []):
            # Create transformed item without the id field
            transformed_item = {k: v for k, v in item.items() if k != "id"}

            # Format any duration fields if present
            if "total_sleep_duration" in transformed_item:
                transformed_item["total_sleep_duration"] = self._format_duration(
                    transformed_item["total_sleep_duration"]
                )

            transformed_data.append(transformed_item)

        # Return with the original structure but with transformed data
        return {"data": transformed_data}

    def get_readiness_data(
        self, start_date: date, end_date: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Get readiness data for a specific date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (optional, defaults to start_date)

        Returns:
            Dictionary containing readiness data
        """
        if end_date is None:
            end_date = start_date

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        url = f"{self.BASE_URL}/daily_readiness"
        response = self.client.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        # Get the raw response
        raw_data = response.json()

        # Transform the data - just return the data array directly
        transformed_data = []

        for item in raw_data.get("data", []):
            # Create transformed item without the id field and timestamp fields
            transformed_item = {
                k: v
                for k, v in item.items()
                if k != "id" and not k.endswith("_timestamp") and k != "timestamp"
            }
            transformed_data.append(transformed_item)

        # Return with the original structure but with transformed data
        return {"data": transformed_data}

    def get_resilience_data(
        self, start_date: date, end_date: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Get resilience data for a specific date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (optional, defaults to start_date)

        Returns:
            Dictionary containing resilience data
        """
        if end_date is None:
            end_date = start_date

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        url = f"{self.BASE_URL}/daily_resilience"
        response = self.client.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            error_msg = f"Error {response.status_code}: {response.text}"
            raise Exception(error_msg)

        # Get the raw response
        raw_data = response.json()

        # Transform the data - just return the data array directly
        transformed_data = []

        for item in raw_data.get("data", []):
            # Create transformed item without the id field
            transformed_item = {k: v for k, v in item.items() if k != "id"}
            transformed_data.append(transformed_item)

        # Return with the original structure but with transformed data
        return {"data": transformed_data}

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


def parse_date(date_str: str) -> date:
    """
    Parse a date string in ISO format (YYYY-MM-DD).

    Args:
        date_str: Date string in ISO format

    Returns:
        Date object
    """
    try:
        return date.fromisoformat(date_str)
    except ValueError as err:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD"
        ) from err


def create_oura_client(access_token: str) -> OuraClient:
    """
    Create an OuraClient instance with the provided access token.
    
    Args:
        access_token: Personal access token for Oura API
        
    Returns:
        OuraClient instance
    """
    if not access_token:
        raise ValueError("Access token is required")
    
    return OuraClient(access_token)


# Create MCP server
mcp = FastMCP("Oura API MCP Server")

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok", "service": "oura-mcp-server", "timestamp": datetime.now().isoformat()}


# Add tools for querying sleep data
@mcp.tool()
def get_sleep_data(access_token: str, start_date: str, end_date: str) -> dict[str, Any]:
    """
    Get sleep data for a specific date range.

    Args:
        access_token: Your Oura Personal Access Token
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)

    Returns:
        Dictionary containing sleep data
    """
    try:
        oura_client = create_oura_client(access_token)
        start = parse_date(start_date)
        end = parse_date(end_date)
        result = oura_client.get_sleep_data(start, end)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_readiness_data(access_token: str, start_date: str, end_date: str) -> dict[str, Any]:
    """
    Get readiness data for a specific date range.

    Args:
        access_token: Your Oura Personal Access Token
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)

    Returns:
        Dictionary containing readiness data
    """
    try:
        oura_client = create_oura_client(access_token)
        start = parse_date(start_date)
        end = parse_date(end_date)
        result = oura_client.get_readiness_data(start, end)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_resilience_data(access_token: str, start_date: str, end_date: str) -> dict[str, Any]:
    """
    Get resilience data for a specific date range.

    Args:
        access_token: Your Oura Personal Access Token
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)

    Returns:
        Dictionary containing resilience data
    """
    try:
        oura_client = create_oura_client(access_token)
        start = parse_date(start_date)
        end = parse_date(end_date)
        result = oura_client.get_resilience_data(start, end)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


# Add tools for querying today's data
@mcp.tool()
def get_today_sleep_data(access_token: str) -> dict[str, Any]:
    """
    Get sleep data for today.

    Args:
        access_token: Your Oura Personal Access Token

    Returns:
        Dictionary containing sleep data for today
    """
    try:
        oura_client = create_oura_client(access_token)
        today = date.today()
        result = oura_client.get_sleep_data(today, today)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_today_readiness_data(access_token: str) -> dict[str, Any]:
    """
    Get readiness data for today.

    Args:
        access_token: Your Oura Personal Access Token

    Returns:
        Dictionary containing readiness data for today
    """
    try:
        oura_client = create_oura_client(access_token)
        today = date.today()
        result = oura_client.get_readiness_data(today, today)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_today_resilience_data(access_token: str) -> dict[str, Any]:
    """
    Get resilience data for today.

    Args:
        access_token: Your Oura Personal Access Token

    Returns:
        Dictionary containing resilience data for today
    """
    try:
        oura_client = create_oura_client(access_token)
        today = date.today()
        result = oura_client.get_resilience_data(today, today)
        oura_client.close()
        return result
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    print("Starting Oura MCP server!")
    print("This server requires users to provide their Oura Personal Access Token dynamically.")
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting server on {host}:{port}")
    
    # Use StreamableHTTP transport for remote deployment
    mcp.run(transport="streamablehttp", host=host, port=port)


if __name__ == "__main__":
    main()

# Example client usage (for reference)
# Basic connection
transport = StreamableHttpTransport(url="https://api.example.com/mcp")
client = Client(transport)

# With custom headers for authentication
transport = StreamableHttpTransport(
    url="https://api.example.com/mcp",
    headers={
        "Authorization": "Bearer your-token-here",
        "X-Custom-Header": "value"
    }
)
client = Client(transport)


