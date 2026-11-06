# -*- coding: utf-8 -*-
"""Block real rider names from entering the repo (PDPA).

Real names live only in gitignored raw data. Tests, docs and published files
must use placeholders or masked names. This scans files for any rider's real
name and fails if one is found. It prints masked names only (王○明), so its
own output never leaks a name.

  python scrapers/check_names.py --build      # refresh the name list from data sources
  python scrapers/check_names.py --staged     # files staged for commit (pre-commit hook)
  python scrapers/check_names.py --ref master # files changed since master
  python scrapers/check_names.py --all        # every tracked text file

The name list is data/processed/_names.json (gitignored). Code and docs are
searched for any 3–4 character CJK stretch or 2–4 word Latin run that is a
rider name; JSON data files only by whole values and words, because masked
data legitimately contains team and race names whose substrings collide with
real names. Two-character names are skipped: too many ordinary words match.

A false positive (a common word that happens to be someone's name) goes in
scrapers/check_names_allow.txt as its sha256, so the allow list holds no names.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
NAMES = os.path.join(ROOT, "data", "processed", "_names.json")
ALLOW = os.path.join(os.path.dirname(__file__), "check_names_allow.txt")
TEXT = re.compile(r"\.(py|md|ts|tsx|astro|mjs|js|sh|cff|txt|ya?ml|json|csv|html)$")
CJK_NAME = re.compile(r"[一-鿿]{3,4}")
LATIN_NAME = re.compile(r"[A-Za-zÀ-ÿ'’.\-]+(?:\s+[A-Za-zÀ-ÿ'’.\-]+){1,3}")
CJK_RUN = re.compile(r"[一-鿿]+")
WORD = re.compile(r"[A-Za-zÀ-ÿ'’.\-]+")


def latin_key(s):
    return " ".join(s.split()).casefold()


def build_names():
    import merge
    names = set()
    for p in merge.discover_sources():
        for r in merge.iter_records(p):
            n = (r.get("name_raw") or "").strip()
            if CJK_NAME.fullmatch(n):
                names.add(n)
            elif LATIN_NAME.fullmatch(n):
                names.add(latin_key(n))
    with open(NAMES, "w", encoding="utf-8") as f:
        json.dump(sorted(names), f, ensure_ascii=False)
    return names


def load_names():
    if not os.path.exists(NAMES):
        return None
    with open(NAMES, encoding="utf-8") as f:
        return set(json.load(f))


def load_allow():
    if not os.path.exists(ALLOW):
        return set()
    with open(ALLOW, encoding="utf-8") as f:
        return {ln.split("#")[0].strip() for ln in f if ln.split("#")[0].strip()}


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def find_in_text(text, names):
    """Names hidden anywhere in code / prose."""
    hits = set()
    for run in CJK_RUN.findall(text):
        for n in (3, 4):
            for i in range(len(run) - n + 1):
                if run[i:i + n] in names:
                    hits.add(run[i:i + n])
    for line in text.splitlines():
        words = WORD.findall(line)
        for n in (2, 3, 4):
            for i in range(len(words) - n + 1):
                k = latin_key(" ".join(words[i:i + n]))
                if k in names:
                    hits.add(" ".join(words[i:i + n]))
    return hits


def find_in_json(obj, names, hits=None):
    """Names as whole values or words of a JSON data file."""
    hits = set() if hits is None else hits
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_in_json(k, names, hits)
            find_in_json(v, names, hits)
    elif isinstance(obj, list):
        for v in obj:
            find_in_json(v, names, hits)
    elif isinstance(obj, str):
        s = obj.strip()
        for part in [s] + re.split(r"[\s,/()（）·、&+]+", s):
            if part in names:
                hits.add(part)
            elif LATIN_NAME.fullmatch(part) and latin_key(part) in names:
                hits.add(part)
    return hits


def scan_file(path, names):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        return set()
    if path.endswith(".json"):
        try:
            return find_in_json(json.loads(text), names)
        except ValueError:
            pass
    return find_in_text(text, names)


def _git(*args):
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def target_files(args):
    if args.staged:
        files = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    elif args.ref:
        files = _git("diff", "--name-only", "--diff-filter=ACMR", "-z", args.ref) + \
            _git("ls-files", "--others", "--exclude-standard", "-z")
    else:
        files = _git("ls-files", "-z")
    return [f for f in files if TEXT.search(f) and os.path.isfile(os.path.join(ROOT, f))]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--build", action="store_true")
    g.add_argument("--staged", action="store_true")
    g.add_argument("--ref")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.build:
        print(f"name list: {len(build_names())} names -> {os.path.relpath(NAMES, ROOT)}")
        return 0
    names = load_names()
    if names is None:
        print("check_names: no name list yet (run with --build); skipped")
        return 0
    allow = load_allow()
    bad = 0
    for f in target_files(args):
        hits = {h for h in scan_file(os.path.join(ROOT, f), names) if _sha(h) not in allow}
        if hits:
            bad += len(hits)
            shown = ", ".join(sorted(common.mask_name(h) for h in hits)[:5])
            print(f"  {f}: {len(hits)} real name(s): {shown}")
    if bad:
        print(f"check_names: {bad} real name(s) found. Use placeholders; if one is a "
              f"false positive, add its sha256 to {os.path.relpath(ALLOW, ROOT)}.")
        return 1
    print("check_names: no real names")
    return 0


if __name__ == "__main__":
    sys.exit(main())
