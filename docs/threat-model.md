# Threat Model

| Threat | Example | Mitigation and boundary |
|---|---|---|
| Payload disclosure | Raw CCM evidence crosses to Cyrisk. | Input models accept only IDs, hashes, and metadata. |
| Schema drift | Unknown CCM record shape is silently parsed. | Exact `ccm.core/v1` version gate. |
| False coverage | Missing evidence produces a candidate. | Missing/incomplete input emits a gap. |
| Control overclaim | CCM status becomes loss/probability conclusion. | Output is a candidate, not a quantitative result. |
| Live-operation claim | Adapter is portrayed as a connected system. | No network, provider, or database dependency. |
