from synq_steep.models.steep import SteepModule
from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    EntityTypeId,
    Relationship,
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

    def to_relationships(self, module: SteepModule) -> list[Relationship]:
        """Generate relationships for a module.

        Currently returns empty list as modules don't have upstream
        data source information (e.g., Snowflake account) in the
        current Steep API response.

        Future enhancement: When Snowflake account info is available,
        this could generate upstream relationships to Snowflake tables.
        """
        return []
