# Telco Example — NetPulse Network Operations

This example demonstrates the IgnitionStack pattern for a **telecom network operations and customer experience platform**.

## Run It

```bash
ignition run examples/telco/use-case.txt --project netpulse
```

Or in tutorial mode:
```bash
ignition run examples/telco/use-case.txt --project netpulse --tutorial
```

## What Gets Generated

- **Bicep infra** with Event Hubs for high-throughput event streaming
- **Network fault agent** with automated root cause analysis
- **Azure AI Search** for RAG over network documentation and runbooks
- **Real-time dashboards** with sub-second metric refresh
- **5G slice management** provisioning scaffolding
- **Multi-region** active-active deployment for five-nines availability

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Network Diagnostician | Correlates alarms, identifies root cause across RAN/transport/core |
| Capacity Planner | Forecasts demand patterns and recommends resource allocation |
| Customer Experience Agent | Proactively detects subscriber quality issues before escalation |

## Key Concepts Demonstrated

1. **High-throughput event processing** — 500K events/second ingestion pipeline
2. **T/B/I/C decomposition** — multi-vendor integration and 5G slicing broken into ~40 atomic tasks
3. **Domain-specific agents** — network diagnostician automatically added for telco domain
4. **Self-healing automation** — agents that detect, diagnose, and remediate known fault patterns
