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

## Ask Bravelog who timed it
Bravelog's `/search` JSON has a `timing_vendor` id per contest. Races whose
2025 edition was on Bravelog but whose 2026 edition vanished mostly share one
vendor id with the races we now get from 伊貝特 — a strong hint the 2026 results
went to (and expired from) gr.e-better.com.tw. Check the vendor before searching
the open web; web search is US-centred and finds little for Taiwanese races.

## A timer's other events
focusline (score.focusline.com.tw) was crawled only for TWB tower rides, but its
activity list also held ranked road challenges (梅山36彎, 西螺媽祖, 蘭陽百K…).
When a timer is already wired up, list all its events, not just the series we
came for.

## Calendars get dates wrong
RACE ON listed 96聯賽台東站 on 10/31; the organizer's site says 12/19. A
"held but not ingested" gap can be a wrong calendar date — check the organizer.
Curated triage in `discover.py` now overrides the computed status for this.

## One parser, one layout
`cycling_crawl.py` reads only the 114年 national-championship PDF layout; the
other 22 road PDFs on cycling.org.tw (2016–2026) parse to 0 rows. A crawler
that "runs fine" can still be silently empty — check rows per input file.
(Fixed 2026-11-06: `cycling_generic.py` reads the per-category pages of all
layouts. Checks that caught bad picks: implied speed = distance ÷ time must be
12–55 km/h, and time must not drop as rank goes up within a category.)

## Sanitised file names can collide
Replacing every CJK character with `_` turned two different 110年 PDF titles
into the same file name, so one silently overwrote the other. Add a hash of
the URL to cached file names. (cyclist_crawl had the same bug: 41/菁英組成績
and 41/市民組成績 shared one file. Fixed 2026-11-06.)

## New ids re-key old athletes
A source that adds UCI ids moves riders from `n:<name>` to `u:<uci>`, which
changes their hashed id and breaks published URLs (216 would have broken).
`data/identity/id_carryover.json` maps the new hash back to the published id.

## One result table, two events
cyclist.org.tw linked the same 11/01 ITT from 花蓮太平洋盃 and KOM. Row-level
dedup split it 47/19 between the two races. `merge.cross_listed_tables` drops
the copy (a table ≥95% inside a larger table of another race, same year).

## Old PDFs: columns by position, not by splitting on spaces
The 2013–2021 cyclist.org.tw pages (`cyclist_archive.py`) come in about six
layouts, and foreign riders' names are several words long ("Jane Q Doe
美利達自行車"). Splitting on whitespace can't tell name from team. Find the
columns from the gaps no data row writes across, then match header labels to
them. Labels don't always sit over their column (編號 / 總排名 swapped places
in 2018–2020), so also check which number column counts 1, 2, 3.
Take the year from the PDF's own header: many old pages also link a 2017
calendar PDF, so the page's upload date says 2017 for 2018–2021 races.
