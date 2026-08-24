"""Pure deterministic adapter logic; intentionally no network, storage, or provider client."""

from __future__ import annotations

from .models import (
    AdapterRequest,
    AdapterResult,
    AssessmentStatus,
    CoverageGap,
    CyriskCandidateInput,
    GapCode,
)


def adapt(request: AdapterRequest) -> AdapterResult:
    """Map declared technical fields or return explicit source-coverage gaps."""

    evidence_by_id = {item.evidence_id: item for item in request.evidence_references}
    candidates: list[CyriskCandidateInput] = []
    gaps: list[CoverageGap] = []
    assessments = {item.assessment_id: item for item in request.assessment_references}

    for mapping in sorted(request.mappings, key=lambda item: item.candidate_id):
        assessment = assessments.get(mapping.assessment_id)
        if assessment is None:
            gaps.append(
                CoverageGap(
                    assessment_id=mapping.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.ASSESSMENT_UNAVAILABLE,
                    detail="The supplied assessment is absent, not assessed, or in error.",
                )
            )
            continue
        unavailable = assessment.status in {
            AssessmentStatus.NOT_ASSESSED,
            AssessmentStatus.ERROR,
        }
        if unavailable:
            gaps.append(
                CoverageGap(
                    assessment_id=mapping.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.ASSESSMENT_UNAVAILABLE,
                    detail="The supplied assessment is absent, not assessed, or in error.",
                )
            )
            continue
        if assessment.coverage_percent == 0:
            gaps.append(
                CoverageGap(
                    assessment_id=assessment.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.ZERO_COVERAGE,
                    detail="The supplied assessment declares zero technical coverage.",
                )
            )
            continue
        evidence = [evidence_by_id.get(identifier) for identifier in assessment.evidence_ids]
        if any(item is None for item in evidence):
            gaps.append(
                CoverageGap(
                    assessment_id=assessment.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.MISSING_EVIDENCE_REFERENCE,
                    detail=(
                        "At least one supplied assessment evidence ID lacks an evidence reference."
                    ),
                )
            )
            continue
        references = [item for item in evidence if item is not None]
        is_expired = any(
            item.expires_at is not None and item.expires_at < request.as_of for item in references
        )
        if is_expired:
            gaps.append(
                CoverageGap(
                    assessment_id=assessment.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.EXPIRED_EVIDENCE_REFERENCE,
                    detail=(
                        "At least one supplied evidence reference is expired at the supplied "
                        "as-of time."
                    ),
                )
            )
            continue
        if tuple(item.content_hash for item in references) != assessment.evidence_hashes:
            gaps.append(
                CoverageGap(
                    assessment_id=assessment.assessment_id,
                    candidate_id=mapping.candidate_id,
                    code=GapCode.HASH_NONCORRESPONDENCE,
                    detail=(
                        "Supplied assessment hashes do not correspond to supplied "
                        "evidence-reference hashes."
                    ),
                )
            )
            continue

        value: int | str
        if mapping.source_field == "coverage_percent":
            value = assessment.coverage_percent
        elif mapping.source_field == "evidence_count":
            value = len(assessment.evidence_ids)
        else:
            value = assessment.status.value
        candidates.append(
            CyriskCandidateInput(
                candidate_id=mapping.candidate_id,
                source_assessment_id=assessment.assessment_id,
                source_control_id=assessment.control_id,
                source_evidence_ids=assessment.evidence_ids,
                source_reference_hashes=assessment.evidence_hashes,
                source_class=mapping.source_class,
                source_field=mapping.source_field,
                value=value,
                unit=mapping.unit,
                confidence=mapping.confidence,
                completeness=mapping.completeness,
                limitation=mapping.limitation,
            ).seal()
        )

    return AdapterResult(
        candidates=tuple(sorted(candidates, key=lambda item: item.candidate_id)),
        coverage_gaps=tuple(sorted(gaps, key=lambda item: (item.candidate_id, item.code.value))),
    ).seal()
