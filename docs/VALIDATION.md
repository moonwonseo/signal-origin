# Validation of the publication draft

Executed 12 November 2026 with Python 3.12.0 on macOS arm64. The tested dependency versions are recorded in `requirements-lock.txt`. These checks concern software correctness and publication preparation, not new evidence of market performance.

| Check | Result |
| --- | --- |
| Public test suite | **187 passed**. Synthetic/input-contract tests cover calendar gaps, threshold boundaries, incomplete outcomes, feature timing, training-only scaling, exports, V4 integration, demo consistency and publication-gate failures. |
| Original V4 archive tests | **100 passed**, executed locally against the unchanged extracted archive. This is a new execution, separate from the bundle's archived receipts. The historical fixtures are excluded from public tests. |
| Local port comparison | All 20 annual policy/horizon/fold configurations matched archived labels, eligible origins and feature calculations; all seven model probabilities matched within a maximum absolute difference of **2.672×10⁻¹⁰**. |
| Synthetic demo rebuild | `python scripts/build_demo.py --check` passed with byte-identical HTML in the recorded local environment. |
| Demo browser interaction | **28 selector combinations passed** (2 horizons × 2 policies × 7 scopes), plus outcome reveal/hide/reset and first/last/next-date controls. No page errors or external page requests were recorded. |
| Layout review | Desktop and 390-pixel mobile screenshots inspected. No horizontal mobile overflow was detected. Local screenshots remain excluded from publication. |
| Packaging | Source distribution and wheel built locally. The installed wheel's baseline and V4 entry points were exercised from outside the repository, including the packaged metadata schema. Built archives are local artifacts and are not proposed Git contents. |
| Public-content gate | Explicit allowlist, file hashes, header-only CSV checks, symlink/path rejection and targeted credential scans passed. Exact contents are in `publication_manifest.json`. |

The port comparison used the original reviewed price loader, not the uncorrected candidate CSV. It rebuilt price/weather alignment and freight/label calculations, compared eligibility and labels with saved design tables, and refitted seven matched models for every annual configuration. The check accepted absolute numerical differences up to 10⁻⁷; the observed maximum was much smaller. It is not a bitwise reproduction of the original full run receipts or all derived reports. The private verification script, detailed logs and historical data remain under ignored `_local_import/`.

The in-app browser integration failed during initialization (`Cannot redefine property: process`). UI checks therefore used a separate headless Chrome instance and a temporary profile against a localhost server serving only `demo/`. The reusable check is `scripts/check_browser.py`; its dependency is optional in `requirements-browser.txt`. No existing user browser profile was inspected.

`build_demo.py --check` is an exact-byte check for the recorded local numerical environment. Floating-point fitting may vary slightly across operating systems or numerical libraries. CI tests the committed synthetic payload's internal consistency and runs the Python suite, file gate and build; it does not claim a cross-platform byte-identical refit. The GitHub workflow has been prepared but has not run remotely because nothing has been pushed.

No public commit, tag, GitHub release, hosted site or push was created. Git staging remains empty. Choosing a project license and approving the exact public file set remain owner decisions.
