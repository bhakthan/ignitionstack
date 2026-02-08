# Changelog

All notable changes to IgnitionStack will be documented in this file.

## [0.1.0] — 2026-02-08

### Added
- Initial release of IgnitionStack CLI
- 7-stage pipeline: Input → Parse → Decompose → PRD → Scaffold → Ralph → Production
- **Plug Mode** (`--plug <path>`) — enhance existing projects with AI agents
  - Discovery stage: auto-detects language, framework, DB, auth, deployment, CI/CD, API endpoints
  - Generates adapters, infra-delta (Bicep/Docker), db-delta, cicd-patch, agent config
  - Full tutorial support for Plug Mode stages
- T/B/I/C Decomposition Test for atomic task validation
- Bicep infrastructure templates (Resource Group, App Service, Cosmos DB, Key Vault, AI, Search, Monitoring)
- Docker Compose fallback for local mode (`--local`)
- Microsoft Agent Framework configuration generation
- Ralph loop scripts (bash + PowerShell)
- Tutorial mode with Rich panels and quiz checkpoints (`--tutorial`)
- 7 domain examples: Healthcare, Finance, Education, Oil & Gas, Construction, Telco, Retail
- CI/CD workflow generation (GitHub Actions)
- Multi-format input support: .txt, .md, .pdf, .pptx, .docx, .png, .jpg
- CLI commands: `run`, `verify`, `example`, `version`
- 103 tests with full lint coverage (ruff)
