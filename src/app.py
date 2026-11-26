from knowledgebridge_tools.server import mcp

app = mcp.http_app(
    path="/mcp",
    stateless_http=True,
    json_response=True,
)