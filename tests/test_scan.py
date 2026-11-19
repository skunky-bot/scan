from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_extract_is_bounded_and_authenticated(monkeypatch):
    monkeypatch.setenv("SKUNKY_SERVICE_TOKEN", "local-test")
    payload = {
        "source_id": "fixture",
        "source_url": "https://example.com/",
        "html": '<a href="mailto:info@example.com">Contact</a><script>secret@example.com</script>'
    }
    assert client.post("/v1/extract", json=payload).status_code == 401
    r = client.post("/v1/extract", json=payload, headers={"X-Skunky-Token": "local-test"})
    assert r.status_code == 200
    assert r.json()["emails"] == ["info@example.com"]
    assert r.json()["network_fetched"] is False


def test_oversized_html_is_rejected(monkeypatch):
    monkeypatch.setenv("SKUNKY_SERVICE_TOKEN", "local-test")
    r = client.post("/v1/extract", headers={"X-Skunky-Token": "local-test"}, json={
        "source_id": "fixture", "source_url": "https://example.com/", "html": "x" * 200001
    })
    assert r.status_code == 422
