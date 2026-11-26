"""Two read-only MCP tools backed by clearly labeled demonstration data."""

import argparse

from fastmcp import FastMCP

# Direct scripts and package imports resolve sibling modules differently.
if __package__:
    from .exampletools import register_tools as register_tools_exampletools
else:
    from exampletools import register_tools as register_tools_exampletools


mcp = FastMCP("KnowledgeBridge")

register_tools_exampletools(mcp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=["http", "streamable-http", "stdio"], default="streamable-http")
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(
            transport="http", host="127.0.0.1", port=8000,
            stateless_http=True, json_response=True, show_banner=False,
        )
