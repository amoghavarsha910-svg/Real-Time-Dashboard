"""
API integration tests for Phase 4 endpoints.

Each test uses the `seeded_client` fixture (in-memory SQLite + seed data)
together with `auth_headers` (admin JWT from seeded admin user).
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------

class TestDataIngest:
    async def test_ingest_valid(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/data/ingest with a known metric returns 201."""
        resp = await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "temperature", "value": 22.5},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["value"] == 22.5
        assert body["status"] in ("normal", "warning", "critical")
        assert "timestamp" in body
        assert "metric_id" in body

    async def test_ingest_unknown_metric(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/data/ingest with unknown metric returns 400."""
        resp = await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "does_not_exist", "value": 1.0},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_ingest_requires_auth(self, seeded_client: AsyncClient):
        """POST /api/data/ingest without token returns 401/403."""
        resp = await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "temperature", "value": 10.0},
        )
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Data history
# ---------------------------------------------------------------------------

class TestDataHistory:
    async def test_history_empty(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/data/history on empty DB returns empty page."""
        resp = await seeded_client.get("/api/data/history", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] == 0

    async def test_history_after_ingest(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """Ingesting a reading makes it appear in history."""
        await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "humidity", "value": 55.0},
            headers=auth_headers,
        )
        resp = await seeded_client.get("/api/data/history", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_history_filter_by_status(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/data/history?status=normal filters correctly."""
        await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "temperature", "value": 20.0},
            headers=auth_headers,
        )
        resp = await seeded_client.get(
            "/api/data/history?status=normal", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["items"]:
            assert item["status"] == "normal"


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

class TestDashboard:
    async def test_summary_empty(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/dashboard/summary works even with no readings."""
        resp = await seeded_client.get(
            "/api/dashboard/summary", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_readings_24h" in body
        assert "active_sources" in body
        assert "active_alerts" in body
        assert "data_rate" in body
        assert "system_status" in body
        assert body["system_status"] in ("normal", "warning", "critical")

    async def test_dashboard_config(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/dashboard/config returns the seeded config."""
        resp = await seeded_client.get(
            "/api/dashboard/config", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "default_time_range" in body
        assert "refresh_interval" in body


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    async def test_list_metrics(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/metrics returns seeded metrics."""
        resp = await seeded_client.get("/api/metrics", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        names = [m["name"] for m in body]
        assert "temperature" in names

    async def test_get_single_metric(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/metrics/{id} returns the metric."""
        metrics_resp = await seeded_client.get("/api/metrics", headers=auth_headers)
        first_id = metrics_resp.json()[0]["id"]
        resp = await seeded_client.get(f"/api/metrics/{first_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == first_id

    async def test_get_metric_not_found(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/metrics/{bad_id} returns 404."""
        resp = await seeded_client.get(
            "/api/metrics/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class TestSources:
    async def test_list_sources(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/sources returns seeded sources."""
        resp = await seeded_client.get("/api/sources", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1

    async def test_create_source(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/sources creates a new source."""
        resp = await seeded_client.post(
            "/api/sources",
            json={"name": "Test Source", "source_type": "simulator"},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["name"] == "Test Source"
        assert "id" in body

    async def test_get_source_not_found(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/sources/{bad_id} returns 404."""
        resp = await seeded_client.get(
            "/api/sources/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Alert rules
# ---------------------------------------------------------------------------

class TestAlerts:
    async def test_list_rules(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/alerts/rules returns seeded rules."""
        resp = await seeded_client.get("/api/alerts/rules", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1

    async def test_create_rule(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/alerts/rules creates a new alert rule."""
        # Get a metric id
        metrics = await seeded_client.get("/api/metrics", headers=auth_headers)
        metric_id = metrics.json()[0]["id"]

        resp = await seeded_client.post(
            "/api/alerts/rules",
            json={
                "name": "Test Rule",
                "metric_id": metric_id,
                "operator": "gt",
                "threshold": 99.0,
                "severity": "warning",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["name"] == "Test Rule"
        assert body["threshold"] == 99.0

    async def test_alert_events_empty(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/alerts/events returns empty list initially."""
        resp = await seeded_client.get("/api/alerts/events", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] == 0


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class TestNotifications:
    async def test_list_notifications_empty(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/notifications returns empty list for fresh user."""
        resp = await seeded_client.get("/api/notifications", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_unread_count(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/notifications/count returns zero for fresh user."""
        resp = await seeded_client.get(
            "/api/notifications/count", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["unread"] == 0

    async def test_notification_created_on_alert(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """Ingesting a value that triggers an alert creates a notification."""
        # temperature > 35.0 triggers "High Temperature" warning
        await seeded_client.post(
            "/api/data/ingest",
            json={"metric_name": "temperature", "value": 40.0},
            headers=auth_headers,
        )
        resp = await seeded_client.get("/api/notifications", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class TestReports:
    async def test_generate_daily_report(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/reports/generate for 'daily' returns report structure."""
        resp = await seeded_client.post(
            "/api/reports/generate",
            json={"type": "daily"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "period" in body
        assert "kpis" in body
        assert "alert_summary" in body
        assert "readings_count" in body

    async def test_generate_custom_report(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """POST /api/reports/generate for 'custom' requires start/end dates."""
        resp = await seeded_client.post(
            "/api/reports/generate",
            json={"type": "custom"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_get_report_by_type(
        self, seeded_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/reports/weekly returns report structure."""
        resp = await seeded_client.get("/api/reports/weekly", headers=auth_headers)
        assert resp.status_code == 200
        assert "period" in resp.json()
