# Sanitized public release candidate

Version: v2.0.0-rc.1 (package 2.0.0rc1). MIT license confirmed by the owner.
Synthetic data only; not clinically validated; not production-cleared.

## Privacy and technical provenance

This repository starts a new public history from an exported source snapshot.
No original Git objects, authors, committers, annotated tags, signatures,
credentials, virtual environments, local caches, patient data or Docker volumes
are included. The original repository and original release candidate remain
unchanged and private. A private mapping of original/public revisions is retained
outside the tracked files. Public commits and the RC tag use a public GitHub
noreply identity rather than a personal email address.

Retained Phase 4/5 evidence is historical evidence sanitized for publication:
personal paths become generic examples and private source revisions are redacted.
Numeric metrics, dataset/model hashes and results are preserved. Redaction changes
file hashes, so old evidence inventories are historical rather than integrity
attestations of these transformed files. A separate public manifest is generated.
These historical reports must not be represented as runs of the new public commit.
Current public-copy tests and actual remote CI results are recorded separately.

## Security boundary

DiskCache 5.6.3 and NLTK 3.10.3 have unresolved dependency audit findings in the
retained audit. Three raw entries include a duplicated DiskCache advisory: two
distinct vulnerabilities. See ../validation/phase5/SECURITY_REVIEW.md. No advisory
ignore list is enabled. Hosted CI and manual CD retain their blocking audit.
No deployment workflow will be manually triggered for this publication.

## Visual demonstration

No authentic browser captures are asserted. Use ../portfolio/DEMO_SCRIPT.md for
the local URLs and exact capture checklist; inspect interfaces locally and keep
tokens/passwords out of screenshots. Services must remain loopback-only.

## Local public-copy validation

The independent hash-locked environment passed 30 tests, Ruff, scoped Mypy,
pip consistency and the synthetic pipeline on clean public source. See
[LOCAL_VALIDATION.json](LOCAL_VALIDATION.json) and [PRIVACY_AUDIT.json](PRIVACY_AUDIT.json).
Local Docker integration was deliberately not rerun against the original stack;
the hosted target workflow provides an isolated environment for that check.
The RC tag identifies the sanitized, tested source commit. Later main commits
may add publication evidence and CI fixes; the original private RC is unchanged.

## Actual GitHub verification

Repository: https://github.com/AbdGhni/MedMLOps (public; MIT).
The remote repository was cloned independently and all reachable commits, blobs,
identities and the annotated RC tag were audited against the private denylist.
No private matches were found. The original source repository and its RC tag
remain unchanged; its provenance mapping is kept locally and is not published.

| Workflow on the verified main source | Actual result | Run |
|---|---|---|
| Legacy reference | Success | [38742095934](https://github.com/AbdGhni/MedMLOps/actions/runs/38742095934) |
| v2 core verification | Success | [38742095904](https://github.com/AbdGhni/MedMLOps/actions/runs/38742095904) |
| Target platform | Failure at blocking dependency audit; all preceding functional steps passed | [38742095841](https://github.com/AbdGhni/MedMLOps/actions/runs/38742095841) |

The target run successfully installed the hash lock, checked pip/tests/Ruff/Mypy,
trained from clean source, built/started Compose, verified real MLflow artifacts,
executed the end-to-end drift/alert/rollback/persistence scenario and reproduced
DVC outputs. Its only failing step was pip-audit: DiskCache 5.6.3 and NLTK 3.10.3,
three raw entries including the duplicate DiskCache advisory. The audit was not
ignored or disabled. Hosted Ubuntu runners supported these integrations; no
runner limitation was observed in these runs. Manual training and deployment
were not triggered and still require an isolated trusted runner and configured
environment reviewers. No production deployment occurred.

The sanitized RC tag was also executed remotely: core and legacy succeeded,
and target failed at the same dependency audit. See [REMOTE_VALIDATION.json](REMOTE_VALIDATION.json),
[remote privacy audit](REMOTE_PRIVACY_AUDIT.json) and the actual
[CI evidence](ci/end-to-end.json). This documentation commit records those verified
source runs; subsequent status is shown by the live badges and Actions pages.

## Recruiter demonstration

Use the actual MLflow experiments/registry, FastAPI Swagger, Grafana dashboard,
Prometheus alert and Evidently report checklist in
[DEMO_SCRIPT.md](../portfolio/DEMO_SCRIPT.md). No screenshots were fabricated:
an authorized browser surface was unavailable. A short narrated recording with
an authenticated prediction, injected synthetic shift and verified rollback is
the highest-value visual follow-up. Keep all local services loopback-only.
Explain deployment authority, failure compensation and why the audit is red;
do not claim clinical performance or production security clearance.
