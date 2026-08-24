# Architecture

The adapter takes a caller-supplied `AdapterRequest` with payload-blind evidence and assessment
projections. It validates the exact CCM Core schema version, then emits lexically ordered candidates
and gaps. The output is hash-bound to the supplied records; it has no remote transport or storage.

| Condition | Result |
|---|---|
| A sealed evidence reference and an assessed control with nonzero coverage exist. | Candidate reference with provenance. |
| Evidence is missing, assessment is `not_assessed`, coverage is zero, or integrity metadata is unavailable. | Explicit coverage gap. |
| Schema does not equal `ccm.core/v1`. | Fail-closed validation error. |

The adapter never translates a CCM pass/fail/partial outcome into a financial conclusion.
