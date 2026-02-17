from pathlib import Path

import httpx
import msgspec

from synq_steep.models.steep import SteepEntity, SteepMetric, SteepModule


class PaginatedResponse[T](msgspec.Struct):
    total: int
    limit: int
    skip: int
    data: list[T]


class SteepClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        mock_dir: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.mock_dir = mock_dir
        self._client = httpx.Client(
            headers={"Authorization": f"ApiKey {token}"},
            timeout=30.0,
        )

    def get_metrics(self, expand: bool = False) -> list[SteepMetric]:
        if self.mock_dir:
            return self._load_mock_metrics()
        return self._fetch_metrics(expand)

    def get_entities(self) -> list[SteepEntity]:
        if self.mock_dir:
            return self._load_mock_entities()
        return self._fetch_entities()

    def get_modules(self) -> list[SteepModule]:
        if self.mock_dir:
            return self._load_mock_modules()
        return self._fetch_modules()

    def _load_mock_metrics(self) -> list[SteepMetric]:
        assert self.mock_dir is not None
        data = (self.mock_dir / "metrics.json").read_bytes()
        metric = msgspec.json.decode(data, type=SteepMetric)
        return [metric]

    def _load_mock_entities(self) -> list[SteepEntity]:
        assert self.mock_dir is not None
        data = (self.mock_dir / "entities.json").read_bytes()
        entity = msgspec.json.decode(data, type=SteepEntity)
        return [entity]

    def _load_mock_modules(self) -> list[SteepModule]:
        assert self.mock_dir is not None
        data = (self.mock_dir / "modules.json").read_bytes()
        modules = msgspec.json.decode(data, type=list[SteepModule])
        return modules

    def _fetch_metrics(self, expand: bool) -> list[SteepMetric]:
        params = {"expand": "true" if expand else "false"}
        response = self._client.get(f"{self.base_url}/v1/metrics", params=params)
        response.raise_for_status()
        result = msgspec.json.decode(
            response.content,
            type=PaginatedResponse[SteepMetric],
        )
        return result.data

    def _fetch_entities(self) -> list[SteepEntity]:
        response = self._client.get(f"{self.base_url}/v1/entities")
        response.raise_for_status()
        result = msgspec.json.decode(
            response.content,
            type=PaginatedResponse[SteepEntity],
        )
        return result.data

    def _fetch_modules(self) -> list[SteepModule]:
        response = self._client.get(f"{self.base_url}/v1/modules")
        response.raise_for_status()
        result = msgspec.json.decode(
            response.content,
            type=PaginatedResponse[SteepModule],
        )
        return result.data

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SteepClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
