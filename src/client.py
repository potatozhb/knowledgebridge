"""Connect to MCP locally (stdio) or through an optional HTTP endpoint."""

import argparse
from contextlib import asynccontextmanager
import asyncio
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

from dotenv import load_dotenv
import httpx2 as httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

load_dotenv(Path(__file__).with_name(".env"), encoding="utf-8-sig")
ALLOWED_TOOLS = {"get_inventory", "get_order_status"}


@asynccontextmanager
async def connect(url: str | None = None):
    """Yield an initialized session, cleaning up its transport on exit."""
    url = url or os.environ.get("MCP_SERVER_URL")
    print(f"Connecting to MCP at {url or 'local stdio server'}...")
    if url:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("MCP_SERVER_URL must be an HTTP(S) URL without embedded credentials")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Remote MCP endpoints require HTTPS")
        token = os.environ.get("MCP_AUTH_TOKEN")
        print(f"Using authentication token: {token is not None}")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(headers=headers, timeout=90) as http:
            async with streamable_http_client(url, http_client=http) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
    else:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).parent / "knowledgebridge_tools" / "server.py"), "--transport", "stdio"],
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def call_tool(session: ClientSession, name: str, arguments: dict) -> str:
    """Call only the two approved tools and return a JSON result for the model."""
    if name not in ALLOWED_TOOLS:
        return json.dumps({"error": "Tool is not allowed"})
    if not isinstance(arguments, dict):
        return json.dumps({"error": "Tool arguments must be a JSON object"})
    result = await session.call_tool(name, arguments=arguments)
    if result.is_error:
        return json.dumps({"error": "Tool rejected the request; check its arguments"})
    if result.structured_content is not None:
        return json.dumps(result.structured_content)
    return "\n".join(block.text for block in result.content if block.type == "text")


async def main(url: str | None = None):
    async with connect(url) as session:
        tools = (await session.list_tools()).tools
        print("Available tools:", ", ".join(tool.name for tool in tools))
        for name, arguments in [
            ("get_inventory", {"sku": "KB-100", "warehouse": "SEA"}),
            ("get_order_status", {"order_id": "SO-1002"}),
        ]:
            print(f"\n{name}:")
            print(await call_tool(session, name, arguments))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Optional HTTP MCP endpoint; default: local server over stdio")
    asyncio.run(main(parser.parse_args().url))
