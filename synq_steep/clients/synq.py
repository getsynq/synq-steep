from typing import Self
import httpx
import msgspec

from synq_steep.models.synq import (
    Relationship,
    SynqEntity,
    SynqUpsertRequest,
    Type,
    UpsertRelationshipsRequest,
    UpsertTypeRequest,
)


class SynqClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        host: str = "developer.synq.io",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.host = host
        self._access_token: str | None = None
        self._client = httpx.Client(timeout=30.0)

    def authenticate(self) -> str | None:
        response = self._client.post(
            f"https://{self.host}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        return self._access_token

    def upsert_entity(self, entity: SynqEntity) -> None:
        if self._access_token is None:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        request = SynqUpsertRequest(entity=entity)
        body = msgspec.json.encode(request)

        response = self._client.post(
            f"https://{self.host}/api/entities/custom/v1/entities",
            content=body,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

    def upsert_type(self, type: Type) -> None:
        if self._access_token is None:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        request = UpsertTypeRequest(type=type)
        body = msgspec.json.encode(request)

        response = self._client.post(
            f"https://{self.host}/api/entities/custom/v1/types",
            content=body,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

    def upsert_relationships(self, relationships: list[Relationship]) -> None:
        if self._access_token is None:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        request = UpsertRelationshipsRequest(relationships=relationships)
        body = msgspec.json.encode(request)

        response = self._client.post(
            f"https://{self.host}/api/entities/custom/v1/relationships",
            content=body,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
