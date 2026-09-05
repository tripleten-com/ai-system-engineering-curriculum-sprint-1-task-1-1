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

import json
from pathlib import Path

import pytest
import yaml

from tests.contract.submission_validation import (
    BASELINE_MARKERS,
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
            "active_ports": ["Retriever", "ObjectStore"],
            "architecture_map": {
                "component_1": "worker",
                "component_2": "postgresql",
                "component_3": "api",
                "component_4": "redis-streams",
                "component_5": "prometheus",
                "component_6": "grafana",
                "component_7": "jaeger",
            },
            "api_trace_id": "0123456789abcdef0123456789abcdef",
            "worker_trace_id": "fedcba9876543210fedcba9876543210",
            "evidence_gap": {
                "source_component": "opentelemetry",
                "target_component": "jaeger",
                "connection_type": "telemetry-export",
                "expected_behavior": "same-trace",
                "observed_result": "not-observed",
            },
            "fidelity_limitation": "no-production-scale",
        }
    }


def test_complete_answer_shape_passes_public_validation(tmp_path: Path) -> None:
    """A complete direct-answer mapping must pass syntax and schema validation."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        yaml.safe_dump(valid_answers(), sort_keys=False),
        encoding="utf-8",
    )

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_architecture_map_accepts_each_running_component_once(tmp_path: Path) -> None:
    """The public sheet accepts a complete seven-component map permutation."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(valid_answers()), encoding="utf-8")

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


@pytest.mark.parametrize("invalid_value", ["", "XXX", "not-a-runtime-component"])
def test_architecture_map_rejects_blank_placeholder_and_unknown_values(
    tmp_path: Path, invalid_value: str
) -> None:
    """A numbered component must be a permitted, completed runtime name."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    architecture_map = answer_mapping["architecture_map"]
    assert isinstance(architecture_map, dict)
    architecture_map["component_1"] = invalid_value
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="architecture_map"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_architecture_map_rejects_repeated_component_names(tmp_path: Path) -> None:
    """A map that repeats a component cannot identify all seven services."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    architecture_map = answer_mapping["architecture_map"]
    assert isinstance(architecture_map, dict)
    architecture_map["component_7"] = "api"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="architecture_map"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


@pytest.mark.parametrize("change", ["remove", "add"])
def test_architecture_map_requires_exactly_the_seven_numbered_entries(
    tmp_path: Path, change: str
) -> None:
    """The public map has no optional diagram number or unnumbered entry."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    architecture_map = answer_mapping["architecture_map"]
    assert isinstance(architecture_map, dict)
    if change == "remove":
        architecture_map.pop("component_7")
    else:
        architecture_map["component_8"] = "api"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="architecture_map"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_active_port_values_use_the_visible_code_interface_names(tmp_path: Path) -> None:
    """The public answer vocabulary matches the five PascalCase port interfaces."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["active_ports"] = ["model-provider", "job-queue"]
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="active_ports"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


@pytest.mark.parametrize(
    "active_ports",
    [
        ["ModelProvider"],
        ["ModelProvider", "Retriever", "ObjectStore", "JobQueue", "SecretProvider"],
    ],
)
def test_active_ports_allow_one_to_five_distinct_interface_names(
    tmp_path: Path,
    active_ports: list[str],
) -> None:
    """Students may add or remove bounded active-port list items."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["active_ports"] = active_ports
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


@pytest.mark.parametrize(
    "active_ports",
    [
        [],
        ["ModelProvider", "ModelProvider"],
        [
            "ModelProvider",
            "Retriever",
            "ObjectStore",
            "JobQueue",
            "SecretProvider",
            "ModelProvider",
        ],
    ],
)
def test_active_ports_reject_empty_duplicate_or_unbounded_lists(
    tmp_path: Path,
    active_ports: list[str],
) -> None:
    """The student-visible list remains non-empty, unique, and bounded to five choices."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["active_ports"] = active_ports
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="active_ports"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_template_explains_that_active_port_items_are_variable() -> None:
    """Two placeholders demonstrate list syntax rather than a fixed answer count."""
    template = (ROOT / "submission.yaml").read_text(encoding="utf-8")

    assert "add or remove list items as needed" in template


def test_trace_ids_must_identify_two_different_traces(tmp_path: Path) -> None:
    """API and worker evidence must not reuse one trace identifier."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["worker_trace_id"] = answer_mapping["api_trace_id"]
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="must differ"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_trace_ids_must_be_exactly_32_lowercase_hex_characters(tmp_path: Path) -> None:
    """A terminal newline must not satisfy a regex end-anchor accidentally."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["api_trace_id"] = "0123456789abcdef0123456789abcdef\n"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="api_trace_id"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_evidence_gap_requires_different_expected_and_observed_states(
    tmp_path: Path,
) -> None:
    """A gap must identify a difference rather than a fully met expectation."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    evidence_gap = answer_mapping["evidence_gap"]
    assert isinstance(evidence_gap, dict)
    evidence_gap["observed_result"] = evidence_gap["expected_behavior"]
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="evidence_gap"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_fidelity_limitation_is_a_bounded_enum_without_free_text(tmp_path: Path) -> None:
    """One controlled limitation answer replaces the prior category-plus-explanation pair."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["fidelity_limitation"] = "local-compose-only"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")

    answer_mapping["fidelity_limitation"] = "invented-limit"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="fidelity_limitation"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_template_describes_each_bounded_fidelity_limitation_option() -> None:
    """The worksheet exposes option meanings without asking for a prose limitation."""
    template = (ROOT / "submission.yaml").read_text(encoding="utf-8")
    schema = json.loads(
        (ROOT / "docs/contracts/submission.schema.json").read_text(encoding="utf-8")
    )
    options = schema["properties"]["answers"]["properties"]["fidelity_limitation"]["enum"]

    assert 'fidelity_limitation: ""' in template
    assert "fidelity_limitation: |" not in template
    field_line = '  fidelity_limitation: ""'
    template_lines = template.splitlines()
    assert field_line in template_lines
    field_index = template_lines.index(field_line)
    preceding_comments: list[str] = []
    for line in reversed(template_lines[:field_index]):
        comment = line.strip()
        if not comment.startswith("#"):
            break
        preceding_comments.append(comment)
    preceding_comments.reverse()

    option_comments = [
        comment.removeprefix("# ").partition(": ")
        for comment in preceding_comments
        if ": " in comment
    ]
    assert [option for option, separator, _ in option_comments if separator] == options
    assert all(description for _, separator, description in option_comments if separator)


def test_student_documentation_describes_the_fidelity_limitation_field() -> None:
    """Every student-facing Task guide must direct students to the controlled enum."""
    for documentation in (ROOT / "README.md", ROOT / "docs/student/codebase-guide.md"):
        content = documentation.read_text(encoding="utf-8")

        assert "`fidelity_limitation`" in content


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

    with pytest.raises(SubmissionError, match="restricted YAML"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def _unsafe_answer_sheet(answer_lines: str) -> str:
    """Add shared valid fields around one intentionally unsafe YAML construct."""
    return f"""answers:
{answer_lines}
  evidence_gap:
    source_component: opentelemetry
    target_component: jaeger
    connection_type: telemetry-export
    expected_behavior: same-trace
    observed_result: not-observed
  fidelity_limitation: no-production-scale
"""


@pytest.mark.parametrize(
    "unsafe_text",
    [
        _unsafe_answer_sheet(
            """  runtime_state: ready
  runtime_state: blocked
  scenario_id: fictional-orientation-scenario
  active_ports: [Retriever, ObjectStore]
  api_trace_id: 0123456789abcdef0123456789abcdef
  worker_trace_id: fedcba9876543210fedcba9876543210"""
        ),
        _unsafe_answer_sheet(
            """  runtime_state: ready
  scenario_id: fictional-orientation-scenario
  active_ports: [Retriever, ObjectStore]
  api_trace_id: 0123456789abcdef0123456789abcdef
  worker_trace_id: fedcba9876543210fedcba9876543210"""
        ).replace("answers:", "answers: &answers", 1),
        "answers: *missing\n",
        _unsafe_answer_sheet(
            """  <<: {runtime_state: ready}
  scenario_id: fictional-orientation-scenario
  active_ports: [Retriever, ObjectStore]
  api_trace_id: 0123456789abcdef0123456789abcdef
  worker_trace_id: fedcba9876543210fedcba9876543210"""
        ),
        _unsafe_answer_sheet(
            """  runtime_state: ready
  scenario_id: 2026-09-04
  active_ports: [Retriever, ObjectStore]
  api_trace_id: 0123456789abcdef0123456789abcdef
  worker_trace_id: fedcba9876543210fedcba9876543210"""
        ),
        _unsafe_answer_sheet(
            """  runtime_state: !custom ready
  scenario_id: fictional-orientation-scenario
  active_ports: [Retriever, ObjectStore]
  api_trace_id: 0123456789abcdef0123456789abcdef
  worker_trace_id: fedcba9876543210fedcba9876543210"""
        ),
    ],
    ids=["duplicate-key", "anchor", "alias", "merge-key", "timestamp", "custom-tag"],
)
def test_non_json_yaml_constructs_are_rejected(tmp_path: Path, unsafe_text: str) -> None:
    """The answer sheet accepts plain JSON-compatible YAML data only."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(unsafe_text, encoding="utf-8")

    with pytest.raises(SubmissionError, match="restricted YAML"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_multiple_yaml_documents_are_rejected(tmp_path: Path) -> None:
    """The restricted profile permits exactly one answer mapping document."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        f"{yaml.safe_dump(valid_answers(), sort_keys=False)}---\nanswers: {{}}\n",
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="exactly one YAML mapping"):
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


def _complete_baseline(template: str) -> str:
    """Fill every narrative placeholder the way a finished student document would."""
    return template.replace("_Write your evidence here._", "Observed runtime evidence.")


def test_untouched_baseline_markers_are_rejected(tmp_path: Path) -> None:
    """The public verifier must require the remaining narrative sections."""
    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text(
        (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="template markers"):
        validate_baseline(baseline)


@pytest.mark.parametrize(
    "narrative_section",
    [
        "Architecture orientation",
        "Baseline trace narrative",
        "Evidence gap and fidelity limit",
    ],
)
def test_each_untouched_narrative_marker_is_rejected(
    tmp_path: Path, narrative_section: str
) -> None:
    """Leaving any single remaining narrative section untouched must still fail."""
    template = (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8")
    assert f"## {narrative_section}" in template

    completed = _complete_baseline(template)
    heading_index = completed.index(f"## {narrative_section}")
    marker_index = completed.index("Observed runtime evidence.", heading_index)
    restored = (
        completed[:marker_index]
        + "_Write your evidence here._"
        + completed[marker_index + len("Observed runtime evidence.") :]
    )

    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text(restored, encoding="utf-8")

    with pytest.raises(SubmissionError, match="template markers"):
        validate_baseline(baseline)


def test_baseline_template_carries_no_second_architecture_map() -> None:
    """Students answer the architecture map in `submission.yaml`, not the baseline document."""
    template = (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8")

    assert "## Architecture map" not in template
    assert "_Create your concise map here._" not in template
    assert "_Create your concise map here._" not in BASELINE_MARKERS


def test_former_architecture_map_marker_is_not_required(tmp_path: Path) -> None:
    """A leftover map placeholder must no longer block a completed narrative."""
    template = (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8")

    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text(
        _complete_baseline(template) + "\n" + "_Create your concise map here._" + "\n",
        encoding="utf-8",
    )

    validate_baseline(baseline)


def test_completed_baseline_without_architecture_map_passes_structure_validation(
    tmp_path: Path,
) -> None:
    """A filled template that carries no architecture map passes structural validation."""
    template = (ROOT / "docs/student/task-1-1-baseline.md").read_text(encoding="utf-8")
    completed = _complete_baseline(template)
    assert "## Architecture map" not in completed

    baseline = tmp_path / "task-1-1-baseline.md"
    baseline.write_text(completed, encoding="utf-8")

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
