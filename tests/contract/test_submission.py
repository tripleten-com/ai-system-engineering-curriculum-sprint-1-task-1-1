"""Coldline — Task 1.1.

===================

File:              tests/contract/test_submission.py
Component:         Contract tests — Test Submission
Purpose:           Tests for the public Task 1.1 answer and path checks.
Interacts With:    Published interfaces and repository boundaries
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Compatibility, ownership, export safety
Tools:             Python 3.12, pytest
"""

from pathlib import Path

import pytest
import yaml

from tests.contract.submission_validation import (
    SubmissionError,
    main,
    validate_baseline,
    validate_changed_paths,
    validate_submission,
)

ROOT = Path(__file__).parents[2]


def valid_answers() -> dict[str, object]:
    """Return a complete fictional answer sheet unrelated to Coldline outcomes."""
    return {
        "answers": {
            "runtime_state": "ready",
            "scenario_id": "fictional-orientation-scenario",
            "active_ports": ["Retriever"],
            "trace_reference": "0123456789abcdef0123456789abcdef",
            "observation": "The fictional request produced a visible service response and trace.",
            "unresolved_gap": "Background work was outside this fictional example.",
            "fidelity_limitation": (
                "This local fictional run does not prove managed-service or production behavior."
            ),
        }
    }


def test_complete_answer_shape_passes_public_validation(tmp_path: Path) -> None:
    """A complete direct-answer mapping must pass syntax and schema validation."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        """answers:
  runtime_state: ready
  scenario_id: fictional-orientation-scenario
  active_ports: [Retriever]
  trace_reference: 0123456789abcdef0123456789abcdef
  observation: The fictional request produced a visible service response and trace.
  unresolved_gap: Background work was outside this fictional example.
  fidelity_limitation: This local fictional run does not prove managed-service behavior.
""",
        encoding="utf-8",
    )

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_blank_template_fails_with_field_address(tmp_path: Path) -> None:
    """An untouched answer sheet must identify an incomplete field."""
    submission = tmp_path / "submission.yaml"
    submission.write_text((ROOT / "submission.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(SubmissionError, match="answers.active_ports"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    """A syntactically invalid answer sheet must fail safely."""
    submission = tmp_path / "submission.yaml"
    submission.write_text("answers: [unterminated", encoding="utf-8")

    with pytest.raises(SubmissionError, match="valid YAML"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_unexpected_answer_field_is_rejected(tmp_path: Path) -> None:
    """Fields outside the published direct-answer schema must fail validation."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["repair_hint"] = "not part of Task 1.1"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="Additional properties"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_exact_sample_copy_is_rejected(tmp_path: Path) -> None:
    """The fictional sample must not be accepted as a student submission."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        (ROOT / "submission-sample.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="fictional sample"):
        validate_submission(
            submission,
            ROOT / "docs/contracts/submission.schema.json",
            sample_path=ROOT / "submission-sample.yaml",
        )


def test_only_two_student_paths_are_permitted() -> None:
    """The advisory path gate must reject a protected source change."""
    validate_changed_paths(["submission.yaml", "docs/student/task-1-1-baseline.md"])

    with pytest.raises(SubmissionError, match="src/api"):
        validate_changed_paths(["src/api/routes.py"])


def test_untouched_baseline_markers_are_rejected(tmp_path: Path) -> None:
    """The public verifier must require both student-owned artifacts."""
    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text(
        (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="template markers"):
        validate_baseline(baseline)


def test_completed_baseline_passes_structure_validation(tmp_path: Path) -> None:
    """The verifier must not grade the content of completed evidence prose."""
    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text("# Evidence\n\nObserved runtime evidence.\n", encoding="utf-8")

    validate_baseline(baseline)


def test_public_entrypoint_reports_an_incomplete_answer_sheet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Catch a verifier entrypoint that skips the real submission contract."""
    (tmp_path / "docs/contracts").mkdir(parents=True)
    (tmp_path / "submission.yaml").write_text(
        (ROOT / "submission.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "submission-sample.yaml").write_text(
        (ROOT / "submission-sample.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "docs/contracts/submission.schema.json").write_text(
        (ROOT / "docs/contracts/submission.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert main(tmp_path, changed_paths=[]) == 1
    assert "answers.active_ports is incomplete" in capsys.readouterr().err
