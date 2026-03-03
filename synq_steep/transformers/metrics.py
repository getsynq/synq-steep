from synq_steep.models.steep import SteepMetric
from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    EntityTypeId,
    Relationship,
    SynqEntity,
)


class MetricTransformer:
    def transform(self, metric: SteepMetric) -> SynqEntity:
        annotations = self._build_annotations(metric)

        return SynqEntity(
            id=CustomIdentifier.for_steep_metric(metric.id),
            name=metric.label[:100],
            type_id=EntityTypeId.METRIC,
            description=metric.description,
            annotations=annotations,
        )

    def _build_annotations(self, metric: SteepMetric) -> list[Annotation]:
        annotations: list[Annotation] = []

        annotations.append(Annotation(name="url", values=[metric.link]))
        annotations.append(Annotation(name="identifier", values=[metric.identifier]))

        if metric.category:
            annotations.append(Annotation(name="category", values=[metric.category]))

        if metric.owners:
            annotations.append(Annotation(name="owners", values=metric.owners))

        if metric.module:
            annotations.append(Annotation(name="schema", values=[metric.module.schema_]))
            annotations.append(Annotation(name="table", values=[metric.module.table]))

        return annotations

    def to_relationships(self, metric: SteepMetric) -> list[Relationship]:
        """Generate relationships for a metric.

        If the metric has a module, creates a relationship where:
        - upstream: the module
        - downstream: the metric

        Returns empty list if no module is present.
        """
        if metric.module is None:
            return []

        return [
            Relationship(
                upstream=CustomIdentifier.for_steep_module(metric.module.id),
                downstream=CustomIdentifier.for_steep_metric(metric.id),
            )
        ]
