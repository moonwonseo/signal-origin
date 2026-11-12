# Proposed public repository contents

Prepared 12 November 2026 for owner review. **No files have been staged, committed or pushed.** Approval of this exact file set is required before any commit or push. No project-wide open-source license has been assigned.

The working Git repository is the `signal-origin/` child of the active project folder, with origin `https://github.com/moonwonseo/signal-origin.git`. A read-only remote check returned no branch references during preparation.

## Proposed contents: 55 files

| Group | Files | What will be public |
| --- | ---: | --- |
| `signal_origin/` | 17 | Existing baseline methods, isolated V3/V4 calculations, portable entry points, artificial-input generators and packaged metadata schema. |
| `tests/` | 10 | Public tests and fixtures using artificial inputs, including publication-gate failure checks. |
| `demo/` | 2 | Synthetic-only offline viewer and its template. All embedded observations, predictions and scores are artificial. |
| `docs/` | 8 | Methodology, qualitative research status, input contract, provenance, data policy, demo script, validation and this review. |
| `config/`, `schema/` | 6 | Deliberately incomplete configuration/metadata templates and header-only input templates. |
| `scripts/` | 3 | Synthetic demo builder, optional browser checks and public-content gate. |
| Root files and CI | 9 | README, packaging files, pinned requirements, baseline wrapper, exclusions, exact file manifest and a read-only CI workflow. |

The complete path-by-path inventory, byte sizes and SHA-256 hashes are in [`publication_manifest.json`](../publication_manifest.json). The manifest omits its own hash to avoid a circular digest. It is an explicit review allowlist, not a list generated automatically by the publication checker. Editing a reviewed file or adding a new public candidate makes that checker fail until the proposal is deliberately updated and reviewed.

## What stays local

The original 12 November download, its nested V4/prior archives and the original historical HTML are excluded. So are raw or cleaned vendor prices, exchange calendar records, NASA observations, FRED/BLS transcriptions, historical feature tables/predictions/parameters, aggregate output files, figures/screenshots, internal handoffs/prompts, credentials and generated local results. The original download remains in the parent folder's `_local_import/`; extracted audit copies remain in this repository's ignored `_local_import/`.

No data-use permission was inferred from public availability. Uncertain source material was withheld. Dependencies are installed locally and referenced by version rather than copied into the public repository. The synthetic demo is generated mathematically without resampling the historical observations.

## Review evidence

- **187 public tests passed**; **100 original V4 archive tests passed locally**.
- All 20 annual configurations matched archived labels, eligibility and features; maximum model-probability difference was approximately **2.672×10⁻¹⁰**.
- The synthetic viewer rebuilt byte-for-byte locally. All **28 browser selector combinations** and navigation/reveal checks passed; desktop/mobile layouts were inspected.
- The source distribution and wheel were built and checked; installed baseline/V4 commands ran from outside the repository.
- The exact public file gate checks hashes, unexpected candidates, CSV content, unsafe paths/symlinks and common credential formats. Its tests confirm representative failures are rejected.

See [`VALIDATION.md`](VALIDATION.md) for scope and limitations. These checks establish software behavior, not forecasting reliability, legal clearance for excluded data or procurement savings. GitHub CI has not run remotely; no hosted demo or release has been published.

## Approval boundary

Review the README, demo, data policy and exact file manifest. Approval should cover these public contents and the choice to leave licensing undecided. This preparation stops before staging, committing or pushing. A later license or data addition requires a new review of the changed proposal.
