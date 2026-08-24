# Cyrisk CCM

> **Offline, payload-blind adapter from supplied CCM Core v0.1.0 reference metadata to Cyrisk input candidates and coverage gaps—not a CCM deployment, cloud collector, evidence store, control evaluator, or risk calculation.**

`cyrisk-ccm` consumes an explicitly supplied, narrow projection of version-pinned CCM Core records.
It preserves stable IDs, hashes, status, severity, coverage percentage, and references while
rejecting raw payloads and unsupported schema versions. It deterministically classifies each input
as a candidate or a coverage gap.

| Input projection | Output | Boundary |
|---|---|---|
| CCM evidence metadata | Evidence-reference candidate or gap | Does not retrieve or inspect payloads. |
| CCM assessment metadata | Scenario-input candidate or gap | Does not evaluate controls or calculate risk. |
| Missing/incompatible data | Ordered coverage gap | Does not replace missing information with a pass. |

The adapter is pinned to [`ccm-core` v0.1.0](https://github.com/kingsokafor777-droid/ccm-core/releases/tag/v0.1.0)
commit `95f62735a4ad05b2205c398781e9f78592cbe121` and supports only `ccm.core/v1`.

## Boundary

This package does not connect to CCM, AWS, Azure, PostgreSQL, or a cloud account. It does not
collect evidence, validate source truth, interpret a control, calibrate a factor, generate a loss
range, determine compliance, approve an assumption, or make a risk decision. A candidate is merely
an attributable input for downstream human review.
