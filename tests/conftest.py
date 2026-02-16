from pathlib import Path

import pytest


@pytest.fixture
def mock_data_dir() -> Path:
    return Path(__file__).parent.parent / "v1"


@pytest.fixture
def metrics_json(mock_data_dir: Path) -> bytes:
    return (mock_data_dir / "metrics.json").read_bytes()


@pytest.fixture
def entities_json(mock_data_dir: Path) -> bytes:
    return (mock_data_dir / "entities.json").read_bytes()


@pytest.fixture
def modules_json(mock_data_dir: Path) -> bytes:
    return (mock_data_dir / "modules.json").read_bytes()
