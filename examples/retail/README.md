# Retail Example — ShelfSmart Operations Platform

This example demonstrates the IgnitionStack pattern for an **intelligent retail operations platform**.

## Run It

```bash
ignition run examples/retail/use-case.txt --project shelfsmart
```

Or in tutorial mode:
```bash
ignition run examples/retail/use-case.txt --project shelfsmart --tutorial
```

## What Gets Generated

- **Bicep infra** with Cosmos DB for global inventory state and Redis for caching
- **Demand forecasting agent** with seasonal and promotional adjustments
- **Azure AI Search** for RAG over product catalogs and customer queries
- **Omnichannel fulfillment** routing with cost/speed optimization
- **PCI-DSS compliant** infrastructure configuration
- **Auto-scaling** to handle Black Friday traffic spikes (10x normal)

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Demand Planner | Forecasts demand at SKU × location granularity, adjusts for events |
| Pricing Analyst | Monitors competitive pricing and recommends dynamic adjustments |
| Inventory Optimizer | Balances stock across 250 stores and 8 distribution centers |

## Key Concepts Demonstrated

1. **Omnichannel architecture** — unified inventory across stores, DCs, and e-commerce
2. **T/B/I/C decomposition** — POS integration and fulfillment logic broken into ~45 atomic tasks
3. **Domain-specific agents** — demand planner automatically added for retail domain
4. **Spike handling** — infrastructure designed for 10x traffic bursts during promotions
