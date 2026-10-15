"""Read-only publication audit of current files, reachable Git objects and identities.

Optional private denylist is read from an ignored local file, never published.
No match values are printed or stored in the public report.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args])


def inspect_text(payload, private_values):
    encoding = 'utf-16' if payload.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8'
    text = payload.decode(encoding, errors='replace')
    findings = []
    patterns = {
        'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        'github-token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',
        'aws-key': r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b',
        'credential-url': r'(?i)https?://[^\s/:]+:[^\s/@]+@',
    }
    for category, pattern in patterns.items():
        if re.search(pattern, text):
            findings.append(category)
    if any(value and value in text for value in private_values):
        findings.append('private-denylist-value')
    for account in re.findall(r'(?i)[A-Z]:[/\\]+Users[/\\]+([^/\\\s"<>]+)', text):
        if account not in ('USER', 'Public', 'Default', '<user>'):
            findings.append('personal-windows-account-path')
    for account in re.findall(r'/(?:home|Users)/([^/\s"<>]+)', text):
        if account not in ('USER', 'runner', 'medmlops'):
            findings.append('personal-unix-account-path')
    return sorted(set(findings))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-denylist')
    parser.add_argument('--output', default='runtime/publication-privacy-audit.json')
    args = parser.parse_args()
    values = []
    if args.private_denylist:
        values = json.loads(Path(args.private_denylist).read_text())['private_values']
    findings = []
    files = [p for p in git('ls-files', '-z').decode().split('\0') if p]
    for name in files:
        categories = inspect_text(Path(name).read_bytes(), values)
        if categories:
            findings.append({'scope': 'current-file', 'path': name, 'categories': categories})
        if name == '.env' or name.startswith(('.publication-local/', 'runtime/', '.venv/', '.dvc/cache/', 'artifacts/')):
            findings.append({'scope': 'tracked-exclusion', 'path': name})
    commits = git('rev-list', '--all').decode().splitlines()
    for commit in commits:
        raw = git('cat-file', 'commit', commit)
        categories = inspect_text(raw, values)
        for line in raw.decode().splitlines():
            if line.startswith(('author ', 'committer ')):
                email = re.search(r'<([^>]+)>', line)
                if not email or not email[1].endswith('@users.noreply.github.com'):
                    categories.append('non-noreply-identity')
        if b'gpgsig ' in raw:
            categories.append('unexpected-commit-signature')
        if categories:
            findings.append({'scope': 'commit-metadata', 'commit': commit, 'categories': categories})
    tags = git('for-each-ref', '--format=%(refname)', 'refs/tags').decode().splitlines()
    for tag in tags:
        if git('cat-file', '-t', tag).strip() == b'tag':
            raw = git('cat-file', 'tag', tag)
            categories = inspect_text(raw, values)
            match = re.search(rb'tagger [^\n]*<([^>]+)>', raw)
            if not match or not match[1].decode().endswith('@users.noreply.github.com'):
                categories.append('non-noreply-tagger')
            if b'BEGIN PGP SIGNATURE' in raw or b'BEGIN SSH SIGNATURE' in raw:
                categories.append('unexpected-tag-signature')
            if categories:
                findings.append({'scope': 'tag-metadata', 'tag': tag, 'categories': categories})
    blobs = 0
    for entry in git('rev-list', '--objects', '--all').decode().splitlines():
        oid, _, name = entry.partition(' ')
        if not name or git('cat-file', '-t', oid).strip() != b'blob':
            continue
        blobs += 1
        categories = inspect_text(git('cat-file', 'blob', oid), values)
        if categories:
            findings.append({'scope': 'history-blob', 'object': oid, 'path': name, 'categories': categories})
    result = {'passed': not findings, 'current_files_scanned': len(files),
              'reachable_commits_scanned': len(commits), 'reachable_history_blobs_scanned': blobs,
              'tags_scanned': len(tags), 'private_denylist_used': bool(args.private_denylist),
              'findings': findings, 'limits': 'Known private denylist, selected credential signatures and personal paths. Third-party license attribution retained. Not a universal secret/PII detector.'}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, indent=2).encode())
    print(json.dumps(result, indent=2))
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
