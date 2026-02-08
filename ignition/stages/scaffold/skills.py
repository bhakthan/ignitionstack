"""Scaffold: Claude Skills — generates SKILL.md folders per Anthropic spec."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ignition.config import IgnitionConfig
from ignition.models import PRD, DiscoveryResult

TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "templates"
)


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
    )


def _detect_domain(prd: PRD) -> str:
    """Infer domain from PRD metadata or project name."""
    meta = prd.metadata or {}
    if "domain" in meta:
        return str(meta["domain"])
    name = prd.project_name.lower()
    for domain in (
        "healthcare", "finance", "education", "oil-and-gas",
        "construction", "telco", "retail",
    ):
        if domain.replace("-", "") in name.replace("-", ""):
            return domain
    return "general"


def _render_skill(
    env: Environment,
    template_name: str,
    dest_dir: Path,
    context: dict,
) -> str:
    """Render a skill template into its kebab-case folder with SKILL.md."""
    tpl = env.get_template(template_name)
    content = tpl.render(**context)
    dest_dir.mkdir(parents=True, exist_ok=True)
    skill_file = dest_dir / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")
    return str(dest_dir.name) + "/SKILL.md"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def scaffold_skills(
    prd: PRD,
    config: IgnitionConfig,
    *,
    discovery: DiscoveryResult | None = None,
) -> list[str]:
    """
    Generate Claude Skills for the project.

    Scaffold mode: ops, agent, data skills.
    Plug mode: adds integrate skill.

    Returns list of generated file paths (relative to work_dir).
    """
    env = _get_jinja_env()
    work = config.ensure_work_dir()
    skills_root = work / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)

    domain = _detect_domain(prd)
    db_name = prd.project_name.replace("-", "_")
    work_dir_name = work.name

    base_ctx = {
        "project_name": prd.project_name,
        "domain": domain,
        "model": config.model,
        "region": config.azure_location,
        "iterations": config.iterations,
        "local_mode": config.local_mode,
        "work_dir_name": work_dir_name,
        "db_name": db_name,
        "metadata_author": "",
    }

    generated: list[str] = []

    # 1. Ops skill
    ops_dir = skills_root / f"{prd.project_name}-ops"
    generated.append(
        "skills/"
        + _render_skill(env, "skills/ops-SKILL.md.j2", ops_dir, base_ctx)
    )

    # 2. Agent skill
    agent_dir = skills_root / f"{prd.project_name}-agent"
    generated.append(
        "skills/"
        + _render_skill(
            env, "skills/agent-SKILL.md.j2", agent_dir, base_ctx,
        )
    )

    # 3. Data skill
    data_dir = skills_root / f"{prd.project_name}-data"
    generated.append(
        "skills/"
        + _render_skill(
            env, "skills/data-SKILL.md.j2", data_dir, base_ctx,
        )
    )

    # 4. Integrate skill (Plug Mode only)
    if config.is_plug_mode and discovery is not None:
        plug_ctx = {
            **base_ctx,
            "language": discovery.language,
            "framework": discovery.framework,
            "database": discovery.database,
            "auth": discovery.auth,
            "deployment": discovery.deployment,
            "cicd": discovery.cicd,
            "plug_dir": work_dir_name,
            "target_path": str(
                config.plug_target or "your-project",
            ),
        }
        integrate_dir = skills_root / f"{prd.project_name}-integrate"
        generated.append(
            "skills/"
            + _render_skill(
                env,
                "skills/integrate-SKILL.md.j2",
                integrate_dir,
                plug_ctx,
            )
        )

    # Write a top-level README for the skills directory
    _write_skills_readme(skills_root, prd, generated, config.is_plug_mode)

    return generated


def _write_skills_readme(
    skills_root: Path,
    prd: PRD,
    generated: list[str],
    is_plug: bool,
) -> None:
    """Create a README explaining the skills directory."""
    skill_names = [g.split("/")[1] for g in generated]
    lines = [
        f"# Claude Skills for {prd.project_name}\n",
        "",
        "These skills teach Claude how to work with this project.",
        "Each folder follows the [Anthropic Agent Skills]"
        "(https://docs.anthropic.com/en/docs/agents-and-tools/skills)"
        " specification.\n",
        "",
        "## Installation\n",
        "",
        "### Claude.ai",
        f"1. Zip a skill folder (e.g., `{prd.project_name}-ops`)",
        "2. Go to **Settings > Capabilities > Skills**",
        "3. Click **Upload skill** and select the zip\n",
        "",
        "### Claude Code",
        "Copy skill folders to your Claude Code skills directory.\n",
        "",
        "## Included Skills\n",
        "",
    ]
    for name in skill_names:
        lines.append(f"- **{name}/**")
    if is_plug:
        lines.append("")
        lines.append(
            "*The integrate skill is Plug Mode specific — "
            "it guides merging artifacts into your existing project.*"
        )
    lines.append("")
    readme = skills_root / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
