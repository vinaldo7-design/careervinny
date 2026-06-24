#!/usr/bin/env python3
"""
CareerVinny batch scout — wide pull, eligibility-only filter, raw signal fields.

Design contract (see CC-BATCH-SCOUT-SPEC.md + the batch brief):
  * ELIGIBILITY gates (visa / location / comp) are the ONLY filter. Physics.
  * PREFERENCE signals (frontier, agency, ic_tell, seniority, esg_edge,
    client_facing, origination) are OBSERVATIONS, not scores. Emitted, never filtered.
  * This script READS the sponsor register; it NEVER writes weights or touches
    any rubric file. One direction only.
  * No fabricated fields. Absent data -> "not stated". Missing eligibility data
    -> KEEP and flag as undetermined (never kill on missing data).
  * Find and stage only. No applying, no messaging.

Python 3.8, stdlib only (no rapidfuzz -> difflib.SequenceMatcher).
"""
import argparse
import csv
import datetime
import functools
import html
import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

# Paths resolve relative to this script so the scout is portable inside the repo
# (skills/discovery/scripts/scout.py). The repo is the sole source of truth
# (CLAUDE.md); ~/Downloads/ssdhj/scout/ is the archived donor.
HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER_PATH = os.path.join(HERE, "..", "data", "sponsor-register.csv")
WORKDAY_REGISTRY_PATH = os.path.join(HERE, "..", "..", "..", "reference", "workday-registry.md")
OUT_DIR = os.path.join(HERE, "..", "out")
KEPT_CACHE = os.path.join(OUT_DIR, "kept.json")
RUN_DATE = datetime.date.today().isoformat()
UA = "Mozilla/5.0 (career-scout; eligibility-filter)"

# Workday cxs searchText queries — the D027 function-hunting set (hunt FUNCTIONS
# and VERBS, not AI-buzzword org names). searchText narrows server-side, so the
# Workday layer skips the title-keyword gate the public boards apply.
WORKDAY_QUERIES = [
    "Responsible AI", "AI Governance", "AI Ethics", "AI Strategy",
    "AI Transformation", "Data and AI", "GTM Strategy", "Strategic Product",
    "AI Adoption", "Value Strategy",
]

# Live public ATS boards confirmed by probe.py (provider, slug, company, vertical).
SOURCES = [
    # vendor / lab
    ("greenhouse", "anthropic", "Anthropic", "vendor/lab"),
    ("ashby", "openai", "OpenAI", "vendor/lab"),
    ("lever", "palantir", "Palantir Technologies", "vendor/lab"),
    ("greenhouse", "databricks", "Databricks", "vendor/lab"),
    ("ashby", "harvey", "Harvey", "vendor/lab"),
    ("greenhouse", "scaleai", "Scale AI", "vendor/lab"),
    ("lever", "mistral", "Mistral AI", "vendor/lab"),
    ("ashby", "elevenlabs", "ElevenLabs", "vendor/lab"),
    ("ashby", "sierra", "Sierra", "vendor/lab"),
    ("ashby", "cohere", "Cohere", "vendor/lab"),
    ("ashby", "synthesia", "Synthesia", "vendor/lab"),
    ("ashby", "baseten", "Baseten", "vendor/lab"),
    ("greenhouse", "togetherai", "Together AI", "vendor/lab"),
    ("greenhouse", "lovable", "Lovable", "vendor/lab"),
    ("ashby", "writer", "Writer", "vendor/lab"),
    ("ashby", "n8n", "n8n", "vendor/lab"),
    ("ashby", "modal", "Modal", "vendor/lab"),
    ("ashby", "poolside", "Poolside", "vendor/lab"),
    ("greenhouse", "stabilityai", "Stability AI", "vendor/lab"),
    # fintech / enterprise
    ("greenhouse", "sumup", "SumUp", "fintech/enterprise"),
    ("greenhouse", "tide", "Tide", "fintech/enterprise"),
    ("greenhouse", "monzo", "Monzo", "fintech/enterprise"),
    ("lever", "zopa", "Zopa", "fintech/enterprise"),
    ("greenhouse", "gocardless", "GoCardless", "fintech/enterprise"),
    ("ashby", "pleo", "Pleo", "fintech/enterprise"),
    ("ashby", "paddle", "Paddle", "fintech/enterprise"),
    ("ashby", "primer", "Primer", "fintech/enterprise"),
    ("ashby", "clearbank", "ClearBank", "fintech/enterprise"),
    ("ashby", "freetrade", "Freetrade", "fintech/enterprise"),
    ("greenhouse", "truelayer", "TrueLayer", "fintech/enterprise"),
    ("greenhouse", "form3", "Form3", "fintech/enterprise"),
    ("greenhouse", "traderepublic", "Trade Republic", "fintech/enterprise"),
    # tech scale-up
    ("greenhouse", "stripe", "Stripe", "tech-scaleup"),
    ("greenhouse", "mongodb", "MongoDB", "tech-scaleup"),
    ("ashby", "snowflake", "Snowflake", "tech-scaleup"),
    ("greenhouse", "datadog", "Datadog", "tech-scaleup"),
    ("greenhouse", "samsara", "Samsara", "tech-scaleup"),
    ("greenhouse", "brex", "Brex", "tech-scaleup"),
    ("greenhouse", "elastic", "Elastic", "tech-scaleup"),
    ("greenhouse", "cloudflare", "Cloudflare", "tech-scaleup"),
    ("greenhouse", "twilio", "Twilio", "tech-scaleup"),
    ("greenhouse", "figma", "Figma", "tech-scaleup"),
    ("ashby", "notion", "Notion", "tech-scaleup"),
    ("greenhouse", "gitlab", "GitLab", "tech-scaleup"),
    ("ashby", "ramp", "Ramp", "tech-scaleup"),
    ("ashby", "plaid", "Plaid", "tech-scaleup"),
    ("greenhouse", "vercel", "Vercel", "tech-scaleup"),
    ("ashby", "benchling", "Benchling", "tech-scaleup"),
    ("ashby", "confluent", "Confluent", "tech-scaleup"),
    ("greenhouse", "airtable", "Airtable", "tech-scaleup"),
    ("greenhouse", "remote", "Remote.com", "tech-scaleup"),
    # UK AI specialist
    ("greenhouse", "graphcore", "Graphcore", "uk-ai-specialist"),
    ("greenhouse", "wayve", "Wayve", "uk-ai-specialist"),
    ("ashby", "faculty", "Faculty AI", "uk-ai-specialist"),
    ("ashby", "quantexa", "Quantexa", "uk-ai-specialist"),
    ("greenhouse", "polyai", "PolyAI", "uk-ai-specialist"),
    ("ashby", "improbable", "Improbable", "uk-ai-specialist"),
    ("greenhouse", "cleo", "Cleo AI", "uk-ai-specialist"),
    ("ashby", "tractable", "Tractable", "uk-ai-specialist"),
    # energy
    ("lever", "octoenergy", "Octopus Energy", "energy"),
]

COVERAGE_NOTE = (
    "60 live public ATS boards (Greenhouse / Lever / Ashby) PLUS a Workday cxs "
    "layer (reference/workday-registry.md) that reaches the verticals the public "
    "boards cannot see — **management consulting**, **large banks**, **big pharma** "
    "— which post via Workday's login-free cxs JSON endpoint. This closes the "
    "2026-06-23 audit blind spot on bullseye role-family #1. Still absent: Taleo / "
    "SuccessFactors tenants (e.g. Capgemini) — a later fallback (career-ops "
    "Playwright) per Q8. The Workday layer adds tier-1 banks (Lloyds, NatWest) the "
    "fintech/enterprise boards miss."
)

# Function-keyword title filter — anchored to the four target role families.
FUNCTION_KEYWORDS = [
    "responsible ai", "ai governance", "ai ethics", "ai safety policy",
    "ai policy", "ai strategy", "ai transformation", "data & ai", "data and ai",
    "gtm strategy", "go-to-market", "go to market", "gtm", "value strategy",
    "value engineer", "strategic product", "ai adoption", "ai enablement",
    "strategy", "strategic", "strategist", "transformation", "solutions strateg",
    "forward deployed", "forward-deployed", "solutions architect",
    "solutions engineer", "solutions consultant", "customer success",
    "applied ai", "ai consultant", "ai solution",
    # family 3 (product / programme), family 1 (advisory), family 2 (commercial)
    "product manager", "product management", "program manager", "programme manager",
    "technical program", "technical programme", "tpm", "consultant", "advisory",
    "principal", "account executive", "account manager", "enterprise account",
    "commercial", "partnerships", "engagement manager", "delivery lead",
    "delivery manager",
]

# Non-UK region tokens that, when present in a TITLE, override an otherwise
# location-agnostic-remote keep (e.g. GitLab "… - South Africa", loc="Remote").
NON_UK_HINTS = ["india", "australia", "anz", "apac", "apj", "singapore",
                "japan", "korea", "china", "brazil", "mexico", "canada",
                "americas", "latam", "latin america", "uae", "dubai", "saudi",
                "qatar", "philippines", "south africa", "united states",
                "germany", "nordics", "dach", "benelux", "iberia"]

LEGAL = {
    "ltd", "limited", "plc", "inc", "incorporated", "llp", "llc", "lp",
    "na", "co", "company", "corp", "corporation", "group", "holding",
    "holdings", "uk", "gb", "england", "international", "intl", "the", "and",
}

KNOWN_LARGE = {
    "accenture", "deloitte", "mckinsey", "kpmg", "pwc", "ey", "ernst young",
    "ibm", "microsoft", "google", "amazon", "aws", "oracle", "salesforce",
    "sap", "nvidia", "databricks", "snowflake", "openai", "anthropic",
    "cohere", "palantir", "mistral", "jpmorgan", "jp morgan", "goldman",
    "morgan stanley", "barclays", "hsbc", "lloyds", "natwest", "santander",
    "citi", "citigroup", "bank of america", "ubs", "deutsche", "bnp paribas",
    "astrazeneca", "gsk", "glaxosmithkline", "novartis", "pfizer", "roche",
    "sanofi", "shell", "bp", "centrica", "national grid", "vodafone", "bt",
    "telefonica", "ericsson", "nokia", "thomson reuters", "reuters",
    "bloomberg", "pearson", "relx", "informa", "wpp", "unilever", "diageo",
    "reckitt", "rolls royce", "bae systems", "siemens", "capgemini",
    "cognizant", "infosys", "tata", "wipro", "mastercard", "visa", "paypal",
    "stripe", "revolut", "monzo", "wise", "meta", "facebook", "apple",
    "netflix", "adobe", "atlassian", "servicenow", "workday", "datadog",
    "mongodb", "thoughtworks", "bcg", "boston consulting", "bain",
    "oliver wyman", "roland berger", "kearney", "pa consulting", "deliveroo",
    "gocardless", "octopus", "samsara", "cloudflare", "elastic", "twilio",
    "gitlab", "snowflake", "confluent", "darktrace", "graphcore", "wayve",
}

UK_TERMS = [
    "london", "united kingdom", "uk", "u.k", "england", "scotland", "wales",
    "northern ireland", "manchester", "edinburgh", "cambridge", "oxford",
    "reading", "bristol", "leeds", "glasgow", "birmingham", "britain",
    "british", "cardiff", "belfast", "remote - uk", "remote, uk",
]
REMOTE_ONLY_TOKENS = {
    "remote", "hybrid", "onsite", "on-site", "global", "anywhere",
    "worldwide", "flexible", "multiple", "locations", "various", "emea",
}

FRONTIER_NAMED = ["agentic", "llm", "large language model", "genai",
                  "generative ai", "rag", "retrieval-augmented",
                  "foundation model", "frontier model", "gpt", "claude",
                  "gemini", "llama", "diffusion model"]
FRONTIER_VAGUE = ["artificial intelligence", "machine learning", "ai", "ml",
                  "ai/ml", "data science"]

AGENCY_HIGH = ["set the strategy", "define the strategy", "own the strategy",
               "shape the strategy", "set strategy", "define strategy",
               "advise", "advisor", "advising", "c-suite", "c-level",
               "board level", "executive stakeholders", "set the direction",
               "define the vision", "trusted advisor", "shape the vision"]
AGENCY_MED = ["influence", "shape ", "drive the", "inform the",
              "contribute to strategy", "help shape", "collaborate with senior"]
AGENCY_LOW = ["support the", "deliver", "execute", "implement", "assist",
              "maintain", "carry out", "fulfil"]

IC_STACK = ["python", "sql", "spark", "kubernetes", "k8s", "scala",
            "tensorflow", "pytorch", "terraform", "java", "golang",
            "c++", "airflow"]
IC_HARD_CUE = ["proficien", "hands-on", "hands on", "must have", "required",
               "requirement", "strong experience", "expert", "writing code",
               "production code", "programming", "coding", "fluent in"]

ESG_TERMS = ["responsible ai", "ai governance", "ai ethics", "ai safety",
             "ethical ai", "esg", "sustainability", "sustainable", "net zero",
             "net-zero", "climate", "carbon", "decarbon", "social impact"]

CLIENT_TERMS = ["client", "customer-facing", "customer facing", "stakeholder",
                "workshop", "advisory", "engagement", "customer success",
                "field-facing", "external partners"]

ORIG_TERMS = ["business development", "pitch", "proposal",
              "statement of work", "pipeline", "revenue", "quota",
              "bookings", "new logo", "upsell", "cross-sell", "land and expand",
              "close deals", "sales target", "go-to-market"]

LEVEL_WORDS = ["intern", "junior", "graduate", "associate", "analyst",
               "consultant", "senior", "staff", "principal", "lead", "manager",
               "head", "director", "vp", "vice president", "partner", "chief"]

FOOTER_MARKERS = [
    "come work with us", "anthropic is a public benefit",
    "as a public benefit corporation", "equal opportunity employer",
    "we are an equal opportunity", "the expected salary range",
    "annual salary range", "salary range for this", "compensation range",
    "our benefits include", "deadline to apply", "e-verify",
    "accommodations for applicants", "guidance on candidates",
    "multimodal neurons", "scaling laws", "concrete problems in ai safety",
    "learning from human preferences", "core views on ai safety",
]
DISCLAIMER_RE = re.compile(
    r"[^.]*\b(vetted recruiting|be cautious of|fraudulent job|"
    r"identify themselves as working on behalf|never ask you to)\b[^.]*\.",
    re.I)
PAPER_NOISE = ["concrete problems in ai safety", "scaling laws",
               "multimodal neurons", "learning from human preferences",
               "come work with us", "equal opportunity"]


# ---------------------------------------------------------------------------
# Word-boundary matching
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _term_re(term):
    return re.compile(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])")


def has_term(text_l, term):
    return _term_re(term).search(text_l) is not None


def find_term(text_l, terms, boundary=True):
    for t in terms:
        if (has_term(text_l, t) if boundary else (t in text_l)):
            return t
    return None


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def http_get_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def http_post_json(url, payload, timeout=60):
    """POST a JSON body and parse the JSON response. Workday's cxs endpoint is
    POST-only. Wrong tenant/wd/site returns HTTP 422 (a trap that looks alive);
    only HTTP 200 is real, so callers treat any HTTPError as 'no data'."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA, "Content-Type": "application/json",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---------------------------------------------------------------------------
# Normalisation + register
# ---------------------------------------------------------------------------
def normalize(name):
    if not name:
        return ""
    s = name.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(t for t in s.split() if t and t not in LEGAL)


def load_register(path):
    exact = defaultdict(set)
    token_index = defaultdict(set)
    n = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw = (row.get("Organisation Name") or "").strip()
            route = (row.get("Route") or "").strip()
            nn = normalize(raw)
            if not nn:
                continue
            exact[nn].add(route)
            for tok in set(nn.split()):
                token_index[tok].add(nn)
            n += 1
    return exact, token_index, n


def is_known_large(nn):
    return any(k in nn for k in KNOWN_LARGE)


def visa_status(company, exact, token_index):
    nn = normalize(company)
    if not nn:
        return ("check", "company name missing — cannot match, flag for review")
    if nn in exact:
        routes = sorted(r for r in exact[nn] if r)
        if any("skilled worker" in r.lower() for r in routes):
            return ("plausible", "on register, Skilled Worker route")
        return ("plausible", "on register (routes: %s)" % (", ".join(routes) or "unspecified"))

    cands = set()
    for tok in nn.split():
        cands |= token_index.get(tok, set())
    cands = list(cands)

    def _tag(name):
        routes = sorted(r for r in exact.get(name, set()) if r)
        return "Skilled Worker route" if any("skilled worker" in r.lower() for r in routes) \
            else ("routes: %s" % (", ".join(routes) or "unspecified"))

    comp_tokens = set(nn.split())
    contain = [c for c in cands if comp_tokens and comp_tokens <= set(c.split())]
    if contain:
        best = min(contain, key=len)
        return ("plausible", 'register entry "%s" contains company name; %s' % (best, _tag(best)))

    if len(cands) > 600:
        cands.sort(key=lambda c: abs(len(c) - len(nn)))
        cands = cands[:600]
    best, best_r = None, 0.0
    for c in cands:
        ratio = SequenceMatcher(None, nn, c).ratio()
        if ratio > best_r:
            best_r, best = ratio, c
    if best_r >= 0.8:
        return ("plausible", 'fuzzy match -> "%s" (%.2f), %s' % (best, best_r, _tag(best)))
    if is_known_large(nn):
        return ("check", "no register match but large/multinational — likely licensed "
                          "under a variant/parent name; verify manually (false negative is costly)")
    return ("unlikely", "no register match; small/unknown firm")


# ---------------------------------------------------------------------------
# Location + comp gates
# ---------------------------------------------------------------------------
def location_status(loc, workplace="", country="", is_remote=None):
    s = (" %s %s %s " % ((loc or ""), (workplace or ""), (country or ""))).lower()
    if not s.strip():
        return ("keep", "location not stated — UNDETERMINED, flag")
    uk = any(has_term(s, t) for t in UK_TERMS)
    remote = (is_remote is True) or ("remote" in s)
    if uk:
        if remote:
            return ("keep", "UK-remote — flag (confirm London/in-person need)")
        return ("keep", "London/UK-anchored" if "london" in s else "UK location")
    leftover = [w for w in re.sub(r"[^a-z0-9 ]+", " ", s).split() if w not in REMOTE_ONLY_TOKENS]
    if remote and not leftover:
        return ("keep", "location-agnostic remote — UK-eligibility UNVERIFIED, flag")
    return ("filter", "non-UK location" + (" (remote)" if remote else ""))


_GBP_RE = re.compile(r"£\s?([0-9][0-9,\.]*)\s?(k|K)?")
_GBP_WORD_RE = re.compile(r"(?:gbp|£)\s?([0-9][0-9,\.]*)\s?(k|K)?", re.I)


def _to_number(num, k):
    try:
        v = float(num.replace(",", ""))
    except ValueError:
        return None
    if k:
        v *= 1000
    elif v < 1000:
        v *= 1000
    return v


def comp_status(comp_str, currency, jd_text):
    if comp_str and currency:
        if currency.upper() == "GBP":
            nums = [n for n in (_to_number(m.group(1), m.group(2))
                                for m in _GBP_WORD_RE.finditer(comp_str)) if n]
            if nums and max(nums) < 60000:
                return ("filter", "stated GBP comp below £60k hard floor, D026 (%s)" % comp_str, comp_str)
            if nums and max(nums) < 80000:
                return ("keep", "stated £60–80k — kept, graduated comp penalty D026", comp_str)
            return ("keep", "stated", comp_str)
        return ("keep", "stated (%s, non-GBP — floor is £-denominated)" % currency, comp_str)
    head = (jd_text or "")[:2500]
    hl = head.lower()
    if "per hour" in hl or "day rate" in hl or "per day" in hl:
        return ("keep", "comp present but hourly/day-rate — floor not applied", "not stated")
    nums = [n for n in (_to_number(m.group(1), m.group(2)) for m in _GBP_RE.finditer(head)) if n]
    if nums:
        mx = max(nums)
        disp = "£%s (parsed from JD)" % "{:,.0f}".format(mx)
        if mx < 60000:
            return ("filter", "stated GBP comp below £60k hard floor, D026 (%s)" % disp, disp)
        if mx < 80000:
            return ("keep", "stated £60–80k — kept, graduated comp penalty D026", disp)
        return ("keep", "stated ≥£80k", disp)
    return ("keep", "comp not stated (kept; confirm in screen)", "not stated")


# ---------------------------------------------------------------------------
# Text + signal extraction (OBSERVATIONS, not scores)
# ---------------------------------------------------------------------------
def clean_text(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def strip_boilerplate(text):
    if not text:
        return ""
    text = DISCLAIMER_RE.sub(" ", text)
    tl = text.lower()
    cut = len(text)
    for m in FOOTER_MARKERS:
        i = tl.find(m)
        if i > 200 and i < cut:
            cut = i
    body = text[:cut].strip()
    return body if len(body) > 150 else text


def looks_boilerplate(snip):
    sl = snip.lower()
    return any(p in sl for p in PAPER_NOISE)


def snippet(text, kw, width=180):
    i = text.lower().find(kw)
    if i < 0:
        return ""
    a = max(0, i - width // 3)
    b = min(len(text), i + width)
    return ("…" if a > 0 else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def sig_frontier(text_l):
    t = find_term(text_l, FRONTIER_NAMED, boundary=True)
    if t:
        return "named-frontier (%s)" % t
    t = find_term(text_l, FRONTIER_VAGUE, boundary=True)
    if t:
        return "vague AI/ML (%s)" % t
    return "none"


def sig_agency(text, text_l):
    for tier, terms in (("high", AGENCY_HIGH), ("med", AGENCY_MED), ("low", AGENCY_LOW)):
        t = find_term(text_l, terms, boundary=False)
        if t:
            q = snippet(text, t.strip(), 130) or t.strip()
            return '%s — "%s"' % (tier, q)
    return "not stated"


def sig_ic_tell(text_l):
    found = sorted({s for s in IC_STACK if has_term(text_l, s)})
    if not found:
        return "no"
    hard = any(c in text_l for c in IC_HARD_CUE)
    return "%s (%s) — %s" % ("yes" if hard else "mentioned",
                             "hard requirement" if hard else "soft/contextual",
                             ", ".join(found))


def sig_seniority(title, text):
    tl = title.lower()
    level = find_term(tl, LEVEL_WORDS, boundary=True)
    tx = text.lower()
    m = re.search(r"(\d+\+?\s*(?:to|[-–—])?\s*\d*\+?\s*years?)(?=[^.]{0,30}experience)", tx)
    if not m:
        m = re.search(r"(?:at least|minimum of|min\.?\s*of)\s*(\d+\+?\s*years?)", tx)
    if not m:
        m = re.search(r"(\d+\+\s*years?)", tx)
    yrs = m.group(1).strip() if m else "years not stated"
    return "%s | %s | level: %s" % (title, yrs, level or "not stated")


def sig_esg(text, text_l):
    for t in ESG_TERMS:
        if t in text_l:
            snip = snippet(text, t, 130)
            if snip and not looks_boilerplate(snip):
                return '"%s"' % snip
    return "not stated"


def sig_client(text_l):
    return "yes" if find_term(text_l, CLIENT_TERMS, boundary=False) else "no"


def sig_origination(text_l):
    t = find_term(text_l, ORIG_TERMS, boundary=False)
    if not t:
        return "no"
    strat = any(k in text_l for k in ("strategy", "strategic", "advisory", "roadmap"))
    return "yes (%s)" % ("strategy-bundled" if strat else "pure-sales lean")


def load_bearing_quote(text, text_l):
    for terms, b in ((ESG_TERMS, False), (AGENCY_HIGH, False),
                     (FRONTIER_NAMED, True), (AGENCY_MED, False), (CLIENT_TERMS, False)):
        t = find_term(text_l, terms, boundary=b)
        if t:
            q = snippet(text, t.strip(), 220)
            if q and not looks_boilerplate(q):
                return q
    return (text[:220] + "…") if text else "not stated"


# ---------------------------------------------------------------------------
# Per-provider fetchers -> normalised role dicts
# ---------------------------------------------------------------------------
def _uniq_join(parts, sep=" | "):
    seen, out = set(), []
    for p in parts:
        p = (p or "").strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return sep.join(out)


def fetch_greenhouse(slug, company):
    data = http_get_json("https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=true" % slug)
    out = []
    for j in data.get("jobs", []):
        out.append({
            "company": company, "title": (j.get("title") or "").strip(),
            "loc": (j.get("location") or {}).get("name", ""),
            "workplace": "", "country": "", "is_remote": None,
            "comp_str": "", "currency": "",
            "url": j.get("absolute_url", ""), "jd": clean_text(j.get("content", "")),
        })
    return out


def fetch_lever(slug, company):
    data = http_get_json("https://api.lever.co/v0/postings/%s?mode=json" % slug)
    out = []
    for j in data:
        cats = j.get("categories") or {}
        lists_txt = " ".join(
            clean_text((l.get("text") or "") + " " + (l.get("content") or ""))
            for l in (j.get("lists") or []))
        jd = " ".join(filter(None, [
            clean_text(j.get("descriptionPlain") or j.get("description") or ""),
            lists_txt, clean_text(j.get("additionalPlain") or "")]))
        out.append({
            "company": company, "title": (j.get("text") or "").strip(),
            "loc": _uniq_join([cats.get("location", "")] + (cats.get("allLocations") or [])),
            "workplace": j.get("workplaceType", "") or "",
            "country": j.get("country", "") or "", "is_remote": None,
            "comp_str": "", "currency": "",
            "url": j.get("hostedUrl", ""), "jd": jd,
        })
    return out


def fetch_ashby(slug, company):
    data = http_get_json("https://api.ashbyhq.com/posting-api/job-board/%s?includeCompensation=true" % slug)
    out = []
    for j in data.get("jobs", []):
        comp = j.get("compensation") or {}
        comp_str = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary") or ""
        currency = ""
        for c in (comp.get("summaryComponents") or []):
            if c.get("compensationType") == "Salary" and c.get("currencyCode"):
                currency = c["currencyCode"]
                break
        secs = j.get("secondaryLocations") or []
        sec = [s.get("location", "") if isinstance(s, dict) else str(s) for s in secs]
        out.append({
            "company": company, "title": (j.get("title") or "").strip(),
            "loc": _uniq_join([j.get("location", "")] + sec),
            "workplace": j.get("workplaceType", "") or "", "country": "",
            "is_remote": j.get("isRemote"),
            "comp_str": comp_str, "currency": currency,
            "url": j.get("jobUrl") or j.get("applyUrl") or "",
            "jd": clean_text(j.get("descriptionPlain") or j.get("descriptionHtml") or ""),
        })
    return out


FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby}


# ---------------------------------------------------------------------------
# Workday cxs layer — reaches the consulting / bank / pharma verticals that
# post via Workday and are INVISIBLE to Greenhouse/Lever/Ashby (the audit
# 2026-06-23 blind spot). The API is the easy part; the curated tenant registry
# (reference/workday-registry.md) is the hard part.
# ---------------------------------------------------------------------------
_WD_COUNT_RE = re.compile(r"^\s*\d+\s+location", re.I)   # "2 Locations" = a count, not a place
_WD_REQID_RE = re.compile(r"^[A-Za-z]{0,3}[-_]?\d{3,}")  # e.g. R00325732, R-254090


def load_workday_registry(path=WORKDAY_REGISTRY_PATH):
    """Parse the markdown table in reference/workday-registry.md into tenant
    dicts. The wd<N> column guard skips the header and |---| separator rows."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 5:
                continue
            company, tenant, wd, site, vertical = cols[:5]
            if not re.match(r"^wd\d+$", wd):  # skips header + separator rows
                continue
            out.append({"company": company, "tenant": tenant, "wd": wd,
                        "site": site, "vertical": vertical})
    return out


def _wd_location(j):
    """Workday puts location in different fields per tenant: locationsText when
    single-site; a bare 'N Locations' count when multi-site (city then only in
    externalPath); absent for Accenture (city in externalPath/bulletFields).
    Read them in that order. NOTE: multi-location roles are gated on their FIRST
    location only — the full list needs the detail endpoint (ingest's job)."""
    loc = (j.get("locationsText") or "").strip()
    if loc and not _WD_COUNT_RE.match(loc):
        return loc
    m = re.match(r"/job/([^/]+)/", j.get("externalPath") or "")
    if m:
        seg = m.group(1).replace("--", ", ").replace("-", " ")
        seg = re.sub(r"\s+", " ", seg).strip(" ,")
        if seg:
            return seg
    for b in (j.get("bulletFields") or [])[1:]:
        b = (b or "").strip()
        if b and not _WD_REQID_RE.match(b):  # skip req-ids
            return b
    return loc


def _workday_record(j, company, vertical, detail_base, matched_kw):
    path = j.get("externalPath") or ""
    return {
        "company": company, "title": (j.get("title") or "").strip(),
        "loc": _wd_location(j), "workplace": "", "country": "", "is_remote": None,
        "comp_str": "", "currency": "",       # cxs list view carries no comp
        "url": (detail_base + path) if path else detail_base,
        "jd": "",                              # discovery never reads the body (D014); that is ingest's job
        "matched_kw": matched_kw, "vertical": vertical, "slug": company,
        "posted": (j.get("postedOn") or "").strip(),
    }


def fetch_workday(entry, queries, limit=20, max_pages=2):
    """Poll one Workday tenant's cxs endpoint across the searchText query set,
    dedup by job path, return role dicts in the scout's normalised shape. Stays
    shallow (<= max_pages per query) — cxs throttles pagination under load."""
    tenant, wd, site = entry["tenant"], entry["wd"], entry["site"]
    company, vertical = entry["company"], entry["vertical"]
    base = "https://%s.%s.myworkdayjobs.com" % (tenant, wd)
    cxs = "%s/wday/cxs/%s/%s/jobs" % (base, tenant, site)
    detail_base = "%s/en-US/%s" % (base, site)
    seen, out = set(), []
    for q in queries:
        for page in range(max_pages):
            offset = page * limit
            try:
                data = http_post_json(cxs, {"appliedFacets": {}, "limit": limit,
                                            "offset": offset, "searchText": q})
            except Exception:  # 422/404/network -> this query yields nothing more
                break
            postings = data.get("jobPostings") or []
            if not postings:
                break
            for j in postings:
                key = j.get("externalPath") or j.get("title")
                if key in seen:
                    continue
                seen.add(key)
                out.append(_workday_record(j, company, vertical, detail_base, q))
            if (data.get("total") or 0) <= offset + limit:
                break
    return out


def fetch_workday_source(entry):
    try:
        return (entry, fetch_workday(entry, WORKDAY_QUERIES), "ok")
    except urllib.error.HTTPError as e:
        return (entry, [], "HTTP %s" % e.code)
    except Exception as e:  # noqa
        return (entry, [], "ERR %s" % type(e).__name__)


def title_matches(title):
    tl = title.lower()
    for kw in FUNCTION_KEYWORDS:
        if kw in tl:
            return kw
    return None


def fetch_source(src):
    provider, slug, company, vertical = src
    try:
        return (src, FETCHERS[provider](slug, company), "ok")
    except urllib.error.HTTPError as e:
        return (src, [], "HTTP %s" % e.code)
    except Exception as e:  # noqa
        return (src, [], "ERR %s" % type(e).__name__)


# ---------------------------------------------------------------------------
# Evaluate + signals
# ---------------------------------------------------------------------------
def evaluate(role, exact, token_index):
    visa = visa_status(role["company"], exact, token_index)
    loc = location_status(role["loc"], role["workplace"], role["country"], role["is_remote"])
    # agnostic-remote keep, but the title names a non-UK region -> filter
    if loc[0] == "keep" and "UNVERIFIED" in loc[1]:
        tl = role["title"].lower()
        if any(has_term(tl, h) for h in NON_UK_HINTS):
            loc = ("filter", "non-UK region named in title (remote)")
    comp = comp_status(role["comp_str"], role["currency"], role["jd"])
    kills = []
    if visa[0] == "unlikely":
        kills.append("visa")
    if loc[0] == "filter":
        kills.append("location")
    if comp[0] == "filter":
        kills.append("comp")
    return {"visa": visa, "loc": loc, "comp": comp, "kills": kills, "kept": not kills}


def signals(role):
    body = strip_boilerplate(role["jd"])
    bl = body.lower()
    return {
        "frontier": sig_frontier(bl), "agency": sig_agency(body, bl),
        "ic_tell": sig_ic_tell(bl), "seniority": sig_seniority(role["title"], body),
        "esg_edge": sig_esg(body, bl), "client_facing": sig_client(bl),
        "origination": sig_origination(bl), "quote": load_bearing_quote(body, bl),
    }


def _record(r):
    """Flatten a kept role + its precomputed signals into a JSON-safe record,
    so re-rendering needs no network and no JD re-parsing."""
    e, sg = r["eval"], signals(r)
    rec = {
        "company": r["company"], "title": r["title"], "vertical": r["vertical"],
        "slug": r.get("slug", ""), "url": r.get("url", ""),
        "loc_display": r.get("loc", ""), "matched_kw": r.get("matched_kw", ""),
        "posted": r.get("posted", ""),
        "visa_status": e["visa"][0], "visa_note": e["visa"][1],
        "loc_decision": e["loc"][0], "loc_reason": e["loc"][1],
        "comp_decision": e["comp"][0], "comp_note": e["comp"][1], "comp_disp": e["comp"][2],
    }
    rec.update(sg)
    return rec


def _write_cache(kept, meta):
    data = {"meta": meta, "kept": [_record(r) for r in kept]}
    with open(KEPT_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    sys.stderr.write("Cached %d kept roles -> %s\n" % (len(kept), KEPT_CACHE))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-firm", type=int, default=12, help="cap rendered kept roles per firm (0=off)")
    ap.add_argument("--chunk", type=int, default=25, help="roles per chunk in roles.md")
    ap.add_argument("--show-filtered", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "roles.md"))
    ap.add_argument("--workday-only", action="store_true",
                    help="poll only the Workday cxs registry (skip public boards)")
    ap.add_argument("--no-workday", action="store_true",
                    help="skip the Workday cxs layer (public boards only)")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    OUT = []
    w = OUT.append

    sys.stderr.write("Loading register…\n")
    exact, token_index, nreg = load_register(REGISTER_PATH)
    pool, source_report, total_pulled = [], [], 0

    if not args.workday_only:
        sys.stderr.write("Register loaded. Fetching %d boards…\n" % len(SOURCES))
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(fetch_source, SOURCES))
        for (provider, slug, company, vertical), roles, status in results:
            total_pulled += len(roles)
            matched = []
            for r in roles:
                kw = title_matches(r["title"])
                if kw:
                    r["matched_kw"] = kw
                    r["vertical"] = vertical
                    r["slug"] = slug
                    matched.append(r)
            pool.extend(matched)
            source_report.append((provider, slug, company, vertical, status, len(roles), len(matched)))

    if not args.no_workday:
        wd_registry = load_workday_registry()
        sys.stderr.write("Polling %d Workday tenants (cxs)…\n" % len(wd_registry))
        if wd_registry:
            with ThreadPoolExecutor(max_workers=6) as ex:
                wd_results = list(ex.map(fetch_workday_source, wd_registry))
            for entry, roles, status in wd_results:
                total_pulled += len(roles)
                # Workday roles are already query-relevant (searchText) — no title gate.
                pool.extend(roles)
                source_report.append(("workday", entry["tenant"], entry["company"],
                                      entry["vertical"], status, len(roles), len(roles)))

    for r in pool:
        r["eval"] = evaluate(r, exact, token_index)
    kept = [r for r in pool if r["eval"]["kept"]]
    filtered = [r for r in pool if not r["eval"]["kept"]]

    gate_filtered, gate_sole = defaultdict(int), defaultdict(int)
    for r in filtered:
        for g in r["eval"]["kills"]:
            gate_filtered[g] += 1
        if len(r["eval"]["kills"]) == 1:
            gate_sole[r["eval"]["kills"][0]] += 1

    # flags over the kept set
    f_visacheck = [r for r in kept if r["eval"]["visa"][0] == "check"]
    f_locflag = [r for r in kept if "flag" in r["eval"]["loc"][1] or "UNVERIFIED" in r["eval"]["loc"][1]]
    f_undet = [r for r in kept if "UNDETERMINED" in r["eval"]["loc"][1]]
    f_compflag = [r for r in kept if "flag" in r["eval"]["comp"][1]]

    kept_by_vert = defaultdict(int)
    for r in kept:
        kept_by_vert[r["vertical"]] += 1

    # cache the FULL kept-set so re-rendering needs no network
    _write_cache(kept, {
        "run_date": RUN_DATE, "nreg": nreg, "ndistinct": len(exact),
        "total_pulled": total_pulled, "n_matched": len(pool),
        "n_kept": len(kept), "n_filtered": len(filtered),
        "kept_by_vertical": dict(kept_by_vert),
        "gate_filtered": dict(gate_filtered), "gate_sole": dict(gate_sole),
        "source_report": [list(x) for x in source_report],
    })

    # ---- header ----
    w("# CareerVinny — batch scout roles (wide pull)\n")
    w("- **Run date:** %s" % RUN_DATE)
    w("- **Sponsor register:** %d rows, %d distinct normalised names (gov.uk, %s)" % (nreg, len(exact), RUN_DATE))
    w("- **Total roles pulled:** %d across %d sources" % (total_pulled, len(source_report)))
    w("- **Title-matched candidate pool:** %d" % len(pool))
    w("- **Kept after eligibility filter:** %d  (rendered, capped %s/firm: see chunks below)" % (len(kept), args.per_firm or "∞"))
    w("- **Filtered out:** %d\n" % len(filtered))
    w("**Kept by vertical:** " + ", ".join("%s %d" % (v, kept_by_vert[v]) for v in sorted(kept_by_vert)) + "\n")
    w("**Coverage:** " + COVERAGE_NOTE + "\n")
    dead = [(p, s) for (p, s, c, v, st, pu, m) in source_report if st != "ok"]
    if dead:
        w("**Dead/empty boards this run:** " + ", ".join("%s(%s)" % (s, st) for (p, s, c, v, st, pu, m) in source_report if st != "ok") + "\n")

    # ---- gate-pressure ----
    w("## Gate-pressure table (reporting only — never acted on)")
    w("| gate | roles filtered | sole-killer |")
    w("|---|---|---|")
    for g in ("visa", "location", "comp"):
        w("| %s | %d | %d |" % (g, gate_filtered.get(g, 0), gate_sole.get(g, 0)))
    w("\n_Market reveals what EXISTS; only the human's verdict reveals what he WANTS. "
      "Weights move on verdicts, never on these volumes. Caveat: register membership is "
      "necessary, not sufficient — licensed ≠ will sponsor THIS role._\n")

    # ---- flags / undetermined ----
    w("## Eligibility flags (kept roles needing human verification)")
    w("- **visa = check** (not matched on register but large/multinational — verify manually): %d" % len(f_visacheck))
    w("- **location flagged** (UK-remote / location-agnostic remote — confirm London/in-person): %d" % len(f_locflag))
    w("- **location UNDETERMINED** (no location data on posting): %d" % len(f_undet))
    w("- **comp flagged** (stated GBP below £80k soft floor): %d" % len(f_compflag))
    if f_visacheck:
        w("\n  visa-check roles: " + "; ".join("%s — %s" % (r["company"], r["title"]) for r in f_visacheck[:20]))
    if f_undet:
        w("\n  undetermined-location roles: " + "; ".join("%s — %s" % (r["company"], r["title"]) for r in f_undet[:20]))
    w("")

    # ---- per-firm cap ----
    if args.per_firm:
        seen, kept_render = defaultdict(int), []
        for r in kept:
            if seen[r["company"]] < args.per_firm:
                kept_render.append(r)
                seen[r["company"]] += 1
    else:
        kept_render = kept

    w("## Roles (%d rendered, capped %s/firm) — raw signal fields, NO scoring band (pre-calibration)\n"
      % (len(kept_render), args.per_firm or "∞"))

    chunk = args.chunk or len(kept_render) or 1
    for ci in range(0, len(kept_render), chunk):
        group = kept_render[ci:ci + chunk]
        w("### Chunk %d (roles %d–%d)\n" % (ci // chunk + 1, ci + 1, ci + len(group)))
        for i, r in enumerate(group, ci + 1):
            e, sg = r["eval"], signals(r)
            comp_disp = e["comp"][2]
            if "flag" in e["comp"][1]:
                comp_disp += " ⚠below £80k soft floor"
            w("**%d. %s — %s**  _(%s)_" % (i, r["company"], r["title"], r["vertical"]))
            w("- meta: %s | %s | comp: %s | visa: **%s** (%s) | %s" % (
                r["loc"] or "not stated", r.get("posted") or "age not stated",
                comp_disp, e["visa"][0], e["visa"][1], r["url"]))
            w("- loc-gate: %s (%s) | kw:`%s`" % (e["loc"][0], e["loc"][1], r["matched_kw"]))
            w("- frontier: %s | ic_tell: %s | client_facing: %s | origination: %s" % (
                sg["frontier"], sg["ic_tell"], sg["client_facing"], sg["origination"]))
            w("- agency: %s" % sg["agency"])
            w("- seniority: %s | esg_edge: %s" % (sg["seniority"], sg["esg_edge"]))
            w("- networkability: — (tested separately)")
            w('- quote: "%s"' % sg["quote"])
            w("")

    # ---- source report (appendix) ----
    w("## Appendix — source report")
    w("| provider | slug | company | vertical | status | pulled | title-matched |")
    w("|---|---|---|---|---|---|---|")
    for p, s, c, v, st, pu, m in source_report:
        w("| %s | %s | %s | %s | %s | %d | %d |" % (p, s, c, v, st, pu, m))
    w("")

    report = "\n".join(OUT)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    sys.stderr.write("Wrote %s (%d kept, %d rendered)\n" % (args.out, len(kept), len(kept_render)))
    # concise console summary
    print("Run %s | pulled %d | matched %d | kept %d | rendered %d | -> %s" %
          (RUN_DATE, total_pulled, len(pool), len(kept), len(kept_render), args.out))
    print("Kept by vertical: " + ", ".join("%s %d" % (v, kept_by_vert[v]) for v in sorted(kept_by_vert)))
    print("Gate-pressure: " + ", ".join("%s filt=%d/sole=%d" % (g, gate_filtered.get(g, 0), gate_sole.get(g, 0)) for g in ("visa", "location", "comp")))
    print("Flags: visa-check=%d, loc-flag=%d, undetermined=%d, comp-flag=%d" %
          (len(f_visacheck), len(f_locflag), len(f_undet), len(f_compflag)))


if __name__ == "__main__":
    main()
