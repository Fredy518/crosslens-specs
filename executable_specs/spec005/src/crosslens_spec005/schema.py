"""JSON Schema generation for SPEC-005 Metric Registry contracts."""

from .models import (
    DerivedMetricRuleTable,
    FactRegistryEntry,
    LabelRegistryEntry,
    MetricRegistryEntry,
)

__all__ = [
    "metric_registry_entry_schema",
    "fact_registry_entry_schema",
    "label_registry_entry_schema",
    "derived_metric_rule_table_schema",
]


def _json_schema(model_cls):
    return model_cls.model_json_schema()


metric_registry_entry_schema = _json_schema(MetricRegistryEntry)
fact_registry_entry_schema = _json_schema(FactRegistryEntry)
label_registry_entry_schema = _json_schema(LabelRegistryEntry)
derived_metric_rule_table_schema = _json_schema(DerivedMetricRuleTable)
