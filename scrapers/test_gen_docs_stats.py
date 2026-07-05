import pytest

from gen_docs_stats import mcp_tool_signatures, replace_block


def test_replace_block_swaps_only_marked_region():
    text = "head\n<!-- gen:x:begin -->\nold\n<!-- gen:x:end -->\ntail"
    out = replace_block(text, "x", "new body")
    assert "old" not in out
    assert "new body" in out
    assert out.startswith("head\n") and out.endswith("\ntail")


def test_replace_block_missing_marker_raises():
    with pytest.raises(SystemExit):
        replace_block("no markers here", "x", "body")


def test_mcp_tool_signatures_parses_defaults_and_multiline():
    src = (
        "@mcp.tool()\n"
        "def dataset_overview() -> dict:\n"
        "    ...\n"
        "@mcp.tool()\n"
        "def race_benchmark(race_key: str, finish_time: str, result_label: str = None,\n"
        "                   age_band: str = None) -> dict:\n"
        "    ...\n"
    )
    assert mcp_tool_signatures(src) == [
        "dataset_overview()",
        "race_benchmark(race_key, finish_time, result_label?, age_band?)",
    ]
