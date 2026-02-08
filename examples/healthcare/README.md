# Healthcare Example — Meridian Health Network

This example demonstrates the IgnitionStack pattern for a **healthcare patient intake portal**.

## Run It

```bash
ignition run examples/healthcare/use-case.txt --project meridian-portal
```

Or in tutorial mode:
```bash
ignition run examples/healthcare/use-case.txt --project meridian-portal --tutorial
```

## What Gets Generated

- **Bicep infra** with HIPAA BAA compliance tags
- **FHIR R4 integration** scaffolding (patient, observation resources)
- **Clinical triage agent** using Microsoft Agent Framework
- **Azure AI Search** for lab results RAG
- **Audit logging** for SOC 2 compliance
- **Azure AD B2C** authentication configuration

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Triage Agent | Classifies symptom urgency using clinical protocols |
| Compliance Checker | Validates HIPAA compliance in all data operations |
| Lab Interpreter | Provides natural language answers about lab results |

## Key Concepts Demonstrated

1. **Multi-format input** — the use case is a plain text file, but could be a PPTX or screenshot
2. **T/B/I/C decomposition** — the complex FHIR integration gets broken into ~40 atomic tasks
3. **Domain-specific agents** — compliance checker automatically added for healthcare domain
4. **Infrastructure as Code** — complete Bicep deployment for Azure with proper security
