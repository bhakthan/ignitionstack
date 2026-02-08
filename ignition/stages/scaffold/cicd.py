"""Scaffold: CI/CD pipeline (GitHub Actions)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ignition.config import IgnitionConfig
from ignition.models import PRD

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"


def scaffold_cicd(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Generate CI/CD workflow files."""
    work = config.ensure_work_dir()
    wf_dir = work / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    files: list[str] = []

    try:
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        tpl = env.get_template("cicd/ci-cd.yml.j2")
        content = tpl.render(
            project_name=prd.project_name,
            has_azure=config.has_azure,
            azure_location=config.azure_location,
        )
    except Exception:
        content = _inline_cicd(prd, config)

    dest = wf_dir / "ci-cd.yml"
    dest.write_text(content, encoding="utf-8")
    files.append(str(dest.relative_to(work)))

    return files


def _inline_cicd(prd: PRD, config: IgnitionConfig) -> str:
    """Fallback inline CI/CD template."""
    deploy_step = ""
    if config.has_azure:
        deploy_step = f"""
      - name: Azure Login
        uses: azure/login@v2
        with:
          creds: ${{{{ secrets.AZURE_CREDENTIALS }}}}

      - name: Deploy Bicep
        uses: azure/arm-deploy@v2
        with:
          scope: subscription
          region: {config.azure_location}
          template: ./infra/main.bicep
          parameters: projectName={prd.project_name}
"""
    else:
        deploy_step = """
      - name: Deploy (local mode)
        run: docker compose up -d --build
"""

    return f"""\
name: CI/CD — {prd.project_name}

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend deps
        run: pip install -r app/backend/requirements.txt

      - name: Run backend tests
        run: cd app/backend && pytest -q

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install frontend deps
        run: cd app/frontend && npm ci

      - name: Build frontend
        run: cd app/frontend && npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
{deploy_step}
"""
