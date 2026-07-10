from core.curated_causal import build_ops_sequence_edges, parse_curated_relations_table


def test_parse_curated_relations_table_accepts_id_headers():
    edges = parse_curated_relations_table(
        "| source_id | relation | target_id | confidence |\n"
        "| --- | --- | --- | --- |\n"
        "| physics.water.freeze | causes | engineering.pipe.crack | 0.9 |\n"
    )
    assert len(edges) == 1
    assert edges[0]["edge_basis"] == "curated_explicit"


def test_ops_sequence_recognizes_practical_domain_metadata_without_priority_filename():
    """_is_practical_ops_file() broadens the priority-filename check: a fact
    curated with metadata.practical_domain is recognized even when its source
    filename doesn't match any PRIORITY_OPS_MARKERS substring."""
    facts = [
        {
            "fact_id": "custom.domain.step_one",
            "type": "METHOD",
            "metadata": {"knowledge_file": "900_CUSTOM_DOMAIN.ru.md", "practical_domain": "custom"},
        },
        {
            "fact_id": "custom.domain.step_two",
            "type": "METHOD",
            "metadata": {"knowledge_file": "900_CUSTOM_DOMAIN.ru.md", "practical_domain": "custom"},
        },
    ]
    edges = build_ops_sequence_edges(facts)
    assert len(edges) == 1
    assert edges[0]["source_id"] == "custom.domain.step_one"
    assert edges[0]["target_id"] == "custom.domain.step_two"
