# ADR 0001: Use offline version-pinned projections

**Status:** Accepted

The first release consumes a small explicit projection of released CCM Core v0.1.0 metadata rather
than importing a live service client or accepting arbitrary payloads. This preserves reproducible
tests and makes incompatibility visible. A future adapter version must be added deliberately with
its own source/target compatibility tests; it must not silently broaden this contract.
