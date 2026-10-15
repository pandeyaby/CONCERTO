# AGENT'27 / IEEE compliance check (2026-10-15)

CFP: https://conf.researchr.org/track/icse-2027/agent-2027-papers (fetched 2026-10-15).

## CFP facts vs. our assumptions

| Item | CFP says | We assumed | Status |
|---|---|---|---|
| Page limit (full paper) | up to 8 pages **including references** | 8 pp + refs | **Contradiction**: references count. Current PDF is 8 pages total, so it complies, with no slack. |
| Short papers | up to 5 pages including references | - | n/a |
| Deadline | **Fri 13 Nov 2026 AoE** | 27 Nov 2026 | **Contradiction**: two weeks earlier. |
| Notification / camera-ready | 11 Dec 2026 / 29 Jan 2027 | - | info |
| Review | single-anonymous | single-blind | consistent; author names stay on the paper |
| Template | IEEE conference proceedings template | IEEEtran conference | consistent |
| Extra pages | cannot be bought | - | info |
| Submission site | https://icse2027-agent.hotcrp.com/ | - | needs an account by Abhinav |
| Required sections | none stated | - | n/a |
| Scope | engineering of *agentic AI systems* (foundation-model agents; testing, multi-agent coordination, AgentOps, incident response) | reliability controllers framed as agents | fit risk: the paper's agents are not LLM-based; the framing in Sec. I-A is the bridge. Judgment call for Abhinav. |

## PDF checks (paper/concerto.pdf)

| Check | Result |
|---|---|
| Class | IEEEtran v1.8b, `[conference]`, no geometry/margin overrides: PASS |
| Paper size | 612 x 792 pt (US letter): PASS |
| Fonts embedded | all 20 fonts embedded and subset (`pdffonts`): PASS |
| Type 3 fonts | none: PASS |
| Margins (text bbox) | left/right 49 pt, bottom >= 73 pt, top ~52 pt (glyph bbox; IEEEtran default 0.75 in): PASS (class defaults untouched) |
| Page count | 8 including references: PASS (at the limit) |
| Undefined references/citations | none: PASS |
| Overfull boxes | none after fixes: PASS |

## Needs Abhinav

- Author block lists **Abhishek Pandey (Meta)** as first author and Abhinav Pandey second. The brief says the author is
  Abhinav Pandey, Independent Researcher, alone. Not changed: removing a co-author is your decision.
- Confirm deadline (13 Nov 2026 AoE) and create the HotCRP account; IEEE copyright form and PDF eXpress check come at
  camera-ready.
- Decide whether the scope fit (non-LLM agents) needs a sentence in the introduction or a different venue.
