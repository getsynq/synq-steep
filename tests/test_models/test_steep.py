import msgspec

from synq_steep.models.steep import (
    SteepEntity,
    SteepMetric,
    SteepModule,
)


class TestSteepModule:
    def test_module_roundtrip(self, modules_json: bytes) -> None:
        modules = msgspec.json.decode(modules_json, type=list[SteepModule])
        module = modules[0]
        encoded = msgspec.json.encode(module)
        decoded = msgspec.json.decode(encoded, type=SteepModule)

        assert decoded == module


class TestSteepEntity:
    def test_entity_roundtrip(self, entities_json: bytes) -> None:
        entity = msgspec.json.decode(entities_json, type=SteepEntity)
        encoded = msgspec.json.encode(entity)
        decoded = msgspec.json.decode(encoded, type=SteepEntity)

        assert decoded == entity


class TestSteepMetric:
    def test_metric_roundtrip(self, metrics_json: bytes) -> None:
        metric = msgspec.json.decode(metrics_json, type=SteepMetric)
        encoded = msgspec.json.encode(metric)
        decoded = msgspec.json.decode(encoded, type=SteepMetric)

        assert decoded == metric
