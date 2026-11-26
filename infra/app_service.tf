variable "app_service_name" {
  description = "Globally unique name for the Python MCP Web App; defaults to a subscription-specific name."
  type        = string
  default     = null
}

locals {
  app_service_name = coalesce(var.app_service_name, "knowledge-bridge-tools-${substr(sha256(var.subscription_id), 0, 4)}")
}

resource "azurerm_service_plan" "tools" {
  name                = "knowledge-bridge-tools-plan"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"
  worker_count        = 1

  tags = {
    project   = "knowledgebridge"
    component = "mcp-tools"
  }
}

resource "azurerm_linux_web_app" "tools" {
  name                                           = local.app_service_name
  resource_group_name                            = data.azurerm_resource_group.main.name
  location                                       = azurerm_service_plan.tools.location
  service_plan_id                                = azurerm_service_plan.tools.id
  https_only                                     = true
  ftp_publish_basic_authentication_enabled       = false
  webdeploy_publish_basic_authentication_enabled = false

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on               = true
    ftps_state              = "Disabled"
    minimum_tls_version     = "1.2"
    scm_minimum_tls_version = "1.2"

    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
  }

  tags = {
    project   = "knowledgebridge"
    component = "mcp-tools"
  }
}

output "app_service_id" {
  description = "Python MCP Web App resource ID."
  value       = azurerm_linux_web_app.tools.id
}

output "app_service_name" {
  description = "Python MCP Web App name for code deployment."
  value       = azurerm_linux_web_app.tools.name
}

output "app_service_url" {
  description = "HTTPS Web App URL. Deploy the MCP server code separately."
  value       = "https://${azurerm_linux_web_app.tools.default_hostname}"
}

output "app_service_identity_principal_id" {
  description = "Managed identity object ID for future database/storage access grants."
  value       = azurerm_linux_web_app.tools.identity[0].principal_id
}
