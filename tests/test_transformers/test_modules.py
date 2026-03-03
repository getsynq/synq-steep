import msgspec

from synq_steep.models.steep import SteepModule
from synq_steep.transformers.modules import ModuleTransformer


def _make_module(
    id: str = "trips_fact_table",
    identifier: str = "TRIPS_FACT",
    table: str = "TRIPS_FACT",
    schema_: str = "PUBLIC",
) -> SteepModule:
    return SteepModule(
        id=id,
        identifier=identifier,
        table=table,
        schema_=schema_,
    )


class TestModuleTransformerRelationships:
    def test_returns_empty_without_snowflake_config(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module()

        relationships = transformer.to_relationships(module)

        assert relationships == []

    def test_returns_empty_with_only_account(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module()

        relationships = transformer.to_relationships(module, snowflake_account="abcd")

        assert relationships == []

    def test_returns_empty_with_only_database(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module()

        relationships = transformer.to_relationships(module, snowflake_database="MART")

        assert relationships == []

    def test_generates_one_relationship_with_full_config(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module()

        relationships = transformer.to_relationships(
            module,
            snowflake_account="abcd",
            snowflake_database="MART",
        )

        assert len(relationships) == 1

    def test_upstream_is_snowflake_identifier(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module(table="TRIPS_FACT", schema_="PUBLIC")

        relationships = transformer.to_relationships(
            module,
            snowflake_account="abcd",
            snowflake_database="MART",
        )

        encoded = msgspec.json.encode(relationships[0])
        decoded = msgspec.json.decode(encoded)

        assert decoded["upstream"] == {
            "snowflakeTable": {
                "account": "abcd",
                "database": "MART",
                "schema": "PUBLIC",
                "table": "TRIPS_FACT",
            }
        }

    def test_downstream_is_steep_module(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module(id="trips_fact_table")

        relationships = transformer.to_relationships(
            module,
            snowflake_account="abcd",
            snowflake_database="MART",
        )

        encoded = msgspec.json.encode(relationships[0])
        decoded = msgspec.json.decode(encoded)

        assert decoded["downstream"] == {
            "custom": {"id": "steep::module::trips_fact_table"}
        }

    def test_uses_module_schema_and_table(self) -> None:
        transformer = ModuleTransformer()
        module = _make_module(table="MY_RAW_TABLE", schema_="RAW")

        relationships = transformer.to_relationships(
            module,
            snowflake_account="myaccount",
            snowflake_database="ANALYTICS",
        )

        encoded = msgspec.json.encode(relationships[0])
        decoded = msgspec.json.decode(encoded)
        sf = decoded["upstream"]["snowflakeTable"]

        assert sf["schema"] == "RAW"
        assert sf["table"] == "MY_RAW_TABLE"
        assert sf["account"] == "myaccount"
        assert sf["database"] == "ANALYTICS"
