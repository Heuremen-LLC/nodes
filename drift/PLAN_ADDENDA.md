# SEAT: the outside seat that reads our live pages. Plan, as committed in the nodes repository (drift/PLAN.md) before the first probe.

## What it does
A GitHub runner, which is not our Mac and not our network, fetches the live site and compares it with what we publish elsewhere. Our own release script checks drift from the same machine that built the pages, which is one seat. This is a second seat that does not share our machine, our network or our clock.

## Reads (fixed now)
1. Page against repository. For each page in drift/targets.json the runner fetches the served page from indahl.ai and the same file from the main branch of github.com/Heuremen-LLC/indahl.ai, and compares SHA-256. MATCH or DIFFER. A release writes the site first and the repository after, so a single DIFFER can be a deploy in progress. A page counts as DRIFT only when it DIFFERs in two consecutive probes.
2. Feed freshness. For each live feed in drift/targets.json the runner fetches the JSON, reads its updated or read stamp, and computes its age in hours. Each feed has a limit set from its rider's cadence at three times the cadence, with a floor of 1.5 hours. FRESH when younger than the limit, STALE when older, UNREACHABLE when the fetch fails or the stamp cannot be read. The stamps are in UTC.
3. Archive chain. The runner downloads chain.jsonl and the manifests from code/archive in the repository and recomputes every digest. OK or BROKEN, with the number of entries.

## Rolling reading
Over the last 24 probes: the number of probes with any DRIFT page, any STALE or UNREACHABLE feed, and a BROKEN chain. Outcome against the claim that the live site is the published site and its feeds are current: CONSISTENT if none of the three occurred in 24 or more probes, ABOVE if any occurred in at least 3 of the last 24, otherwise CANNOT_TELL. Fewer than 24 probes: CANNOT_TELL.

## Probes
Triggered by Nova's tick bus through repository_dispatch, never on a schedule. Every probe is saved whole to data/drift/history.jsonl in this repository by the runner, with the run's own timestamp from the runner's clock.

## Known-good
The probe fetches one page it knows is current (the front page) and one URL it knows is missing, and must read MATCH and UNREACHABLE for them. A probe that fails this saves a row marked CONTROL_FAILED and no reading.

## Not claimed
That the content is true. That nothing changed between probes. That the runner's view is the view from everywhere: one runner is one seat.

## Note 1 (29 Oct, at the first probe)
The first row of data/drift/history.jsonl, stamped before the first dispatch, was written by running the probe on the author's own Mac to test it. It is not a reading from the outside seat and should be ignored. Every later row is written by the GitHub runner. The plan and the probe were committed in the same commit, before the first runner probe.

## Addendum 1 (29 Oct, from the internal audit)
1. Limits. The plan sets each feed's limit at three times its rider's cadence with a floor of 1.5 hours. Feeds added after the plan took a default of 40 hours, so a fast feed could be a day stale and read FRESH. Every limit is now set from its rider's cadence in Nova ticks at 6.5 minutes a tick (REVISE 78 hours, FEDSEP 234, STACK 3.9, SEAT 2.9, CADA 1.5, COIN 7.8, and so on), and the target list is regenerated from the tick bus cadences.
2. Incidents. A feed that stays stale, or a broken chain that is not repaired, was flagged on every probe, so one incident seen by three probes read ABOVE. The rolling reading now counts incidents, which are runs of consecutive flagged probes. ABOVE is three or more incidents in the last 24 probes, CONSISTENT is none, otherwise CANNOT_TELL.
3. Age. The reading covered the last 24 probes however old they were, so if probing stopped the last good reading would stand for ever. If the newest probe is more than three hours old the reading is CANNOT_TELL and the page shows how old it is.

## Addendum (29 Oct, after the home page and division rebuild)
The target list still held /sad, which now redirects to /hermes/model, so every probe counted one page as unreachable. It is removed, and /hermes, /hermes/model, /hpt, /weights and /airline are added as pages, with the feeds of the last three. No rule changed. The old target gave one false mismatch in each probe since the rename, so the page-match count in the probes since 29 Oct reads one lower than it should have.

## Addendum 2 (30 Oct, from the site pass)
1. Limits. Addendum 1 said every limit follows its rider's cadence, but hosts, campus, airq, ailuminate, hpt, weights, airline and tape still carried the 40 hour default, pkglicense, hflicense, hfsize, secrecords and pkginstall carried 39, and REVISE (78) and FEDSEP (234) were far above three times a 36 tick cadence. Every limit tied to a tick bus rider is now three times the rider's cadence in ticks at 6.5 minutes a tick, floor 1.5 hours (for example REVISE and FEDSEP 11.7 hours, HPT 565.5, TAPE 2.0). The qia feeds, activity and headlines keep the limits they had.
2. Stamps. A feed whose top-level stamp is a one-time read names the stamp its live keeper writes, in a "stamps" entry of targets.json. airq/live.json reads live.updated and airline/live.json reads faa.updated.
3. Targets added. Pages atlas/electricity, atlas/power-plants, atlas/carbon and atlas/planned-plants. Feeds coin/trends.json (every 24 ticks) and iris/live.json (every 2 ticks). Feeds of finished runs (iris/bench.json, iris/bench-results.json, iris/train.json), feeds written by a run and not by a schedule (hermes/model/live.json, qia/t1t2.json) and replies.json (no time stamp) are not targets.

## Addendum 3 (30 Oct, COIN removed)
The COIN desk was removed from indahl.ai on 30 Oct by Wayfinder's word. The page /coin and the feeds coin/live.json and coin/trends.json are no
longer targets, so probes from this commit on do not count them. Probes between the removal and this commit (about 13:12 to 17:30 UTC) read
/coin and coin/live.json as unreachable, which was the removal, not an outage. No rule changed.
