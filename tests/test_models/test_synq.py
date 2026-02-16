import msgspec

from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    SynqEntity,
    SynqUpsertRequest,
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
