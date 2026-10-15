# Dependency and application security review

Review date: 2026-10-15. Scope: synthetic, loopback-only, single-operator demonstration.
Raw current audit: [dependency-audit.json](dependency-audit.json). No IDs ignored.

## Three findings, two distinct vulnerabilities

| Raw finding | Installed version / active dependency path | Impact and exposure | Compatible correction |
|---|---|---|---|
| 1: PYSEC-2026-2447 / CVE-2025-69872 / GHSA-w8v5-vhqr-4h9v | DVC 3.67.1 → dvc-data 3.18.3 → diskcache 5.6.3 (`>=5.2.1`) | Pickle decoding can execute attacker-controlled code if an attacker can write a cache later read by DVC. DVC actually uses this dependency; the HTTP API exposes no cache upload. Local filesystem compromise remains relevant. | PyPI still publishes 5.6.3 as latest; audit returns no fixed version. No supported upgrade found. |
| 2: same identifiers and description as finding 1 | Same package and dependency path | Exact duplicate in the service response, not a second DiskCache vulnerability. Retained in raw evidence. | Same unresolved correction. |
| 3: PYSEC-2026-3740 / CVE-2026-81726 / GHSA-8mgp-746c-j5xp | Evidently 0.7.23 → nltk 3.10.3 (`>=3.6.7`) | Model import/export helpers can read/write outside pathsec roots when untrusted callers choose paths. Application code uses tabular `DataDriftPreset`, not NLTK model persistence or NLP resources. No API accepts such model paths. Installed dependency remains vulnerable. | Latest PyPI version remains 3.10.3; no fixed version returned. Removing a required transitive dependency or forcing an older vulnerable release is not a compatible correction. |

Sources checked: [DiskCache advisory](https://github.com/advisories/GHSA-w8v5-vhqr-4h9v),
[NLTK advisory](https://github.com/advisories/GHSA-8mgp-746c-j5xp),
[DiskCache release metadata](https://pypi.org/pypi/diskcache/json),
[NLTK release metadata](https://pypi.org/pypi/nltk/json).
`upstream-versions.json` records the live lookup; `dependency-inventory.json` records installed dependency edges.

## Residual risk and decision

Do not consume caches writable by other users, mount shared untrusted cache directories,
accept uploaded models, or enable NLP model loading from untrusted paths. Repository
and runtime write access must remain restricted to the operator. These are operating
constraints, not a verified host ACL guarantee. No exploit payload was run.

The same large environment is currently installed in the API image, so unused vulnerable
packages are present there too. A future supported split of training, monitoring and
serving dependency locks would reduce attack surface; deleting package requirements
without upstream compatibility evidence would conceal the issue. Dependency updates
must regenerate hashes, pass `pip check`, all tests and live service acceptance.

Installed-source inspection confirms `dvc_data/hashfile/state.py` creates links
and hash caches using `dvc_data/hashfile/cache.py`. Its `Disk` subclasses DiskCache's
default serializer and wraps errors, not unsafe deserialization; it sets pickle
protocol 4. The risk is therefore relevant to DVC cache reads, even though normal
hash entries are simple values. Evidently's NLTK imports occur in text descriptors,
word/sentiment features and guards; those paths are not called by this tabular demo.

Security audit exits 1. CI and controlled CD retain a blocking audit with no ignore list.
This RC is not cleared for production. Recheck upstream advisories before publication.

## Code and configuration findings

- Fixed non-ASCII bearer comparison: compare encoded bytes, yielding 401 instead of a TypeError/500. Regression test in `test_target_api.py`.
- Fixed registry version path input: positive numeric IDs only, checked before artifact network access and CLI cache-path construction. Regression includes traversal, absolute paths and shell punctuation.
- Credentials are random and generated once in ignored `.env`; Docker excludes `.env`. Added `.env.*`, private-key and build-output ignore patterns. `release-inventory.json` records history and working-tree scan findings without secret values. This scanner covers known local credentials and selected token/key patterns, not every possible secret.
- API input is strict, finite, bounded and rejects unknown fields. Bodies are capped at 1 MiB including streamed bodies. Prediction events contain counts, not feature values. SQL uses parameters; migration identifiers/passwords use psycopg SQL quoting.
- API database role cannot approve or deploy. Audit UPDATE/DELETE is rejected; this is not tamper-proof against a database owner/superuser, TRUNCATE, host access or backup replacement.
- PostgreSQL owns deployment truth; aliases are reconciled using an outbox. Generation guards protect stale compensation. Approval evidence and registry artifacts assume a trusted operator/registry; hashes are integrity checks, not digital signatures or adversarial supply-chain attestation.
- No enterprise IAM, TLS termination, distributed rate limiting, shared-user isolation, off-host backup/restore certification or clinical validation. MLflow is an unauthenticated trusted local operator endpoint. Never expose this Compose stack publicly.

## GitHub boundary

Target CI runs code on a hosted runner without repository deployment secrets. Manual
CT/CD uses an explicitly labelled operator runner and protected `local-demo` environment.
No fork PR workflow may execute on that runner. Required reviewers and branch/tag
protection must be configured remotely; YAML cannot enforce their existence. Actions
use version tags rather than immutable action SHAs, a remaining supply-chain hardening task.
