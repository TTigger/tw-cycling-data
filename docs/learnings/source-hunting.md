# Finding results that "aren't online"

Lessons from the 2026-11 source hunt, which added ~15,000 finishes that had
been written off as unavailable.

## Look for the timer's own results site, not the registration site
Registration platforms and results sites are often separate hosts. 伊貝特's
registration site (bao-ming.com) has a bot check — we don't bypass it — but its
results site (gr.e-better.com.tw) is public. The 96 league's timer (Dynamic
Intelligences) has its own JSON API (raceresult.sport-result.com) that is more
complete than the organizer's PDF. When a race leaves Bravelog, ask who timed it.

## Some sources delete old results
gr.e-better.com.tw keeps only the last few months. `ebetter_crawl.py` caches
every pull in `data/raw/ebetter/` and never re-fetches a cached event; that
cache (gitignored, real names) is the only copy once the page is gone, so it
must be part of the backup. Ingest new e-better events promptly
(`ebetter_crawl.py --scan LO HI`).

## "Blocked" can mean "blocked from where we tried"
ATSport refused the overseas cloud host but works from a Taiwan connection.
Re-test blocked sources from the machine that actually runs the crawl.

## Listing pages can point to the wrong page
cyclist.org.tw category listings sometimes link a race-year's certificate page
while the results PDFs sit on an unlisted neighbouring pno. A full pno scan
found ~40 unlisted pages. Before adding one, check the year (PDF upload names
are the best clue; page dates are often a placeholder like 2017-03-12) and that
no listed sibling page already gave the same race-year.

## Sanity-check per-course lists
ATSport race 23 returns the identical list for two different courses, so the
course of each row is unknowable — excluded. Compare course lists (or counts)
before trusting a course filter.

## Team fields leak names
Riders type people's names into the team field, alone or inside longer text
("<name>&<name>親友團"). `merge.mask_person_team` masks any 3–4 character run
that is a rider's real name. Names of people who never raced can't be detected.

## Keep the misses on record
`data/known_races.json` lists race-years we know about but can't collect, with
status, note and lead link. Calendars forget a race once it has passed; this
list doesn't. `discover.py` folds it into `coverage.json`.
