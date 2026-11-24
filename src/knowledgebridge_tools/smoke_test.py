"""Discover and call both tools through MCP, rather than importing their functions."""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client


def payload(result) -> dict:
    if result.isError:
        raise AssertionError(f"Tool failed: {result.content}")
    return json.loads(next(block.text for block in result.content if block.type == "text"))


async def check(session: ClientSession) -> None:
    await session.initialize()
    tools = (await session.list_tools()).tools
    assert {tool.name for tool in tools} == {"get_inventory", "get_order_status"}
    assert all(tool.annotations and tool.annotations.readOnlyHint for tool in tools)

    inventory = payload(await session.call_tool("get_inventory", {"sku": "kb-100", "warehouse": "sea"}))
    assert inventory["source"] == "demo" and inventory["available"] == 24
    order = payload(await session.call_tool("get_order_status", {"order_id": "so-1002"}))
    assert order["source"] == "demo" and order["status"] == "shipped"
    missing = payload(await session.call_tool("get_inventory", {"sku": "UNKNOWN"}))
    assert missing["found"] is False
    missing_order = payload(await session.call_tool("get_order_status", {"order_id": "SO-9999"}))
    assert missing_order["found"] is False
    invalid = await session.call_tool("get_order_status", {"order_id": "not-an-order"})
    assert invalid.isError, "Malformed order IDs must be rejected"
    invalid_sku = await session.call_tool("get_inventory", {"sku": "../secret"})
    assert invalid_sku.isError, "Malformed SKU must be rejected"
    print(json.dumps({"get_inventory": inventory, "get_order_status": order}, indent=2))
    print("PASS: discovery, read-only annotations, both tools, missing records, and invalid inputs")


async def main(url: str | None) -> None:
    if url:
        async with streamable_http_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await check(session)
    else:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).with_name("server.py")), "--transport", "stdio"],
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await check(session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Test an already running Streamable HTTP server instead of stdio")
    asyncio.run(main(parser.parse_args().url))
