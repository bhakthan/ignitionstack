# Finance Example — RiskView Portfolio Dashboard

This example demonstrates the IgnitionStack pattern for a **portfolio risk assessment dashboard**.

## Run It

```bash
ignition run examples/finance/use-case.txt --project riskview

# Or locally without Azure
ignition run examples/finance/use-case.txt --project riskview --local
```

## What Gets Generated

- **Bicep infra** optimized for compute-heavy analytics
- **Risk calculation engine** with VaR models
- **Risk monitoring agent** for real-time threshold alerts
- **SOX-compliant audit logging**
- **Client-facing React dashboard** with interactive charts

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Risk Analyst | Validates financial calculations and regulatory compliance |
| Market Monitor | Tracks market data feeds and triggers alerts |
| Report Generator | Creates formatted regulatory and client reports |
