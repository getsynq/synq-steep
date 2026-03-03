import json

import httpx
import pytest
import respx

from synq_steep.clients.synq import SynqClient
from synq_steep.models.synq import (
    Annotation,
    CustomIdentifier,
    EntityTypeId,
    Relationship,
    SynqEntity,
    Type,
)


class TestSynqClientAuthentication:
    @respx.mock
    def test_authenticate_exchanges_credentials_for_token(self) -> None:
        client = SynqClient(
            client_id="test-client-id",
            client_secret="test-client-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-access-token", "token_type": "bearer"},
            )
        )

        token = client.authenticate()

        assert token == "test-access-token"

    @respx.mock
    def test_authenticate_sends_client_credentials(self) -> None:
        client = SynqClient(
            client_id="my-client-id",
            client_secret="my-client-secret",
            host="developer.synq.io",
        )

        route = respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "token_type": "bearer"},
            )
        )

        client.authenticate()

        assert route.called
        request = route.calls[0].request
        assert b"client_id=my-client-id" in request.content
        assert b"client_secret=my-client-secret" in request.content
        assert b"grant_type=client_credentials" in request.content

    @respx.mock
    def test_authenticate_handles_invalid_credentials(self) -> None:
        client = SynqClient(
            client_id="invalid",
            client_secret="invalid",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(401, json={"error": "invalid_client"})
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.authenticate()

        assert exc_info.value.response.status_code == 401


class TestSynqClientUpsertEntity:
    @respx.mock
    def test_upsert_entity_sends_correct_request(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/entities"
        ).mock(return_value=httpx.Response(200, json={}))

        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test123"),
            name="Test Metric",
            type_id=EntityTypeId.METRIC,
            annotations=[Annotation(name="category", values=["Test"])],
        )

        client.authenticate()
        client.upsert_entity(entity)

        assert upsert_route.called
        request = upsert_route.calls[0].request
        assert request.headers["Authorization"] == "Bearer test-token"

    @respx.mock
    def test_upsert_entity_serializes_entity_correctly(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/entities"
        ).mock(return_value=httpx.Response(200, json={}))

        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("abc123"),
            name="My Metric",
            type_id=30,
            description="A test description",
            annotations=[
                Annotation(name="url", values=["https://example.com"]),
            ],
        )

        client.authenticate()
        client.upsert_entity(entity)

        request = upsert_route.calls[0].request
        import json

        body = json.loads(request.content)

        assert body["entity"]["id"]["custom"]["id"] == "steep::metric::abc123"
        assert body["entity"]["name"] == "My Metric"
        assert body["entity"]["typeId"] == 30

    @respx.mock
    def test_upsert_entity_handles_error(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(400, json={"error": "Invalid entity"})
        )

        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test"),
            name="Test",
            type_id=EntityTypeId.METRIC,
        )

        client.authenticate()
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.upsert_entity(entity)

        assert exc_info.value.response.status_code == 400

    @respx.mock
    def test_upsert_entity_requires_authentication(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        entity = SynqEntity(
            id=CustomIdentifier.for_steep_metric("test"),
            name="Test",
            type_id=EntityTypeId.METRIC,
        )

        with pytest.raises(RuntimeError, match="Not authenticated"):
            client.upsert_entity(entity)


class TestSynqClientUpsertType:
    @respx.mock
    def test_upsert_type_sends_correct_request(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/types"
        ).mock(return_value=httpx.Response(200, json={}))

        custom_type = Type(
            type_id=30,
            name="Steep Metric",
            svg_icon="<svg></svg>",
            description="A custom metric type",
        )

        client.authenticate()
        client.upsert_type(custom_type)

        assert upsert_route.called
        request = upsert_route.calls[0].request
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Content-Type"] == "application/json"

    @respx.mock
    def test_upsert_type_serializes_type_correctly(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/types"
        ).mock(return_value=httpx.Response(200, json={}))

        custom_type = Type(
            type_id=30,
            name="Steep Metric",
            svg_icon="<svg></svg>",
            description="A custom metric type",
        )

        client.authenticate()
        client.upsert_type(custom_type)

        request = upsert_route.calls[0].request
        body = json.loads(request.content)

        assert body["type"]["typeId"] == 30
        assert body["type"]["name"] == "Steep Metric"
        assert body["type"]["svgIcon"] == "<svg></svg>"
        assert body["type"]["description"] == "A custom metric type"

    @respx.mock
    def test_upsert_type_omits_none_description(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/types"
        ).mock(return_value=httpx.Response(200, json={}))

        custom_type = Type(
            type_id=31,
            name="Steep Entity",
            svg_icon="<svg></svg>",
        )

        client.authenticate()
        client.upsert_type(custom_type)

        request = upsert_route.calls[0].request
        body = json.loads(request.content)

        assert "description" not in body["type"]

    @respx.mock
    def test_upsert_type_handles_error(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(400, json={"error": "Invalid type"})
        )

        custom_type = Type(
            type_id=30,
            name="Test",
            svg_icon="<svg></svg>",
        )

        client.authenticate()
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.upsert_type(custom_type)

        assert exc_info.value.response.status_code == 400

    @respx.mock
    def test_upsert_type_requires_authentication(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        custom_type = Type(
            type_id=30,
            name="Test",
            svg_icon="<svg></svg>",
        )

        with pytest.raises(RuntimeError, match="Not authenticated"):
            client.upsert_type(custom_type)


class TestSynqClientUpsertRelationships:
    @respx.mock
    def test_upsert_relationships_sends_correct_request(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        relationships = [
            Relationship(
                upstream=CustomIdentifier.for_steep_metric("metric1"),
                downstream=CustomIdentifier.for_steep_entity("entity1"),
            ),
        ]

        client.authenticate()
        client.upsert_relationships(relationships)

        assert upsert_route.called
        request = upsert_route.calls[0].request
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Content-Type"] == "application/json"

    @respx.mock
    def test_upsert_relationships_serializes_batch_correctly(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        relationships = [
            Relationship(
                upstream=CustomIdentifier.for_steep_metric("metric1"),
                downstream=CustomIdentifier.for_steep_entity("entity1"),
            ),
            Relationship(
                upstream=CustomIdentifier.for_steep_module("module1"),
                downstream=CustomIdentifier.for_steep_metric("metric2"),
            ),
        ]

        client.authenticate()
        client.upsert_relationships(relationships)

        request = upsert_route.calls[0].request
        body = json.loads(request.content)

        assert len(body["relationships"]) == 2
        assert (
            body["relationships"][0]["upstream"]["custom"]["id"]
            == "steep::metric::metric1"
        )
        assert (
            body["relationships"][0]["downstream"]["custom"]["id"]
            == "steep::entity::entity1"
        )
        assert (
            body["relationships"][1]["upstream"]["custom"]["id"]
            == "steep::module::module1"
        )
        assert (
            body["relationships"][1]["downstream"]["custom"]["id"]
            == "steep::metric::metric2"
        )

    @respx.mock
    def test_upsert_relationships_handles_empty_list(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        client.authenticate()
        client.upsert_relationships([])

        assert upsert_route.called
        request = upsert_route.calls[0].request
        body = json.loads(request.content)
        assert body["relationships"] == []

    @respx.mock
    def test_upsert_relationships_handles_error(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(
            return_value=httpx.Response(400, json={"error": "Invalid relationships"})
        )

        relationships = [
            Relationship(
                upstream=CustomIdentifier.for_steep_metric("metric1"),
                downstream=CustomIdentifier.for_steep_entity("entity1"),
            ),
        ]

        client.authenticate()
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.upsert_relationships(relationships)

        assert exc_info.value.response.status_code == 400

    @respx.mock
    def test_upsert_relationships_requires_authentication(self) -> None:
        client = SynqClient(
            client_id="test-client",
            client_secret="test-secret",
            host="developer.synq.io",
        )

        relationships = [
            Relationship(
                upstream=CustomIdentifier.for_steep_metric("metric1"),
                downstream=CustomIdentifier.for_steep_entity("entity1"),
            ),
        ]

        with pytest.raises(RuntimeError, match="Not authenticated"):
            client.upsert_relationships(relationships)
