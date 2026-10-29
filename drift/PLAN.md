# DRIFT SEAT: an outside seat that reads our live pages and feeds. Plan, written before the first probe.

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
