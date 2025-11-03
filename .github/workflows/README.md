# GitHub Workflows

This directory contains GitHub Actions workflows for the project.

## Copilot Agent Setup Workflow

### `copilot-setup-steps.yml`
**Purpose:** Automated environment setup for GitHub Copilot Agents

**When it runs:**
- Automatically when GitHub Copilot Agent starts working in the repository
- Manually via `workflow_dispatch`

**What it does:**
1. ✅ Checks out repository with recursive submodules
2. ✅ Updates all submodules to their latest versions
3. ✅ Installs `uv` package manager (using astral-sh/setup-uv@v3)
4. ✅ Installs Python and project dependencies
5. ✅ Installs MicroPython ESP32 stubs to `typings/` directory
6. ✅ Caches environment for faster subsequent runs

**Cache locations:**
- `.venv` - Python virtual environment
- `typings` - MicroPython type stubs
- `~/.cache/uv` - UV package cache

## Related Documentation

- **GitHub Copilot Agent Customization:** https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment
- **UV Package Manager:** https://docs.astral.sh/uv/guides/integration/github/
- **Setup UV Action:** https://github.com/astral-sh/setup-uv

## Local Development

To replicate the Copilot agent environment locally:

```bash
# Clone with submodules
git clone --recurse-submodules <repo-url>

# Or update existing clone
git submodule update --init --recursive

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix
# or
irm https://astral.sh/uv/install.ps1 | iex  # Windows

# Install dependencies
uv sync

# Install MicroPython stubs
uv pip install micropython-esp32-stubs --target typings
```

## Troubleshooting

### Submodule Issues
```bash
# Force update submodules
git submodule sync --recursive
git submodule update --init --recursive --remote --force
```

### UV Cache Issues
```bash
# Clear UV cache
uv cache clean

# Reinstall dependencies
uv sync --reinstall
```

### Missing MicroPython Stubs
```bash
# Reinstall stubs
rm -rf typings
uv pip install micropython-esp32-stubs --target typings
```
