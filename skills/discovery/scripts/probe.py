#!/usr/bin/env python3
"""Validate candidate ATS slugs across Greenhouse/Lever/Ashby (threaded).
Prints ready-to-paste SOURCES tuples for the boards that are live."""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (career-scout)"}
PROV = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/%s/jobs",
    "lever": "https://api.lever.co/v0/postings/%s?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/%s",
}

CAND = [
    # vendor / lab
    ("anthropic", "Anthropic", "vendor/lab"), ("openai", "OpenAI", "vendor/lab"),
    ("cohere", "Cohere", "vendor/lab"), ("mistral", "Mistral AI", "vendor/lab"),
    ("databricks", "Databricks", "vendor/lab"), ("scaleai", "Scale AI", "vendor/lab"),
    ("huggingface", "Hugging Face", "vendor/lab"), ("perplexityai", "Perplexity", "vendor/lab"),
    ("elevenlabs", "ElevenLabs", "vendor/lab"), ("synthesia", "Synthesia", "vendor/lab"),
    ("glean", "Glean", "vendor/lab"), ("harvey", "Harvey", "vendor/lab"),
    ("writer", "Writer", "vendor/lab"), ("sierra", "Sierra", "vendor/lab"),
    ("anysphere", "Anysphere (Cursor)", "vendor/lab"), ("togetherai", "Together AI", "vendor/lab"),
    ("baseten", "Baseten", "vendor/lab"), ("modal", "Modal", "vendor/lab"),
    ("replicate", "Replicate", "vendor/lab"), ("runwayml", "Runway", "vendor/lab"),
    ("stabilityai", "Stability AI", "vendor/lab"), ("hippocraticai", "Hippocratic AI", "vendor/lab"),
    ("poolside", "Poolside", "vendor/lab"), ("contextualai", "Contextual AI", "vendor/lab"),
    ("lovable", "Lovable", "vendor/lab"), ("n8n", "n8n", "vendor/lab"),
    # fintech / enterprise (UK-leaning)
    ("monzo", "Monzo", "fintech/enterprise"), ("gocardless", "GoCardless", "fintech/enterprise"),
    ("revolut", "Revolut", "fintech/enterprise"), ("wise", "Wise", "fintech/enterprise"),
    ("starlingbank", "Starling Bank", "fintech/enterprise"), ("checkoutcom", "Checkout.com", "fintech/enterprise"),
    ("thoughtmachine", "Thought Machine", "fintech/enterprise"), ("pleo", "Pleo", "fintech/enterprise"),
    ("sumup", "SumUp", "fintech/enterprise"), ("traderepublic", "Trade Republic", "fintech/enterprise"),
    ("klarna", "Klarna", "fintech/enterprise"), ("paddle", "Paddle", "fintech/enterprise"),
    ("freetrade", "Freetrade", "fintech/enterprise"), ("zopa", "Zopa", "fintech/enterprise"),
    ("clearbank", "ClearBank", "fintech/enterprise"), ("form3", "Form3", "fintech/enterprise"),
    ("primer", "Primer", "fintech/enterprise"), ("truelayer", "TrueLayer", "fintech/enterprise"),
    ("moneybox", "Moneybox", "fintech/enterprise"), ("tide", "Tide", "fintech/enterprise"),
    # tech scale-up (UK office)
    ("stripe", "Stripe", "tech-scaleup"), ("gitlab", "GitLab", "tech-scaleup"),
    ("hashicorp", "HashiCorp", "tech-scaleup"), ("datadog", "Datadog", "tech-scaleup"),
    ("mongodb", "MongoDB", "tech-scaleup"), ("elastic", "Elastic", "tech-scaleup"),
    ("cloudflare", "Cloudflare", "tech-scaleup"), ("snowflake", "Snowflake", "tech-scaleup"),
    ("confluent", "Confluent", "tech-scaleup"), ("twilio", "Twilio", "tech-scaleup"),
    ("notion", "Notion", "tech-scaleup"), ("figma", "Figma", "tech-scaleup"),
    ("airtable", "Airtable", "tech-scaleup"), ("ramp", "Ramp", "tech-scaleup"),
    ("brex", "Brex", "tech-scaleup"), ("plaid", "Plaid", "tech-scaleup"),
    ("samsara", "Samsara", "tech-scaleup"), ("benchling", "Benchling", "tech-scaleup"),
    ("deel", "Deel", "tech-scaleup"), ("remote", "Remote.com", "tech-scaleup"),
    ("miro", "Miro", "tech-scaleup"), ("personio", "Personio", "tech-scaleup"),
    ("canva", "Canva", "tech-scaleup"), ("grammarly", "Grammarly", "tech-scaleup"),
    ("vercel", "Vercel", "tech-scaleup"), ("retool", "Retool", "tech-scaleup"),
    # UK AI specialist
    ("quantexa", "Quantexa", "uk-ai-specialist"), ("faculty", "Faculty AI", "uk-ai-specialist"),
    ("tractable", "Tractable", "uk-ai-specialist"), ("polyai", "PolyAI", "uk-ai-specialist"),
    ("darktrace", "Darktrace", "uk-ai-specialist"), ("improbable", "Improbable", "uk-ai-specialist"),
    ("wayve", "Wayve", "uk-ai-specialist"), ("graphcore", "Graphcore", "uk-ai-specialist"),
    ("benevolentai", "BenevolentAI", "uk-ai-specialist"), ("exscientia", "Exscientia", "uk-ai-specialist"),
    ("peakai", "Peak AI", "uk-ai-specialist"), ("onfido", "Onfido", "uk-ai-specialist"),
    ("cleo", "Cleo AI", "uk-ai-specialist"), ("signalai", "Signal AI", "uk-ai-specialist"),
    ("builderai", "Builder.ai", "uk-ai-specialist"),
    # energy / publishing
    ("octoenergy", "Octopus Energy", "energy"), ("octopusenergy", "Octopus Energy", "energy"),
    ("financialtimes", "Financial Times", "publishing"), ("economistgroup", "The Economist Group", "publishing"),
    ("guardian", "Guardian Media Group", "publishing"),
]


def try_one(prov, slug):
    try:
        req = urllib.request.Request(PROV[prov] % slug, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        n = len(d) if prov == "lever" else len(d.get("jobs", []))
        return (prov, n) if n > 0 else None
    except Exception:
        return None


def probe(item):
    slug, company, vert = item
    for prov in ("greenhouse", "lever", "ashby"):
        res = try_one(prov, slug)
        if res:
            return (slug, company, vert, res[0], res[1])
    return (slug, company, vert, None, 0)


with ThreadPoolExecutor(max_workers=16) as ex:
    rows = list(ex.map(probe, CAND))

hits = [r for r in rows if r[3]]
miss = [r for r in rows if not r[3]]
print("HITS (%d) — paste into SOURCES:" % len(hits))
for slug, co, ve, prov, n in sorted(hits, key=lambda x: (x[2], -x[4])):
    print('    ("%s", "%s", "%s", "%s"),  # %d jobs' % (prov, slug, co, ve, n))
print("\nMISSES (%d): %s" % (len(miss), ", ".join(r[0] for r in miss)))
