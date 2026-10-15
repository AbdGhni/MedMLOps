# Limits, residual risks and next steps

| Area | Current boundary | Next meaningful improvement |
|---|---|---|
| Clinical use | Entirely synthetic features/outcome; no external or clinical validation | Separate governed clinical study and representative validation; not a demo extension |
| Evaluation | One artificial fixture; repeated held-out gates; v2 does not implement v1 age-slice approval | Independent release test set, subgroup/calibration analysis and model/data governance |
| Security | Unfixed DiskCache/NLTK advisories; one shared local API token | Supported upstream fixes, per-service locks/images, enterprise identity and scoped authorization |
| Identity/audit | Actor strings are operator assertions; owner can bypass database protections | Authenticated identities, signed approvals and external tamper-evident retention |
| Registry trust | Trusted local MLflow and uploaded verification evidence; digest is not a signature | Artifact signing, independent verifier and restricted registry write identity |
| Availability | Local Compose, no HA or horizontal scaling | Deployment platform, recovery drills and explicit SLO/load tests |
| Storage | Named volumes and local DVC remote; recreation verified | Off-host backups and tested restore; local remote is not durable remote storage |
| Monitoring | Synthetic shifts and reversed labels; last-window drift gauge | Real window scheduling, label-delay handling, incident lifecycle and alert delivery |
| Supply chain | Hash-locked Python artifacts; action version tags; third-party image tags | Immutable action/image digests, image scanning and platform-specific SBOM/license notices |
| GitHub | Public repository verified; core/legacy pass and target functional steps pass, but audit blocks target CI | Resolve advisories; configure branch protection, reviewers and isolated runner before manual CD |
| Visual proof | No authorized browser surface in Phase 5 | Manual authentic captures using DEMO_SCRIPT checklist; never fabricate panels |
| Release licensing | MIT file predates Phase 5; owner confirmation pending | Confirm existing license, preserve dependency notices before binary redistribution |

See [security detail](../validation/phase5/SECURITY_REVIEW.md),
[license inventory](../validation/phase5/LICENSE_REVIEW.md) and
[final verification report](../validation/phase5/FINAL_REPORT.md).
