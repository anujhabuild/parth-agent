"""Model picker always exposes Parth Agent rows."""
from parth.constants.providers import PROVIDER_PARTH_AGENT
from parth.tui.model_modal import model_picker_rows, _BUILTIN_PARTH_ROWS


def test_model_picker_rows_always_includes_parth_agent():
    rows = model_picker_rows()
    parth = [(src, mid) for src, mid, _ in rows if src == PROVIDER_PARTH_AGENT]
    assert len(parth) >= len(_BUILTIN_PARTH_ROWS)
    assert rows[0][0] == PROVIDER_PARTH_AGENT
    assert rows[0][1] == "deepseek-v4-flash-free"
