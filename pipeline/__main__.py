# -*- coding: utf-8 -*-
"""CLI: python -m pipeline refresh [...] | python -m pipeline steps"""
import argparse
import sys

from .core import build_plan, run_plan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("refresh", help="scrape -> merge -> validate -> build -> backup")
    r.add_argument("--skip-scrape", action="store_true",
                   help="rebuild from existing data/processed source files")
    r.add_argument("--source", action="append", metavar="NAME",
                   help="scrape only these sources (repeatable): cyclist, bravelog, "
                        "tsu, cycling, league, irunner, criterium, focusline, taiwanbike")
    r.add_argument("--clean-race", action="store_true",
                   help="clear web/public/data/v1/race first (after race_key changes)")
    r.add_argument("--og", action="store_true", help="also rebuild the OG share image")
    r.add_argument("--no-backup", action="store_true")
    r.add_argument("--resume", action="store_true",
                   help="continue after the last completed step of a failed run")
    r.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")

    sub.add_parser("steps", help="list the full step registry")

    args = ap.parse_args(argv)
    if args.cmd == "steps":
        for st in build_plan():
            print(f"{st.group:9} {st.name:26} {' '.join(st.argv) or '(internal)'}"
                  + (f"   # {st.note}" if st.note else ""))
        return 0

    plan = build_plan(skip_scrape=args.skip_scrape, sources=args.source,
                      clean_race=args.clean_race, with_og=args.og,
                      with_backup=not args.no_backup)
    return run_plan(plan, resume=args.resume, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
