from core.curated_causal import parse_curated_relations_table


def test_parse_curated_relations_table_accepts_id_headers():
    edges = parse_curated_relations_table(
        "| source_id | relation | target_id | confidence |\n"
        "| --- | --- | --- | --- |\n"
        "| physics.water.freeze | causes | engineering.pipe.crack | 0.9 |\n"
    )
    assert len(edges) == 1
    assert edges[0]["edge_basis"] == "curated_explicit"
