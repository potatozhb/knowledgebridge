"""Two read-only MCP tools backed by clearly labeled demonstration data."""

import argparse

from mcp.server.fastmcp import FastMCP

# Direct scripts and package imports resolve sibling modules differently.
if __package__:
    from .exampletools import register_tools as register_tools_exampletools
else:
    from exampletools import register_tools as register_tools_exampletools


mcp = FastMCP(
    "KnowledgeBridge",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
    json_response=True,
)

register_tools_exampletools(mcp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=["streamable-http", "stdio"], default="streamable-http")
    args = parser.parse_args()
    mcp.run(transport=args.transport)
