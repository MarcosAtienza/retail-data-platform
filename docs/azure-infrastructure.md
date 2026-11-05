# Azure Infrastructure

## Environment

- Cloud Provider: Microsoft Azure
- Subscription: Azure Free Account
- Region: West Europe
- Resource Group: rg-retail-data-platform-dev

## Naming Convention

| Resource        | Prefix   |
|-----------------|----------|
| Resource Group  | rg       |
| Storage Account | st       |
| Data Factory    | adf      |
| Databricks      | dbw      |

## Storage Account

- Resource group: rg-retail-data-platform-dev
- Region: spaincentral
- Performance: Standard
- Redundancy: Locally redundant storage (LRS)
- Hierarchical namespace: Enabled
- Container: retail-data

## Container Structure

Container: retail-data
Access level: Private

- bronze/olist/: original source data
- silver/olist/: cleaned and transformed data
- gold/retail/: analytics-ready data
