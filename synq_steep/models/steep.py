from typing import Literal

import msgspec


class SteepModule(msgspec.Struct, rename="camel"):
    id: str
    identifier: str
    table: str
    schema_: str = msgspec.field(name="schema")
    label: str | None = None
    description: str | None = None
    external_source: Literal["dbt-cloud", "cube", "code"] | None = None


class SteepDimension(msgspec.Struct, rename="camel"):
    id: str
    label: str | None
    type: Literal["string-or-boolean", "city", "country", "time", "h3-cell-index"]
    description: str | None


class SteepSliceFilter(msgspec.Struct, rename="camel"):
    column: str
    operator: Literal[
        "equals",
        "not-equals",
        "less-than",
        "less-than-or-equal",
        "greater-than",
        "greater-than-or-equal",
        "in",
        "not-in",
        "is",
        "is-not",
        "like",
        "not-like",
    ]
    expression: str


class SteepSlice(msgspec.Struct, rename="camel"):
    id: str
    label: str
    filter: SteepSliceFilter | None
    description: str | None = None


class SteepCohort(msgspec.Struct, rename="camel"):
    delta_time_calculation_type: Literal["calendar-periods", "rolling-periods"]
    time: str
    label: str | None = None
    calculate_retention: bool | None = None
    time_grains: list[Literal["daily", "weekly", "monthly", "quarterly", "yearly"]] | None = None


class SteepMetric(msgspec.Struct, rename="camel"):
    id: str
    identifier: str
    label: str
    description: str | None
    link: str
    is_private: bool
    is_unlisted: bool
    updated_at: str
    dimensions: list[SteepDimension] | None
    module: SteepModule | None
    slices: list[SteepSlice] | None
    cohort: SteepCohort | None
    owners: list[str] | None
    category: str | None
    time_resampling: Literal["sum/divide", "average/repeat"] | None
    time_grains: list[Literal["daily", "weekly", "monthly", "quarterly", "yearly"]] | None
    filters: list[SteepSliceFilter] | None

    calculation: str | None = None
    value: str | None = None
    numerator: str | None = None
    denominator: str | None = None
    numerator_sql: str | None = None
    denominator_sql: str | None = None
    numerator_metric_id: str | None = None
    denominator_metric_id: str | None = None
    sql_expression: str | None = None
    distinct_on: str | None = None
    format: Literal["number", "percentage"] | None = None


class SteepEntity(msgspec.Struct, rename="camel"):
    id: str
    name: str
    module_id: str
    created_at: str
    updated_at: str
