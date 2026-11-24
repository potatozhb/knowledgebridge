# KnowledgeBridge Python MCP example

Runnable local server exposing exactly two read-only tools:

| Tool | Input example | Example result |
| --- | --- | --- |
| `get_inventory` | `{"sku":"KB-100","warehouse":"SEA"}` | Demo stock: 24 available, 6 reserved. |
| `get_order_status` | `{"order_id":"SO-1002"}` | Demo order: shipped. |

Both tools use in-memory fixtures and label results `source: demo`. Unknown records return `found: false`; malformed identifiers are rejected. There are no live API calls, SQL access, write tools, or PDF lifecycle operations in this example.

## Run locally

Python 3.10+ is required. From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

The MCP endpoint is `http://127.0.0.1:8000/mcp`, using Streamable HTTP. It is an MCP endpoint, not a plain REST route per tool. In a second terminal, discover tools and call both over HTTP:

```powershell
.\.venv\Scripts\python.exe smoke_test.py --url http://127.0.0.1:8000/mcp
```

Or test through stdio without starting a server separately:

```powershell
.\.venv\Scripts\python.exe smoke_test.py
```

The smoke client checks tool discovery, read-only annotations, known/missing records, and rejection of malformed identifiers. The dependency is explicitly bounded to the official MCP SDK's supported v1 API used by this example. Review the [official v1 SDK documentation](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x) before upgrading to v2.

Validated on 2026-11-23 with Python 3.13.5 and MCP SDK 1.30.0: the smoke client passed over both stdio and Streamable HTTP; `pip check` reported no broken requirements. The temporary HTTP test server was stopped after verification.

## VS Code debugging and import errors

The example uses MCP SDK `>=1.30,<2` and the current `streamable_http_client` import. The old `streamablehttp_client` spelling is deprecated and can be absent in newer SDKs. A traceback under `AppData/Roaming/Python/...` means VS Code used a user-wide package rather than this project's virtual environment.

From the repository root, refresh the project environment and run:

```powershell
src/knowledgebridge_tools/.venv/Scripts/python.exe -m pip install -r src/knowledgebridge_tools/requirements.txt
src/knowledgebridge_tools/.venv/Scripts/python.exe src/knowledgebridge_tools/smoke_test.py
```

In VS Code, choose **Python: Select Interpreter**, then select `src/knowledgebridge_tools/.venv/Scripts/python.exe`. For F5, select **MCP: smoke test (stdio)** in Run and Debug. The provided launch configurations explicitly use this interpreter even if another interpreter was previously selected. Use **MCP: server (HTTP)** followed by **MCP: smoke test (HTTP, server must be running)** for HTTP debugging.

## Connect real business systems

- Replace `INVENTORY` with an adapter calling the inventory read service using managed identity and a fixed configured endpoint.
- Replace `ORDERS` with an adapter calling the approved internal order API. Enforce order-level authorization there; a user-supplied order ID is not permission to read it.
- Add validated token authentication, caller roles, trusted user context, dependency timeouts, bounded responses, and redacted request logging.

The server binds only to loopback and has no authentication. Before exposing it remotely or connecting Microsoft Foundry, deploy it behind HTTPS with supported MCP/Entra authentication and the selected private-network setup. Read-only annotations describe behavior; they are not an authorization mechanism. Resource-group creation does not host this server or register it with an agent.

## Foundry agent setup

See [Foundry setup instructions](../../infra/README.md) for the Terraform project and setup_foundry_agent.py command. It accepts a remote HTTPS MCP URL, allows only get_inventory and get_order_status, and supports --dry-run. Install requirements-foundry.txt for the Azure SDK dependencies. The existing local MCP server and its two tool implementations are reused unchanged.
