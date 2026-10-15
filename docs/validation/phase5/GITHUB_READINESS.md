# GitHub publication readiness

> Historical private-source report, sanitized for public redistribution. Private revision references are redacted. For current public results and MIT confirmation, see [publication status](../../publication/PUBLICATION.md).

No remote repository exists in the inspected configuration. No push, release,
repository creation, secret upload or remote workflow execution was performed.

## Workflows

| Workflow | Execution / permissions | Checks |
|---|---|---|
| target-ci.yml | Hosted Ubuntu, Python 3.12, `contents: read`; no deployment secrets | Hashed install, pip check, pytest, Ruff, scoped Mypy, clean-source training, Docker build/start, actual registry/artifact verification, E2E acceptance and DVC reproduction; blocking pip-audit; evidence upload and teardown even on failure |
| core-ci.yml | Hosted Ubuntu; read only | Mathematical core verification with locked dependencies; no promotion |
| ci.yml | Hosted Ubuntu; read only | Preserved v1 reference tests/demo; no v2 release claim |
| controlled-training.yml | Manual only; labelled self-hosted local runner; protected local-demo environment | Train and publish candidate, no approval/deploy |
| controlled-deploy.yml | Manual only; same runner/environment, timeout and serialized deployment | Hashed install, pip check and blocking audit before explicit approve and verified deploy |

Fixed: target CI created a shell redirect into missing `runtime/`; it now creates
the directory first. Added missing scoped static typing. Service evidence writes
to ignored `runtime/ci-evidence` so it does not dirty source before provenance
capture or overwrite historical evidence. Manual workflows explicitly use Bash;
the operator runner must provide Bash, Python 3.12 and the locked target environment.

## Remote configuration required after publication approval

1. Choose destination repository, visibility and confirm preservation of the existing MIT license.
2. Push the reviewed local branch/tag only after explicit permission.
3. Enable hosted CI; require successful target checks before merging. Current security gate is expected to fail until upstream advisories are fixed; do not ignore IDs to obtain green status.
4. Create protected `local-demo` environment with required reviewers and prevent self-review where supported. Restrict deployment refs to reviewed protected branches/tags.
5. Configure a dedicated trusted `medmlops-local` runner with loopback stack access, Python 3.12/Bash and operator-managed environment. Never run untrusted PR jobs on it; public repository runner exposure needs particular care.
6. Set environment-scoped secrets `MEDMLOPS_API_TOKEN` and `GOVERNANCE_DB_PASSWORD` to match the existing local stack. Default host DB port is 5433 and tracking URI is 127.0.0.1:5000. Container bootstrap secrets belong locally, not in committed YAML. Manual training needs access to the local MLflow service, not API deployment credentials.
7. Verify remote logs, artifact uploads, actual environment protection and runner isolation; do not infer these from YAML. External action SHA pinning and image scanning remain hardening work.

No PAT or cloud credentials are required for hosted CI; use GitHub's read-only
workflow token. GitHub protection feature availability depends on repository and
account settings; if required reviewers cannot be enforced, do not enable manual CD.

References checked: [GitHub environment configuration](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
and [runner security guidance](https://github.com/github/docs/blob/main/content/actions/reference/security/secure-use.md).

## Repository hygiene

The ignore rules exclude runtime, generated cohorts/models, virtual environments,
credentials and common private key/build artifacts. `.env.example` stays tracked.
Docker excludes `.git`, `.env`, data and host runtime. The local scanner examines
all reachable Git history blobs and current tracked/project files for known local
credentials and selected key/token patterns; it is not a universal secret detector.
See `release-inventory.json` for actual findings and exact scope.

Release version is `2.0.0rc1` (intended local tag `v2.0.0-rc.1`). See FINAL_REPORT
for actual commits/tag and clean-clone installation results. Source-only publication
must preserve the unresolved-security and third-party-license disclosures.
