terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "location" {
  default = "centralus"
}

variable "node_vm_size" {
  default = "Standard_D2als_v6"
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "golden-whisk-rg"
  location = var.location
}

# 2. AKS cluster + node pool with 2 VMs
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "golden-whisk-aks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "goldenwhisk"
  sku_tier            = "Free"

  default_node_pool {
    name            = "system"
    node_count      = 2
    vm_size         = var.node_vm_size
    os_disk_size_gb = 30
  }

  identity {
    type = "SystemAssigned"
  }
}

output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}