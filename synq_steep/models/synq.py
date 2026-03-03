import base64
from enum import IntEnum

import msgspec


class EntityTypeId(IntEnum):
    """Entity type IDs for Steep entities in SYNQ."""

    METRIC = 30
    ENTITY = 31
    MODULE = 32


class CustomId(msgspec.Struct, frozen=True):
    """Custom identifier ID wrapper."""

    id: str


class SnowflakeTableId(msgspec.Struct, frozen=True):
    """Snowflake table coordinates."""

    account: str
    database: str
    schema: str
    table: str


class CustomIdentifier(msgspec.Struct, frozen=True):
    """Custom identifier for SYNQ entities and relationship endpoints."""

    custom: CustomId

    @property
    def str_id(self) -> str:
        return self.custom.id

    @classmethod
    def for_steep_metric(cls, steep_id: str) -> "CustomIdentifier":
        return cls(custom=CustomId(id=f"steep::metric::{steep_id}"))

    @classmethod
    def for_steep_entity(cls, steep_id: str) -> "CustomIdentifier":
        return cls(custom=CustomId(id=f"steep::entity::{steep_id}"))

    @classmethod
    def for_steep_module(cls, steep_id: str) -> "CustomIdentifier":
        return cls(custom=CustomId(id=f"steep::module::{steep_id}"))


class SnowflakeConfig(msgspec.Struct, frozen=True):
    """Snowflake connection configuration for upstream table relationships."""

    account: str
    database: str


class SnowflakeIdentifier(msgspec.Struct, frozen=True):
    """Snowflake table identifier for SYNQ relationships."""

    snowflake_table: SnowflakeTableId = msgspec.field(name="snowflakeTable")

    @classmethod
    def for_snowflake_table(
        cls,
        account: str,
        database: str,
        schema: str,
        table: str,
    ) -> "SnowflakeIdentifier":
        return cls(
            snowflake_table=SnowflakeTableId(
                account=account,
                database=database,
                schema=schema,
                table=table,
            )
        )


class Annotation(msgspec.Struct, frozen=True):
    """Annotation for entity metadata."""

    name: str
    values: list[str]


class SynqEntity(msgspec.Struct, rename="camel", frozen=True):
    """Entity to be synced to SYNQ."""

    id: CustomIdentifier
    name: str
    type_id: int
    description: str | None = None
    annotations: list[Annotation] | None = None


class SynqUpsertRequest(msgspec.Struct, frozen=True):
    """Request wrapper for entity upsert API."""

    entity: SynqEntity


class Type(msgspec.Struct, rename="camel", omit_defaults=True, frozen=True):
    """Custom entity type definition for SYNQ."""

    type_id: int
    name: str
    svg_icon: str
    description: str | None = None


class UpsertTypeRequest(msgspec.Struct, frozen=True):
    """Request wrapper for type upsert API."""

    type: Type


class Relationship(msgspec.Struct, frozen=True):
    """Relationship between two entities (upstream -> downstream)."""

    upstream: CustomIdentifier | SnowflakeIdentifier
    downstream: CustomIdentifier


class UpsertRelationshipsRequest(msgspec.Struct, frozen=True):
    """Request wrapper for batch relationship upsert API."""

    relationships: list[Relationship]


# Feather Icons SVG for Steep entity types
# Source: https://feathericons.com/
# Icons are base64-encoded as required by SYNQ API

# bar-chart-2 icon for metrics
_METRIC_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
_METRIC_ICON = base64.b64encode(_METRIC_SVG.encode("utf-8")).decode("utf-8")

# box icon for entities
_ENTITY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>'
_ENTITY_ICON = base64.b64encode(_ENTITY_SVG.encode("utf-8")).decode("utf-8")

# folder icon for modules
_MODULE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>'
_MODULE_ICON = base64.b64encode(_MODULE_SVG.encode("utf-8")).decode("utf-8")


STEEP_METRIC_TYPE = Type(
    type_id=EntityTypeId.METRIC,
    name="Steep Metric",
    svg_icon=_METRIC_ICON,
)

STEEP_ENTITY_TYPE = Type(
    type_id=EntityTypeId.ENTITY,
    name="Steep Entity",
    svg_icon=_ENTITY_ICON,
)

STEEP_MODULE_TYPE = Type(
    type_id=EntityTypeId.MODULE,
    name="Steep Module",
    svg_icon=_MODULE_ICON,
)

ALL_STEEP_TYPES: tuple[Type, ...] = (
    STEEP_METRIC_TYPE,
    STEEP_ENTITY_TYPE,
    STEEP_MODULE_TYPE,
)
