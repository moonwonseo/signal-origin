"""Meaningful failure checks for the public-file gate; no real credentials."""
import hashlib
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/check_publication.py"
spec = importlib.util.spec_from_file_location("publication", MODULE)
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


def manifest(root, content="A public research description.\n"):
    (root / "README.md").write_text(content)
    (root / publication.MANIFEST).write_text('{}\n')
    data = (root / "README.md").read_bytes()
    return {"files": [{"path": "README.md", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}]}


def test_unexpected_files_including_tracked_ignored_inputs_fail(tmp_path):
    m = manifest(tmp_path)
    problems = publication.validate(tmp_path, {"README.md", publication.MANIFEST, "data/private.csv"}, m)
    assert "Unexpected public candidate: data/private.csv" in problems


def test_changed_reviewed_file_fails_hash_check(tmp_path):
    m = manifest(tmp_path)
    (tmp_path / "README.md").write_text("Changed after review.")
    assert any("Changed since publication review" in p for p in publication.validate(tmp_path, {"README.md", publication.MANIFEST}, m))


def test_credential_detection_withholds_the_value(tmp_path):
    fake = "AKIA" + "A" * 16
    m = manifest(tmp_path, fake)
    problems = publication.validate(tmp_path, {"README.md", publication.MANIFEST}, m)
    assert any("AWS access key" in p for p in problems)
    assert all(fake not in p for p in problems)


def test_symlinks_and_parent_traversal_are_rejected(tmp_path):
    manifest(tmp_path)
    (tmp_path / "linked.md").symlink_to(tmp_path / "README.md")
    assert publication.inspect_file(tmp_path, "linked.md")[0].startswith("Symlink excluded")
    assert publication.inspect_file(tmp_path, "../outside.md")[0].startswith("Unsafe manifest path")


def test_csv_values_cannot_enter_as_templates(tmp_path):
    (tmp_path / "schema").mkdir()
    path = tmp_path / "schema/template.csv"
    path.write_text("date,value\n")
    assert not publication.inspect_file(tmp_path, "schema/template.csv")
    path.write_text("date,value\n2000-01-01,100\n")
    assert publication.inspect_file(tmp_path, "schema/template.csv")
