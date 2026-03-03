from synq_steep.models.steep import SteepModule
from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    EntityTypeId,
    Identifier,
    Relationship,
    SnowflakeIdentifier,
    SynqEntity,
)


class ModuleTransformer:
    def transform(self, module: SteepModule) -> SynqEntity:
        name = module.label if module.label else module.identifier
        annotations = self._build_annotations(module)

        return SynqEntity(
            id=CustomIdentifier.for_steep_module(module.id),
            name=name[:100],
            type_id=EntityTypeId.MODULE,
            description=module.description,
            annotations=annotations,
        )

    def _build_annotations(self, module: SteepModule) -> list[Annotation]:
        annotations: list[Annotation] = [
            Annotation(name="identifier", values=[module.identifier]),
            Annotation(name="schema", values=[module.schema_]),
            Annotation(name="table", values=[module.table]),
        ]

        if module.external_source:
            annotations.append(Annotation(name="externalSource", values=[module.external_source]))

        return annotations

    def to_relationships(
        self,
        module: SteepModule,
        snowflake_account: str | None = None,
        snowflake_database: str | None = None,
    ) -> list[Relationship]:
        """Generate relationships for a module.

        When snowflake_account and snowflake_database are both provided,
        creates a relationship where:
        - upstream: the Snowflake table (using module's schema and table)
        - downstream: the Steep module

        Returns empty list if Snowflake config is not provided.
        """
        if snowflake_account is None or snowflake_database is None:
            return []

        return [
            Relationship(
                upstream=SnowflakeIdentifier.for_snowflake_table(
                    account=snowflake_account,
                    database=snowflake_database,
                    schema=module.schema_,
                    table=module.table,
                ),
                downstream=Identifier.for_steep_module(module.id),
            )
        ]
