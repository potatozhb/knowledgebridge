
"""Demo tools registered on the MCP instance supplied by server.py."""

import logging
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field


logger = logging.getLogger(__name__)

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
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)


def register_tools(mcp: FastMCP) -> None:
    """Attach these tools to the server's existing MCP instance."""
    logger.info("Registering demo tools on MCP instance %s", mcp.name)
    
    @mcp.tool(annotations=READ_ONLY)
    def get_inventory(
        sku: Annotated[str, Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9-]+$")],
        warehouse: Annotated[str, Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9-]+$")] = "SEA",
    ) -> dict:
        """Look up DEMO stock for a SKU and warehouse. This is sample data, not live inventory."""
        sku, warehouse = sku.upper(), warehouse.upper()
        stock = INVENTORY.get((sku, warehouse))
        logger.info("Looking up inventory for %s at %s", sku, warehouse)
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
        logger.info("Looking up order status for %s", order_id)
        return {
            "source": "demo",
            "found": order is not None,
            "order_id": order_id,
            **(order or {}),
        }
