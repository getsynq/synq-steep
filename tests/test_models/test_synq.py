import pytest
import msgspec

from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    Relationship,
    SnowflakeIdentifier,
    SnowflakeTableId,
    SynqEntity,
    SynqUpsertRequest,
    UpsertRelationshipsRequest,
)


class TestCustomIdentifier:
    def test_create_steep_metric_identifier(self) -> None:
        identifier = CustomIdentifier.for_steep_metric("abc123")

        assert identifier.custom.id == "steep::metric::abc123"

    def test_create_steep_entity_identifier(self) -> None:
        identifier = CustomIdentifier.for_steep_entity("xyz789")

        assert identifier.custom.id == "steep::entity::xyz789"

    def test_create_steep_module_identifier(self) -> None:
        identifier = CustomIdentifier.for_steep_module("mod456")

        assert identifier.custom.id == "steep::module::mod456"

    def test_identifier_serializes_correctly(self) -> None:
        identifier = CustomIdentifier.for_steep_metric("test")
        encoded = msgspec.json.encode(identifier)
        decoded = msgspec.json.decode(encoded)

        assert decoded == {"custom": {"id": "steep::metric::test"}}


class TestAnnotation:
    def test_create_annotation_with_single_value(self) -> None:
        annotation = Annotation(name="category", values=["Rides"])

        assert annotation.name == "category"
        assert annotation.values == ["Rides"]

    def test_create_annotation_with_multiple_values(self) -> None:
        annotation = Annotation(name="owners", values=["owner1", "owner2", "owner3"])

        assert len(annotation.values) == 3

    def test_annotation_serializes_correctly(self) -> None:
        annotation = Annotation(name="url", values=["https://example.com"])
        encoded = msgspec.json.encode(annotation)
        decoded = msgspec.json.decode(encoded)

        assert decoded == {"name": "url", "values": ["https://example.com"]}


class TestSynqEntity:
    def test_create_entity_with_required_fields(self) -> None:
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test123"),
            name="Test Metric",
            type_id=30,
        )

        assert entity.name == "Test Metric"
        assert entity.id.custom.id == "steep::metric::test123"
        assert entity.type_id == 30

    def test_create_entity_with_all_fields(self) -> None:
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test123"),
            name="Test Metric",
            type_id=30,
            description="A test metric description",
            annotations=[
                Annotation(name="category", values=["Test"]),
                Annotation(name="url", values=["https://example.com"]),
            ],
        )

        assert entity.type_id == 30
        assert entity.description == "A test metric description"
        assert entity.annotations and len(entity.annotations) == 2

    def test_name_truncation_to_100_chars(self) -> None:
        long_name = "x" * 150
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test"),
            name=long_name[:100],
            type_id=30,
        )

        assert len(entity.name) == 100

    def test_entity_serializes_correctly(self) -> None:
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test123"),
            name="Test Metric",
            type_id=30,
            annotations=[Annotation(name="category", values=["Test"])],
        )
        encoded = msgspec.json.encode(entity)
        decoded = msgspec.json.decode(encoded)

        assert decoded["id"]["custom"]["id"] == "steep::metric::test123"
        assert decoded["name"] == "Test Metric"
        assert decoded["typeId"] == 30


class TestSynqUpsertRequest:
    def test_create_upsert_request(self) -> None:
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test"),
            name="Test",
            type_id=30,
        )
        request = SynqUpsertRequest(entity=entity)

        assert request.entity == entity

    def test_upsert_request_serializes_correctly(self) -> None:
        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test"),
            name="Test Metric",
            type_id=30,
        )
        request = SynqUpsertRequest(entity=entity)
        encoded = msgspec.json.encode(request)
        decoded = msgspec.json.decode(encoded)

        assert "entity" in decoded
        assert decoded["entity"]["name"] == "Test Metric"


class TestSnowflakeTableId:
    def test_create_snowflake_table_id(self) -> None:
        table_id = SnowflakeTableId(
            account="abcd",
            database="MART",
            schema="myschema",
            table="mytable",
        )

        assert table_id.account == "abcd"
        assert table_id.database == "MART"
        assert table_id.schema == "myschema"
        assert table_id.table == "mytable"

    def test_serializes_correctly(self) -> None:
        table_id = SnowflakeTableId(
            account="abcd",
            database="MART",
            schema="myschema",
            table="mytable",
        )
        encoded = msgspec.json.encode(table_id)
        decoded = msgspec.json.decode(encoded)

        assert decoded == {
            "account": "abcd",
            "database": "MART",
            "schema": "myschema",
            "table": "mytable",
        }

    def test_is_frozen(self) -> None:
        table_id = SnowflakeTableId(
            account="abcd",
            database="MART",
            schema="myschema",
            table="mytable",
        )

        with pytest.raises(AttributeError):
            table_id.account = "other"  # type: ignore[misc]


class TestSnowflakeIdentifier:
    def test_create_via_factory(self) -> None:
        identifier = SnowflakeIdentifier.for_snowflake_table(
            account="abcd",
            database="MART",
            schema="myschema",
            table="mytable",
        )

        assert identifier.snowflake_table.account == "abcd"
        assert identifier.snowflake_table.database == "MART"
        assert identifier.snowflake_table.schema == "myschema"
        assert identifier.snowflake_table.table == "mytable"

    def test_serializes_with_camel_case_key(self) -> None:
        identifier = SnowflakeIdentifier.for_snowflake_table(
            account="abcd",
            database="MART",
            schema="myschema",
            table="mytable",
        )
        encoded = msgspec.json.encode(identifier)
        decoded = msgspec.json.decode(encoded)

        assert decoded == {
            "snowflakeTable": {
                "account": "abcd",
                "database": "MART",
                "schema": "myschema",
                "table": "mytable",
            }
        }

    def test_json_key_is_snowflake_table_not_snake_case(self) -> None:
        identifier = SnowflakeIdentifier.for_snowflake_table(
            account="x", database="Y", schema="z", table="t",
        )
        raw = msgspec.json.encode(identifier).decode("utf-8")

        assert "snowflakeTable" in raw
        assert "snowflake_table" not in raw


class TestRelationshipWithSnowflakeUpstream:
    def test_relationship_with_snowflake_upstream_serializes(self) -> None:
        relationship = Relationship(
            upstream=SnowflakeIdentifier.for_snowflake_table(
                account="abcd",
                database="MART",
                schema="PUBLIC",
                table="TRIPS_FACT",
            ),
            downstream=CustomIdentifier.for_steep_module("trips_fact_table"),
        )
        encoded = msgspec.json.encode(relationship)
        decoded = msgspec.json.decode(encoded)

        assert "snowflakeTable" in decoded["upstream"]
        assert decoded["upstream"]["snowflakeTable"]["account"] == "abcd"
        assert decoded["upstream"]["snowflakeTable"]["database"] == "MART"
        assert decoded["upstream"]["snowflakeTable"]["schema"] == "PUBLIC"
        assert decoded["upstream"]["snowflakeTable"]["table"] == "TRIPS_FACT"
        assert decoded["downstream"]["custom"]["id"] == "steep::module::trips_fact_table"

    def test_relationship_with_custom_upstream_still_works(self) -> None:
        relationship = Relationship(
            upstream=CustomIdentifier.for_steep_module("mod1"),
            downstream=CustomIdentifier.for_steep_metric("metric1"),
        )
        encoded = msgspec.json.encode(relationship)
        decoded = msgspec.json.decode(encoded)

        assert "custom" in decoded["upstream"]
        assert decoded["upstream"]["custom"]["id"] == "steep::module::mod1"

    def test_upsert_request_with_mixed_relationships(self) -> None:
        relationships = [
            Relationship(
                upstream=CustomIdentifier.for_steep_module("mod1"),
                downstream=CustomIdentifier.for_steep_metric("metric1"),
            ),
            Relationship(
                upstream=SnowflakeIdentifier.for_snowflake_table(
                    account="abcd",
                    database="MART",
                    schema="PUBLIC",
                    table="MY_TABLE",
                ),
                downstream=CustomIdentifier.for_steep_module("mod1"),
            ),
        ]
        request = UpsertRelationshipsRequest(relationships=relationships)
        encoded = msgspec.json.encode(request)
        decoded = msgspec.json.decode(encoded)

        assert len(decoded["relationships"]) == 2
        assert "custom" in decoded["relationships"][0]["upstream"]
        assert "snowflakeTable" in decoded["relationships"][1]["upstream"]
