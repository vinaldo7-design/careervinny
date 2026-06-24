#!/usr/bin/env python3
"""Fixture tests for the Workday cxs layer — parse + gate wiring, no network.

The fixtures are REAL cxs jobPostings captured during the 2026-06-24 probe
(DL001: behaviour verified, not asserted). Run from this directory:
    python3 test_workday.py
"""
import scout

# --- Real cxs jobPostings captured 2026-06-24 -------------------------------
ACCENTURE_LONDON = {  # Accenture omits locationsText; city is in externalPath
    "title": "IAM Consultant - London",
    "externalPath": "/job/London/IAM-Consultant---London_R00325732",
    "postedOn": "Posted 27 Days Ago",
    "bulletFields": ["R00325732", "Location Negotiable"],
}
ACCENTURE_VIETNAM = {
    "title": "Senior SAP BPE Consultant",
    "externalPath": "/job/Ho-ChiMinh-Viettel-Building/Senior-SAP-BPE-Consultant_R00317995",
    "postedOn": "Posted Today",
    "bulletFields": ["R00317995", "Ho Chiminh, Viettel Building"],
}
GSK_LONDON = {  # multi-location: 'N Locations' count -> city only in externalPath
    "title": "Supported Studies Asset Study Delivery Lead",
    "externalPath": "/job/UK--London--New-Oxford-Street/Supported-Studies-Asset-Study-Delivery-Lead_443248-1",
    "locationsText": "2 Locations", "postedOn": "Posted Yesterday",
    "bulletFields": ["443248"],
}
AZ_CHINA = {
    "title": "MR", "externalPath": "/job/China/MR_R-254090",
    "locationsText": "China", "postedOn": "Posted Today", "bulletFields": ["R-254090"],
}
AZ_LONDON = {
    "title": "Regulatory Affairs Manager",
    "externalPath": "/job/UK---London/Regulatory-Affairs-Manager_R-1",
    "locationsText": "UK - London", "postedOn": "Posted Today", "bulletFields": ["R-1"],
}

DETAIL = "https://x.wd3.myworkdayjobs.com/en-US/Careers"
fails = []


def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# --- _wd_location: the three location sources, read in order ---
check("accenture loc from externalPath", scout._wd_location(ACCENTURE_LONDON) == "London")
check("accenture vietnam loc from externalPath", "ho chiminh" in scout._wd_location(ACCENTURE_VIETNAM).lower())
check("gsk loc falls back past 'N Locations' to externalPath", "london" in scout._wd_location(GSK_LONDON).lower())
check("az loc from locationsText", scout._wd_location(AZ_LONDON) == "UK - London")
check("az china loc", scout._wd_location(AZ_CHINA) == "China")

# --- record shape ---
rec = scout._workday_record(ACCENTURE_LONDON, "Accenture", "consulting", DETAIL, "AI Strategy")
check("record url is detail_base + externalPath",
      rec["url"] == DETAIL + "/job/London/IAM-Consultant---London_R00325732")
check("record carries matched_kw", rec["matched_kw"] == "AI Strategy")
check("record jd empty (no body at discovery)", rec["jd"] == "")
check("record posted preserved", rec["posted"] == "Posted 27 Days Ago")


# --- gate wiring: London keeps, non-UK filters ---
def loc_decision(j):
    r = scout._workday_record(j, "X", "pharma", DETAIL, "q")
    return scout.location_status(r["loc"], r["workplace"], r["country"], r["is_remote"])[0]


check("London role passes location gate", loc_decision(ACCENTURE_LONDON) == "keep")
check("GSK London (multi-loc) passes location gate", loc_decision(GSK_LONDON) == "keep")
check("AZ London passes location gate", loc_decision(AZ_LONDON) == "keep")
check("China role filtered by location gate", loc_decision(AZ_CHINA) == "filter")

# --- full evaluate() on a known sponsor (Accenture is KNOWN_LARGE + on register) ---
exact, token_index, _ = scout.load_register(scout.REGISTER_PATH)
ev = scout.evaluate(scout._workday_record(ACCENTURE_LONDON, "Accenture", "consulting", DETAIL, "AI Strategy"),
                    exact, token_index)
check("Accenture London role is kept (gate-passing)", ev["kept"] is True)
check("Accenture visa not 'unlikely'", ev["visa"][0] != "unlikely")

# --- registry parser skips header/separator, reads 5 cols ---
reg = scout.load_workday_registry()
check("registry parses >= 5 tenants", len(reg) >= 5)
check("registry rows all have wd<N>", all(r["wd"].startswith("wd") for r in reg))
check("registry spans all three families",
      {"consulting", "bank", "pharma"} <= {r["vertical"] for r in reg})

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
