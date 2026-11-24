# Simple Foundry + MCP example

```text
src/
  .env
  requirements.txt
  agent.py
  client.py
  knowledgebridge_tools/
    server.py
```

- `server.py`: defines the inventory and order tools.
- `client.py`: connects to the server through MCP.
- `agent.py`: asks the Foundry model a question and runs the tools it requests.

The flow is: **question -> Foundry model -> MCP client -> tool -> answer**.

Your existing `.env` supplies `PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME`.

From the repository root:

```powershell
src/.venv/Scripts/python.exe -m pip install -r src/requirements.txt
az login
src/.venv/Scripts/python.exe src/agent.py "What is the status of SO-1002?"
```

The agent automatically starts the local MCP server. All tool results are demo data.

To call both tools directly without using a model:

```powershell
src/.venv/Scripts/python.exe src/client.py
```
