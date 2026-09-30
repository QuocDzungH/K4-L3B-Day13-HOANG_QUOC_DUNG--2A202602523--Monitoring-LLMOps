from __future__ import annotations

from app import mock_llm


class RecordingClient:
    def __init__(self) -> None:
        self.updates: list[dict] = []

    def update_current_generation(self, **kwargs) -> None:
        self.updates.append(kwargs)


def test_generation_records_model_usage_and_cost_without_raw_prompt(monkeypatch) -> None:
    client = RecordingClient()
    monkeypatch.setattr(mock_llm, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(mock_llm.random, "randint", lambda _low, _high: 100)
    result = mock_llm.FakeLLM.generate.__wrapped__(mock_llm.FakeLLM(), "secret prompt")

    update = client.updates[0]
    assert update["model"] == result.model
    assert update["usage_details"] == {"input": result.usage.input_tokens, "output": 100}
    assert update["cost_details"]["total"] == mock_llm.estimate_cost(result.usage.input_tokens, 100)
    assert "secret prompt" not in str(update)
