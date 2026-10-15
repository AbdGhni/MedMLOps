# Dependency review — 2026-10-14

The real `pip-audit` report is retained as `dependency-audit.json`.
pip was upgraded from 24.0 to 26.2.1, Flask from 3.0.3 to 3.1.3.
The second scan reports three advisories in two distributions, with no fix
versions supplied by the advisory service: DiskCache 5.6.3 and NLTK 3.10.3.
This is not a clean security scan and prevents an unrestricted production claim.

DiskCache is a DVC transitive dependency: its pickle serialization can execute
code if an attacker can write its cache. Only the local repository operator may
write this demo's cache; do not consume untrusted caches or expose them over a
shared writable mount. NLTK is brought in by Evidently; this tabular application
does not use NLP model import/export or accept model paths from API clients.
Keep these dependencies under review, rerun the audit before release, and upgrade
when maintained fixes become available. These mitigations reduce exposure; they
do not erase the advisories. CI retains a failing audit gate without ignore IDs.
