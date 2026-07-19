from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_community_hub_links_core_paths() -> None:
    hub = (ROOT / "community/README.md").read_text(encoding="utf-8")
    assert "Requests for Mods" in hub
    assert "modding create mod" in hub
    assert "evaluation cases" in hub
    assert "domain reviewer" in hub.lower()


def test_initial_rfm_set_is_complete() -> None:
    content = (ROOT / "community/rfms/README.md").read_text(encoding="utf-8")
    for number in range(1, 6):
        assert f"RFM-{number:03d}" in content
    for heading in ("Problem", "Intended users", "Desired behaviour", "Risks", "Acceptance evidence"):
        assert heading in content


def test_request_for_mod_template_collects_required_evidence() -> None:
    payload = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/request-for-mod.yml").read_text(encoding="utf-8"))
    assert payload["name"] == "Request for Mod"
    ids = {item.get("id") for item in payload["body"] if isinstance(item, dict)}
    assert {"problem", "users", "behaviour", "risks", "evidence", "contribution"}.issubset(ids)


def test_catalogue_references_every_current_mod_and_recipe() -> None:
    catalogue = (ROOT / "community/catalogue.md").read_text(encoding="utf-8")
    for manifest in (ROOT / "mods").glob("**/mod.yaml"):
        name = yaml.safe_load(manifest.read_text(encoding="utf-8"))["name"]
        assert name.replace("-", " ").title() in catalogue
    for manifest in (ROOT / "recipes").glob("**/recipe.yaml"):
        name = yaml.safe_load(manifest.read_text(encoding="utf-8"))["name"]
        assert name.replace("-", " ").title() in catalogue
