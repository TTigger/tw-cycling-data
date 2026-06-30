import os
import build_manifest

DOC = os.path.join(os.path.dirname(__file__), "..", "docs", "API.md")


def test_api_doc_lists_every_endpoint_and_license():
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    assert "CC-BY-4.0" in text or "CC BY 4.0" in text
    for ep in build_manifest.ENDPOINTS:
        assert ep["path"] in text, f"API.md missing endpoint {ep['path']}"
