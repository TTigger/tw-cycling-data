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
