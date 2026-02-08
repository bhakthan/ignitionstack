"""Scaffold: Bicep infrastructure templates (or Docker Compose for local mode)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ignition.config import IgnitionConfig
from ignition.models import PRD

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )


def scaffold_bicep(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Generate Bicep infrastructure files."""
    env = _get_jinja_env()
    work = config.ensure_work_dir()
    infra = work / "infra"
    modules = infra / "modules"
    modules.mkdir(parents=True, exist_ok=True)

    ctx = {
        "project_name": prd.project_name,
        "location": config.azure_location,
        "subscription_id": config.azure_subscription_id,
        "domain": prd.domain,
    }

    files_written: list[str] = []

    # Main orchestrator
    tpl = env.get_template("bicep/main.bicep.j2")
    dest = infra / "main.bicep"
    dest.write_text(tpl.render(**ctx), encoding="utf-8")
    files_written.append(str(dest.relative_to(work)))

    # Module templates
    module_names = ["rg", "app", "db", "kv", "ai", "search", "mon"]
    for mod in module_names:
        tpl_path = f"bicep/modules/{mod}.bicep.j2"
        try:
            tpl = env.get_template(tpl_path)
            dest = modules / f"{mod}.bicep"
            dest.write_text(tpl.render(**ctx), encoding="utf-8")
            files_written.append(str(dest.relative_to(work)))
        except Exception:
            # Template not found — write placeholder
            dest = modules / f"{mod}.bicep"
            dest.write_text(
                f"// {mod}.bicep — placeholder (add template at templates/{tpl_path})\n",
                encoding="utf-8",
            )
            files_written.append(str(dest.relative_to(work)))

    return files_written


def scaffold_docker_compose(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Generate docker-compose.yml for local mode."""
    env = _get_jinja_env()
    work = config.ensure_work_dir()
    ctx = {
        "project_name": prd.project_name,
        "domain": prd.domain,
    }
    try:
        tpl = env.get_template("docker-compose.yml.j2")
        dest = work / "docker-compose.yml"
        dest.write_text(tpl.render(**ctx), encoding="utf-8")
        return [str(dest.relative_to(work))]
    except Exception:
        # Fallback inline template
        content = f"""\
# Docker Compose — {prd.project_name} (local mode)
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: {prd.project_name.replace("-", "_")}
      POSTGRES_USER: app
      POSTGRES_PASSWORD: localdev123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: ./app/backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://app:localdev123@db:5432/{prd.project_name.replace("-", "_")}
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  pgdata:
"""
        dest = work / "docker-compose.yml"
        dest.write_text(content, encoding="utf-8")
        return ["docker-compose.yml"]


def scaffold_infra(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Entry point — dispatches to Bicep or Docker Compose."""
    if config.local_mode:
        return scaffold_docker_compose(prd, config)
    return scaffold_bicep(prd, config)
