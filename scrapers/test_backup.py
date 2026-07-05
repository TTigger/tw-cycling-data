# -*- coding: utf-8 -*-
import os

import pytest
import pyzipper

import backup
import common


def _mkfiles(tmp_path, names):
    out = []
    for n in names:
        p = tmp_path / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("content of " + n, encoding="utf-8")
        out.append(p)
    return out


def test_create_and_verify_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "ROOT", tmp_path)
    files = _mkfiles(tmp_path, ["data/processed/master.json"])
    z = backup.create_archive(files, b"pw", tmp_path / "out", stamp="TEST")
    assert z.name == "master-TEST.zip"
    assert backup.verify_archive(z, b"pw") == ["data/processed/master.json"]


def test_verify_rejects_wrong_passphrase(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "ROOT", tmp_path)
    files = _mkfiles(tmp_path, ["data/processed/master.json"])
    z = backup.create_archive(files, b"right", tmp_path / "out")
    with pytest.raises(RuntimeError):
        try:
            backup.verify_archive(z, b"wrong")
        except Exception as e:  # pyzipper raises zlib/BadZipFile variants
            raise RuntimeError(str(e))


def test_collect_files_exits_when_nothing_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "ROOT", tmp_path)
    with pytest.raises(SystemExit):
        backup.collect_files([])


def test_upload_uses_bucket_and_key(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "ROOT", tmp_path)
    files = _mkfiles(tmp_path, ["data/processed/master.json"])
    z = backup.create_archive(files, b"pw", tmp_path / "out")
    calls = []

    class Fake:
        def upload_file(self, path, bucket, key):
            calls.append((path, bucket, key))

    key = backup.upload(z, "twcd", client=Fake())
    assert key == "backup/" + z.name
    assert calls == [(str(z), "twcd", key)]


def test_archive_response_writes_blob_and_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RAW_ARCHIVE_DIR", str(tmp_path))
    monkeypatch.delenv("TWCD_RAW_ARCHIVE", raising=False)
    blob = common.archive_response("https://example.tw/results?page=1",
                                   b"<html>rank</html>", when=0)
    assert blob and blob.endswith(".gz") and os.path.exists(blob)
    day_dir = os.path.dirname(blob)
    assert os.path.basename(os.path.dirname(day_dir)) == "example.tw"
    manifest = open(os.path.join(day_dir, "manifest.jsonl"), encoding="utf-8").read()
    assert '"url": "https://example.tw/results?page=1"' in manifest
    # identical payload dedupes to the same blob, manifest gains a second event
    blob2 = common.archive_response("https://example.tw/results?page=1",
                                    b"<html>rank</html>", when=0)
    assert blob2 == blob
    manifest2 = open(os.path.join(day_dir, "manifest.jsonl"), encoding="utf-8").read()
    assert manifest2.count('"sha1"') == 2


def test_archive_response_opt_out(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RAW_ARCHIVE_DIR", str(tmp_path))
    monkeypatch.setenv("TWCD_RAW_ARCHIVE", "0")
    assert common.archive_response("https://x.tw/a", b"data") is None
    assert list(tmp_path.iterdir()) == []
