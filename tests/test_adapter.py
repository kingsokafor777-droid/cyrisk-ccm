from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cyrisk_ccm.adapter import adapt
from cyrisk_ccm.cli import main
from cyrisk_ccm.models import (
    AdapterRequest,
    AssessmentStatus,
    CandidateMapping,
    CCMAssessmentReference,
    CCMEvidenceReference,
    Completeness,
    Confidence,
    TechnicalUnit,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def evidence(
    identifier: str = "evidence_one", expires_at: str | None = None
) -> CCMEvidenceReference:
    return CCMEvidenceReference(
        evidence_id=identifier,
        kind="configuration",
        collected_at="2026-08-01T00:00:00Z",
        expires_at=expires_at,
        payload_hash=HASH_A,
        content_hash=HASH_A,
        reference_locator="synthetic://ccm/evidence_one",
    )


def assessment(
    identifier: str = "assessment_one",
    status: AssessmentStatus = AssessmentStatus.PARTIAL,
    coverage: int = 50,
    evidence_ids: tuple[str, ...] = ("evidence_one",),
    evidence_hashes: tuple[str, ...] = (HASH_A,),
) -> CCMAssessmentReference:
    return CCMAssessmentReference(
        assessment_id=identifier,
        control_id="control_one",
        status=status,
        assessed_at="2026-08-01T00:00:00Z",
        coverage_percent=coverage,
        evidence_ids=evidence_ids,
        evidence_hashes=evidence_hashes,
    )


def mapping(identifier: str = "candidate_one", field: str = "coverage_percent") -> CandidateMapping:
    unit = TechnicalUnit.PERCENT if field == "coverage_percent" else TechnicalUnit.COUNT
    if field == "assessment_status":
        unit = TechnicalUnit.BOOLEAN
    return CandidateMapping(
        assessment_id="assessment_one",
        candidate_id=identifier,
        source_field=field,  # type: ignore[arg-type]
        unit=unit,
        confidence=Confidence.DECLARED_MEDIUM,
        completeness=Completeness.DECLARED_BOUNDED,
        limitation="Synthetic metadata must be reviewed before downstream use.",
    )


def request(**overrides: object) -> AdapterRequest:
    payload: dict[str, object] = {
        "as_of": "2026-08-15T00:00:00Z",
        "evidence_references": (evidence(),),
        "assessment_references": (assessment(),),
        "mappings": (mapping(),),
    }
    payload.update(overrides)
    return AdapterRequest(**payload)  # type: ignore[arg-type]


def test_adapts_sealed_reference_to_candidate_with_stable_manifest() -> None:
    first = adapt(request())
    second = adapt(request())
    assert first == second
    assert first.manifest_hash is not None
    assert first.coverage_gaps == ()
    assert first.candidates[0].value == 50
    assert first.candidates[0].candidate_hash is not None
    assert "do not establish" in first.limitation


@pytest.mark.parametrize(
    ("field", "expected"),
    [("evidence_count", 1), ("assessment_status", "partial")],
)
def test_adapts_each_declared_nonfinancial_field(field: str, expected: int | str) -> None:
    result = adapt(request(mappings=(mapping(field=field),)))
    assert result.candidates[0].value == expected


@pytest.mark.parametrize(
    ("inputs", "expected_code"),
    [
        ({"assessment_references": ()}, "assessment_unavailable"),
        ({"assessment_references": (assessment(coverage=0),)}, "zero_coverage"),
        ({"evidence_references": ()}, "missing_evidence_reference"),
        (
            {"evidence_references": (evidence(expires_at="2026-08-14T00:00:00Z"),)},
            "expired_evidence_reference",
        ),
        (
            {"assessment_references": (assessment(evidence_hashes=(HASH_B,)),)},
            "hash_noncorrespondence",
        ),
        (
            {"assessment_references": (assessment(status=AssessmentStatus.NOT_ASSESSED),)},
            "assessment_unavailable",
        ),
        (
            {"assessment_references": (assessment(status=AssessmentStatus.ERROR),)},
            "assessment_unavailable",
        ),
    ],
)
def test_emits_explicit_gaps_for_unusable_supplied_metadata(
    inputs: dict[str, object], expected_code: str
) -> None:
    result = adapt(request(**inputs))
    assert result.candidates == ()
    assert result.coverage_gaps[0].code.value == expected_code


def test_sorts_candidate_and_gap_outputs() -> None:
    result = adapt(
        request(
            mappings=(mapping("candidate_z"), mapping("candidate_a")),
        )
    )
    assert [item.candidate_id for item in result.candidates] == ["candidate_a", "candidate_z"]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "evidence_id": "evidence_one",
            "kind": "configuration",
            "collected_at": "2026-08-01T00:00:00Z",
            "payload_hash": "not-a-hash",
            "content_hash": HASH_A,
            "reference_locator": "synthetic://reference",
        },
        {
            "evidence_id": "evidence_one",
            "kind": "configuration",
            "collected_at": "2026-08-01T00:00:00Z",
            "payload_hash": HASH_A,
            "content_hash": HASH_A,
            "reference_locator": "synthetic://reference",
            "raw_payload": "forbidden",
        },
    ],
)
def test_rejects_invalid_or_raw_evidence_payloads(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        CCMEvidenceReference(**payload)


def test_rejects_duplicate_ids_and_unsupported_schema() -> None:
    with pytest.raises(ValidationError, match="evidence_id values must be unique"):
        request(evidence_references=(evidence(), evidence()))
    with pytest.raises(ValidationError):
        AdapterRequest.model_validate({**request().model_dump(), "schema_version": "ccm.core/v2"})


def test_cli_is_local_json_in_json_out(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(request().model_dump_json(), encoding="utf-8")
    assert main([str(input_path), str(output_path)]) == 0
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["candidates"][0]["candidate_id"] == "candidate_one"
