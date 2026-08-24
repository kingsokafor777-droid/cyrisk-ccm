"""Strict, non-financial reference contracts for the offline CCM adapter."""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Final, Literal

from cyrisk_core.canonical import content_hash
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

CCM_CORE_SCHEMA_VERSION: Final = "ccm.core/v1"
ADAPTER_SCHEMA_VERSION: Final = "cyrisk.ccm/v1"
DIGEST_PATTERN: Final = re.compile(r"^[a-f0-9]{64}$")
UTC_TIMESTAMP_PATTERN: Final = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
STABLE_ID_PATTERN: Final = re.compile(r"^[a-z][a-z0-9_]{1,63}$")

StableId = Annotated[str, StringConstraints(pattern=STABLE_ID_PATTERN.pattern)]
UTCDateTime = Annotated[str, StringConstraints(pattern=UTC_TIMESTAMP_PATTERN.pattern)]
NonEmpty = Annotated[str, StringConstraints(min_length=1, max_length=512)]


class StrictModel(BaseModel):
    """Fail closed on unknown data to keep raw evidence out of the adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class AssessmentStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"
    ERROR = "error"


class TechnicalUnit(str, Enum):
    PERCENT = "percent"
    COUNT = "count"
    BOOLEAN = "boolean"


class Confidence(str, Enum):
    DECLARED_LOW = "declared_low"
    DECLARED_MEDIUM = "declared_medium"
    DECLARED_HIGH = "declared_high"


class Completeness(str, Enum):
    DECLARED_PARTIAL = "declared_partial"
    DECLARED_BOUNDED = "declared_bounded"
    DECLARED_COMPLETE_FOR_SCOPE = "declared_complete_for_scope"


class SourceClass(str, Enum):
    CCM_EVIDENCE_REFERENCE = "ccm_evidence_reference"
    CCM_ASSESSMENT_REFERENCE = "ccm_assessment_reference"


class GapCode(str, Enum):
    ASSESSMENT_UNAVAILABLE = "assessment_unavailable"
    ZERO_COVERAGE = "zero_coverage"
    MISSING_EVIDENCE_REFERENCE = "missing_evidence_reference"
    EXPIRED_EVIDENCE_REFERENCE = "expired_evidence_reference"
    HASH_NONCORRESPONDENCE = "hash_noncorrespondence"


class CCMEvidenceReference(StrictModel):
    """A payload-blind projection of a sealed CCM Core evidence record."""

    schema_version: Literal["ccm.core/v1"] = CCM_CORE_SCHEMA_VERSION
    evidence_id: StableId
    kind: NonEmpty
    collected_at: UTCDateTime
    expires_at: UTCDateTime | None = None
    payload_hash: str
    content_hash: str
    reference_locator: NonEmpty

    @field_validator("payload_hash", "content_hash")
    @classmethod
    def require_digest(cls, value: str) -> str:
        if not DIGEST_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase SHA-256 digest")
        return value


class CCMAssessmentReference(StrictModel):
    """A payload-blind projection of a CCM Core assessment, not a control decision."""

    schema_version: Literal["ccm.core/v1"] = CCM_CORE_SCHEMA_VERSION
    assessment_id: StableId
    control_id: StableId
    status: AssessmentStatus
    assessed_at: UTCDateTime
    coverage_percent: int = Field(ge=0, le=100)
    evidence_ids: tuple[StableId, ...]
    evidence_hashes: tuple[str, ...]

    @field_validator("evidence_hashes")
    @classmethod
    def require_digests(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(DIGEST_PATTERN.fullmatch(digest) is None for digest in value):
            raise ValueError("evidence_hashes must be lowercase SHA-256 digests")
        return value


class CandidateMapping(StrictModel):
    """A caller-declared mapping; no confidence, completeness, or limitation is inferred."""

    assessment_id: StableId
    candidate_id: StableId
    source_field: Literal["coverage_percent", "evidence_count", "assessment_status"]
    unit: TechnicalUnit
    source_class: SourceClass = SourceClass.CCM_ASSESSMENT_REFERENCE
    confidence: Confidence
    completeness: Completeness
    limitation: NonEmpty


class AdapterRequest(StrictModel):
    """All inputs are caller supplied; the adapter makes no remote calls."""

    schema_version: Literal["cyrisk.ccm/v1"] = ADAPTER_SCHEMA_VERSION
    as_of: UTCDateTime
    evidence_references: tuple[CCMEvidenceReference, ...]
    assessment_references: tuple[CCMAssessmentReference, ...]
    mappings: tuple[CandidateMapping, ...]

    @field_validator("evidence_references", "assessment_references", "mappings")
    @classmethod
    def require_unique_ids(cls, value: tuple[object, ...]) -> tuple[object, ...]:
        attribute = (
            "evidence_id"
            if value and isinstance(value[0], CCMEvidenceReference)
            else "assessment_id"
        )
        if value and isinstance(value[0], CandidateMapping):
            attribute = "candidate_id"
        values = [str(getattr(item, attribute)) for item in value]
        if len(values) != len(set(values)):
            raise ValueError(f"{attribute} values must be unique")
        return value


class CyriskCandidateInput(StrictModel):
    """Attributable non-financial technical input for downstream human review."""

    schema_version: Literal["cyrisk.ccm/v1"] = ADAPTER_SCHEMA_VERSION
    candidate_id: StableId
    source_assessment_id: StableId
    source_control_id: StableId
    source_evidence_ids: tuple[StableId, ...]
    source_reference_hashes: tuple[str, ...]
    source_class: SourceClass
    source_field: Literal["coverage_percent", "evidence_count", "assessment_status"]
    value: int | str
    unit: TechnicalUnit
    confidence: Confidence
    completeness: Completeness
    limitation: NonEmpty
    candidate_hash: str | None = None

    def seal(self) -> CyriskCandidateInput:
        return self.model_copy(
            update={"candidate_hash": content_hash(self.model_dump(exclude={"candidate_hash"}))}
        )


class CoverageGap(StrictModel):
    """An explicit missing or unsuitable source condition, never a synthetic substitute."""

    schema_version: Literal["cyrisk.ccm/v1"] = ADAPTER_SCHEMA_VERSION
    assessment_id: StableId
    candidate_id: StableId
    code: GapCode
    detail: NonEmpty


class AdapterResult(StrictModel):
    """Deterministic result with an integrity manifest over references and output."""

    schema_version: Literal["cyrisk.ccm/v1"] = ADAPTER_SCHEMA_VERSION
    source_schema_version: Literal["ccm.core/v1"] = CCM_CORE_SCHEMA_VERSION
    candidates: tuple[CyriskCandidateInput, ...]
    coverage_gaps: tuple[CoverageGap, ...]
    limitation: NonEmpty = (
        "Candidates preserve supplied technical metadata only; they do not establish "
        "evidence truth, "
        "control effectiveness, probability, loss, financial exposure, or a risk decision."
    )
    manifest_hash: str | None = None

    def seal(self) -> AdapterResult:
        return self.model_copy(
            update={"manifest_hash": content_hash(self.model_dump(exclude={"manifest_hash"}))}
        )
