# Simple Foundry + MCP example

```text
src/
  .env
  requirements.txt
  localagent.py
  client.py
  knowledgebridge_tools/
    server.py
    exampletools.py
```

- `server.py`: creates the MCP server and starts it.
- `exampletools.py`: registers the inventory and order tools using `register_tools(mcp)`.
- `client.py`: connects to the server through MCP.
- `localagent.py`: asks the Foundry model a question and runs the tools it requests.

The flow is: **question -> Foundry model -> MCP client -> tool -> answer**.

Your existing `.env` supplies `PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME`.

From the repository root:

```powershell
src/.venv/Scripts/python.exe -m pip install -r src/requirements.txt
az login
src/.venv/Scripts/python.exe src/localagent.py "What is the status of SO-1002?"
```

The agent automatically starts the local MCP server. All tool results are demo data.

To call both tools directly without using a model:

```powershell
src/.venv/Scripts/python.exe src/client.py
```

To add more tools, define them inside `register_tools(mcp)` in `knowledgebridge_tools/exampletools.py` using `@mcp.tool()`. For another tool file, give it its own registration function and call that function with the same `mcp` object in `server.py`.

## If the MCP connection closes during startup

This example requires MCP SDK `>=1.30,<2`. MCP 2.x removed the `mcp.server.fastmcp` API. If a traceback points to `AppData/Roaming/Python/...`, you are using user-wide packages instead of this project environment.

From the repository root, run:

```powershell
src/.venv/Scripts/python.exe src/client.py
src/.venv/Scripts/python.exe src/localagent.py "Check KB-100 stock"
```

In VS Code, use **Python: Select Interpreter** and select `src/.venv/Scripts/python.exe`. Use the named **Foundry: agent with MCP tools** debug configuration. It explicitly selects that interpreter. No global package changes are required.
