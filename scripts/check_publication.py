#!/usr/bin/env python3
"""Check the exact proposed public file set without staging or changing Git."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "publication_manifest.json"
BLOCKED_PARTS = {"_local_import", "private", "data", "results", "runs", "model_archive", ".aws", ".codex", ".agents", ".venv"}
BLOCKED_SUFFIXES = {".zip", ".parquet", ".pickle", ".pkl", ".joblib", ".pem", ".key", ".p12"}
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "OpenAI-style token": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential assignment": re.compile(r"(?im)^\s*(?:api_key|api_secret|access_token|password)\s*[=:]\s*['\"]?[A-Za-z0-9_+/=-]{20,}"),
}


def inspect_file(root: Path, relative: str):
    issues = []
    q = PurePosixPath(relative)
    if q.is_absolute() or ".." in q.parts or str(q) != relative or "\\" in relative:
        return [f"Unsafe manifest path: {relative}"]
    path = root / relative
    if any((root.joinpath(*q.parts[:i])).is_symlink() for i in range(1, len(q.parts) + 1)):
        return [f"Symlink excluded: {relative}"]
    if not path.is_file():
        return [f"Missing file: {relative}"]
    if set(q.parts) & BLOCKED_PARTS or path.suffix.lower() in BLOCKED_SUFFIXES or path.name.startswith(".env"):
        issues.append(f"Private/data/credential path excluded: {relative}")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeError:
        return issues + [f"Unreviewed binary file: {relative}"]
    for label, pattern in SECRET_PATTERNS.items():
        match = pattern.search(content)
        if match:
            line = content.count("\n", 0, match.start()) + 1
            issues.append(f"Potential {label}: {relative}:{line} (value withheld)")
    if path.suffix == ".csv":
        if q.parts[0] != "schema" or len(list(csv.reader(io.StringIO(content)))) != 1:
            issues.append(f"Only header-only schema CSVs are allowed: {relative}")
    return issues


def validate(root: Path, candidates, manifest):
    entries = manifest.get("files", [])
    paths = [entry["path"] for entry in entries]
    issues = []
    if len(paths) != len(set(paths)):
        issues.append("Duplicate allowlist entries.")
    expected = set(paths) | {MANIFEST}
    actual = set(candidates)
    issues += [f"Unexpected public candidate: {name}" for name in sorted(actual - expected)]
    issues += [f"Expected public file missing or ignored: {name}" for name in sorted(expected - actual)]
    for entry in entries:
        name = entry["path"]
        problems = inspect_file(root, name)
        issues += problems
        if problems:
            continue
        blob = (root / name).read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry["sha256"] or len(blob) != entry["bytes"]:
            issues.append(f"Changed since publication review: {name}")
    issues += inspect_file(root, MANIFEST)
    return issues


def main():
    manifest = json.loads((ROOT / MANIFEST).read_text())
    # --cached includes already tracked files even if .gitignore would hide them.
    output = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    candidates = {p for p in output.decode().split("\0") if p}
    issues = validate(ROOT, candidates, manifest)
    if issues:
        raise SystemExit("Publication checks failed:\n" + "\n".join(issues))
    print(f"Publication checks passed: {len(candidates)} exact allowed files; hashes and targeted credential checks match.")


if __name__ == "__main__":
    main()
