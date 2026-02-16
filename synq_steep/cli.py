from pathlib import Path
from typing import Annotated

import msgspec
import typer

from synq_steep.clients.steep import SteepClient
from synq_steep.clients.synq import SynqClient
from synq_steep.models.steep import SteepEntity, SteepMetric, SteepModule
from synq_steep.models.synq import ALL_STEEP_TYPES, Relationship, SynqEntity
from synq_steep.transformers.entities import EntityTransformer
from synq_steep.transformers.metrics import MetricTransformer
from synq_steep.transformers.modules import ModuleTransformer

app = typer.Typer(
    name="synq-steep",
    help="Sync Steep analytics data to SYNQ data catalog",
    no_args_is_help=True,
)


def get_env_or_none(name: str) -> str | None:
    import os
    return os.environ.get(name)


@app.command()
def sync(
    steep_url: Annotated[
        str,
        typer.Option(
            envvar="STEEP_URL",
            help="Steep API base URL",
        ),
    ] = "https://api.steep.app",
    steep_token: Annotated[
        str | None,
        typer.Option(
            envvar="STEEP_TOKEN",
            help="Steep API bearer token",
        ),
    ] = None,
    synq_client_id: Annotated[
        str | None,
        typer.Option(
            envvar="SYNQ_CLIENT_ID",
            help="SYNQ OAuth2 client ID",
        ),
    ] = None,
    synq_client_secret: Annotated[
        str | None,
        typer.Option(
            envvar="SYNQ_CLIENT_SECRET",
            help="SYNQ OAuth2 client secret",
        ),
    ] = None,
    synq_host: Annotated[
        str,
        typer.Option(
            envvar="SYNQ_HOST",
            help="SYNQ API host",
        ),
    ] = "developer.synq.io",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Print entities instead of uploading",
        ),
    ] = False,
    mock_dir: Annotated[
        Path | None,
        typer.Option(
            help="Use local JSON files instead of Steep API",
        ),
    ] = None,
    types: Annotated[
        str | None,
        typer.Option(
            help="Comma-separated entity types to sync (metrics,entities,modules)",
        ),
    ] = None,
    skip_types: Annotated[
        bool,
        typer.Option(
            "--skip-types",
            help="Skip custom type definition phase",
        ),
    ] = False,
    skip_relationships: Annotated[
        bool,
        typer.Option(
            "--skip-relationships",
            help="Skip relationship creation phase",
        ),
    ] = False,
) -> None:
    """Sync Steep data to SYNQ."""
    if mock_dir is None and steep_token is None:
        typer.echo("Error: --steep-token is required when not using --mock-dir")
        raise typer.Exit(1)

    if not dry_run:
        if synq_client_id is None or synq_client_secret is None:
            typer.echo("Error: --synq-client-id and --synq-client-secret are required when not using --dry-run")
            raise typer.Exit(1)

    type_set = _parse_types(types)

    with SteepClient(
        base_url=steep_url,
        token=steep_token or "",
        mock_dir=mock_dir,
    ) as steep_client:
        entities, raw_data = _fetch_and_transform(steep_client, type_set)

    if dry_run:
        _print_entities(entities)
    else:
        assert synq_client_id is not None
        assert synq_client_secret is not None
        _upload_all(
            entities=entities,
            raw_data=raw_data,
            type_set=type_set,
            client_id=synq_client_id,
            client_secret=synq_client_secret,
            host=synq_host,
            skip_types=skip_types,
            skip_relationships=skip_relationships,
        )


class RawData:
    """Container for raw Steep data used for relationship extraction."""

    def __init__(self) -> None:
        self.metrics: list[SteepMetric] = []
        self.entities: list[SteepEntity] = []
        self.modules: list[SteepModule] = []


def _parse_types(types: str | None) -> set[str]:
    if types is None:
        return {"metrics", "entities", "modules"}
    return {t.strip() for t in types.split(",")}


def _fetch_and_transform(
    client: SteepClient,
    type_set: set[str],
) -> tuple[list[SynqEntity], RawData]:
    entities: list[SynqEntity] = []
    raw_data = RawData()

    if "metrics" in type_set:
        raw_data.metrics = client.get_metrics(expand=True)
        transformer = MetricTransformer()
        entities.extend(transformer.transform(m) for m in raw_data.metrics)

    if "entities" in type_set:
        raw_data.entities = client.get_entities()
        transformer = EntityTransformer()
        entities.extend(transformer.transform(e) for e in raw_data.entities)

    if "modules" in type_set:
        raw_data.modules = client.get_modules()
        transformer = ModuleTransformer()
        entities.extend(transformer.transform(m) for m in raw_data.modules)

    return entities, raw_data


def _print_entities(entities: list[SynqEntity]) -> None:
    typer.echo(f"Found {len(entities)} entities (dry run):")
    typer.echo()
    for entity in entities:
        typer.echo(f"  {entity.id.custom.id}: {entity.name}")
        encoded = msgspec.json.encode(entity)
        typer.echo(f"    {encoded.decode()}")
        typer.echo()


def _collect_relationships(raw_data: RawData, type_set: set[str]) -> list[Relationship]:
    """Collect relationships from all transformers."""
    relationships: list[Relationship] = []

    if "metrics" in type_set:
        transformer = MetricTransformer()
        for metric in raw_data.metrics:
            relationships.extend(transformer.to_relationships(metric))

    if "entities" in type_set:
        transformer = EntityTransformer()
        for entity in raw_data.entities:
            relationships.extend(transformer.to_relationships(entity))

    if "modules" in type_set:
        transformer = ModuleTransformer()
        for module in raw_data.modules:
            relationships.extend(transformer.to_relationships(module))

    return relationships


def _upload_all(
    entities: list[SynqEntity],
    raw_data: RawData,
    type_set: set[str],
    client_id: str,
    client_secret: str,
    host: str,
    skip_types: bool,
    skip_relationships: bool,
) -> None:
    with SynqClient(
        client_id=client_id,
        client_secret=client_secret,
        host=host,
    ) as synq_client:
        synq_client.authenticate()

        # Phase 1: Define custom types
        if not skip_types:
            typer.echo("Defining custom entity types...")
            for steep_type in ALL_STEEP_TYPES:
                typer.echo(f"  Defining type: {steep_type.name}")
                synq_client.upsert_type(steep_type)
            typer.echo(f"Successfully defined {len(ALL_STEEP_TYPES)} types")

        # Phase 2: Upload entities
        typer.echo("Uploading entities...")
        for entity in entities:
            typer.echo(f"  Uploading {entity.id.custom.id}...")
            synq_client.upsert_entity(entity)
        typer.echo(f"Successfully uploaded {len(entities)} entities")

        # Phase 3: Create relationships
        if not skip_relationships:
            relationships = _collect_relationships(raw_data, type_set)
            if relationships:
                typer.echo("Creating relationships...")
                typer.echo(f"  Uploading {len(relationships)} relationships...")
                synq_client.upsert_relationships(relationships)
                typer.echo(f"Successfully created {len(relationships)} relationships")
            else:
                typer.echo("No relationships to create")


if __name__ == "__main__":
    app()
