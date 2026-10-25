"""Negative lineage/split fixtures; no preparation workflow is invoked."""
import copy
import pytest

from src.data.semantic_provenance import validate_feature_metadata
from src.semantic_pipeline.config import load_config, DEFAULT_CONFIG
from src.semantic_pipeline.integrity import validate_partition_graph, validate_table_links
from src.semantic_pipeline.authorization import ExecutionDenied
from src.semantic_pipeline.workflow import prepare, preflight


def fixture():
    entities = [
        dict(component_id="g0", namespace="n0", split="train", account_id="a0", vpa_id="a@upi"),
        dict(component_id="g0", namespace="n0", split="train", account_id="b0", vpa_id="b@upi"),
        dict(component_id="g1", namespace="n1", split="validation", account_id="a1", vpa_id="c@upi"),
        dict(component_id="g1", namespace="n1", split="validation", account_id="b1", vpa_id="d@upi"),
    ]
    events = [
        dict(event_id="e0", history_namespace="n0", event_seq=0, event_time_utc_us=1767225600000000,
             source_vpa_id="a@upi", beneficiary_vpa_id="b@upi", amount_paise=100),
        dict(event_id="e1", history_namespace="n1", event_seq=0, event_time_utc_us=1768521600000000,
             source_vpa_id="c@upi", beneficiary_vpa_id="d@upi", amount_paise=100),
    ]
    return entities, events


def test_literal_entity_graph_and_chronology():
    entities, events = fixture()
    validate_partition_graph(entities, events, load_config(DEFAULT_CONFIG))


@pytest.mark.parametrize("corruption", ["alias", "counterparty", "namespace", "future", "duplicate"])
def test_independent_graph_or_temporal_corruption(corruption):
    entities, events = fixture()
    if corruption == "alias":
        entities[2]["account_id"] = "a0"
    elif corruption == "counterparty":
        events[1]["beneficiary_vpa_id"] = "b@upi"
    elif corruption == "namespace":
        entities[2]["namespace"] = "n0"
    elif corruption == "future":
        events[0]["event_time_utc_us"] = events[1]["event_time_utc_us"]
    else:
        events.append(copy.deepcopy(events[0]))
    with pytest.raises(ValueError):
        validate_partition_graph(entities, events, load_config(DEFAULT_CONFIG))


def test_label_row_links_and_leakage_column_rejection():
    from src.data.semantic_provenance import feature_metadata
    rows = [dict(event_id="e0", namespace="n0", event_seq=0,
                 values=[1., 0, 0, 1])]
    labels = [dict(event_id="e0", target=1)]
    validate_table_links(rows, labels, ["e0"], feature_metadata())
    with pytest.raises(ValueError):
        validate_table_links([dict(rows[0], fraud_label=1)], labels, ["e0"], feature_metadata())
    with pytest.raises(ValueError):
        validate_table_links(rows, [dict(event_id="other", target=1)], ["e0"], feature_metadata())
    with pytest.raises(ValueError):
        validate_table_links(rows, labels, ["e0", "e0"], feature_metadata())
    with pytest.raises(ValueError):
        validate_feature_metadata(dict(feature_metadata(), extractor_source_digest="bad"))


@pytest.mark.parametrize("function", [preflight, prepare])
def test_no_production_preflight_or_preparation_in_implementation_scope(function, tmp_path):
    with pytest.raises(ExecutionDenied):
        function(load_config(DEFAULT_CONFIG), execution_id="no", root=tmp_path, permit=None)
    assert list(tmp_path.iterdir()) == []
