from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
HTML_PATH = Path(__file__).with_name("dashboard.html")


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 2)


def _number(record: dict[str, Any], field: str) -> float | None:
    value = record.get(field)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def _read_records(log_path: Path, now: datetime, minutes: int) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    start = now.replace(second=0, microsecond=0) - timedelta(minutes=minutes - 1)
    records = []
    with log_path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    continue
                timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    continue
                timestamp = timestamp.astimezone(timezone.utc)
            except (json.JSONDecodeError, KeyError, AttributeError, ValueError, TypeError):
                continue
            if start <= timestamp <= now:
                record["_minute"] = timestamp.replace(second=0, microsecond=0)
                records.append(record)
    return records


def build_dashboard(log_path: Path, now: datetime | None = None) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    minutes = config["time_range_minutes"]
    records = _read_records(log_path, now, minutes)
    first_minute = now.replace(second=0, microsecond=0) - timedelta(minutes=minutes - 1)
    buckets: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[record["_minute"]].append(record)
    timeline = [first_minute + timedelta(minutes=index) for index in range(minutes)]

    requests = [record for record in records if record.get("event") == "request_received"]
    responses = [record for record in records if record.get("event") == "response_sent"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latency = [value for record in responses if (value := _number(record, "latency_ms")) is not None]
    ttft = [value for record in responses if (value := _number(record, "ttft_ms")) is not None]
    costs = [value for record in responses if (value := _number(record, "cost_usd")) is not None]
    quality = [value for record in responses if (value := _number(record, "quality_score")) is not None]
    tool_events = [record for record in records if isinstance(record.get("tool_success"), bool)]
    error_counts: dict[str, int] = defaultdict(int)
    for record in failures:
        error_counts[str(record.get("error_type") or "unknown")] += 1

    summary = {
        "latency": [
            ("P50", _percentile(latency, 50)),
            ("P95", _percentile(latency, 95)),
            ("P99", _percentile(latency, 99)),
            ("TTFT P95", _percentile(ttft, 95)),
        ],
        "traffic": [("Requests", len(requests)), ("Rate/min", round(len(requests) / minutes, 2))],
        "errors": [
            ("Error rate %", round(len(failures) / len(requests) * 100, 2) if requests else None),
            ("Errors", len(failures)),
            ("Retrieval success %", round(sum(record["tool_success"] for record in tool_events) / len(tool_events) * 100, 2) if tool_events else None),
            ("By type", ", ".join(f"{key}: {value}" for key, value in sorted(error_counts.items())) or "none"),
        ],
        "cost": [("Total USD", round(sum(costs), 6))],
        "tokens": [
            ("Input", sum(_number(record, "tokens_in") or 0 for record in responses)),
            ("Output", sum(_number(record, "tokens_out") or 0 for record in responses)),
        ],
        "quality": [("Mean", round(sum(quality) / len(quality), 3) if quality else None)],
    }

    def bucket_values(bucket: list[dict[str, Any]], panel_id: str) -> float | None:
        received = [record for record in bucket if record.get("event") == "request_received"]
        sent = [record for record in bucket if record.get("event") == "response_sent"]
        failed = [record for record in bucket if record.get("event") == "request_failed"]
        if panel_id == "latency":
            return _percentile([value for record in sent if (value := _number(record, "latency_ms")) is not None], 95)
        if panel_id == "traffic":
            return float(len(received))
        if panel_id == "errors":
            return round(len(failed) / len(received) * 100, 2) if received else None
        if panel_id == "cost":
            return sum(_number(record, "cost_usd") or 0 for record in sent)
        if panel_id == "tokens":
            return sum((_number(record, "tokens_in") or 0) + (_number(record, "tokens_out") or 0) for record in sent)
        scores = [value for record in sent if (value := _number(record, "quality_score")) is not None]
        return round(sum(scores) / len(scores), 3) if scores else None

    panels = []
    for panel in config["panels"]:
        panel_id = panel["id"]
        cumulative = 0.0
        series = []
        for minute in timeline:
            value = bucket_values(buckets[minute], panel_id)
            if panel_id in {"cost", "tokens"}:
                cumulative += value or 0
                value = round(cumulative, 6 if panel_id == "cost" else 2)
            series.append({"minute": minute.isoformat(), "value": value})
        panels.append(
            {
                "id": panel_id,
                "title": panel["title"],
                "unit": panel["unit"],
                "threshold": panel["threshold"],
                "metrics": [{"label": label, "value": value} for label, value in summary[panel_id]],
                "series": series,
            }
        )

    return {
        "generated_at": now.isoformat(),
        "time_range_minutes": minutes,
        "refresh_seconds": config["refresh_seconds"],
        "source": str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path),
        "panels": panels,
    }
