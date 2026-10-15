# Incident catalogue: public postmortems of interacting reliability mechanisms

Compiled 2026-10-15 by one coder (Abhinav Pandey). Data: `audit/incidents.csv` (one row per screened candidate).
Purpose (as stated in the paper): evidence of **existence and mechanism** outside simulation, **not prevalence**.

## 1. Search procedure

Sources searched (all public, primary):

- **AWS Post-Event Summaries**: the full index at <https://aws.amazon.com/premiumsupport/technology/pes/> (17 entries
  linked on 2026-10-15), plus the 2025-10-20 summary (<https://aws.amazon.com/message/101925/>), which is linked
  from danluu/post-mortems but not from the index page as fetched.
- **danluu/post-mortems** README (fetched 2026-10-15): entries matching
  `autoscal|retr(y|ies)|health check|circuit break|shed|throttl|thundering|rate limit|backoff|panic` were opened.
- **Targeted vendor postmortems** named in the brief: Google Cloud status reports, Microsoft Azure PIR, Cloudflare,
  GitHub, Slack, Discord, Roblox, Fastly, Stripe.
- **Web search** (2026-10-15) for postmortems combining autoscaling, load shedding, retries and health checks; this
  surfaced Auth0 (2021), Discord (2026), GitHub (Aug 2026) and the Google SRE Workbook case studies. Third-party
  mirrors (e.g. postmortem.io) were used only to locate the primary source; every row cites the operator's own URL.

Every URL in `incidents.csv` returned HTTP 200 on 2026-10-15 (column `http_status`). Every evidence quote was checked
by script to occur verbatim (after whitespace and curly-quote normalisation) in the fetched page text.
Heroku incident 2451 returned 200 but renders client-side, so its content could not be read (excluded, E1).

## 2. Codebook

**Inclusion** (all must hold):

- **I1 Primary, public, retrievable.** Written by the operating organisation (or its own publication, e.g. the Google
  SRE Workbook) and retrievable at the cited URL.
- **I2 Real incident.** A specific event that happened, not a hypothetical or fictional illustration.
- **I3 Two or more mechanisms.** At least two distinct *automated* reliability mechanisms, each with its own sensing and
  actuation, from this class: autoscaler/capacity provisioner; load shedder, rate limiter, throttle or quota;
  admission or concurrency limit; retry/reconnect policy (including timeout-then-retry); circuit breaker; health check,
  outlier ejection or failure-detector-driven removal/replacement; failover, re-replication or rebalancing.
  Operator actions are not mechanisms, even if they use the same tool (e.g. a throttle applied by hand as mitigation).
- **I4 Stated interaction.** The text states that the action of one mechanism changed the load, capacity, serving set
  or signal seen by another, and that this caused or worsened the incident. Interaction purely through a software
  defect (one mechanism's input triggering a bug in another) does not count.
- **Independence.** Functions of a single controller count once.

**Exclusion codes**: E1 not primary / not retrievable / insufficient detail; E2 not a real incident; E3 fewer than two
automated mechanisms in the causal chain (incl. mechanisms that appear only as manual mitigation); E4 no stated
mechanism-mechanism interaction, or interaction only via a code defect; E5 independence fails (one controller).

**Channel** (multi-label; first label = primary), as defined in Section III of the paper:

- **A, actuation**: two mechanisms concurrently move the same plant variable (capacity, admitted load, serving set).
- **O, observation**: one mechanism's action changes the signal another reads (masking or inflating it).
- **T, topological**: one mechanism's action redistributes or adds load (ejection, failover, re-replication,
  retries/reconnects), pushing other components or mechanisms past their thresholds. Retry amplification counts as T
  (the paper treats it as a temporal variant of topological coupling).

**Confidence**: *high*, both mechanisms and the causal link are stated explicitly; *medium*, both named and the link
stated, but one mechanism's role or independence needs interpretation; *low*, borderline mechanism class or link.

## 3. Coding passes and agreement (single-coder test-retest)

- **Pass 1**: coded from the full postmortem text.
- **Pass 2**: the same coder re-applied the codebook strictly to the extracted evidence quotes only, without consulting
  the pass-1 codes. Both passes were done on 2026-10-15 in one working session. This is **test-retest consistency of a
  single coder, not inter-rater reliability**; recall of pass 1 makes the agreement optimistic.
  The paper previously said both authors would code independently; that was not done.

| Measure | Value |
|---|---|
| Candidates screened | 45 |
| Include/exclude agreement | 43/45 (95.6%), Cohen's kappa = 0.87 |
| Included in pass 1 / pass 2 / both | 11 / 9 / 9 |
| Primary-channel agreement (9 included in both) | 8/9 |
| Exact channel-set agreement (9 included in both) | 8/9 |
| Exclusion-code agreement (34 excluded in both) | 33/34 |

Disagreements: I03 (DynamoDB 2015; pass 2: retry and self-disqualification are one routine, E5), I05 (Discord 2017;
pass 2: session buffering is outside the mechanism class, E3), I07 (Auth0; primary O vs T), I11 (GitHub Aug 2026;
O dropped in pass 2 as inferred from a remediation item), X03 (E3 vs E4). **Resolution rule**: an incident is in the
final catalogue only if both passes include it; I03 and I05 are reported as *borderline*.

## 4. Results

Screened 45 (AWS 18, Google 5 including the SRE Workbook, GitHub 3, Discord 3, Cloudflare 3, Slack 2, one each from
Auth0, Meta, Roblox, Fastly, Stripe, Azure, LaunchDarkly, Spotify, Heroku, Chef).
**Final: 9 included, 2 borderline, 34 excluded** (E3 27, E4 3, E1 2, E2 1, E5 1; pass-1 codes).

Channels among the 9 (labels present in both passes): **T 9, A 1, O 1**. Primary channel: T 7 or 8, A 1, O 0 or 1
(Auth0's primary channel is the one disagreement).

| ID | Org, date | Mechanisms (abridged) | Channels | Conf. |
|---|---|---|---|---|
| I01 | AWS, 2011-04-21 | EBS re-mirroring; re-mirror search without back-off; control-plane API timeout | T | med |
| I02 | AWS, 2014-06-13 | lock-service de-registration; handshake timeout + retry; node self-removal | T | high |
| I04 | Google/Niantic, 2016 | load-balancer GET retries; client retries (constant backoff) | T | high |
| I06 | Slack, 2021-01-04 | health-check replacement; autoscaler; (panic mode, retries, circuit breaking) | A;T | high |
| I07 | Auth0, 2021-04-20 | timeout + retry; utilization autoscaler (37 to 100 nodes); cache-bypass fallback | O;T / T;O | high |
| I08 | AWS, 2021-12-07 | automated capacity scaling; client retries with failed back-off | T | high |
| I09 | AWS, 2025-10-20 | NLB health checks; automatic AZ DNS failover; health-check-triggered terminations | T | high |
| I10 | Discord, 2026-03-25 | client reconnect; session-start rate limit; health-based hash-ring failover | T | med |
| I11 | GitHub, 2026-08-17 | sidecar concurrency limit; autoscaler on host service; gateway and client retries | T;O / T | med |
| (I03) | AWS, 2015-09-20 | membership timeout + retry; self-disqualification | T | borderline |
| (I05) | Discord, 2017-03-20 | session reconnect; session buffer-and-retransmit | T | borderline |

## 5. What the catalogue does and does not show

- Interactions between independently designed mechanisms appear in real postmortems from several operators over 15
  years; in every included case the operator names the interaction as a cause or amplifier.
- The catalogue is dominated by **topological** coupling (retry amplification, failover or re-replication that moves
  load). One incident (Auth0) states an **observation** path: retry-inflated in-flight work drove a utilization
  autoscaler to its maximum, which then overloaded the database. GitHub (Aug 2026) is consistent with observation
  coupling (an autoscaler that did not account for a saturated sidecar concurrency limit) but the text does not state
  masking. **No screened postmortem documents the paper's threshold-ordering trap itself** (a shedder hiding demand from
  an autoscaler). The closest public description is the Google SRE Workbook's *fictional* "Dressy" case study
  (shedding hid errors from a utilization-aware load balancer), excluded here as E2 and cited in the paper as
  practitioner literature, together with that chapter's advice to autoscale before load shedding engages.
- Not a prevalence estimate: publication is selective, the search was not exhaustive, and one coder screened.

## 6. Reproducing the coding

`audit/incident_coding/pass1_coding.py` holds the pass-1 records and verifies each evidence quote against fetched page
text; `pass2_agreement.py` holds the pass-2 codes, computes agreement and writes `incidents.csv`. The fetched page
texts are not committed (third-party copyright); re-fetch the URLs in `incidents.csv` to `<name>.txt` files to rerun.
