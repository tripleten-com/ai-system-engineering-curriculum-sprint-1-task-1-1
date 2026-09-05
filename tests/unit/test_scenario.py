"""Coldline — Task 1.1.

===================

File:              tests/unit/test_scenario.py
Component:         Unit tests — Published scenario output
Purpose:           Keep one API and worker trace reference in the Task command output
Interacts With:    tests.e2e.scenario
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Deterministic evidence shape
Tools:             Python 3.12, pytest
"""

from __future__ import annotations

import json
from typing import Any

from tests.e2e import scenario


class _Response:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._body


class _Client:
    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def post(self, *_: object, **__: object) -> _Response:
        return _Response({"status_url": "/api/v1/exceptions/example"})


class _TraceClient:
    def get(self, *_: object, **__: object) -> _Response:
        return _Response(
            {
                "data": [
                    {"traceID": "older-trace", "spans": [{"startTime": 10}]},
                    {"traceID": "newer-trace", "spans": [{"startTime": 20}]},
                ]
            }
        )


def test_published_scenario_prints_one_api_and_one_worker_trace_id(monkeypatch, capsys) -> None:
    """Students receive one singular field for each service's trace evidence."""
    monkeypatch.setattr(scenario.httpx, "Client", lambda **_: _Client())
    monkeypatch.setattr(
        scenario,
        "_wait_for_completion",
        lambda *_: {"exception_id": "exception-example", "state": "COMPLETED"},
    )
    monkeypatch.setattr(
        scenario,
        "_wait_for_traces",
        lambda _, service, __: f"{service}-trace-id",
    )

    assert scenario.main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["api_trace_id"] == "coldline-api-trace-id"
    assert output["worker_trace_id"] == "coldline-worker-trace-id"
    assert "api_trace_ids" not in output
    assert "worker_trace_ids" not in output


def test_trace_lookup_selects_the_most_recent_matching_trace() -> None:
    """Repeated local runs still give students one current trace reference."""
    assert (
        scenario._wait_for_traces(_TraceClient(), "coldline-api", "exception-example")
        == "newer-trace"
    )
