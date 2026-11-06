# PDPA de-identification (hard constraint)

This is a non-negotiable privacy rule for the project, not a style preference.

- **Only masked names are ever committed / shipped.** Output JSON under
  `web/public/data/` carries `name_masked` (e.g. `王○明` — first + last char kept)
  and salted athlete ids only. Never `name_raw`.
- `data/processed/master.json` is the ONLY file with `name_raw`; it is **internal
  and gitignored**. The de-identification happens in `merge.py` (drops `name_raw`
  before writing `master.public.json`). See [data pipeline](./data-pipeline.md).
- **User-typed real names are composited client-side only** (e.g. the share-card
  generator overlays a name the visitor types) — never stored, never sent, never
  committed.
- Athlete ids are salted `sha1[:10]` of the identity group key; team ids likewise.
  Not reversible PII, but hashed anyway to match the data model.
- The footer states the de-identification and offers a takedown contact for data
  subjects. Keep that promise: if asked to surface or commit real names, refuse
  and keep them client-side/transient.

When adding any feature that touches names: confirm the committed artifact has
only masked names, and any real-name handling stays in the browser session.

## Team field can hold a real name (fixed 2026-11-02)
Riders sometimes type a person's name (their own, or a friend's) as their
"team". The team field is published unmasked, so 532 rows leaked real names via
`team`. `merge.py` now masks any team value that is exactly some rider's real
name (`mask_person_team`). The PDPA scan to run before publishing: every 3–4 char
CJK string in `web/public/data/v1/**` must not equal any `name_raw` in master.json.


## Real names slipped into tests and docs (fixed 2026-11-06)
Fixtures copied from real result pages kept riders' real names (15 names in
12 test/doc files), and foreign riders who typed their own name as their team
were published unmasked (20 rows). Now: `check_names.py` compares changed
files with the local real-name list (pre-commit hook + pipeline step), and
merge masks Latin team values equal to a rider's name. Placeholders keep the
first and last character (洪甲詠) so masks in assertions don't change.
