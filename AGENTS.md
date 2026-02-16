# Agent Guidelines

## Project Overview

Python ETL pipeline that syncs Steep analytics data to SYNQ data catalog.

## Quick Reference

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=synq_steep

# Type check
uv run pyright

# Run CLI
uv run synq-steep --help
```

## Project Structure

```
synq_steep/
├── cli.py                 # Typer CLI entry point
├── models/
│   ├── steep.py           # Steep API response models (msgspec)
│   └── synq.py            # SYNQ entity models (msgspec)
├── clients/
│   ├── steep.py           # Steep HTTP client (supports mock files)
│   └── synq.py            # SYNQ OAuth2 + REST client
└── transformers/
    ├── metrics.py         # Metric → SynqEntity
    ├── entities.py        # Entity → SynqEntity
    └── modules.py         # Module → SynqEntity

tests/                     # Mirrors synq_steep/ structure
v1/                        # Mock JSON data for testing
```

## Key Patterns

### Models (msgspec)

All models use `msgspec.Struct` with `rename="camel"` for JSON serialization:

```python
class SteepModule(msgspec.Struct, rename="camel"):
    id: str
    schema_: str = msgspec.field(name="schema")  # Reserved word handling
```

### Transformers

Each transformer has a `transform()` method returning `SynqEntity`:

```python
class MetricTransformer:
    def transform(self, metric: SteepMetric) -> SynqEntity:
        return SynqEntity(
            id=CustomIdentifier.for_steep_metric(metric.id),
            name=metric.label[:100],
            type_id=EntityTypeId.METRIC,
            annotations=self._build_annotations(metric),
        )
```

### SYNQ Identifiers

Format: `steep::{type}::{id}` where type is `metric`, `entity`, or `module`.

### Mock Data Support

Clients accept `mock_dir` parameter to load from local JSON files instead of API:

```python
client = SteepClient(base_url="...", token="...", mock_dir=Path("v1"))
```

## Testing

- **TDD workflow**: Write failing test → implement → refactor
- **Mock files**: `v1/metrics.json`, `v1/entities.json`, `v1/modules.json`
- **HTTP mocking**: Use `respx` for mocking httpx requests
- **Fixtures**: `conftest.py` provides `mock_data_dir`, `metrics_json`, etc.

## API References

- **Steep API**: https://help.steep.app/api/reference
- **SYNQ API**: https://docs.synq.io/api-reference/synqentitiescustomv1entitiesservice/upsertentity

## Adding New Entity Types

1. Add model to `models/steep.py`
2. Create transformer in `transformers/`
3. Update `_fetch_and_transform()` in `cli.py`
4. Add mock JSON file to `v1/`
5. Write tests following existing patterns

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `STEEP_TOKEN` | Steep API bearer token |
| `STEEP_URL` | Steep API base URL |
| `SYNQ_CLIENT_ID` | SYNQ OAuth2 client ID |
| `SYNQ_CLIENT_SECRET` | SYNQ OAuth2 client secret |
| `SYNQ_HOST` | SYNQ API host |
