"""Tests for scan and clean API endpoints."""


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestScanEndpoint:
    def test_scan_clean_text(self, client):
        resp = client.post("/api/v1/scan", json={"text": "Hello world"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_invisible_chars"] is False
        assert data["total_invisible_count"] == 0
        assert data["findings"] == []

    def test_scan_with_zero_width_space(self, client):
        resp = client.post("/api/v1/scan", json={"text": "Hello\u200Bworld"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_invisible_chars"] is True
        assert data["total_invisible_count"] == 1
        assert data["findings"][0]["char"] == "U+200B"
        assert data["findings"][0]["threat_level"] == "high"

    def test_scan_with_smart_chars(self, client):
        resp = client.post(
            "/api/v1/scan",
            json={"text": "\u201CHello\u201D", "include_smart_chars": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["smart_chars"] is not None
        assert len(data["smart_chars"]) == 2

    def test_scan_smart_chars_default_off(self, client):
        resp = client.post("/api/v1/scan", json={"text": "\u201CHello\u201D"})
        data = resp.json()
        assert data["smart_chars"] is None

    def test_scan_empty_text_rejected(self, client):
        resp = client.post("/api/v1/scan", json={"text": ""})
        assert resp.status_code == 422

    def test_scan_context_present(self, client):
        resp = client.post("/api/v1/scan", json={"text": "Hello\u200Bworld"})
        data = resp.json()
        assert "explanation" in data["context"]
        assert "likely_source" in data["context"]


class TestCleanEndpoint:
    def test_clean_removes_invisible_chars(self, client):
        resp = client.post("/api/v1/clean", json={"text": "Hello\u200Bworld"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["cleaned_text"] == "Helloworld"
        assert data["chars_removed"] == 1

    def test_clean_preserves_clean_text(self, client):
        resp = client.post("/api/v1/clean", json={"text": "Hello world"})
        data = resp.json()
        assert data["cleaned_text"] == "Hello world"
        assert data["chars_removed"] == 0

    def test_clean_normalizes_smart_chars(self, client):
        resp = client.post(
            "/api/v1/clean",
            json={"text": "\u201CHello\u201D", "normalize_smart_chars": True},
        )
        data = resp.json()
        assert data["cleaned_text"] == '"Hello"'
        assert data["chars_removed"] == 2

    def test_clean_smart_chars_preserved_by_default(self, client):
        resp = client.post("/api/v1/clean", json={"text": "\u201CHello\u201D"})
        data = resp.json()
        assert data["cleaned_text"] == "\u201CHello\u201D"

    def test_clean_empty_text_rejected(self, client):
        resp = client.post("/api/v1/clean", json={"text": ""})
        assert resp.status_code == 422

    def test_clean_removals_list(self, client):
        resp = client.post("/api/v1/clean", json={"text": "a\u200Bb\u200Bc"})
        data = resp.json()
        assert len(data["removals"]) == 1
        assert data["removals"][0]["char"] == "U+200B"
        assert data["removals"][0]["count"] == 2
