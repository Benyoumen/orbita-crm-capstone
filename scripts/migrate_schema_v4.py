# -*- coding: utf-8 -*-
"""One-off migration (31/10/2026): the CRM fields become picklists where a sales CRM reports on categories.

    python scripts/migrate_schema_v4.py

What changes: agent/field_schema.json (version 4: `options` and `allow_other` per field), the CRM seed
(data/opportunities.json, data/clients.json), the saved answers (eval/reference_outputs), the few-shot
examples (examples/EX1-2) and the oracle (eval/expected_results.json). Every old value is mapped by hand
below; an unmapped value stops the script, so nothing is guessed. The specifics that a category cannot hold
(a name, a figure, a system) move to the field's note. Run once; a second run finds nothing to map and stops.
"""
import json
import os
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(KIT, *a)


def rj(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def wj(p, o):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)
        f.write("\n")


OPTIONS = {
    "objection": ["Integration with current systems", "User adoption and ease of use", "Mobile or offline access", "Data residency and privacy",
                  "Budget freeze or no budget", "Price or discount", "Payback or ROI", "Timing or other priorities", "Implementation effort",
                  "Data migration", "Security or IT review"],
    "decision_criteria": ["Pipeline management", "Lead capture and routing", "Tasks and follow-up reminders", "Email and calendar sync",
                          "WhatsApp messaging", "Mobile app", "Offline mode", "Visit and activity tracking", "Orders and quotes",
                          "Renewal and contract tracking", "Account hierarchy", "Reporting and dashboards", "Forecasting", "Integrations and API",
                          "Data hosted in Brazil", "Ease of use"],
    "paper_process": ["Signature by the economic buyer", "Procurement review", "Competitive quotes required", "Legal contract review",
                      "Data processing agreement", "Security questionnaire", "Purchase order", "Board approval"],
    "customer_need": ["Customer data scattered across spreadsheets and inboxes", "No pipeline view leaders can trust", "Missed follow-ups or renewals",
                      "Leads lost or not routed", "Visits and orders not tracked", "Legacy system nobody likes", "Manual reporting",
                      "Teams do not share one view", "Data must stay in the country"],
    "competitors": ["Northwind CRM", "PipeSpark", "Clarion Sales Cloud", "Helix CRM", "Vantage Sales", "In-house build"],
    "integrations": ["Email and calendar", "ERP", "Billing system", "WhatsApp Business", "Website forms", "Single sign-on", "Marketing automation",
                     "Telephony", "Industry or in-house system"],
    "budget": ["No budget allocated", "Budget exists but amount not shared", "Under USD 50k per year", "USD 50k-100k per year",
               "USD 100k-150k per year", "USD 150k-250k per year", "Over USD 250k per year"],
    "employee_count": ["1-49", "50-199", "200-499", "500-999", "1000-4999", "5000+"],
    "current_solution": ["Spreadsheets", "Email and shared inbox", "WhatsApp groups", "Paper forms", "Shared drive", "Another CRM",
                         "Legacy on-premise CRM", "ERP module", "Partner portal"],
}
NOTE_RULE = "Put the specifics (names, figures, systems) in the note."
FIELD_PATCH = {
    "objection": dict(type="multiselect", allow_other=True,
        definition="The concerns or blockers the customer raised in this conversation, as categories.",
        evidence="A concern stated by a customer-side speaker. Our own worries do not count.",
        format="One or more options separated by '; '; 'Other: <few words>' when none fits. " + NOTE_RULE,
        good="Integration with current systems; User adoption and ease of use",
        bad="a sentence that retells the conversation (the specifics go in the note)"),
    "decision_criteria": dict(type="multiselect", allow_other=True,
        definition="What the customer will judge the CRM on: the capabilities they say they need.",
        evidence="A requirement, must-have or comparison point stated by the customer. List every supported criterion, not only the first.",
        format="One or more options separated by '; '; 'Other: <few words>' for a capability not in the list. " + NOTE_RULE,
        good="Pipeline management; Email and calendar sync; Mobile app", bad="Good CRM (no capability)"),
    "paper_process": dict(type="multiselect", allow_other=True,
        definition="How a decided purchase gets signed: the steps between the yes and the signature.",
        evidence="A stated step: who signs, procurement, quotes, legal review, data processing agreement. A contract routing written in a chat counts.",
        format="One or more options separated by '; '; 'Other: <few words>' when none fits. " + NOTE_RULE,
        good="Procurement review; Competitive quotes required; Signature by the economic buyer", bad="They will sign soon (no step)"),
    "customer_need": dict(type="multiselect", allow_other=True,
        definition="The business pain the CRM must solve, as categories.",
        evidence="A problem described by the customer (what goes wrong today, and its cost).",
        format="One or more options separated by '; '; 'Other: <few words>' when none fits. " + NOTE_RULE,
        good="Customer data scattered across spreadsheets and inboxes; Missed follow-ups or renewals", bad="Wants a CRM (no pain)"),
    "competitors": dict(type="multiselect", allow_other=True,
        definition="Other CRM vendors the customer is evaluating or using.",
        evidence="A vendor named as an alternative being considered. A status-quo tool (spreadsheets) belongs in Current solution.",
        format="One or more vendors from the list separated by '; '; 'Other: <vendor name>' for a vendor not in the list.",
        good="Northwind CRM; PipeSpark", bad="Spreadsheets (that is the current solution)"),
    "integrations": dict(type="multiselect", allow_other=True,
        definition="The systems the CRM must connect to.",
        evidence="A system the customer says the CRM must read from or write to.",
        format="One or more options separated by '; '; 'Other: <system>' when none fits. Name the actual systems in the note.",
        good="ERP; Email and calendar; Single sign-on", bad="Integrations (no system)"),
    "budget": dict(type="select", allow_other=False,
        definition="The money the customer says is available for the CRM, as a band.",
        evidence="An amount, range or explicit 'no budget' stated by the customer. A request to record a deal amount is seller-only, never budget.",
        format="Exactly one option. A figure on a band boundary goes to the higher band; a stated range goes to the band that holds most of it. Put the exact figure in the note.",
        good="USD 50k-100k per year", bad="USD 80,000 per year (not an option: choose the band and put the figure in the note)"),
    "employee_count": dict(type="select", allow_other=False, label="Company size (employees)",
        definition="How many people the client company employs, as a band.",
        evidence="A headcount stated by the customer.",
        format="Exactly one option. Put the exact figure in the note.",
        good="500-999", bad="850 (not an option: choose the band)"),
    "current_solution": dict(type="multiselect", allow_other=True,
        definition="What the client uses today to manage customers and sales.",
        evidence="A tool or practice the customer says they use now.",
        format="One or more options separated by '; '; 'Other: <few words>' when none fits. " + NOTE_RULE,
        good="Spreadsheets; Email and shared inbox", bad="Nothing good (no tool)"),
}

# ---- old value -> new value (seed records and examples' context)
SEED = {
    "objection": {"Patient data must stay in Brazil": "Data residency and privacy",
                  "Procurement wants a 12% discount for a 3-year term": "Price or discount",
                  "Wants payback within 18 months": "Payback or ROI"},
    "decision_criteria": {"Contract renewals pipeline; account hierarchy; forecast dashboards": "Renewal and contract tracking; Account hierarchy; Forecasting; Reporting and dashboards",
                          "Referral tracking; patient-relations cases; clinic dashboards": "Reporting and dashboards; Other: referral tracking; Other: patient-relations cases"},
    "customer_need": {"Dealer visits and orders tracked in one place (from a trade-fair lead)": "Visits and orders not tracked",
                      "Manage distributor orders and quotes in one CRM instead of spreadsheets and a shared inbox": "Customer data scattered across spreadsheets and inboxes; Visits and orders not tracked",
                      "One view of orders and visits for 40 distributors": "Visits and orders not tracked",
                      "Portal for distributors to place orders (raised during the key account call)": "Other: distributor ordering portal",
                      "Replace the 2014 on-premise CRM with one shared view of B2B energy contracts and renewals": "Legacy system nobody likes; Teams do not share one view",
                      "Track B2B lab-services contracts with hospitals and clinics": "Other: lab-services contracts not tracked",
                      "Track patient relations and doctor referrals for 14 clinics in one CRM, with data hosted in Brazil": "Teams do not share one view; Data must stay in the country",
                      "Track prospective students from first contact to enrolment across 6 campuses": "Leads lost or not routed; Teams do not share one view",
                      "Wants a CRM for the sales team (from the inbound web form)": "Other: wants a CRM for the sales team"},
    "competitors": {"Northwind CRM": "Northwind CRM"},
    "integrations": {"Billing system; email and calendar": "Billing system; Email and calendar", "Clinic scheduling system": "Industry or in-house system"},
    "budget": {"USD 90,000 per year": "USD 50k-100k per year", "USD 150,000 per year": "USD 150k-250k per year",
               "USD 200,000 per year": "USD 150k-250k per year", "USD 50,000 per year": "USD 50k-100k per year"},
    "employee_count": {"700": "500-999", "900": "500-999", "1200": "1000-4999", "1500": "1000-4999", "1800": "1000-4999", "2400": "1000-4999",
                       "2600": "1000-4999", "3100": "1000-4999", "5200": "5000+"},
    "current_solution": {"Broker portal plus spreadsheets for the channel team": "Partner portal; Spreadsheets",
                         "Legacy on-premise CRM from 2014": "Legacy on-premise CRM",
                         "Patient-relations module of the clinic ERP, plus spreadsheets": "ERP module; Spreadsheets",
                         "Spreadsheets and a shared inbox for distributor orders": "Spreadsheets; Email and shared inbox",
                         "Spreadsheets per key account manager": "Spreadsheets",
                         "Two regional CRMs that do not share accounts": "Another CRM",
                         "WhatsApp groups and spreadsheets per distributor": "WhatsApp groups; Spreadsheets"},
}
# ---- the saved answers and the examples: (case, field) -> (value, note); note None keeps the existing note
REF = {
    ("T1", "objection"): ("Integration with current systems; User adoption and ease of use", "In-house TMS integration, especially near peak season; reps abandoned a previous sales tool."),
    ("T1", "decision_criteria"): ("Pipeline management; Email and calendar sync; Mobile app; Renewal and contract tracking; Reporting and dashboards; Integrations and API", "Renewal alerts; Outlook email sync; dashboards for Marina; shipment status from the TMS."),
    ("T1", "paper_process"): ("Procurement review; Competitive quotes required; Signature by the economic buyer", "Three quotes for anything above USD 50,000; then Marina signs."),
    ("T1", "customer_need"): ("Customer data scattered across spreadsheets and inboxes; Missed follow-ups or renewals; No pipeline view leaders can trust", "Two renewals missed last quarter; they need one place for every account and deal."),
    ("T1", "integrations"): ("Industry or in-house system; ERP; Email and calendar", "In-house TMS; Orion ERP; Outlook email."),
    ("T1", "budget"): ("USD 50k-100k per year", "USD 80,000-100,000 per year."),
    ("T1", "employee_count"): ("500-999", "About 850 employees."),
    ("T1", "current_solution"): ("Spreadsheets; Email and shared inbox; Shared drive", "Spreadsheets, Outlook and a shared drive for proposals."),
    ("T2", "objection"): ("User adoption and ease of use", "A previous BI tool failed because it was too complicated and the store teams stopped using it."),
    ("T2", "customer_need"): ("Customer data scattered across spreadsheets and inboxes; Visits and orders not tracked", "Franchisees and wholesale buyers managed in WhatsApp groups: orders, visits and complaints."),
    ("T2", "budget"): ("No budget allocated", None),
    ("T2", "employee_count"): ("1000-4999", "About 1,200 employees."),
    ("T2", "current_solution"): ("WhatsApp groups; Spreadsheets", None),
    ("T3", "objection"): ("Budget freeze or no budget", "The board froze all new IT projects until the January budget review."),
    ("T3", "budget"): ("USD 50k-100k per year", "The budget itself is unchanged: USD 90,000 per year."),
    ("T5", "decision_criteria"): ("Visit and activity tracking; Mobile app; Other: sample tracking", "Plan visits, record what was discussed, track samples, works on a tablet."),
    ("T5", "customer_need"): ("Legacy system nobody likes", "Visit reports live in a very old system nobody likes; Delta is looking at options for next year."),
    ("T6", "paper_process"): ("Legal contract review; Signature by the economic buyer", "Helena Duarte (CFO) approves; Legal reviews the contract in about two weeks; then Helena signs."),
    ("T6", "budget"): ("USD 100k-150k per year", "USD 120,000 per year."),
    ("T7", "objection"): ("User adoption and ease of use; Mobile or offline access", "External brokers won't use anything complicated; sales stands often have no mobile signal."),
    ("T7", "decision_criteria"): ("Lead capture and routing; WhatsApp messaging; Pipeline management", "Leads from the website, WhatsApp and stands routed to brokers; one funnel per launch."),
    ("T7", "paper_process"): ("Legal contract review; Signature by the economic buyer", "Legal reviews the contract; then Sofia signs."),
    ("T7", "customer_need"): ("Leads lost or not routed", "Every lead from the website, WhatsApp and sales stands in one place, routed to a broker, one funnel per launch."),
    ("T7", "integrations"): ("Website forms; WhatsApp Business", None),
    ("T7", "budget"): ("USD 50k-100k per year", "USD 60,000 per year."),
    ("T7", "employee_count"): ("200-499", "About 400 employees."),
    ("T7", "current_solution"): ("Paper forms; WhatsApp groups; Spreadsheets", "Paper forms, the website form and WhatsApp, typed into a spreadsheet."),
    ("T9", "objection"): ("Data residency and privacy; Security or IT review", "Student data must stay in Brazil; a data protection assessment comes before go-live."),
    ("T9", "decision_criteria"): ("Lead capture and routing; Tasks and follow-up reminders; Pipeline management; WhatsApp messaging", "Leads from campaigns; counsellor follow-up lists; enrolment funnel per campus; WhatsApp on the prospect record."),
    ("T9", "paper_process"): ("Procurement review; Data processing agreement", "Procurement needs the standard contract and the data processing agreement two weeks before signature."),
    ("T9", "integrations"): ("Industry or in-house system; Marketing automation; WhatsApp Business", "Campus One student information system; Mailwave; WhatsApp business account."),
    ("T9", "budget"): ("USD 100k-150k per year", "USD 110,000-130,000 per year."),
    ("T9", "current_solution"): ("Spreadsheets; WhatsApp groups", "Spreadsheets per campus and WhatsApp."),
    ("T10", "objection"): ("Mobile or offline access; User adoption and ease of use", "No mobile signal in the fields; reps are not used to apps."),
    ("T10", "decision_criteria"): ("Offline mode; Visit and activity tracking; Orders and quotes", "Works offline; GPS check-in at each visit; dealer visit and order records."),
    ("T10", "customer_need"): ("Visits and orders not tracked", "One place for every dealer visit, order and promise."),
    ("T10", "integrations"): ("ERP", "Orion ERP."),
    ("T10", "budget"): ("USD 50k-100k per year", "USD 70,000 per year."),
    ("T10", "employee_count"): ("200-499", "About 450 employees."),
    ("T10", "current_solution"): ("Paper forms; Spreadsheets", "Paper visit reports typed into a spreadsheet."),
    ("T11", "paper_process"): ("Procurement review; Signature by the economic buyer", "Talita Moura (Procurement) routes the contract on 9 Nov; Henrique Prado signs right after."),
    ("T11", "integrations"): ("Billing system; Email and calendar; Single sign-on", "Adds Microsoft Entra single sign-on from day one to the existing list."),
    ("EX1", "objection"): ("Implementation effort", "Small, busy team; cannot take on a heavy implementation."),
    ("EX1", "customer_need"): ("Customer data scattered across spreadsheets and inboxes; Missed follow-ups or renewals", "One place for every group request and corporate account, with follow-up reminders."),
    ("EX1", "decision_criteria"): ("Pipeline management; Tasks and follow-up reminders", "Shared view of group requests and corporate accounts; follow-up reminders."),
    ("EX1", "employee_count"): ("500-999", "About 600 employees."),
    ("EX1", "current_solution"): ("Email and shared inbox; Spreadsheets", None),
    ("EX2", "objection"): ("Timing or other priorities", "The clinic managers' team is being reorganised; no new date for the demo."),
    ("EX2", "budget"): ("USD 50k-100k per year", "USD 50,000 per year."),
}
# ---- the oracle: (case, field) -> the new expectation (replaces the old one)
EXP = {
    ("T1", "objection"): {"status": "proposed", "must_include": [["Integration with current systems"], ["User adoption"]]},
    ("T1", "decision_criteria"): {"status": "proposed", "must_include": [["Pipeline management"], ["Renewal and contract tracking"], ["Mobile app"]]},
    ("T1", "paper_process"): {"status": "proposed", "must_include": [["Competitive quotes required", "Procurement review"]]},
    ("T1", "customer_need"): {"status": "proposed", "must_include": [["Customer data scattered"], ["Missed follow-ups or renewals", "No pipeline view"]]},
    ("T1", "integrations"): {"status": "proposed", "must_include": [["Industry or in-house system"], ["ERP"]]},
    ("T1", "budget"): {"status": "proposed", "value": "USD 50k-100k per year"},
    ("T1", "employee_count"): {"status": "proposed", "value": "500-999"},
    ("T1", "current_solution"): {"status": "proposed", "must_include": [["Spreadsheets"], ["Email and shared inbox"]]},
    ("T2", "objection"): {"status": "proposed", "must_include": [["User adoption"]]},
    ("T2", "customer_need"): {"status": "proposed", "must_include": [["Customer data scattered", "Visits and orders not tracked"]]},
    ("T2", "employee_count"): {"status": "proposed", "value": "1000-4999"},
    ("T2", "current_solution"): {"status": "proposed", "must_include": [["WhatsApp groups"], ["Spreadsheets"]]},
    ("T3", "objection"): {"status": "proposed", "must_include": [["Budget freeze", "Timing or other priorities"]]},
    ("T3", "budget"): {"status_any": ["unchanged", "proposed"], "value": "USD 50k-100k per year"},
    ("T5", "decision_criteria"): {"status": "proposed", "must_include": [["Visit and activity tracking"], ["sample"]]},
    ("T5", "customer_need"): {"status": "proposed", "must_include": [["Legacy system"]]},
    ("T6", "paper_process"): {"status": "proposed", "must_include": [["Legal contract review"]]},
    ("T6", "budget"): {"status": "proposed", "value": "USD 100k-150k per year", "must_not_include": ["Over USD 250k"]},
    ("T7", "objection"): {"status": "proposed", "must_include": [["User adoption"], ["Mobile or offline access"]]},
    ("T7", "decision_criteria"): {"status": "proposed", "must_include": [["Lead capture and routing"], ["Pipeline management"]]},
    ("T7", "paper_process"): {"status_any": ["proposed", "no_evidence"], "must_include": [["Legal contract review"]]},
    ("T7", "customer_need"): {"status": "proposed", "must_include": [["Leads lost or not routed"]]},
    ("T7", "integrations"): {"status_any": ["proposed", "no_evidence"], "must_include": [["Website forms", "WhatsApp Business"]]},
    ("T7", "budget"): {"status": "proposed", "value": "USD 50k-100k per year"},
    ("T7", "employee_count"): {"status": "proposed", "value": "200-499"},
    ("T7", "current_solution"): {"status": "proposed", "must_include": [["Spreadsheets"]]},
    ("T9", "objection"): {"status": "proposed", "must_include": [["Data residency and privacy"]]},
    ("T9", "decision_criteria"): {"status": "proposed", "must_include": [["Lead capture and routing"], ["Pipeline management"], ["WhatsApp messaging"]]},
    ("T9", "paper_process"): {"status": "proposed", "must_include": [["Data processing agreement"]]},
    ("T9", "customer_need"): {"status_any": ["proposed", "unchanged", "no_evidence"], "must_include": [["Leads lost", "Teams do not share", "student", "enrol"]]},
    ("T9", "integrations"): {"status": "proposed", "must_include": [["Industry or in-house system"], ["Marketing automation"], ["WhatsApp Business"]]},
    ("T9", "budget"): {"status": "proposed", "value": "USD 100k-150k per year"},
    ("T9", "current_solution"): {"status": "proposed", "must_include": [["Spreadsheets"], ["WhatsApp groups"]]},
    ("T10", "objection"): {"status": "proposed", "must_include": [["Mobile or offline access"]]},
    ("T10", "decision_criteria"): {"status": "proposed", "must_include": [["Offline mode"], ["Visit and activity tracking"]]},
    ("T10", "customer_need"): {"status": "proposed", "must_include": [["Visits and orders not tracked"]]},
    ("T10", "integrations"): {"status": "proposed", "must_include": [["ERP"]]},
    ("T10", "budget"): {"status": "proposed", "value": "USD 50k-100k per year"},
    ("T10", "employee_count"): {"status": "proposed", "value": "200-499"},
    ("T10", "current_solution"): {"status": "proposed", "must_include": [["Paper forms"], ["Spreadsheets"]]},
    ("T11", "paper_process"): {"status": "proposed", "must_include": [["Procurement review"], ["Signature by the economic buyer"]]},
    ("T11", "integrations"): {"status_any": ["proposed", "no_evidence"], "must_include": [["Single sign-on"]]},
}


def main():
    sp = P("agent", "field_schema.json")
    schema = rj(sp)
    if schema.get("version", 0) >= 4:
        sys.exit("schema already at version %s: nothing to migrate" % schema["version"])
    for d in schema["fields"]:
        if d["key"] in FIELD_PATCH:
            d.update(FIELD_PATCH[d["key"]])
            d["options"] = OPTIONS[d["key"]]
            d.pop("max_words", None)
        if d["key"] == "departments":
            d.update(type="multiselect", allow_other=False, options=schema["departments"],
                     format="One or more options separated by '; '.")
        if d["key"] in ("call_summary", "commitment", "next_step", "metrics", "decision_process"):
            d["type"] = "text"
    schema.pop("departments", None)
    schema["version"] = 4
    schema["description"] = schema["description"].replace("Values are always stored as strings (or null)",
        "Values are always stored as strings (or null); picklist fields (select, multiselect) hold their options, several joined by '; ', and 'Other: <text>' where allow_other is true")
    wj(sp, schema)

    miss = []

    def seed(rec_fields, where):
        for k, table in SEED.items():
            v = (rec_fields.get(k) or {}).get("value")
            if v is None or v == "":
                continue
            if v in table:
                rec_fields[k]["value"] = table[v]
            elif v not in table.values():
                miss.append("%s %s: %r" % (where, k, v))

    for name in ("opportunities.json", "clients.json"):
        p = P("data", name)
        recs = rj(p)
        for r in recs:
            seed(r.get("fields") or {}, r.get("opportunity_id") or r.get("client_id"))
        wj(p, recs)

    def answer(case, out_path):
        o = rj(out_path)
        for f in o.get("fields", []):
            key = (case, f["field"])
            if key in REF:
                f["value"], note = REF[key]
                if note is not None:
                    f["note"] = note
            elif f["field"] in OPTIONS and f.get("value") and not all(x.strip() in OPTIONS[f["field"]] for x in f["value"].split(";")):
                miss.append("%s %s: %r" % (case, f["field"], f["value"]))
        wj(out_path, o)

    for name in sorted(os.listdir(P("eval", "reference_outputs"))):
        if name.endswith(".json"):
            answer(name[:-5], P("eval", "reference_outputs", name))
    for ex in ("EX1", "EX2"):
        answer(ex, P("examples", ex + "_expected_output.json"))
        cp = P("examples", ex + "_context.json")
        ctx = rj(cp)
        for rec in [ctx.get("opportunity") or {}, ctx.get("client") or {}]:
            seed(rec.get("fields") or {}, ex + " context")
        wj(cp, ctx)

    ep = P("eval", "expected_results.json")
    exp = rj(ep)
    for c in exp["cases"]:
        for k in list((c.get("fields") or {}).keys()):
            if (c["case_id"], k) in EXP:
                c["fields"][k] = EXP[(c["case_id"], k)]
            elif k in OPTIONS and any(x in c["fields"][k] for x in ("value", "value_any", "must_include")) and not (
                    c["fields"][k].get("value") in OPTIONS[k] or all(any(o.lower().startswith(g.lower()) or g.lower() in o.lower() for o in OPTIONS[k]) for grp in c["fields"][k].get("must_include", []) for g in grp[:1])):
                miss.append("expected %s %s: %s" % (c["case_id"], k, json.dumps(c["fields"][k])))
        # a list of departments keeps its value (departments were already a picklist)
    wj(ep, exp)
    if miss:
        print("UNMAPPED (fix the tables, then restore the files and run again):")
        for m in miss:
            print("  " + m)
        sys.exit(1)
    print("schema v4 written; seed, saved answers, examples and expected results migrated")


if __name__ == "__main__":
    main()
