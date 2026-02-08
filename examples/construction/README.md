# Construction Example — SiteSync Project Management

This example demonstrates the IgnitionStack pattern for a **smart construction project management platform**.

## Run It

```bash
ignition run examples/construction/use-case.txt --project sitesync
```

Or in tutorial mode:
```bash
ignition run examples/construction/use-case.txt --project sitesync --tutorial
```

## What Gets Generated

- **Bicep infra** with IoT Hub for field device telemetry
- **BIM integration** scaffolding via IFC open standard
- **Safety & compliance agent** with OSHA citation risk scoring
- **Azure AI Search** for RAG over project documents (submittals, RFIs, drawings)
- **Offline-capable** mobile API patterns (sync queue, conflict resolution)
- **Budget forecasting** engine with cost-to-complete models

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Safety Inspector | Validates OSHA compliance, generates daily safety checklists |
| Document Classifier | Auto-categorizes submittals, RFIs, change orders, and drawings |
| Cost Analyst | Tracks budget burn-down and forecasts cost-to-complete |

## Key Concepts Demonstrated

1. **Offline-first architecture** — field workers on remote sites with intermittent connectivity
2. **T/B/I/C decomposition** — BIM integration and compliance workflows broken into ~45 atomic tasks
3. **Domain-specific agents** — safety inspector automatically added for construction domain
4. **Multi-system integration** — scheduling (P6), accounting (Sage), and BIM (IFC)
