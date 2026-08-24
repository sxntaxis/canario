import importlib.util
from pathlib import Path


PROOF = Path(__file__).resolve().parents[1] / "notebook/implementation/prove_processor_codex_001.py"
spec = importlib.util.spec_from_file_location("prove_processor_codex_001", PROOF)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_table_metrics_match_research_semantics_for_padding_and_false_cells():
    expected = [["ALCALDÍA", "601420299", "BIENVENIDO VENEGAS PORRAS", "PUSC"]]

    padded = module._table_metrics(
        [{"rows": [["ALCALDÍA", "601420299", "BIENVENIDO VENEGAS PORRAS", "PUSC", ""]]}],
        expected,
    )
    assert padded["exact_row_recall"] == 1.0
    assert padded["cell_fidelity"] == 1.0
    assert padded["false_cell_count"] == 0

    extra_content = module._table_metrics(
        [{"rows": [["ALCALDÍA", "601420299", "BIENVENIDO VENEGAS PORRAS", "PUSC", "EXTRA"]]}],
        expected,
    )
    assert extra_content["exact_row_recall"] == 1.0
    assert extra_content["cell_fidelity"] == 1.0
    assert extra_content["false_cell_count"] == 1
