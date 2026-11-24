# KnowledgeBridge Foundry infrastructure

`main.tf` looks up the manually created `knowledge-bridge` resource group and uses its location (currently Canada Central) to add a Microsoft Foundry account (`AIServices`, S0) with a `knowledge-bridge` project. The account and project use system-assigned identities. API-key authentication is disabled; development access uses a public endpoint with Entra authentication. Private networking remains a later infrastructure phase.

The default account/subdomain name includes a stable subscription hash. Override `foundry_account_name` if the name is already taken. Set `resource_group_name` to use a different existing group. Terraform does not create or manage the resource group. A `removed` block with `destroy = false` safely releases the previously tracked group from state on apply while preserving it in Azure; this requires Terraform 1.7 or later. Do not import the group.

From `infra/`:

```powershell
az login
terraform init
terraform fmt -check
terraform validate
terraform plan -out="foundry.tfplan"
# Review the plan: only Foundry resources may be created; the group is read and safely forgotten if previously tracked.
terraform apply foundry.tfplan
terraform output -raw foundry_project_endpoint
```

Terraform outputs the account ID, project ID, and project endpoint. Keep state and saved plans private. Previously saved plans predate the switch to an existing-group lookup. Generate a fresh plan before applying; do not apply an old plan.

No model deployment or MCP hosting is included. Before creating the agent, deploy a compatible model in this Foundry account and grant the setup identity Foundry User (previously Azure AI User) access to the project. Configuring an authenticated MCP connection also requires the relevant project connection permissions. Resource-management Contributor access alone does not imply agent data-plane access.

## Prepare the agent with the existing MCP tools

The [Python MCP server](../src/knowledgebridge_tools/README.md) exposes `get_inventory` and `get_order_status` with demonstration data. The setup command allowlists those exact tools, requires tool-call approval, and instructs the agent to label demo results. It does not host or modify the existing server.

Run from the repository root:

```powershell
src/knowledgebridge_tools/.venv/Scripts/python.exe -m pip install -r src/knowledgebridge_tools/requirements-foundry.txt
$projectEndpoint = terraform -chdir=infra output -raw foundry_project_endpoint
src/knowledgebridge_tools/.venv/Scripts/python.exe src/knowledgebridge_tools/setup_foundry_agent.py --project-endpoint $projectEndpoint --model-deployment '<existing-model-deployment>' --mcp-url 'https://<your-mcp-host>/mcp' --dry-run
```

Replace both placeholders, then remove `--dry-run` to create a persistent agent version. Each execution creates a new version under `knowledge-bridge`; it does not delete existing versions. Add `--connection-id '<project-connection-name-or-id>'` for a Foundry project connection holding MCP authentication; do not pass secrets in URLs or source code.

Foundry must be able to reach the HTTPS MCP URL. `127.0.0.1:8000/mcp` works only for the local smoke test and is rejected by the setup command. Configure hosting, authentication, and the chosen network path before connecting real data. A Foundry project alone does not deploy the server or register an agent.

Use the Foundry playground or a Responses API client to invoke the created agent. Clients must handle `mcp_approval_request` and submit approval responses. Example questions: "How many KB-100 are available in SEA?" and "What is the status of SO-1002?" Both answers must identify their source as demo data.

References: [Foundry Terraform resources](https://learn.microsoft.com/en-us/azure/foundry/how-to/create-resource-terraform), [Foundry remote MCP tools](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol?view=foundry).

## Verification (2026-11-24)

Terraform formatting and validation passed with AzureRM 4.81.0. The current authenticated plan saved as `foundry.tfplan` reads the existing group and reports 2 to add, 0 to change, 0 to destroy; only the Foundry account and project are created. No apply was run. The agent setup dry-run and syntax check passed. The existing MCP smoke test passed discovery, both tool calls, missing records, and malformed inputs. Live agent creation and Foundry-to-MCP calls await a model deployment and hosted HTTPS MCP URL.

## Recover a soft-deleted Foundry account

Azure retains soft-deleted accounts and reserves their names. If apply returns `FlagMustBeSetForRestore`, recover the existing account and import it into Terraform rather than purging it. For the default KnowledgeBridge account, run from the repository root:

```powershell
az cognitiveservices account recover --name knowledge-bridge-foundry-46535bec --resource-group knowledge-bridge --location canadacentral --subscription 2f482561-182f-4bd5-840b-1dc7d21f0811
terraform -chdir=infra import azurerm_cognitive_account.foundry /subscriptions/2f482561-182f-4bd5-840b-1dc7d21f0811/resourceGroups/knowledge-bridge/providers/Microsoft.CognitiveServices/accounts/knowledge-bridge-foundry-46535bec
terraform -chdir=infra plan -out="foundry.tfplan"
terraform -chdir=infra apply foundry.tfplan
```

Import only if the account is not already in state (`terraform -chdir=infra state list`). Use the actual account name and region if overridden. After recovery, generate a fresh plan; previously saved create plans are obsolete. The resource group remains externally managed.

References: [Azure CLI account recovery](https://learn.microsoft.com/cli/azure/cognitiveservices/account#az-cognitiveservices-account-recover), [Terraform account import](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_account).

## Agent builder access

Set `foundry_user_object_ids` to the Entra object IDs of users who need to build or use agents. Terraform assigns Foundry User at this project only. The local ignored `terraform.tfvars` includes the current developer; use `terraform.tfvars.example` as a template for other environments. Use the user object ID from the subscription tenant, especially for guest accounts.

```powershell
az ad signed-in-user show --query id -o tsv
terraform -chdir=infra plan -out="foundry-access.tfplan"
terraform -chdir=infra apply foundry-access.tfplan
```

Owner or Contributor resource-management access does not replace Foundry agent data-plane access. Applying role assignments requires role-assignment permissions. After assignment, allow Azure RBAC propagation and refresh the Foundry portal; sign out and in again if the existing session remains stale.

[Foundry RBAC documentation](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry).
