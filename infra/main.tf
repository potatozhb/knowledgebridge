terraform {
  required_version = ">= 1.7, < 2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.81, < 5.0"
    }
    
    azapi = {
      source ="Azure/azapi"
      version = ">= 2.9, < 3.0"
    }
  }
}

provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}

provider "azapi" {
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  description = "Subscription containing the KnowledgeBridge resource group."
  type        = string
  default     = "2f482561-182f-4bd5-840b-1dc7d21f0811"
}

variable "resource_group_name" {
  description = "Name of the manually created resource group in which to create Foundry."
  type        = string
  default     = "knowledge-bridge"
}

# Stop managing the previously tracked group without deleting it in Azure.
removed {
  from = azurerm_resource_group.main

  lifecycle {
    destroy = false
  }
}

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}
output "resource_group_id" {
  description = "KnowledgeBridge Azure resource group ID."
  value       = data.azurerm_resource_group.main.id
}

variable "foundry_account_name" {
  description = "Globally unique account/subdomain name; defaults to a subscription-specific name."
  type        = string
  default     = null
}

variable "foundry_project_name" {
  description = "Project within the KnowledgeBridge Foundry account."
  type        = string
  default     = "knowledge-bridge"
}

locals {
  foundry_account_name = coalesce(var.foundry_account_name, "knowledge-bridge-foundry-${substr(sha256(var.subscription_id), 0, 8)}")
}

resource "azurerm_cognitive_account" "foundry" {
  name                       = local.foundry_account_name
  resource_group_name        = data.azurerm_resource_group.main.name
  location                   = data.azurerm_resource_group.main.location
  kind                       = "AIServices"
  sku_name                   = "S0"
  custom_subdomain_name      = local.foundry_account_name
  project_management_enabled = true
  local_auth_enabled         = false

  # Development access uses Entra authentication; private networking is a later phase.
  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_account_project" "main" {
  name                 = var.foundry_project_name
  display_name         = "KnowledgeBridge"
  description          = "KnowledgeBridge assistant using the get_inventory and get_order_status MCP tools."
  cognitive_account_id = azurerm_cognitive_account.foundry.id
  location             = azurerm_cognitive_account.foundry.location

  identity {
    type = "SystemAssigned"
  }
}

output "foundry_account_id" {
  description = "Microsoft Foundry account resource ID."
  value       = azurerm_cognitive_account.foundry.id
}

output "foundry_project_id" {
  description = "Microsoft Foundry project resource ID."
  value       = azurerm_cognitive_account_project.main.id
}

output "foundry_project_endpoint" {
  description = "Project endpoint for the agent setup command."
  value       = "https://${azurerm_cognitive_account.foundry.custom_subdomain_name}.services.ai.azure.com/api/projects/${azurerm_cognitive_account_project.main.name}"
}
variable "foundry_user_object_ids" {
  description = "Entra object IDs of users who can build and use agents in this project."
  type        = set(string)
  default     = []
}

resource "azurerm_role_assignment" "foundry_user" {
  for_each = var.foundry_user_object_ids

  scope              = azurerm_cognitive_account_project.main.id
  role_definition_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
  principal_id       = each.value
  principal_type     = "User"
}


variable "agent_model_deployment" {
  description = "Name of an existing Foundry model deployment."
  type        = string
}

variable "agent_mcp_url" {
  description = "URL of the MCP server to be used by the Foundry agent."
  type        = string
}

resource "azapi_data_plane_resource" "knowledgebridge_agent" {
  type      = "Microsoft.Foundry/agents@v1"
  parent_id = "${azurerm_cognitive_account.foundry.custom_subdomain_name}.services.ai.azure.com/api/projects/${azurerm_cognitive_account_project.main.name}"
  name      = "knowledgebridge-agent"

  body = {
    name = "knowledgebridge-agent"
    definition = {
      kind = "prompt"
      model = var.agent_model_deployment
      instructions = <<-TEXT
        You are a helpful assistant that can answer questions about the KnowledgeBridge inventory and order status.
        You have access to two tools: get_inventory and get_order_status.
        Use these tools to answer user questions accurately and concisely.
      TEXT
      tools = [
        {
          type = "mcp"
          server_label = "KnowledgeBridge_MCP_Tools"
          server_url = var.agent_mcp_url
          allowed_tools = ["get_inventory", "get_order_status"]
          require_approval = {
            never ={
              tool_names = [ "get_order_status"]
            }
            always = {
              tool_names = ["get_inventory"]
            }
          }
        }
      ]
    }
  }

  depends_on = [
    azurerm_role_assignment.foundry_user
  ]

}

output "agent_name" {
  description = "Name of the Foundry agent resource."
  value       = azapi_data_plane_resource.knowledgebridge_agent.name
}