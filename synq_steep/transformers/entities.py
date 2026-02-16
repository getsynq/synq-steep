from synq_steep.models.steep import SteepEntity
from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    EntityTypeId,
    Identifier,
    Relationship,
    SynqEntity,
)


class EntityTransformer:
    def transform(self, entity: SteepEntity) -> SynqEntity:
        annotations = self._build_annotations(entity)

        return SynqEntity(
            id=CustomIdentifier.for_steep_entity(entity.id),
            name=entity.name[:100],
            type_id=EntityTypeId.ENTITY,
            annotations=annotations,
        )

    def _build_annotations(self, entity: SteepEntity) -> list[Annotation]:
        return [
            Annotation(name="moduleId", values=[entity.module_id]),
            Annotation(name="createdAt", values=[entity.created_at]),
            Annotation(name="updatedAt", values=[entity.updated_at]),
        ]

    def to_relationships(self, entity: SteepEntity) -> list[Relationship]:
        """Generate relationships for an entity.

        Creates a relationship where:
        - upstream: the module (referenced by module_id)
        - downstream: the entity
        """
        return [
            Relationship(
                upstream=Identifier.for_steep_module(entity.module_id),
                downstream=Identifier.for_steep_entity(entity.id),
            )
        ]
