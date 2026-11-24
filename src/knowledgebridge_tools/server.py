"""Two read-only MCP tools backed by clearly labeled demonstration data."""

import argparse
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

mcp = FastMCP(
    "KnowledgeBridge",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
    json_response=True,
)

# Replace these fixtures with authenticated inventory/internal API adapters.
# No tool connects directly to SQL or accepts arbitrary URLs or SQL statements.
INVENTORY = {
    ("KB-100", "SEA"): {"description": "USB-C dock", "available": 24, "reserved": 6},
    ("KB-100", "NYC"): {"description": "USB-C dock", "available": 8, "reserved": 2},
    ("KB-200", "SEA"): {"description": "Wireless keyboard", "available": 42, "reserved": 3},
}
ORDERS = {
    "SO-1001": {"status": "processing", "sku": "KB-100", "quantity": 2, "warehouse": "SEA"},
    "SO-1002": {"status": "shipped", "sku": "KB-200", "quantity": 1, "warehouse": "SEA"},
}
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


@mcp.tool(annotations=READ_ONLY)
def get_inventory(
    sku: Annotated[str, Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9-]+$")],
    warehouse: Annotated[str, Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9-]+$")] = "SEA",
) -> dict:
    """Look up DEMO stock for a SKU and warehouse. This is sample data, not live inventory."""
    sku, warehouse = sku.upper(), warehouse.upper()
    stock = INVENTORY.get((sku, warehouse))
    print(f"Looking up inventory tool is called for {sku} at {warehouse}")
    return {
        "source": "demo",
        "found": stock is not None,
        "sku": sku,
        "warehouse": warehouse,
        **(stock or {}),
    }


@mcp.tool(annotations=READ_ONLY)
def get_order_status(
    order_id: Annotated[str, Field(min_length=4, max_length=32, pattern=r"^[Ss][Oo]-[0-9]+$")],
) -> dict:
    """Look up DEMO order status by order ID. This is sample data, not a live business system."""
    order_id = order_id.upper()
    order = ORDERS.get(order_id)
    print(f"Looking up order status tool is called for {order_id}")
    return {
        "source": "demo",
        "found": order is not None,
        "order_id": order_id,
        **(order or {}),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=["streamable-http", "stdio"], default="streamable-http")
    args = parser.parse_args()
    mcp.run(transport=args.transport)
