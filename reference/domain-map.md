---
title: Domain map — industry × role-archetype taxonomy
purpose: Tag each role with a domain so calibration batches sample diverse industries + seat-types. Updated as new companies are scouted.
schema-version: 1
---

# Domain map

Roles carry a `domain: <industry>:<archetype>` tag in jd.md frontmatter. The queue builder uses the `industry` half to enforce diversity per batch (≤4 of 20 per industry).

## Industries
- `consulting` — Big-4 + boutique strategy houses
- `bank` — retail, corporate, investment
- `hedge-fund` — quant, discretionary, macro
- `asset-mgmt` — long-only, PE, infra
- `pharma` — large pharma, biotech (use `biotech` for clearly biotech-mode)
- `biotech` — early-stage / VC-backed therapeutics
- `ai-lab` — frontier labs (OpenAI, Anthropic, Google DeepMind, Cohere, Mistral, …)
- `climate-tech` — energy transition, carbon, climate-AI
- `govt` — civil service, regulators, think-tanks
- `industrial` — semis, chips, defense, manufacturing
- `health-tech` — digital health, payor/provider tech

## Archetypes
- `strategy` — generalist strategy (corporate, business)
- `ai-strategy` — AI/ML strategy, governance, applied
- `frontier-strategy` — frontier-model strategy (LLM, agentic, foundation)
- `partnerships` — BD, strategic partnerships
- `policy` — AI policy, regulatory affairs
- `business-analyst` — IC-leaning analytic seat
- `product` — product mgmt (technical or non-technical)
- `ml-research` — IC ML research / engineering

## Seed: companies → industry (extends workday-registry.md)
| company | industry |
|---|---|
| Accenture | consulting |
| Lloyds Banking Group | bank |
| NatWest Group | bank |
| GSK | pharma |
| AstraZeneca | pharma |
| Graphcore | industrial |
| OpenAI | ai-lab |
| Anthropic | ai-lab |
| Google DeepMind | ai-lab |
| Cohere | ai-lab |
| McKinsey & Company | consulting |
| Bain & Company | consulting |
| Boston Consulting Group | consulting |
| Deloitte | consulting |
| KPMG | consulting |
| EY | consulting |
| PwC | consulting |
| HSBC | bank |
| Barclays | bank |
| Standard Chartered | bank |
| JPMorgan | bank |
| Goldman Sachs | bank |
| Morgan Stanley | bank |
| BlackRock | asset-mgmt |
| Bridgewater Associates | hedge-fund |
| Citadel | hedge-fund |
| Two Sigma | hedge-fund |
| Man Group | hedge-fund |
| Roche | pharma |
| Pfizer | pharma |
| Novartis | pharma |
| Moderna | biotech |
| Recursion | biotech |
| Insitro | biotech |
| Octopus Energy | climate-tech |
| BeZero Carbon | climate-tech |
| Watershed | climate-tech |
| AI Safety Institute | govt |
| UK Government Digital Service | govt |
| Bank of England | govt |
| Arm | industrial |
| Imagination Technologies | industrial |
| ASML | industrial |
| Babylon Health | health-tech |
| Hinge Health | health-tech |
| Cera | health-tech |

## Notes
- Companies not in this seed get classified at ingest time. The classifier reads JD body + company name and proposes industry × archetype; the human ratifies.
- Industry is REQUIRED for queue diversity. Archetype is currently informational (queue diversity is industry-only in v0).
- This file is calibration-driven, not load-bearing rubric. Extending it never changes the score.
