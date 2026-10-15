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
