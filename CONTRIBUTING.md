# Contributing to IgnitionStack

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone
git clone https://github.com/openagentschool/ignitionstack.git
cd ignitionstack

# Create virtual environment
python -m venv .venv
.venv/Scripts/Activate.ps1  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install in editable mode with dev deps
pip install -e ".[dev]"

# Verify
ignition version
pytest -q
```

## Running Tests

```bash
# All tests
pytest -q

# With coverage
pytest --cov=ignition --cov-report=html

# Specific test file
pytest tests/test_models.py -v
```

## Linting

```bash
ruff check ignition/ tests/
ruff format ignition/ tests/
```

## Adding a Domain Example

1. Create `examples/<domain>/use-case.txt` — detailed use-case description
2. Create `examples/<domain>/README.md` — how to run, what gets generated
3. Add domain-specific agent in `ignition/stages/scaffold/agents.py`
4. Add parametrized test in `tests/test_examples.py`

## Adding a Jinja2 Template

1. Place template in `templates/<category>/<name>.j2`
2. Reference it from the appropriate scaffold module
3. Test that the template renders correctly

## Adding Plug Mode Adapters

1. Add Jinja2 template in `templates/plug/<name>.j2`
2. Add inline fallback generator in `ignition/stages/scaffold/plug.py`
3. Wire into `scaffold_plug()` sub-stages
4. Add tests in `tests/test_plug.py`

## Commit Convention

```
<scope>: <brief description>

# Examples:
scaffold: add IoT Hub Bicep template
examples: add manufacturing domain
tutorial: improve decomposition quiz
cli: add --dry-run flag
```

## Pull Request Checklist

- [ ] Tests pass (`pytest -q`)
- [ ] Linter passes (`ruff check`)
- [ ] New features include tests
- [ ] Domain examples include README.md
- [ ] CLI help text is clear and accurate
