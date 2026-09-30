from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.dashboard import build_dashboard


def test_dashboard_uses_actual_log_events_and_excludes_old_or_invalid_lines(tmp_path: Path) -> None:
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    log_path = tmp_path / "logs.jsonl"
    recent = (now - timedelta(minutes=1)).isoformat()
    old = (now - timedelta(hours=2)).isoformat()
    rows = [
        {"ts": recent, "event": "request_received"},
        {"ts": recent, "event": "request_received"},
        {"ts": recent, "event": "response_sent", "latency_ms": 100, "ttft_ms": 20,
         "cost_usd": 0.01, "tokens_in": 10, "tokens_out": 20,
         "quality_score": 0.9, "tool_success": True},
        {"ts": recent, "event": "request_failed", "error_type": "RuntimeError",
         "tool_success": False},
        {"ts": old, "event": "request_failed", "tool_success": False},
    ]
    log_path.write_text("\n".join(json.dumps(row) for row in rows) + "\ninvalid json\n", encoding="utf-8")

    dashboard = build_dashboard(log_path, now)
    panels = {panel["id"]: panel for panel in dashboard["panels"]}

    assert len(panels) == 6
    assert dashboard["time_range_minutes"] == 60
    assert {item["label"]: item["value"] for item in panels["traffic"]["metrics"]}["Requests"] == 2
    errors = {item["label"]: item["value"] for item in panels["errors"]["metrics"]}
    assert errors["Error rate %"] == 50
    assert errors["Retrieval success %"] == 50
    assert errors["By type"] == "RuntimeError: 1"
    assert {item["label"]: item["value"] for item in panels["latency"]["metrics"]}["TTFT P95"] == 20
    assert panels["cost"]["series"][-1]["value"] == 0.01
    assert panels["tokens"]["series"][-1]["value"] == 30


def test_dashboard_handles_missing_log_file(tmp_path: Path) -> None:
    dashboard = build_dashboard(tmp_path / "missing.jsonl")
    assert len(dashboard["panels"]) == 6
    assert dashboard["panels"][0]["metrics"][0]["value"] is None
