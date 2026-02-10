# IgnitionStack Infographic — Image Generation Prompt

> Use this prompt with an AI image generator (Midjourney, DALL-E 3, Ideogram, etc.) to produce a detailed architectural infographic explaining IgnitionStack.

---

## Master Prompt

```
Create a high-resolution (8192 × 4096 px, 8K) landscape infographic poster titled "IgnitionStack — From Use Case to Production Azure Workload" in a modern Flat UI 2.0 design style on a clean light (#F8F9FA) background. Use a coherent color palette: Azure Blue (#0078D4) for infrastructure, Teal (#00B7C3) for agents, Amber (#FFB900) for the Ralph loop, Coral (#F25022) for key callouts, Slate (#2B2B2B) for text, and subtle light-gray (#E8EAED) for section dividers. All text must be crisp, sans-serif (Segoe UI or Inter family), and legible at 100% zoom on a 4K monitor. No gradients on backgrounds — flat color fills only. Subtle drop shadows (2px, 8% opacity) on cards for depth. Rounded corners (12px radius) on all containers.

The infographic has SEVEN horizontal zones stacked top-to-bottom, each clearly labeled with a section header bar. Use generous whitespace between zones.

---

ZONE 1 — HERO BANNER (top 10% of canvas)

Centered headline in 120pt bold: "Agents Are the New Apps"
Subheadline in 48pt regular: "Where the last decade shipped containers, the next decade ships agents."
Below that, a single-line pipeline ribbon showing 10 colored pill-shaped badges connected by thin arrows:
  📄 Input → 🔍 Parse → 🧩 Decompose → 📋 PRD → 📊 Plan Gate → 🏗️ Scaffold → 🔄 Ralph ×20 → 🔍 Review Gate → ✅ Verify → 🧠 Reflect
Each pill uses the stage's accent color. The three compound-only stages (Plan Gate, Review Gate, Reflect) use Magenta (#B4009E) fill. The arrow from "Verify" to "Reflect" and a dashed feedback arrow from "Reflect" back to "Plan Gate" should pulse visually (thicker, glowing Magenta) to show the compound learning loop.

In the top-right corner, show the IgnitionStack logo mark: a stylized ignition spark icon in Azure Blue with "IgnitionStack" wordmark.

Below the ribbon, a concise tagline in 32pt italic:
"One CLI command. One use-case document. One production Azure workload."
And a secondary tagline in 24pt:
"Add --compound for recursive self-improvement: each sprint makes the next one easier."

---

ZONE 2 — THE PARADIGM SHIFT (next 12%)

Title bar: "The Paradigm Shift: Apps → Agents"

Split this zone into two side-by-side comparison panels:

LEFT PANEL — "Traditional App Scaffolding" (grayed out, desaturated)
Show a short vertical flow:
  Scaffold CLI → "Hello World" boilerplate → Manual wiring (weeks) → Maybe production
A red ✗ mark at the end. Caption: "Stops at Hello World. You do the rest."

RIGHT PANEL — "IgnitionStack" (full color, vibrant)
Show the same vertical flow but extended:
  Use-Case Document → IgnitionStack CLI → Complete Azure Workload (infra + agents + app + CI/CD) → Ralph Loop ×20 → Production ✓
A green ✓ at the end. Caption: "Seed to production. Agents are first-class."

Between the panels, a large "VS" divider circle.

Below both panels, a callout box with rounded corners:
"Agents are not an afterthought bolted on. IgnitionStack scaffolds agents as deployment-ready artifacts from day one — alongside infrastructure, database, and CI/CD."

---

ZONE 3 — THE 10-STAGE PIPELINE (next 22% — this is the largest zone)

Title bar: "The 10-Stage Pipeline — Use Case → Production (Compound Mode)"

Render this as a SWIM LANE DIAGRAM flowing left-to-right with 3 horizontal swim lanes:

SWIM LANE A (top): "Human / Input"
SWIM LANE B (middle): "IgnitionStack CLI (Python)"  
SWIM LANE C (bottom): "Generated Output"

Stage nodes are large rounded rectangles with icons, numbers, and brief descriptions:

LANE A:
  [1] 📄 INPUT — "Screenshot, PDF, PPTX, DOCX, or .txt describing a use case"
  Arrow crosses down into Lane B.

LANE B (the engine — all processing happens here):
  [2] 🔍 PARSE — "Extracts structured requirements via Vision API or text parsing"
    Outputs: {summary, features, constraints, domain, actors}
  [3] 🧩 DECOMPOSE — "Breaks requirements into 30–50 atomic tasks"
    Callout bubble: "Each task must pass T/B/I/C: Testable, Bounded, Independent, Committable"
  [4] 📋 PRD GENERATOR — "Produces PRD.json (task backlog) + progress.txt (agent memory)"
  A diamond decision node: "Mode?" with two branches:
    → "scaffold" leads to Compound? decision diamond
    → "plug" leads to [0] 🔎 DISCOVERY → [5b] 🔌 PLUG SCAFFOLD
  Compound? diamond (Magenta border):
    → "yes" leads to [5] 📊 PLANNING GATE — "LLM validates plan quality across 5 dimensions (completeness, clarity, testability, scope, dependencies). Enriches weak tasks." (Magenta #B4009E fill)
    → "no" leads directly to [6] 🏗️ SCAFFOLD
  [5] feeds into [6] 🏗️ SCAFFOLD (both branches converge)
  [6] 🏗️ SCAFFOLD — "Generates Bicep/Docker, agents, DB, app, CI/CD"
  [7] 🔄 RALPH ×20 — "20 iterations: read PRD → pick task → implement → test → git commit"
    Show a circular arrow looping back on itself with "×20" label.
  Compound? diamond (Magenta border):
    → "yes" leads to [8] 🔍 REVIEW GATE — "Catches technical debt, coupling issues, alignment gaps. Tracks findings in debt ledger." (Magenta fill)
    → "no" leads directly to [9] ✅ VERIFY
  [8] feeds into [9] ✅ VERIFY — diamond shape: pass → next, fail → back to Ralph
  Compound? diamond (Magenta border):
    → "yes" leads to [10] 🧠 REFLECTION — "Sprint retrospective: extracts patterns, flags anti-patterns, generates feed-forward context." (Magenta fill)
    A DASHED FEEDBACK ARROW loops from [10] back to [5] labeled "feed-forward: learnings injected into next sprint's planning"
    → "no" leads to 🚀 Production
  [10] feeds into 🚀 Production

LANE C (outputs at each stage):
  Below Stage 4: PRD.json icon + progress.txt icon
  Below Stage 5 (compound): planning-report.json icon
  Below Stage 6: exploded folder tree (detailed in Zone 4)
  Below Stage 5b: ignition-plug/ folder icon
  Below Stage 7: git commit icons (20 small circles in a row)
  Below Stage 8 (compound): review-report.json icons, debt-ledger.json icon
  Below Stage 9: 🚀 "Production Azure Workload" badge
  Below Stage 10 (compound): retrospective.json icon, feed-forward.md icon, compound-metrics.md icon

---

ZONE 4 — EXPLODED VIEW: THE GENERATED TEMPLATE (next 25% — second largest zone)

Title bar: "Exploded View — What IgnitionStack Generates (the Ralph Loop Template)"

This is the CORE visualization. Render it as an EXPLODED ISOMETRIC DIRECTORY TREE with each folder as a 3D-ish flat card floating in space, connected by thin lines to its parent. Use color coding per category.

ROOT: ignition-output/ (dark slate card)

BRANCH 1 — INFRASTRUCTURE (Azure Blue #0078D4 cards):
  infra/
  ├── main.bicep ← "Subscription-scoped orchestrator — deploys all modules"
  └── modules/
      ├── rg.bicep ← "Resource Group"
      ├── app.bicep ← "App Service + Plan"
      ├── db.bicep ← "Cosmos DB or PostgreSQL"
      ├── kv.bicep ← "Key Vault (secrets)"
      ├── ai.bicep ← "Microsoft Foundry (AI workspace)"
      ├── search.bicep ← "Azure AI Search (agentic RAG)"
      └── mon.bicep ← "Application Insights + Log Analytics"
  
  Show a MINI AZURE ARCHITECTURE DIAGRAM next to this branch:
  Resource Group box containing icons for: App Service, Cosmos DB, Key Vault, AI Foundry, AI Search, App Insights — all connected with thin lines.

BRANCH 2 — AGENTS (Teal #00B7C3 cards):
  agents/
  └── agent-config.json ← "Microsoft Agent Framework configuration"
  
  Callout: Show 4 small agent persona icons: 🤖 Planner, 🧑‍💻 Coder, 🔍 Reviewer, 🏥 Domain Specialist
  Caption: "Domain-aware agents. Healthcare gets compliance-checker. Finance gets risk-analyst."

BRANCH 3 — DATABASE (Green #107C10 cards):
  db/
  ├── migrations/
  │   └── 001_initial.sql ← "Schema + indexes"
  └── seed.sql ← "Domain-specific sample data"

BRANCH 4 — APPLICATION (Purple #5C2D91 cards):
  app/
  ├── backend/
  │   ├── main.py ← "FastAPI with /health, domain endpoints"
  │   ├── requirements.txt
  │   └── Dockerfile
  └── frontend/
      ├── package.json ← "React + Vite + TypeScript"
      └── src/

BRANCH 5 — CI/CD (Orange #FF8C00 cards):
  .github/workflows/
  └── ci-cd.yml ← "Build → Test → Bicep Deploy → App Deploy"

BRANCH 6 — RALPH LOOP (Amber #FFB900 cards, HIGHLIGHTED with glow):
  ralph.sh ← "The 30-line bash loop — the engine"
  ralph.ps1 ← "PowerShell equivalent"
  PRD.json ← "Task backlog: 30-50 atomic tasks"
  progress.txt ← "Agent's external memory (append-only)"

BRANCH 7 — CLAUDE SKILLS (Coral #F25022 cards):
  skills/
  ├── {project}-ops/SKILL.md ← "Deploy, run, debug, troubleshoot"
  ├── {project}-agent/SKILL.md ← "Interact with, test, customize agents"
  ├── {project}-data/SKILL.md ← "Migrations, seed data, RAG indexing"
  └── {project}-integrate/SKILL.md ← "Plug Mode: mount middleware, wire RAG"
  Caption: "Follows Anthropic Agent Skills spec — YAML frontmatter + step-by-step instructions"

BRANCH 8 — COMPOUND ENGINEERING (Magenta #B4009E cards, DASHED BORDERS):
  .ignition/ ← "Persistent state across sprints"
  ├── compound-state.json ← "Sprint history, patterns, debt ledger, trend data"
  ├── feed-forward.md ← "Context injected into next sprint's planning"
  ├── reviews/ ← "Per-iteration review reports"
  │   └── review-iter-{N}.json
  └── retrospectives/ ← "Per-sprint retrospective analysis"
      └── retrospective-sprint-{N}.json
  planning-report.json ← "5-dimension quality scores per task"
  compound-metrics.md ← "Self-improvement dashboard"
  Caption: "Knowledge compounds: each sprint feeds learnings into the next. 80% plan/review, 20% execution."

At the center of the exploded view, a large arrow labeled "Ralph reads PRD.json → implements next task → appends to progress.txt → git commit → repeat ×20"
Below the center arrow, a second Magenta dashed arrow labeled "Compound Mode: Plan gate validates → Review gate catches debt → Reflection extracts patterns → Feed-forward accelerates next sprint"

---

ZONE 5 — THE RALPH LOOP DEEP DIVE (next 15%)

Title bar: "The Ralph Loop — 20 Iterations from Template to Production"

Render as a CIRCULAR FLOWCHART (clock-like) showing one iteration:

12 o'clock: "📋 Read PRD.json + progress.txt"
3 o'clock: "🎯 Pick next pending task (dependencies satisfied)"
6 o'clock: "🧑‍💻 Implement (write code + tests)"
9 o'clock: "✅ Mark done → append progress.txt → git commit"
Center: "×20" in large bold text with a circular arrow

Around the circle, show 20 small numbered dots (1–20) arranged in a spiral, with dots 1–12 filled (complete) and 13–20 outlined (pending). This visualizes progress through iterations.

To the right of the circle, show three key properties as icon+text badges:
  🧹 "Context Window Hygiene — each iteration starts clean"
  ⚛️ "Atomic Commits — one task = one commit, git bisect friendly"
  🛡️ "Fault Tolerance — if iteration 12 fails, 1–11 are already committed"

Below the circle, an additional COMPOUND ENGINEERING callout box (Magenta #B4009E border):
  Title: "Compound Mode: Plan → Work → Review → Compound"
  Show 4 quadrants within the iteration circle:
    Q1 (top-right): "📊 Pre-iteration: read planning report + feed-forward context"
    Q2 (bottom-right): "🧑‍💻 Execute: implement task with enriched context"
    Q3 (bottom-left): "🔍 Post-iteration: review gate scans for debt"
    Q4 (top-left): "🧠 Post-sprint: reflect → extract patterns → feed-forward"
  Caption: "80% planning & review, 20% execution — the inverse of traditional engineering"

Below, a code snippet panel (monospace, dark background card) showing the core ralph.sh logic:
```
for i in $(seq 1 $ITERATIONS); do
  TASK=$(jq -r '.tasks[] | select(.status=="pending") | .id' PRD.json | head -1)
  gh copilot suggest "Implement task $TASK per PRD.json. Update progress.txt."
  git add -A && git commit -m "iteration $i: task $TASK"
done
```

---

ZONE 6 — PLUG MODE + 7 DOMAINS (next 10%)

Title bar: "Two Modes × Seven Domains"

LEFT HALF — TWO MODE CARDS side by side:

CARD 1: "🏗️ Scaffold Mode" (Azure Blue border)
  "Greenfield — generates a complete new project"
  Mini tree: infra/ + agents/ + db/ + app/ + .github/ + skills/

CARD 2: "🔌 Plug Mode" (Teal border)
  "Brownfield — enhances an existing project"
  Mini tree: adapters/ + infra-delta/ + db-delta/ + cicd-patch/ + skills/ (with integrate)
  
  Arrow from "Existing Project" → [🔎 Discovery] → "ignition-plug/" folder
  Caption: "Auto-detects: language, framework, DB, auth, deployment, CI/CD, API endpoints"

RIGHT HALF — DOMAIN GRID (2 rows × 4 columns, last cell empty or "Your Domain"):
  🏥 Healthcare — Patient intake, FHIR, triage
  💰 Finance — Risk assessment, portfolio
  🎓 Education — Student tracking, progress
  🛢️ Oil & Gas — Predictive maintenance
  🚧 Construction — BIM, safety compliance
  📡 Telco — Network ops, customer XP
  🛍️ Retail — Demand forecasting, omnichannel
  ➕ Your Domain — "ignition run your-idea.txt"

---

ZONE 7 — GETTING STARTED FOOTER (bottom 6%)

Title bar: "Get Started in 3 Commands"

Three large numbered command cards in a row:

[1] pip install -e .
[2] ignition run examples/healthcare/use-case.txt --project meridian
[3] ./ralph.sh   # sit back and watch 20 iterations build your app

Below: "Learn more at openagentschool.org | github.com/bhakthan/ignitionstack | MIT License"

QR code placeholder in bottom-right corner linking to the GitHub repo.

---

GLOBAL DESIGN NOTES:
- Light theme throughout (#F8F9FA background, no dark sections except code snippets)
- Flat UI 2.0: no skeuomorphism, no heavy gradients, flat color fills with subtle shadows
- All icons should be simple line/flat style (Fluent UI or Phosphor style)
- Typography hierarchy: H1 120pt, H2 64pt, H3 48pt, body 28pt, code 24pt mono
- Use thin (1px) connecting lines between related elements; thicker (3px) for primary flow
- Every zone must be visually distinct but harmonious — use the section divider color (#E8EAED)
- The overall reading direction is top-to-bottom, left-to-right
- Aspect ratio: 2:1 landscape (optimized for wide display, print, or slide deck embed)
```

---

## Alternative Prompts (Shorter Variants)

### Variant A — Social Media (16:9, 4K)

```
Create a 3840×2160 infographic titled "IgnitionStack — Agents Are the New Apps" in Flat UI 2.0 style, light background (#F8F9FA). Show a 10-stage horizontal pipeline (Input → Parse → Decompose → PRD → Plan Gate → Scaffold → Ralph ×20 → Review Gate → Verify → Reflect) with compound stages in Magenta (#B4009E), plus an exploded isometric view of the generated directory tree below it. Color code: Azure Blue for infra (Bicep modules), Teal for agents, Amber for the Ralph loop, Coral for Claude Skills, Magenta for compound engineering (.ignition/ folder). Include the tagline "One use case. One command. One production Azure workload. Add --compound for recursive self-improvement." Crisp sans-serif text, flat colors, subtle shadows. Show 7 domain icons (healthcare, finance, education, oil-gas, construction, telco, retail) as a horizontal strip at the bottom.
```

### Variant B — Slide Deck Hero (16:9, simplified)

```
Create a clean 1920×1080 slide graphic showing the IgnitionStack pipeline. Center: a horizontal flow of 10 connected nodes (Input → Parse → Decompose → PRD → Plan Gate → Scaffold → Ralph ×20 → Review Gate → Verify → Reflect), with compound stages (Plan Gate, Review Gate, Reflect) highlighted in Magenta. Below the flow, show an exploded folder tree of the generated output (infra/modules/*.bicep, agents/agent-config.json, db/migrations/, app/backend+frontend, .github/workflows/ci-cd.yml, skills/*-ops,agent,data, .ignition/compound-state.json). A dashed Magenta feedback arrow from Reflect back to Plan Gate labeled "feed-forward". Light background, Flat UI 2.0 style, Azure Blue, Teal, and Magenta accents. Title: "Agents Are the New Apps — Use Case to Production in One Command. --compound for Recursive Self-Improvement."
```

### Variant C — Vertical Poster (9:16, mobile-friendly)

```
Create a 2160×3840 vertical infographic poster for "IgnitionStack — From Napkin Sketch to Production." Flat UI 2.0, light theme. Stack vertically: (1) Hero: "Agents Are the New Apps" headline, (2) 10-stage pipeline as a vertical timeline with icons (compound stages in Magenta), (3) Exploded directory tree of generated files color-coded by category (including .ignition/ compound state in Magenta), (4) Ralph Loop circle diagram showing the 20-iteration cycle with compound engineering 4-quadrant overlay, (5) Two mode cards: Scaffold vs Plug, (6) 7 domain icons in a grid, (7) "pip install -e . && ignition run --compound" getting-started footer with feed-forward loop diagram. Azure Blue, Teal, Amber, Coral, Magenta color scheme. Sans-serif typography.
```

---

## Color Reference

| Element | Hex | Usage |
|---------|-----|-------|
| Azure Blue | `#0078D4` | Infrastructure, Bicep, Azure resources |
| Teal | `#00B7C3` | Agents, Microsoft Agent Framework |
| Amber | `#FFB900` | Ralph Loop, iterations, progress |
| Coral | `#F25022` | Claude Skills, key callouts, highlights |
| Green | `#107C10` | Database, migrations, verification pass |
| Purple | `#5C2D91` | Application code (backend + frontend) |
| Orange | `#FF8C00` | CI/CD, GitHub Actions |
| Magenta | `#B4009E` | Compound engineering (Plan Gate, Review Gate, Reflect, .ignition/) |
| Slate | `#2B2B2B` | Primary text color |
| Light Gray | `#E8EAED` | Section dividers, subtle backgrounds |
| Background | `#F8F9FA` | Canvas background |

---

## File Inventory for Accuracy

When generating, ensure these exact file names appear in the exploded directory view:

```
ignition-output/
├── PRD.json
├── progress.txt
├── ralph.sh
├── ralph.ps1
├── planning-report.json          (Compound Mode)
├── compound-metrics.md            (Compound Mode)
├── .ignition/                     (Compound Mode — persistent state)
│   ├── compound-state.json
│   ├── feed-forward.md
│   ├── reviews/
│   │   └── review-iter-{N}.json
│   └── retrospectives/
│       └── retrospective-sprint-{N}.json
├── infra/
│   ├── main.bicep
│   └── modules/
│       ├── rg.bicep        (Resource Group)
│       ├── app.bicep       (App Service + Plan)
│       ├── db.bicep        (Cosmos DB / PostgreSQL)
│       ├── kv.bicep        (Key Vault)
│       ├── ai.bicep        (Microsoft Foundry)
│       ├── search.bicep    (Azure AI Search)
│       └── mon.bicep       (Application Insights)
├── agents/
│   └── agent-config.json
├── db/
│   ├── migrations/
│   │   └── 001_initial.sql
│   └── seed.sql
├── app/
│   ├── backend/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/
│       ├── package.json
│       └── src/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
└── skills/
    ├── README.md
    ├── {project}-ops/
    │   └── SKILL.md
    ├── {project}-agent/
    │   └── SKILL.md
    ├── {project}-data/
    │   └── SKILL.md
    └── {project}-integrate/   (Plug Mode only)
        └── SKILL.md
```
