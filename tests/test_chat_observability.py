from __future__ import annotations

import json
import asyncio
import re
from pathlib import Path

import httpx

from app import logging_config
from app.main import agent
from app.main import app
from app.agent import AgentResult
from app.pii import hash_user_id


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/chat",
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Explain observability",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]
    assert response_event["ttft_ms"] == response.json()["ttft_ms"]
    assert response_event["tool_name"] == "retrieval"
    assert response_event["tool_success"] is True


def test_request_id_and_safe_context_are_shared_across_response_and_logs(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    agent_calls = []

    def fake_run(**kwargs) -> AgentResult:
        agent_calls.append(kwargs)
        return AgentResult(
            answer="Safe answer",
            latency_ms=10,
            ttft_ms=2,
            tokens_in=1,
            tokens_out=2,
            cost_usd=0.0,
            quality_score=0.8,
        )

    monkeypatch.setattr(
        agent,
        "run",
        fake_run,
    )

    async def send_requests() -> list[httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            responses = []
            for request_id in ("req-abcdef12", "invalid-id", None):
                headers = {"x-request-id": request_id} if request_id else {}
                responses.append(
                    await client.post(
                        "/chat",
                        headers=headers,
                        json={
                            "user_id": "student@example.com",
                            "session_id": "session-0901234567",
                            "feature": "qa",
                            "message": "CCCD 012345678901, card 4111 1111 1111 1111",
                        },
                    )
                )
            return responses

    responses = asyncio.run(send_requests())
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 6
    ids = []
    for response, request_log, response_log, agent_call in zip(
        responses, records[::2], records[1::2], agent_calls
    ):
        assert response.status_code == 200
        request_id = response.headers["x-request-id"]
        assert re.fullmatch(r"req-[0-9a-fA-F]{8}", request_id)
        assert response.json()["correlation_id"] == request_id
        assert float(response.headers["x-response-time-ms"]) >= 0
        assert request_log["correlation_id"] == response_log["correlation_id"] == request_id
        assert agent_call["correlation_id"] == request_id
        for record in (request_log, response_log):
            assert record["user_id_hash"] == hash_user_id("student@example.com")
            assert record["session_id"] == "session-[REDACTED_PHONE_VN]"
            assert record["feature"] == "qa"
            assert record["model"] == agent.model
            assert "env" in record
        ids.append(request_id)

    assert ids[0] == "req-abcdef12"
    assert len(set(ids)) == 3
    raw_logs = log_path.read_text(encoding="utf-8")
    for pii in ("student@example.com", "0901234567", "012345678901", "4111 1111 1111 1111"):
        assert pii not in raw_logs
