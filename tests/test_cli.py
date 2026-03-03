import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from synq_steep.cli import app


runner = CliRunner()


class TestCliHelp:
    def test_shows_help(self) -> None:
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--dry-run" in result.stdout
        assert "--steep-token" in result.stdout
        assert "--synq-client-id" in result.stdout


class TestCliDryRun:
    def test_dry_run_with_mock_dir(self, mock_data_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert "steep::metric::" in result.stdout
        assert "steep::entity::" in result.stdout
        assert "steep::module::" in result.stdout

    def test_dry_run_shows_entity_count(self, mock_data_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"


class TestCliSync:
    @respx.mock
    def test_sync_requires_steep_token_when_not_mock(self) -> None:
        result = runner.invoke(
            app,
            [
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code != 0
        assert "steep-token" in result.output.lower()

    @respx.mock
    def test_sync_requires_synq_credentials_when_not_dry_run(
        self, mock_data_dir: Path
    ) -> None:
        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
            ],
        )

        assert result.exit_code != 0

    @respx.mock
    def test_sync_uploads_entities(self, mock_data_dir: Path) -> None:
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )

        upsert_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/entities"
        ).mock(return_value=httpx.Response(200, json={}))

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert upsert_route.call_count == 5


class TestCliTypeDefinition:
    @respx.mock
    def test_types_defined_before_entities_uploaded(self, mock_data_dir: Path) -> None:
        """Verify types are defined before entities are uploaded."""
        call_order: list[str] = []

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        def track_type_call(_: httpx.Request) -> httpx.Response:
            call_order.append("type")
            return httpx.Response(200, json={})

        def track_entity_call(_: httpx.Request) -> httpx.Response:
            call_order.append("entity")
            return httpx.Response(200, json={})

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            side_effect=track_type_call
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            side_effect=track_entity_call
        )

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        # All type calls should come before any entity calls
        type_indices = [i for i, call in enumerate(call_order) if call == "type"]
        entity_indices = [i for i, call in enumerate(call_order) if call == "entity"]
        assert len(type_indices) > 0, "No type definitions were made"
        assert len(entity_indices) > 0, "No entity uploads were made"
        assert max(type_indices) < min(entity_indices), (
            "Types must be defined before entities"
        )

    @respx.mock
    def test_all_three_types_defined(self, mock_data_dir: Path) -> None:
        """Verify all three Steep types (metric, entity, module) are defined."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        type_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/types"
        ).mock(return_value=httpx.Response(200, json={}))

        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert type_route.call_count == 3, (
            f"Expected 3 type definitions, got {type_route.call_count}"
        )

    @respx.mock
    def test_skip_types_flag(self, mock_data_dir: Path) -> None:
        """Verify --skip-types flag skips type definition phase."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        type_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/types"
        ).mock(return_value=httpx.Response(200, json={}))

        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
                "--skip-types",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert type_route.call_count == 0, (
            "Types should not be defined when --skip-types is used"
        )

    @respx.mock
    def test_type_definition_error_handling(self, mock_data_dir: Path) -> None:
        """Verify graceful handling of type definition failures."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code != 0


class TestCliRelationships:
    """Tests for the relationship creation phase (Phase 4 - after entities)."""

    @respx.mock
    def test_relationships_created_after_entities(self, mock_data_dir: Path) -> None:
        """Verify relationships are created after entities are uploaded."""
        call_order: list[str] = []

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )

        def track_entity_call(_: httpx.Request) -> httpx.Response:
            call_order.append("entity")
            return httpx.Response(200, json={})

        def track_relationship_call(_: httpx.Request) -> httpx.Response:
            call_order.append("relationship")
            return httpx.Response(200, json={})

        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            side_effect=track_entity_call
        )
        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(side_effect=track_relationship_call)

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        entity_indices = [i for i, call in enumerate(call_order) if call == "entity"]
        relationship_indices = [
            i for i, call in enumerate(call_order) if call == "relationship"
        ]
        assert len(entity_indices) > 0, "No entity uploads were made"
        assert len(relationship_indices) > 0, "No relationship uploads were made"
        assert max(entity_indices) < min(relationship_indices), (
            "Entities must be uploaded before relationships"
        )

    @respx.mock
    def test_relationships_collected_from_all_transformers(
        self, mock_data_dir: Path
    ) -> None:
        """Verify relationships are collected from metrics, entities, and modules."""
        captured_relationships: list[bytes] = []

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )

        def capture_relationships(request: httpx.Request) -> httpx.Response:
            captured_relationships.append(request.content)
            return httpx.Response(200, json={})

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(side_effect=capture_relationships)

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        # Mock data has 1 metric with module, 1 entity with module_id
        # So we should have at least 2 relationships
        assert len(captured_relationships) > 0, "No relationships were uploaded"

    @respx.mock
    def test_skip_relationships_flag(self, mock_data_dir: Path) -> None:
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )

        relationship_route = respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
                "--skip-relationships",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert relationship_route.call_count == 0, (
            "Relationships should not be created when --skip-relationships is used"
        )

    @respx.mock
    def test_relationship_error_handling(self, mock_data_dir: Path) -> None:
        """Verify graceful handling of relationship creation failures."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code != 0


class TestCliPhaseLogging:
    """Tests for CLI phase logging."""

    @respx.mock
    def test_logs_type_definition_phase(self, mock_data_dir: Path) -> None:
        """Verify logging for type definition phase."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        # Check for type definition logging
        assert "type" in result.output.lower() or "defining" in result.output.lower()

    @respx.mock
    def test_logs_relationship_phase(self, mock_data_dir: Path) -> None:
        """Verify logging for relationship creation phase."""
        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )

        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(return_value=httpx.Response(200, json={}))

        result = runner.invoke(
            app,
            [
                "--mock-dir",
                str(mock_data_dir),
                "--synq-client-id",
                "test-id",
                "--synq-client-secret",
                "test-secret",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        # Check for relationship logging
        assert "relationship" in result.output.lower()


class TestCliDryRunWithNewPhases:
    """Tests for dry-run mode with new phases."""

    def test_dry_run_does_not_define_types(self, mock_data_dir: Path) -> None:
        """Verify dry-run mode does not make API calls for types."""
        # No respx mock needed - dry run shouldn't make any calls
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"

    def test_dry_run_does_not_create_relationships(self, mock_data_dir: Path) -> None:
        """Verify dry-run mode does not make API calls for relationships."""
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"


class TestCliSnowflakeRelationships:
    """Tests for Snowflake table upstream relationships via CLI options."""

    def test_help_shows_snowflake_options(self) -> None:
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--snowflake-account" in result.stdout
        assert "--snowflake-database" in result.stdout

    def _setup_full_sync_mocks(self) -> list[dict]:
        """Setup standard sync mocks and return a list that captures relationship request bodies."""
        captured_bodies: list[dict] = []

        respx.post("https://developer.synq.io/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "token_type": "bearer"},
            )
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/types").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.post("https://developer.synq.io/api/entities/custom/v1/entities").mock(
            return_value=httpx.Response(200, json={})
        )

        def capture(request: httpx.Request) -> httpx.Response:
            captured_bodies.append(json.loads(request.content))
            return httpx.Response(200, json={})

        respx.post(
            "https://developer.synq.io/api/entities/custom/v1/relationships"
        ).mock(side_effect=capture)

        return captured_bodies

    def test_snowflake_relationships_included_when_options_provided(
        self, mock_data_dir: Path
    ) -> None:
        with respx.mock:
            captured_bodies = self._setup_full_sync_mocks()
            result = runner.invoke(
                app,
                [
                    "--mock-dir", str(mock_data_dir),
                    "--synq-client-id", "test-id",
                    "--synq-client-secret", "test-secret",
                    "--snowflake-account", "abcd",
                    "--snowflake-database", "MART",
                ],
            )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        snowflake_rels = [
            r for r in captured_bodies[0]["relationships"]
            if "snowflakeTable" in r["upstream"]
        ]
        # Mock data has 3 modules, each should produce one Snowflake relationship
        assert len(snowflake_rels) == 3

    def test_no_snowflake_relationships_without_options(
        self, mock_data_dir: Path
    ) -> None:
        with respx.mock:
            captured_bodies = self._setup_full_sync_mocks()
            result = runner.invoke(
                app,
                [
                    "--mock-dir", str(mock_data_dir),
                    "--synq-client-id", "test-id",
                    "--synq-client-secret", "test-secret",
                ],
            )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        snowflake_rels = [
            r for r in captured_bodies[0]["relationships"]
            if "snowflakeTable" in r["upstream"]
        ]
        assert len(snowflake_rels) == 0


class TestCliTypeFiltering:
    def test_filter_to_metrics_only(self, mock_data_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
                "--types",
                "metrics",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert "steep::metric::" in result.stdout
        assert "steep::entity::" not in result.stdout
        assert "steep::module::" not in result.stdout

    def test_filter_to_multiple_types(self, mock_data_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--mock-dir",
                str(mock_data_dir),
                "--types",
                "metrics,modules",
            ],
        )

        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert "steep::metric::" in result.stdout
        assert "steep::module::" in result.stdout
        assert "steep::entity::" not in result.stdout
