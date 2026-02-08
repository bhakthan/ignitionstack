"""Tutorial Mode — guided step-by-step learning experience with Rich panels."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# ---------------------------------------------------------------------------
# Stage explanations
# ---------------------------------------------------------------------------

STAGE_INFO: dict[str, dict[str, Any]] = {
    "discovery": {
        "title": "Stage 0 — Discovery (Plug Mode)",
        "before": (
            "Before we do anything, we scan the existing "
            "project to understand what's already there.\n\n"
            "Discovery detects:\n"
            "  \u2022 Language (Python, TypeScript, C#, Java, Go, Rust)\n"
            "  \u2022 Framework (FastAPI, Express, ASP.NET, Spring Boot, etc.)\n"
            "  \u2022 Database (PostgreSQL, Cosmos DB, MongoDB, etc.)\n"
            "  \u2022 Auth mechanism (Azure AD, JWT, OAuth, etc.)\n"
            "  \u2022 Deployment model (Bicep, Terraform, Docker, K8s)\n"
            "  \u2022 CI/CD provider (GitHub Actions, Azure Pipelines, etc.)\n"
            "  \u2022 API endpoints (route decorators from source files)\n\n"
            "This produces discovery.json \u2014 the foundation for "
            "generating integration-only artifacts."
        ),
        "after": "Discovery complete — existing stack analyzed.",
        "key_files": ["discovery.json"],
        "quiz": {
            "question": "Why does Plug Mode scan the existing project first?",
            "options": [
                "To delete conflicting files",
                "To understand the stack and generate only additive artifacts",
                "To benchmark performance",
            ],
            "answer": 1,
        },
    },
    "plug_scaffold": {
        "title": "Stage 5 — Plug Scaffold",
        "before": (
            "Unlike full Scaffold mode, Plug Scaffold generates "
            "ONLY integration artifacts:\n\n"
            "  \u2022 [bold]Adapters[/bold] \u2014 Agent middleware + "
            "RAG connector for your existing app\n"
            "  \u2022 [bold]Infra Delta[/bold] \u2014 Incremental Bicep "
            "(AI + Search + KV) or Docker override\n"
            "  \u2022 [bold]DB Delta[/bold] \u2014 Additive migration "
            "for agent state tables\n"
            "  \u2022 [bold]CI/CD Patch[/bold] \u2014 Steps to merge "
            "into your existing pipeline\n"
            "  \u2022 [bold]Agent Config[/bold] — Microsoft Agent Framework tuned to your stack\n\n"
            "Nothing is deleted or overwritten in your existing project. "
            "All artifacts go into a separate ignition-plug/ directory."
        ),
        "after": "Plug artifacts generated in ignition-plug/.",
        "key_files": [
            "adapters/agent_middleware.py",
            "adapters/rag_connector.py",
            "infra-delta/delta.bicep",
            "db-delta/001_agent_state.sql",
            "cicd-patch/ai-steps.yml",
        ],
    },
    "input": {
        "title": "Stage 1 — Input",
        "before": (
            "The pipeline begins by accepting your use-case document.\n\n"
            "Supported formats: .txt, .md, .pdf, .pptx, .docx, .png, .jpg\n\n"
            "The IgnitionStack pattern is format-agnostic — it can start from a napkin sketch "
            "(screenshot) or a formal PowerPoint deck. The key insight: the input is just a seed. "
            "The real work happens in decomposition."
        ),
        "after": "Your input file has been validated and its type detected.",
        "key_files": [],
    },
    "parse": {
        "title": "Stage 2 — Parse",
        "before": (
            "Now the LLM extracts structured requirements from your raw input.\n\n"
            "For text files, it reads the content directly. For PDFs and PPTX, it extracts text. "
            "For images/screenshots, it uses the Vision API to describe what it sees.\n\n"
            "The output is a structured object with:\n"
            "  • Summary — one-paragraph project description\n"
            "  • Features — extracted feature list\n"
            "  • Constraints — non-functional requirements\n"
            "  • Domain — detected domain (healthcare, finance, etc.)\n"
            "  • Actors — identified user roles"
        ),
        "after": "Requirements have been extracted and structured.",
        "key_files": [],
    },
    "decompose": {
        "title": "Stage 3 — Decompose (T/B/I/C Test)",
        "before": (
            "This is the CRITICAL stage. The LLM breaks requirements into 30-50 atomic tasks.\n\n"
            "Every task must pass the Decomposition Test — four gates:\n\n"
            "  [bold cyan]T[/bold cyan]estable  — Can a type-checker or test verify it?\n"
            "  [bold cyan]B[/bold cyan]ounded   — Can it be done in ONE iteration (<30 min)?\n"
            "  [bold cyan]I[/bold cyan]ndependent — No coupling to incomplete tasks?\n"
            "  [bold cyan]C[/bold cyan]ommittable — Does it produce a meaningful git commit?\n\n"
            "If a task fails any gate, it gets split further. This is what makes the Ralph loop "
            "work — each iteration gets a clean, achievable task."
        ),
        "after": "Tasks decomposed and T/B/I/C validated.",
        "key_files": [],
        "quiz": {
            "question": "What does T/B/I/C stand for?",
            "options": [
                "Testable, Bounded, Independent, Committable",
                "Typed, Built, Integrated, Complete",
                "Tested, Balanced, Isolated, Checked",
            ],
            "answer": 0,
        },
    },
    "prd": {
        "title": "Stage 4 — PRD Generator",
        "before": (
            "The PRD (Product Requirements Document) is the task backlog.\n\n"
            "It's a JSON file that the Ralph loop reads at each iteration. Think of it as the "
            "agent's 'todo list' — each task has an ID, category, description, dependencies, "
            "and status.\n\n"
            "We also initialize progress.txt — the agent's 'external memory'. This file tracks "
            "what the agent has done across iterations, providing context without polluting the "
            "LLM's context window."
        ),
        "after": "PRD.json and progress.txt created.",
        "key_files": ["PRD.json", "progress.txt"],
    },
    "scaffold": {
        "title": "Stage 5 — Scaffold",
        "before": (
            "Now we generate the actual project files from templates.\n\n"
            "This includes:\n"
            "  • [bold]Infrastructure[/bold] — Bicep modules (or Docker Compose for local mode)\n"
            "  • [bold]Agents[/bold] — Microsoft Agent Framework configuration\n"
            "  • [bold]Database[/bold] — Migration scripts and seed data\n"
            "  • [bold]Application[/bold] — FastAPI backend + React frontend stubs\n"
            "  • [bold]CI/CD[/bold] — GitHub Actions workflow\n"
            "  • [bold]Ralph scripts[/bold] — The bash/PowerShell loop\n\n"
            "All files come from Jinja2 templates, customized for your project name and domain."
        ),
        "after": "All project files scaffolded.",
        "key_files": [
            "infra/main.bicep",
            "agents/agent-config.json",
            "ralph.sh",
        ],
        "quiz": {
            "question": (
                "Why use a simple bash loop instead of a complex framework?"
            ),
            "options": [
                "Bash is faster than Python",
                "Context window hygiene — each iteration starts clean",
                "Frameworks cost money",
            ],
            "answer": 1,
        },
    },
    "ralph": {
        "title": "Stage 6 — Ralph Loop (×N iterations)",
        "before": (
            "The Ralph loop is the heart of IgnitionStack.\n\n"
            "Each iteration:\n"
            "  1. Read PRD.json + progress.txt\n"
            "  2. Pick the next pending task (dependencies satisfied)\n"
            "  3. Implement it (write code, add tests)\n"
            "  4. Mark it done in PRD.json\n"
            "  5. Append to progress.txt\n"
            "  6. git commit\n\n"
            "The genius is in the simplicity: no state accumulation, no framework overhead, "
            "no context window bloat. Just read → do → commit × 20.\n\n"
            "In this template, we generate the scripts. You'll run them separately."
        ),
        "after": "Ralph loop scripts generated and ready to run.",
        "key_files": ["ralph.sh", "ralph.ps1"],
    },
    "skills": {
        "title": "Stage 7 — Claude Skills",
        "before": (
            "Now we generate Claude Skills — folders that teach Claude \n"
            "how to work with your scaffolded project.\n\n"
            "Following the Anthropic Skills spec, each skill is a folder \n"
            "containing a SKILL.md with YAML frontmatter + instructions:\n\n"
            "  • [bold]{project}-ops[/bold] — Deploy, run, debug, \n"
            "    troubleshoot the generated stack\n"
            "  • [bold]{project}-agent[/bold] — Interact with, test, \n"
            "    and customize the AI agents\n"
            "  • [bold]{project}-data[/bold] — Manage data pipelines, \n"
            "    migrations, and RAG indexing\n"
            "  • [bold]{project}-integrate[/bold] (Plug Mode only) — \n"
            "    Mount middleware, wire RAG, merge CI/CD\n\n"
            "Skills use progressive disclosure: frontmatter gives intent, \n"
            "the body gives step-by-step instructions."
        ),
        "after": "Claude Skills generated in skills/ directory.",
        "key_files": [
            "skills/README.md",
            "skills/{project}-ops/SKILL.md",
            "skills/{project}-agent/SKILL.md",
            "skills/{project}-data/SKILL.md",
        ],
        "quiz": {
            "question": "What is the REQUIRED file in every Claude Skill folder?",
            "options": [
                "README.md",
                "SKILL.md",
                "skill.json",
            ],
            "answer": 1,
        },
    },
    "verify": {
        "title": "Stage 8 — Verification",
        "before": (
            "Final step: we verify the scaffolded output is structurally correct.\n\n"
            "Checks include:\n"
            "  • All expected files exist\n"
            "  • PRD has sufficient tasks (30-50)\n"
            "  • All tasks pass T/B/I/C test\n"
            "  • Infrastructure templates are valid\n"
            "  • CI/CD workflow is present"
        ),
        "after": "Verification complete!",
        "key_files": [],
        "quiz": {
            "question": "How many iterations does the default Ralph loop run?",
            "options": ["10", "20", "50"],
            "answer": 1,
        },
    },
}


class TutorialRunner:
    """Drives the tutorial experience with Rich panels and checkpoints."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.score = 0
        self.total_quizzes = 0

    def before_stage(self, stage: str) -> None:
        """Show explanation before a pipeline stage runs."""
        info = STAGE_INFO.get(stage)
        if not info:
            return

        self.console.print()
        self.console.print(
            Panel(
                info["before"],
                title=f"📖 {info['title']}",
                border_style="blue",
                padding=(1, 2),
            )
        )

        if not Confirm.ask("  [dim]Ready to proceed?[/dim]", default=True):
            self.console.print("  [dim]Continuing anyway...[/dim]")

    def after_stage(self, stage: str, extra: str = "") -> None:
        """Show results and optional quiz after a stage."""
        info = STAGE_INFO.get(stage)
        if not info:
            return

        msg = info["after"]
        if extra:
            msg += f"\n  → {extra}"

        self.console.print(f"\n  [green]✅ {msg}[/green]")

        # Show key files
        key_files = info.get("key_files", [])
        if key_files:
            self.console.print("  [dim]Key files to inspect:[/dim]")
            for f in key_files:
                self.console.print(f"    📄 {f}")

        # Quiz checkpoint
        quiz = info.get("quiz")
        if quiz:
            self._run_quiz(quiz)

    def _run_quiz(self, quiz: dict) -> None:
        """Run an interactive quiz checkpoint."""
        self.total_quizzes += 1
        self.console.print()
        self.console.print(
            Panel(
                f"[bold]{quiz['question']}[/bold]",
                title="🧠 Checkpoint",
                border_style="yellow",
            )
        )

        options = quiz["options"]
        for i, opt in enumerate(options):
            self.console.print(f"  [{i + 1}] {opt}")

        answer = Prompt.ask(
            "  Your answer",
            choices=[str(i + 1) for i in range(len(options))],
            default=str(quiz["answer"] + 1),
        )

        if int(answer) - 1 == quiz["answer"]:
            self.score += 1
            self.console.print("  [bold green]✅ Correct![/bold green]")
        else:
            correct = options[quiz["answer"]]
            self.console.print(f"  [yellow]Not quite — the answer is: {correct}[/yellow]")

    def summary(self) -> None:
        """Show final learning summary."""
        self.console.print()

        table = Table(title="📊 Tutorial Summary", border_style="cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        table.add_row("Quiz Score", f"{self.score}/{self.total_quizzes}")
        table.add_row("Stages Completed", "7/7")

        self.console.print(table)
        self.console.print()
        self.console.print(
            Panel(
                "[bold]What you learned:[/bold]\n\n"
                "• The 7-stage IgnitionStack pipeline\n"
                "• The T/B/I/C Decomposition Test for atomic tasks\n"
                "• How the Ralph loop maintains context window hygiene\n"
                "• Infrastructure-as-Code with Bicep templates\n"
                "• Microsoft Agent Framework configuration\n"
                "• CI/CD automation with GitHub Actions\n\n"
                "[dim]Learn more at[/dim] [bold cyan]https://openagentschool.org[/bold cyan]",
                title="🎓 Learning Complete",
                border_style="green",
            )
        )
