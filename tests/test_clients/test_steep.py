import httpx
import pytest
import respx

from synq_steep.clients.steep import SteepClient


class TestSteepClientLiveMode:
    @respx.mock
    def test_get_metrics_from_api(self) -> None:
        client = SteepClient(
            base_url="https://api.steep.app",
            token="test-token",
        )

        respx.get("https://api.steep.app/v1/metrics").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total": 1,
                    "limit": 100,
                    "skip": 0,
                    "data": [
                        {
                            "id": "metric1",
                            "identifier": "test_metric",
                            "label": "Test Metric",
                            "description": "A test metric",
                            "link": "https://steep.app/metric1",
                            "isPrivate": False,
                            "isUnlisted": False,
                            "updatedAt": "2024-01-01T00:00:00Z",
                            "dimensions": None,
                            "module": None,
                            "slices": None,
                            "cohort": None,
                            "owners": None,
                            "category": None,
                            "timeResampling": None,
                            "timeGrains": None,
                            "filters": None,
                        }
                    ],
                },
            )
        )

        metrics = client.get_metrics()

        assert len(metrics) == 1
        assert metrics[0].id == "metric1"

    @respx.mock
    def test_get_metrics_sends_bearer_token(self) -> None:
        client = SteepClient(
            base_url="https://api.steep.app",
            token="my-secret-token",
        )

        route = respx.get("https://api.steep.app/v1/metrics").mock(
            return_value=httpx.Response(
                200,
                json={"total": 0, "limit": 100, "skip": 0, "data": []},
            )
        )

        client.get_metrics()

        assert route.called
        request = route.calls[0].request
        assert request.headers["Authorization"] == "ApiKey my-secret-token"

    @respx.mock
    def test_get_metrics_with_expand_param(self) -> None:
        client = SteepClient(
            base_url="https://api.steep.app",
            token="test-token",
        )

        route = respx.get("https://api.steep.app/v1/metrics").mock(
            return_value=httpx.Response(
                200,
                json={"total": 0, "limit": 100, "skip": 0, "data": []},
            )
        )

        client.get_metrics(expand=True)

        assert route.called
        request = route.calls[0].request
        assert "expand=true" in str(request.url)

    @respx.mock
    def test_handles_rate_limit_error(self) -> None:
        client = SteepClient(
            base_url="https://api.steep.app",
            token="test-token",
        )

        respx.get("https://api.steep.app/v1/metrics").mock(
            return_value=httpx.Response(429, json={"message": "Too many requests"})
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.get_metrics()

        assert exc_info.value.response.status_code == 429

    @respx.mock
    def test_handles_unauthorized_error(self) -> None:
        client = SteepClient(
            base_url="https://api.steep.app",
            token="invalid-token",
        )

        respx.get("https://api.steep.app/v1/metrics").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.get_metrics()

        assert exc_info.value.response.status_code == 401
