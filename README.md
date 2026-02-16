# synq-steep

ETL pipeline that syncs Steep analytics data (metrics, entities, modules) to SYNQ data catalog as custom entities.

## Installation

```bash
# Using uv
uv sync

# Or pip
pip install -e .
```

## Usage

```bash
# Dry run (preview entities without uploading)
uv run synq-steep --dry-run --mock-dir ./v1

# Sync all entity types
uv run synq-steep \
  --steep-token $STEEP_TOKEN \
  --synq-client-id $SYNQ_CLIENT_ID \
  --synq-client-secret $SYNQ_CLIENT_SECRET

# Sync specific types only
uv run synq-steep \
  --steep-token $STEEP_TOKEN \
  --synq-client-id $SYNQ_CLIENT_ID \
  --synq-client-secret $SYNQ_CLIENT_SECRET \
  --types metrics,modules
```

### Options

| Option | Env Variable | Description |
|--------|--------------|-------------|
| `--steep-url` | `STEEP_URL` | Steep API base URL (default: `https://api.steep.app`) |
| `--steep-token` | `STEEP_TOKEN` | Steep API bearer token |
| `--synq-client-id` | `SYNQ_CLIENT_ID` | SYNQ OAuth2 client ID |
| `--synq-client-secret` | `SYNQ_CLIENT_SECRET` | SYNQ OAuth2 client secret |
| `--synq-host` | `SYNQ_HOST` | SYNQ API host (default: `developer.synq.io`) |
| `--dry-run` | - | Print entities instead of uploading |
| `--mock-dir` | - | Use local JSON files instead of Steep API |
| `--types` | - | Comma-separated types: `metrics`, `entities`, `modules` |

## GitHub Actions Workflow

Create `.github/workflows/sync-steep.yml`:

```yaml
name: Sync Steep to SYNQ

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:        # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Sync Steep data to SYNQ
        env:
          STEEP_TOKEN: ${{ secrets.STEEP_TOKEN }}
          SYNQ_CLIENT_ID: ${{ secrets.SYNQ_CLIENT_ID }}
          SYNQ_CLIENT_SECRET: ${{ secrets.SYNQ_CLIENT_SECRET }}
        run: uv run synq-steep
```

### Required Secrets

Add these secrets in GitHub repository settings:

- `STEEP_TOKEN` - Steep API bearer token
- `SYNQ_CLIENT_ID` - SYNQ OAuth2 client ID
- `SYNQ_CLIENT_SECRET` - SYNQ OAuth2 client secret

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=synq_steep

# Type checking
uv run pyright
```

## Entity Mapping

| Steep Type | SYNQ Identifier | Annotations |
|------------|-----------------|-------------|
| Metric | `steep::metric::{id}` | url, identifier, category, owners, schema, table |
| Entity | `steep::entity::{id}` | moduleId, createdAt, updatedAt |
| Module | `steep::module::{id}` | identifier, schema, table, externalSource |
