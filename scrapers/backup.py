# -*- coding: utf-8 -*-
"""Encrypted off-site backup of the canonical dataset (roadmap 0-1 / D5).

master.json contains real names (name_raw), so the archive is AES-256
encrypted BEFORE it leaves the machine; the passphrase never travels with it.

Usage (on the pipeline machine, after merge.py):
    python scrapers/backup.py                      # zip + upload to R2
    python scrapers/backup.py --no-upload          # zip only (no R2 yet)
    python scrapers/backup.py --include data/raw_archive   # add raw snapshots
    python scrapers/backup.py --verify data/backups/master-XXXX.zip  # restore drill

Environment:
    TWCD_BACKUP_PASSPHRASE   required — AES passphrase (keep it OFF the cloud)
    R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY   for upload
    TWCD_R2_BUCKET           bucket name (default: twcd)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import pyzipper

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGETS = [
    "data/processed/master.json",
    "data/processed/master.public.json",
    "data/processed/master_summary.json",
]
BACKUP_DIR = ROOT / "data" / "backups"
KEY_PREFIX = "backup/"


def _passphrase() -> bytes:
    p = os.environ.get("TWCD_BACKUP_PASSPHRASE")
    if not p:
        sys.exit("TWCD_BACKUP_PASSPHRASE is not set — refusing to write an "
                 "unencrypted backup (master.json contains real names).")
    return p.encode("utf-8")


def collect_files(includes: list[str]) -> list[Path]:
    files: list[Path] = []
    for rel in DEFAULT_TARGETS:
        p = ROOT / rel
        if p.exists():
            files.append(p)
    for inc in includes:
        base = ROOT / inc
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(sorted(q for q in base.rglob("*") if q.is_file()))
    if not files:
        sys.exit("nothing to back up — no default targets exist and no valid "
                 "--include given (is this the machine that holds master.json?)")
    return files


def create_archive(files: list[Path], passphrase: bytes, out_dir: Path,
                   stamp: str | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or time.strftime("%Y%m%d-%H%M%S")
    out = out_dir / f"master-{stamp}.zip"
    with pyzipper.AESZipFile(out, "w", compression=pyzipper.ZIP_DEFLATED,
                             encryption=pyzipper.WZ_AES) as z:
        z.setpassword(passphrase)
        for f in files:
            z.write(f, arcname=str(f.relative_to(ROOT)))
    return out


def verify_archive(path: Path, passphrase: bytes) -> list[str]:
    """Restore drill: decrypt + CRC-check every member, return the name list."""
    with pyzipper.AESZipFile(path) as z:
        z.setpassword(passphrase)
        bad = z.testzip()  # reads + CRC-checks every member (decrypts)
        if bad is not None:
            raise RuntimeError(f"corrupt member in {path.name}: {bad}")
        return z.namelist()


def r2_client():
    import boto3  # deferred: not needed for --no-upload / --verify
    account = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload(archive: Path, bucket: str, client=None) -> str:
    client = client or r2_client()
    key = KEY_PREFIX + archive.name
    client.upload_file(str(archive), bucket, key)
    return key


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--include", action="append", default=[],
                    help="extra file/dir (repo-relative) to add, repeatable")
    ap.add_argument("--no-upload", action="store_true",
                    help="create the encrypted zip but skip R2")
    ap.add_argument("--verify", metavar="ZIP",
                    help="restore drill: decrypt + CRC-check an existing backup")
    args = ap.parse_args(argv)

    pw = _passphrase()
    if args.verify:
        names = verify_archive(Path(args.verify), pw)
        print(f"OK — {len(names)} members decrypt + CRC-check clean:")
        for n in names[:10]:
            print("  ", n)
        return 0

    files = collect_files(args.include)
    archive = create_archive(files, pw, BACKUP_DIR)
    print(f"wrote {archive}  ({archive.stat().st_size:,} bytes, "
          f"{len(files)} files, sha256 {sha256(archive)[:16]}…)")
    # immediate self-check so a bad passphrase/zip never goes off-site unnoticed
    verify_archive(archive, pw)
    print("self-verify OK")

    if args.no_upload:
        print("skipped upload (--no-upload)")
        return 0
    bucket = os.environ.get("TWCD_R2_BUCKET", "twcd")
    key = upload(archive, bucket)
    print(f"uploaded r2://{bucket}/{key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
