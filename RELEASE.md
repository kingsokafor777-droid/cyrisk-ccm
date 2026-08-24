# Release Governance

## Candidate: v0.1.0

| Item | Verified local value |
|---|---|
| Package | `cyrisk-ccm` v0.1.0 |
| Source dependency | `cyrisk-core` commit `4d68f385ef382a6420466dff0196244a2c915f1f` |
| CCM compatibility basis | `ccm-core` v0.1.0 commit `95f62735a4ad05b2205c398781e9f78592cbe121` |
| Input schema gate | `ccm.core/v1` only |
| Adapter output schema | `cyrisk.ccm/v1` |
| Synthetic result fixture SHA-256 | `53cc05b82e2097e6c6b196db0c3c98bc4826f7dc842766332db7fc8357fc0e1e` |
| Wheel SHA-256 | `1c727d5340a973a747032ce5e3736b45cef7d471acf3e543007e24678dd19969` |
| Local quality result | `make check` passed: Ruff, strict mypy, 15 tests, 98.15% branch-aware coverage, wheel check |

Publication remains approval-gated. After explicit approval, the release procedure must create the
public repository, tag the reviewed commit, attach the verified wheel, wait for successful hosted
`Quality`, Python 3.10–3.13, and `Analyze Python` checks, retrieve their exact context names, apply
protected-main policy, and then update the profile and program ledger.

The successful CodeQL workflow is evidence of that workflow only. Repository code-scanning alerts
must not be characterized as empty unless the platform endpoint is accessible and independently
returns that result.
