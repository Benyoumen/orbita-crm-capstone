# -*- coding: utf-8 -*-
"""Writes the PRD v4 (capstone-prd_v4.xlsx) from the v3 sheet: column F gets the answers of the
current prototype (any sales conversation into Orbita's own CRM: transcripts from any notetaker and
WhatsApp exports, attribution to the right opportunity or a new one, 22 fields with MEDDPICC,
per-field permissions, Explore), and row F33 (eval results) is generated from eval/results.json and
the test suites, so it can be regenerated after every live eval. The v3 file is never modified.

    python scripts/fill_prd.py            # runs the guardrail and Granola tests, reads eval/results.json
    python scripts/fill_prd.py --no-tests # uses the last known test counts
"""
import json
import os
import re
import shutil
import subprocess
import sys
from copy import copy

import openpyxl

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(KIT, "capstone-prd_v3.xlsx")
OUT = os.path.join(KIT, "capstone-prd_v4.xlsx")
# the mockup gate (python mockups/dados/qa_capstone.py) of 2026-10-28: behaviour and design checks at
# 1440 and 1280 px, and the checks of the full loop through the local server
GATE = {"probe": 536, "server": 12}


def rj(*p):
    with open(os.path.join(KIT, *p), encoding="utf-8") as fp:
        return json.load(fp)


def node_count(script):
    """Runs a node test file of the kit and returns (ok, total)."""
    r = subprocess.run(["node", script], cwd=KIT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = len(re.findall(r"^OK ", r.stdout, re.M))
    bad = len(re.findall(r"^FAIL ", r.stdout, re.M))
    return ok, ok + bad


def output_savings():
    """Size of the sparse, line-cited answers vs the same answers in the v3 contract (every field,
    current values echoed, timestamp and speaker per quote): a proxy for output tokens."""
    sparse = full = 0
    for f in sorted(os.listdir(os.path.join(KIT, "eval", "reference_outputs"))):
        ref = rj("eval", "reference_outputs", f)
        ref.pop("meeting_id", None)
        case = f.replace(".json", "")
        out = rj("eval", "outputs", "mock", case + ".json")
        v3 = {k: out[k] for k in ("meeting_id", "opportunity_id", "source_status", "run_status", "block_reason", "ignored_out_of_scope")}
        v3["fields"] = [{k: x[k] for k in ("field", "current_value", "current_approved", "status", "proposed_value", "note")}
                        | {"evidence": [{"timestamp": e["timestamp"], "speaker": e["speaker"], "quote": e["quote"]} for e in x["evidence"]]}
                        for x in out["fields"]]
        sparse += len(json.dumps(ref, ensure_ascii=False))
        full += len(json.dumps(v3, ensure_ascii=False))
    return sparse, full


def eval_text(tests):
    res = rj("eval", "results.json")
    cases = {c["case_id"]: c for c in rj("eval", "expected_results.json")["cases"]}
    labels = res["labels"]
    n_fields = len(rj("agent", "field_schema.json")["fields"])
    lines = ["Test set: the %d synthetic conversations of F32, each scored from the seed CRM by eval/run_eval.mjs against the expected status of all %d fields (and the value, key facts, notes, the new client and the ignored requests where the case defines them)." % (len(cases), n_fields)]
    live = {k: v for k, v in labels.items() if k != "mock"}
    m = labels.get("mock")
    if m:
        lines.append("")
        lines.append("Platform check (saved answers through the same reading, attribution, pre-checks, validator and write path, no model): %d/%d cases pass." % (m["passed"], m["total"]))
    lines.append("")
    if live:
        lines.append("Live model results (run %s):" % res["run_at"][:10])
        for k, v in live.items():
            u = v["usage"]
            lines.append("- %s: %d/%d cases pass · %d model calls · %s input + %s cached + %s output tokens · USD %.4f in total, USD %.4f per analysed conversation."
                         % (k, v["passed"], v["total"], u["calls"], f"{u['input_tokens']:,}", f"{u['cache_read_input_tokens']:,}", f"{u['output_tokens']:,}", u["cost_usd"], v["cost_per_call_usd"] or 0))
            for row in v["rows"]:
                if row["verdict"] != "PASS":
                    lines.append("  · %s failed (%s): %s" % (row["case_id"], cases[row["case_id"]]["name"].split(" - ")[0], "; ".join(row["fails"])[:220]))
        lines.append("Where a human was needed: every field that needs approval still goes through the seller's review; the failures above are what the seller would have had to catch.")
    else:
        lines.append("Live model results: NOT RUN YET. On 2026-10-28 this machine had no Anthropic API key, so no model was called. The comparison is ready to run (node agent/pipeline.mjs --all --model claude-sonnet-5-5 | claude-haiku-5-5 | claude-opus-5-5, then node eval/run_eval.mjs); this row is regenerated from eval/results.json by scripts/fill_prd.py, failures included.")
    g_ok, g_tot = tests["guardrails"]
    l_ok, l_tot = tests["granola"]
    lines.append("")
    lines.append("Guardrails in code: %d/%d tests pass (eval/guardrail_tests.mjs). Each feeds a deliberate defect and checks that the code catches it, for example: an invented quote, a stage jump, Closed Won, an impossible date, an unattributed economic buyer or champion, a seller-only field, a cut recording, another seller's opportunity, fields written before the new opportunity is approved, an automatic write on a contradiction, a field set to Never, an ambiguous match, a WhatsApp date that reads both ways, and Explore asked about an opportunity the user cannot read." % (g_ok, g_tot))
    lines.append("Optional Granola connector: %d/%d tests pass against a fake public API." % (l_ok, l_tot))
    lines.append("Prototype: the mockup gate passes %d behaviour and design checks in Edge at 1440 and 1280 px (each sample file dropped or pasted, attribution, new opportunity, permissions and Undo, Explore, contrast, accessibility, no prototype jargon) and %d checks of the full loop through the local server." % (GATE["probe"], GATE["server"]))
    return "\n".join(lines)


def answers(tests):
    sparse, full = output_savings()
    cut = round(100 * (1 - sparse / full))
    C = {}
    C[5] = "Sales: turn any sales conversation (a meeting transcript or a WhatsApp chat) into a seller-controlled update of the right opportunity in the company's own CRM"
    C[6] = "2026-10-28"
    F = {}
    F[9] = """The primary user is a B2B Account Executive at Orbita CRM, a mid-sized software company that sells a CRM to mid-sized businesses. They own a portfolio of open opportunities and talk to buyers all day: video calls recorded by a notetaker (Teams, Zoom, Google Meet, Granola, Otter), and WhatsApp threads in between. After each interaction they are expected to keep the opportunity accurate: the pain, the metrics, the economic buyer, the decision criteria and process, the paper process, the champion, the competition, the scope and budget, the commitments, the next step with its owner and date, and whether the stage has changed.

The seller is measured on closing deals, not on CRM administration. Updating the CRM competes with the next meeting, so it is delayed, done from memory or skipped, and the qualification fields go first. What is said on WhatsApp rarely reaches the CRM at all.

The sales manager is a secondary stakeholder: they rely on complete records for pipeline reviews and forecasts, and they use the same CRM to ask about the pipeline."""
    F[10] = """The workflow is the post-conversation CRM update: after every customer meeting or chat, the seller records what happened in the right opportunity. It recurs several times a day for every seller.

Today, the seller finishes the call and the notetaker produces a transcript; the buyer confirms terms on WhatsApp in the evening. Later, the seller opens the CRM, finds the opportunity, re-reads the transcript or scrolls the chat, works out what matters, and types it field by field. A new prospect needs a client and an opportunity created by hand first.

Because this is manual, deferred and spread across channels, records end up incomplete, vague or inconsistent. Qualification (MEDDPICC) is rarely complete, so the manager cannot tell real pipeline from hope and chases sellers before each pipeline review."""
    F[11] = """The workflow starts when the seller adds a conversation to Meetings: they drop the transcript file or the chat export, or paste the text, right after the meeting or the chat.

Example: "The discovery call with Acme Logistics has ended; the Teams transcript (.vtt) is dropped in Meetings, with Select your opportunity left on Detect."

The platform reads the format, names the voices (seller side from the roster, customer side from the client's contacts, unnamed voices as unattributed) and attributes the conversation: to the client's one open opportunity when the speakers, the title or the company named in it point to one client; to a new client and opportunity when nothing matches; or it asks the seller to choose. The seller can also pick the opportunity first. One click on Prepare CRM update creates the run.

A conversation that belongs to another seller's opportunity, or a recording cut mid-sentence, is blocked with the reason. An optional connector can also sync a Granola folder."""
    F[12] = """1. The seller runs a customer meeting on a video call, with a notetaker transcribing it, or exchanges messages on WhatsApp.

2. The seller moves straight to the next meeting; the CRM update is postponed.

3. Later, the seller opens the CRM, finds the right client and opportunity (or creates them for a new prospect), and opens the transcript or the chat side by side.

4. The seller looks for what matters: the pain and its metrics, who decides and how, the paper process, the champion, the competition, the scope and budget, the timeline, the commitments, the next step, its owner and date, and whether the stage should change.

5. The seller types or pastes this into the CRM fields and writes a short summary.

6. When the update has been postponed too long, the seller fills it in from memory, leaves the qualification fields blank, or never records what was agreed on WhatsApp.

7. Before the weekly pipeline review, the sales manager checks the records and chases sellers for missing or unclear updates."""
    F[13] = """1. Delay: the update happens hours or days later, from memory.

2. Admin time: re-reading transcripts and chats to find a few facts, then retyping them field by field.

3. Scattered channels: what is agreed on WhatsApp or in a quick call never reaches the CRM.

4. Attribution: the seller has to find the right client and opportunity, or create them, before anything else.

5. Qualification gaps: MEDDPICC elements (economic buyer, metrics, paper process, champion) are rarely recorded, so forecasts rest on guesswork.

6. Missed commitments: promises, owners and due dates are not captured, so follow-ups slip.

7. Stage drift: the stage is not updated, or is changed without evidence (a "let's sign" from someone who does not sign).

8. Unreliable sources: a recording can be cut, a voice can be unnamed, a conversation can belong to another seller. A solution must detect this instead of guessing.

9. Adoption risk: if reviewing takes longer than doing it by hand, sellers will not use it."""
    F[14] = """The agent should do the post-conversation CRM update for the seller: read the conversation in whatever format it comes, attribute it to the right opportunity (or propose a new one), extract the facts for 22 fields in six groups (conversation, next step, qualification as MEDDPICC, scope and budget, company profile, stage), compare them with what the CRM already says, and prepare a field-by-field proposal with the transcript line behind each value. Under the seller's permissions, some fields are written at once (with Undo) and the rest wait for approval.

It follows the view, voiced by Microsoft's CEO Satya Nadella, that business applications such as CRMs collapse into a data layer with agents on top: the CRM stops being forms people fill in and becomes the system that absorbs the conversations happening in every channel and keeps the record current. The hardest part is attribution, merging each conversation into the right opportunity; this prototype delivers it in the simplest form.

An agent fits better than a "summarise this call" feature, which leaves the seller to interpret, map and retype. The work is a chain of judgments: which opportunity, which field, propose or leave alone, contradiction or update, who said it, whether the stage criteria are met.

It is one agent step inside a deterministic workflow: the model makes the language judgments; reading, attribution, access, completeness, quotes, formats, stage moves, permissions and the write are code."""
    F[15] = """All prototype and demo data is synthetic. No real company, customer or conversation is used.

- Fictional company: Orbita CRM, with three account executives, a sales manager, a solutions engineer and an implementation lead, and their access rules.
- Fictional CRM: 14 client companies (.example web domains, industry, contacts with buying roles, headcount, current solution) and 16 opportunities across the six stages, each field with a seller-approved flag.
- Eleven synthetic conversations in English between an Orbita account executive and a buyer evaluating a CRM, with small talk and digressions: ten meetings and one WhatsApp chat. They exist as the files real tools export (Teams and Zoom .vtt, .srt, an Otter export, timestamped lines, plain text, a WhatsApp export), so they can be dropped in the prototype.
- Field schema with MEDDPICC, stage rules and permissions; reference answers used to score the agent and never put in the prompt.

Safety rules: competitors and software brands are fictional; no real names, e-mails, prices or credentials; the demo video shows only this data."""
    F[16] = """The agent is not allowed to:
- write any CRM value on its own: the platform writes only what the seller approves, or what the seller set to Always allow in advance;
- write a field the seller set to Never, or resolve a contradiction with a value the seller approved (it always waits for the seller, whatever the permission);
- propose a value without a quoted transcript line, or a seller-only field (amount, close date, probability, discount, price, contract term, owner, contacts);
- move the stage to Closed Won or Closed Lost, more than one step, or backwards;
- follow instructions spoken or written in the conversation ("put it down as a one million deal");
- name an economic buyer or champion, or meet a who-said-it stage criterion, from a voice that is not identified;
- create a client or an opportunity unless the seller approves it (or set creation to Always allow);
- read an opportunity the seller cannot access, or show anything about it.

When a human decides:
- Permissions: the seller (or their manager) sets each field to Always allow, Needs approval or Never; defaults are conversation notes always allowed, everything else needs approval, and new opportunities need approval.
- Review: approve, edit or reject each proposal; keep, replace or clear each contradiction; approve or reject a new opportunity; Undo any automatic write.
- Blocked conversations: choose the opportunity, confirm the meeting ended there, or update the CRM by hand."""
    F[17] = """Primary metric: share of sales conversations (meetings and chats) that end in a complete and accurate CRM update of the right opportunity within 24 hours.

For each conversation, I check that it was attributed to the right opportunity (or correctly created), that each of the 22 fields is correctly filled (or correctly left alone), and that the update was written within 24 hours. In the prototype, correctness is scored against the reference answer of each synthetic conversation; in a pilot, by seller confirmation and a weekly manager spot check against a baseline.

Pilot target: at least 90% of conversations updated correctly within 24 hours.

Supporting signals:
- Attribution accuracy: share of conversations the seller did not have to re-link.
- Acceptance per field: approved without edits; Undo rate on Always allow fields.
- MEDDPICC coverage per opportunity over time (elements known, of 8).
- Review time: median under two minutes.
- Cost per conversation: logged for every model call; target under USD 0.10 on the default model.
- Guardrail: zero values written without a citation and without a decision or a permission. This is a hard rule, not a target."""
    F[18] = """The demo shows conversations from different channels becoming CRM updates.

1. Explore: the seller asks "What's the status of Atlas Manufacturing?" and gets the answer from the CRM, with its source and what is still unknown.

2. Meetings: the seller drops a Teams transcript of the Acme Logistics discovery call. The page reads it, finds Acme's opportunity from the speakers, and the agent prepares the update.

3. Review: the conversation notes are already written (Always allow, with Undo); 19 other fields wait, each with the quote it comes from; MEDDPICC shows 8 of 8 known after this call. The seller approves the qualification section, edits the pain, rejects one field and submits. The stage moves to Solution.

4. New prospect: a Delta Pharma transcript matches no client; the review proposes the new client (with Livia Prado as contact) and the opportunity; the seller approves the creation.

5. WhatsApp: a chat export with Solaris Energy's Commercial VP is attributed by the contact name; his written agreement moves the deal from Negotiation to Contract.

6. Settings: the three permission levels, and the activity log of everything written."""
    F[19] = """Job statement: "When I finish a conversation with a customer, in a meeting or on WhatsApp, put what matters into the right opportunity, with evidence, so my CRM stays complete (qualification included) without retyping, and I stay in control of what is written."

The agent is hired to do the post-conversation CRM update: read the conversation, attribute it, extract the facts for the 22 in-scope fields, compare them with the CRM, and prepare a field-by-field proposal, writing at once only what the seller allowed in advance.

It is not hired to sell, decide the opportunity strategy, recommend solutions, draft proposals, price deals or talk to the customer. It succeeds when the seller trusts it enough to set more fields to Always allow over time, and when the CRM reflects what was actually said."""
    F[20] = """1. The seller adds a conversation to Meetings: drops the transcript or the chat export, or pastes it (or a Granola folder syncs it).

2. The platform reads the format, names the voices and attributes the conversation to one open opportunity, proposes a new client and opportunity, or asks the seller to choose.

3. Pre-checks run in code: access, completeness, and whether creating an opportunity is allowed. Blocked conversations stop here with the reason.

4. The agent reads the conversation with the opportunity's and client's current values and proposes the fields with evidence; contradictions are flagged; values equal to the approved ones are marked unchanged.

5. Fields under Always allow are written at once (with Undo); fields set to Never are dropped; the rest wait for the seller.

6. The seller reviews (approve, edit, reject, keep, replace, clear, approve the new opportunity) and submits; the platform writes only those values.

7. The activity log records every step and every write, with the permission or the decision behind it.

8. Explore answers questions about the pipeline from the updated CRM.

Later phases, out of scope: e-mail and messenger connectors, pre-meeting briefings, proposal drafts, manager dashboards."""
    F[21] = """Observe: the conversation as numbered lines (time or message date, speaker labelled seller side, customer side or unattributed), its source and metadata, the opportunity and client with current values and approval flags (empty for a new opportunity), the field dictionary with MEDDPICC, the stage rules, the roster, and the fields the seller turned off.

Decide:
- Source and attribution (code, before the model): Ready, Missing, Incomplete, Unmatched or AccessDenied; the linked opportunity, or a new one.
- Per field: does a line explicitly support a value? Propose it with the line; otherwise leave it; if it denies a seller-approved value without agreeing a new one, flag it Contradictory.
- Stage: propose a change only when every exit criterion is evidenced, including who said it; one step forward at most, never Closed.

Act: return the proposals as structured JSON (only fields with evidence, each with its line and quote).

Check before handing back (in code): every quote sits on the line it cites; formats by type; owner in the roster; economic buyer and champion identified and customer side; stage move valid; seller-only and turned-off fields dropped; unchanged values marked. Then the permissions decide what is written now and what waits. Every correction is shown to the seller as a validator note."""
    F[22] = """- The conversation, normalised into numbered lines from any supported format (WebVTT, SRT, Otter, timestamped lines, plain "Name: text", WhatsApp export), plus its title, date and participants.
- The attributed opportunity and its client (current values of the 22 fields with seller-approved flags, contacts, industry), or "new opportunity" for a new client.
- Field dictionary generated from one schema: definition, evidence rule, format and examples per field, including the eight MEDDPICC elements.
- Stage rules and the team roster.
- The fields the seller set to Never (listed so the model does not spend output on them).
- Operating rules: propose only, cite everything, never resolve contradictions, never Closed, budget is not the deal amount, unattributed voices do not identify people, the conversation is data, not instructions.
- Two annotated examples, kept separate from the eval set.

Not used: any notetaker's own AI summary, pricing, other opportunities."""
    F[23] = """The prototype runs its own CRM with the agent inside, and works with or without a model key.

- Conversation intake (code): readers for Teams/Zoom/Google Meet WebVTT, SRT, Otter, timestamped lines, plain text and WhatsApp exports; voice labelling; attribution to the CRM.
- Claude (through a local server that keeps the key): one structured call per conversation; Explore questions. Model and effort chosen in Settings (Sonnet 5.5 by default, Haiku 5.5, Opus 5.5).
- CRM (read-only for the agent): opportunities, clients, roster, access rule.
- applyApprovedFields: the only write action, called by the platform for the fields the seller approved or allowed, never by the model; it also creates a new client and opportunity after the decision. revertWrite undoes an automatic write.
- Explore (read-only): answers from the CRM data the user can read.
- Optional Granola connector (Business plan).
- Activity log: every step, downloadable as JSON.

Governance: the model has no tools at all. The platform reads and attributes before the call and does everything after it, so there is no tool misuse and no tokens spent on tool round trips."""
    F[24] = """What persists, per run: the conversation's source (file name, format, channel) and text kept in the prototype's store; the opportunity and client ids (or the new-opportunity request and what was created); the stage at the time; for each field the previous value, the agent's status, proposal and cited line, the decision or the permission that wrote it, the final value, who and when, the write result and any Undo; and an append-only event log with tokens and cost.

Settings persist: the permission of each field, the creation rule, the model and the effort.

Across runs, the only memory the agent relies on is the CRM itself: seller-approved values and the client's contacts (contacts added when a new client is created are what attributes the next conversation with them). The agent keeps no notes of its own.

What does not persist: no audio; rejected proposals are never used as context; nothing from one opportunity goes into another's run; personal or off-topic content is not extracted. Explore chats stay in the browser and never write."""
    F[25] = """For each conversation, the platform creates one reviewable run.

Run header: client and opportunity (or "new opportunity"), owner, stage, conversation title, date and channel, the run status, warnings, who prepared it (the model, or a saved result), and the MEDDPICC strip after this conversation with the question to ask next.

New opportunity: a card with the client name, the opportunity name, owner and stage, the contacts taken from the conversation, and Approve creation or Reject.

Proposal table: one row per field in six groups, with the current value (seller-approved or not), the proposal, a quote that opens the transcript at its line, and the decision. Always allow rows arrive written, with Undo; proposed rows have Approve, Edit (typed editor) or Reject; contradictory rows have Keep, Replace or Clear; no evidence, unchanged and off rows are folded per group; a section can be approved at once. Notes list the missing stage criteria, the ignored requests and the validator's corrections.

Blocked runs show the reason and the way out, and nothing to submit. After Submit: the result of each write, the record with its history, one sentence in the activity log."""
    F[26] = """The agent stops proposing when evidence is missing, unclear or contradictory, and the platform stops the run when the source is not usable.

Full stop (Blocked, no proposals), decided in code before the model:
- no readable transcript;
- a recording cut mid-sentence (with a booked length: under 60% of it); the seller can confirm the meeting ended there;
- another seller's opportunity: nothing about it is shown, the attempt is logged;
- no matching opportunity while creating opportunities is set to Never.

Ask the seller: several opportunities could match, or the company is new and needs a name.

Field-level stop: No evidence; Contradictory (the conversation cancels an approved value without agreeing a new one); Unchanged; Off (set to Never).

Risky cases: a "let's sign" from someone who does not sign does not move the stage; an unnamed voice cannot be the economic buyer or the champion; a spoken deal amount is ignored, never turned into budget; a contradiction never goes through Always allow; a failed write is shown as Failed with the old value kept.

Every stop, flag, decision and automatic write is recorded."""
    F[27] = """There are two checkpoints, both owned by the seller.

1. Permissions, set in advance in Settings (the pattern of tool permissions in Claude): for each field, Always allow (written as soon as the update is prepared, with Undo), Needs approval (proposed for review, written only after approval) or Never (left alone). The same three levels apply to creating a new client and opportunity. Defaults: conversation notes always allowed, everything else needs approval, new opportunities need approval.

2. The review page, for everything that needs approval: Approve, Edit (with the editor of the field's type) or Reject with an optional reason; Keep, Replace or Clear a contradiction; Approve creation or Reject a new opportunity. A section can be approved at once (one decision per field). Submit writes only approved or edited values; the platform re-checks the seller's own values first.

Fixed rules no permission changes: contradictions always wait for the seller; the stage never moves more than one step or to Closed; seller-only fields are never written by the agent.

Every decision and automatic write is recorded: field, previous value, proposal, cited line, decision or permission, final value, who, when, write result, Undo."""
    F[28] = """A fixed set of synthetic conversations linked to fictional opportunities, each with a written expected result for all 22 fields.

Case 1, happy path: a complete discovery call (all eight MEDDPICC elements, the stage moves one step).
Case 2, no evidence: no follow-up date and no further meeting; "No budget allocated" only because the customer says so.
Case 3, contradiction: the approved demo is cancelled with no new date.
Case 4, unusable source: a recording cut mid-sentence.
Case 5, new client: a company not in the CRM; nothing is created before the seller's decision.
Case 6, stage boundary: "let's sign" before the economic buyer has the proposal, a spoken "one million deal", a stated budget, a champion who is not the buyer.
Case 7, seller edit (pasted text).
Case 8, access boundary: another seller's opportunity.
Case 9, solution fit: a scope session with typed fields.
Case 10, speaker attribution: voices the notetaker could not name.
Case 11, chat: terms agreed on WhatsApp move the stage to Contract.

Every case also checks: the format read, the attribution, a citation on every proposal, quotes on the cited line, no seller-only fields, permissions respected, and a complete run log."""
    F[29] = """One loop, end to end and for real: a sales conversation in any common format becomes a proposed CRM update of the right opportunity (or a new one), with a citation for each value; per-field permissions decide what is written at once and what waits; the seller decides the rest; everything is logged. Explore answers questions about the pipeline.

Two parts share the same code:
- The kit: the field schema, a pure core (readers, attribution, pre-checks, validator, the only write path), Explore, the pipeline that calls Claude (one call per conversation, cached system prompt, structured output), the eval with its scorer and adversarial tests, and eleven sample files.
- Orbita's CRM, a web prototype that embeds the same core: Explore, Meetings (add a conversation), Review, Opportunities by stage, Clients, Chat, and Settings (permissions, agent, sources, team, activity log, quality checks, data).

It runs offline (saved results for the sample files, Explore from rules over the CRM) and live through a small local server that keeps the Claude key."""
    F[30] = """- Explore: ask about a client, an opportunity or the pipeline (status, overdue follow-ups, what is missing to qualify, competition, what waits for review), or click a suggested question; open the opportunity from the answer.
- Meetings: leave Select your opportunity on Detect (or pick one, or New opportunity), then drop a file or paste the text; check the format, the speakers and the attribution with its reason; Prepare CRM update.
- Review: read each proposal and its quote (a click opens the transcript at that line); Approve, Edit, Reject, Keep, Replace, Clear; approve a whole section; Undo an automatic write; approve or reject a new opportunity; Submit.
- Opportunities and Clients: the funnel by stage with MEDDPICC per deal, one card per client, the record drawer with the questions to ask next and the history.
- Settings: set each field to Always allow, Needs approval or Never; choose the model and the effort; see the sources; switch user to see the access rules; read the activity log; replay the quality checks; reset the CRM."""
    F[31] = """All files are synthetic, created for this project (fictional company: Orbita CRM).

1. Field schema (agent/field_schema.json): 22 fields in six groups with record, type, format, evidence rule, examples, MEDDPICC letter and question, and default permission. The dictionary, output schema, validator, scorer, permissions page and screens derive from it.
2. CRM seed: 14 clients and 16 opportunities (data/clients.json, data/opportunities.json), also as CSV.
3. Team roster with access rules (data/team.json).
4. Eleven conversations: ten meetings (data/granola/authoring/, also in the Granola API format) and one WhatsApp export (data/channels/): T1 Acme Logistics discovery; T2 Verde Retail intro; T3 Nimbus Health demo cancelled; T4 Verde Retail cut recording; T5 Delta Pharma, a new client; T6 Atlas Manufacturing "let's sign"; T7 Cedro Construtora; T8 Horizonte Foods, another seller's; T9 Lumen Education scope session; T10 Pampa Agro, unnamed voices; T11 Solaris Energy on WhatsApp.
5. samples/: the same eleven as the files real tools export (WebVTT, SRT, Otter, timestamped lines, plain text, WhatsApp), each checked to read back to the same text.
6. Stage rules and agent policy (policies/); output and run-log schemas (agent/).
7. Two annotated few-shot examples, kept out of the test set.
8. Expected results and reference answers (eval/), scored by eval/run_eval.mjs."""
    F[32] = """Eleven test conversations, each run from the seed CRM and scored on all 22 fields:

T1 Happy path (Acme Logistics, Teams .vtt): every MEDDPICC element with a citation; Qualified Opportunity → Solution; due 2026-11-06 from "by Friday".
T2 No evidence (Verde Retail): due date and stage left alone; "No budget allocated".
T3 Contradiction (Nimbus Health, Otter): next step and due date Contradictory; budget Unchanged.
T4 Unusable source (Verde Retail, Zoom .vtt): cut mid-sentence → Blocked: Incomplete.
T5 New client (Delta Pharma): a new client and opportunity proposed, named from the file, with the contact; nothing created before approval.
T6 Stage boundary (Atlas Manufacturing, .srt): no stage change, the note names the CFO; "one million deal" ignored; budget USD 120,000; champion Tiago Mendes; paper process.
T7 Seller edit (Cedro Construtora, pasted text): the CRM gets the seller's text, both versions kept.
T8 Access boundary (Horizonte Foods): Blocked: AccessDenied, nothing shown.
T9 Solution fit (Lumen Education): seats 120, departments, integrations, decision process, paper process, go-live 2027-05; Solution → Proposal.
T10 Speaker attribution (Pampa Agro): unnamed voices; no economic buyer, no champion, no stage change.
T11 Chat (Solaris Energy, WhatsApp): attributed by the contact; "tomorrow" → 2026-11-06; Negotiation → Contract.

Boundary tests in code (eval/guardrail_tests.mjs) feed deliberate defects to the readers, the attribution, the validator, the permissions, the write path, Explore and the scorer; the mockup gate checks the same cases through the seller's screens."""
    F[33] = eval_text(tests)
    F[34] = """What changed after testing v3 (Teams only, 8 fields) and building v4:

1. Any conversation: readers for the common transcript exports and WhatsApp, and attribution in code to the right opportunity (or a new one); v3 needed a pre-linked Teams meeting.
2. New opportunities: a company the CRM does not know becomes a proposed client and opportunity, with its contacts; nothing is created without the seller.
3. Permissions in three levels per field, with Undo, instead of approving every field every time; contradictions still always wait.
4. MEDDPICC qualification: eight elements with coverage on every deal and the question to ask next.
5. Evidence cited by line; the validator fills time and speaker and fixes a quote on the wrong line.
6. Fewer output tokens: only fields with evidence, no echo of current values: %d%% less output than the v3 format on the reference answers (%s vs %s characters); the static prompt (~27k characters) is cached.
7. Structured outputs from the field schema: no parse failures or retries.
8. Completeness that fits files without a booked length: a mid-sentence ending blocks, with a seller override; chats are never cut.
9. Speaker rule: an unnamed voice cannot be the economic buyer or the champion (T10).
10. One core for every host (CLI, server, page), and Explore over the same CRM.
11. Bugs found by the mockup gate, now guarded: a page under the sticky bar, a drawer that lost its route, a pasted text read as a company name, unreadable MEDDPICC letters.

Model choice: Sonnet 5.5, Haiku 5.5 and Opus 5.5 run on the same conversations, with accuracy and cost per conversation (F33); Sonnet 5.5 stays the default until that scoreboard exists.""" % (cut, f"{sparse:,}", f"{full:,}")
    F[35] = """- Live accuracy is not measured yet: no model has been called on this machine (no API key on 2026-10-28). F33 will carry the live scoreboard, failures included.
- Offline, only the eleven sample files have a result; any other conversation needs the local server with a Claude key.
- Attribution is heuristic (contacts who speak, the client in the title or file name, the domain, mentions); a new contact at a known client, or a shared first word, can need the seller's choice.
- Readers cover the common exports (WebVTT, SRT, Otter, timestamped and plain lines, WhatsApp on Android and iPhone); a .docx must be pasted as text.
- Speaker names depend on the notetaker; unnamed voices limit what can be proven about who said what.
- Completeness is a heuristic (a mid-sentence ending); the seller can override it.
- The CRM, the permissions and the chats live in the prototype's browser store: no multi-user backend, no real-time notification.
- E-mail, Telegram and Messenger are not connected yet; Granola is an optional connector (Business plan).
- The agent never edits contacts (it adds the speakers of a new client) and never writes amount, close date or probability.
- English only. The eval set is small (11 conversations) and author-written; a pilot needs real, consented conversations."""
    F[36] = """The working prototype is Orbita's CRM with the agent inside.

1. Explore: "What's the status of Atlas Manufacturing?" is answered from the CRM (stage, amount, next step overdue since 5 Nov, MEDDPICC 3 of 8, what to ask next), with its source and a button to the record.
2. Meetings: the banner shows meetings of yours and updates waiting for review; the Acme Logistics .vtt is dropped and attributed on its own ("Marina Lopes is a contact at Acme Logistics").
3. Review: 22 fields in six groups, the conversation notes already written with Undo, MEDDPICC 8 of 8 after this call; the seller approves the qualification section, edits the pain and submits; Acme moves to Solution and the client profile lands on the client record.
4. Delta Pharma: a new client and opportunity, created only after Approve creation, appear in Clients and in the funnel at New Lead.
5. WhatsApp: the Solaris Energy chat moves the deal to Contract, with "tomorrow" resolved from the message date.
6. Edge cases on screen: a contradiction (Keep, Replace or Clear), a cut recording (blocked, with "the meeting ended there"), "let's sign" with a "one million deal" (no stage change, amount ignored), unnamed voices (no economic buyer), another seller's conversation (nothing shown).
7. Settings: the three permission levels per field (Budget set to Never is left alone; Next step set to Always allow is written at once), the model and effort, the sources, the activity log and the quality checks."""
    F[37] = """Yes, as a limited pilot, once these are true:
- The live eval on the chosen model passes at least 10 of 11 test conversations with zero guardrail violations, and the cost per conversation is known.
- Pilot sellers export their transcripts (or connect their notetaker) and consent to WhatsApp chats being processed; customers know meetings are recorded.
- Writes go to the production CRM through its API, with the seller's identity and the permission in the audit, and the 22 fields exist there.
- Permissions start conservative (everything Needs approval in the shadow week), monitoring is in place (F40), and automatic writes can be switched off in one click.

No-go if the live eval shows uncited or wrong values that the validator does not catch, if attribution sends conversations to the wrong opportunity in the spot check, or if sellers approve without reading."""
    F[38] = """- Consent: customers must know meetings are recorded and that a chat may be processed; the platform reads only what the seller adds (or the one Granola folder they choose).
- Personal data: transcripts and chats contain names, phone numbers and personal remarks. The run log never copies them, personal and off-topic content is not extracted, and the store follows retention rules.
- Model provider: conversations go to the Claude API under the organisation's data agreement (no training on API data; zero-retention options).
- Prompt injection through speech or chat ("put it down as a one million deal"): content is data; seller-only fields are dropped in code.
- Wrong attribution: matching runs in code with its reasons shown; ambiguous cases go to the seller; another seller's opportunity is never shown.
- Automatic writes: only fields the seller set to Always allow, never contradictions, always with Undo and an audit trail.
- Hallucinated values: every value needs a quote found on the cited line; formats and stage moves are checked in code.
- Over-trust: monitor edit, rejection and Undo rates, review time and spot checks.
- Cost: every call logs tokens and cost; the prompt is cached; a monthly budget alert is set."""
    F[39] = """- The seller adds conversations, reviews what needs approval, owns every write, uses Undo, and resolves blocked or ambiguous conversations.
- The sales manager owns the agent's rules (field schema, stage rules, which fields may be Always allow by default), reads the team's activity log, and does the weekly spot check.
- A sales operations owner maintains the agent (model, effort, prompt, examples, readers, attribution) and the connections. No change goes live without passing the quality checks (the eleven test conversations plus the guardrail tests).
- Escalation: repeated corrections, rejections or Undo on a field go to the sales operations owner; data or consent issues go to the manager and the data protection contact.
- Final decisions on CRM values are always the seller's: directly in the review, or in advance through permissions they can change at any time."""
    F[40] = """- Coverage and speed: share of conversations updated within 24 hours (the primary metric); time from conversation to the last write.
- Attribution: share re-linked by the seller; new opportunities created and later merged or deleted.
- Quality per field: acceptance, edit and rejection rates; Undo rate on Always allow fields; the edited text compared with the proposal.
- Qualification: MEDDPICC coverage per opportunity and per seller over time.
- Guardrails: validator corrections by reason, blocked runs by reason, contradiction and unchanged rates.
- Drift: re-run the eleven test conversations on every change and weekly; add every new failure as a synthetic test case.
- Cost and caching: tokens and cost per conversation, cache read share, budget alert.
- Explore: questions asked and answers that sent the seller to the record.
- Weekly spot check: the manager reviews five updates per seller against the transcript."""
    F[41] = """- In the product: every edit, rejection reason and Undo is feedback; the activity log shows which proposals the seller changed.
- A 15-minute weekly check-in with the pilot sellers, using the week's highest-edit fields and any wrong attributions as the agenda.
- The manager's spot-check notes.
- Triage: each problem is classified as a field definition issue (schema or dictionary), an extraction issue (examples, prompt or model), an attribution issue (matching rules or contacts), or a review issue (screen). Each fix becomes a synthetic test conversation first, then the change, then the quality checks.
- Permissions as a trust signal: fields sellers move to Always allow, and back, show where the agent has earned trust."""
    F[42] = """Smallest safe launch: three account executives and their manager for four weeks.
- Each seller adds their meeting transcripts (and, with consent, WhatsApp exports) for their own opportunities.
- Week 1, shadow mode: every field on Needs approval; sellers still update the CRM by hand too, and we compare the two.
- Weeks 2 to 4: writes on; conversation notes on Always allow; other fields move to Always allow only when their edit rate stays under 10%.
- Success at the end: at least 90% of conversations updated within 24 hours, correct attribution in at least 95%, median review under two minutes, edit rate under 20% per field, zero uncited writes.
- Rollback: set every field to Needs approval or turn the agent off; the CRM keeps the reviewed values and the audit."""
    F[43] = """0:00-0:30 Intro and problem: an account executive at a CRM company, back-to-back calls and WhatsApp threads, a CRM that is always behind.
0:30-1:00 Discovery and vision: where it breaks (delay, retyping, scattered channels, attribution, missing qualification); the CRM that absorbs conversations instead of waiting for forms.
1:00-2:30 Demo: Explore question → drop the Acme transcript (attributed on its own) → review with Always allow already written, approve, edit, submit → Delta Pharma as a new client → the WhatsApp chat to Contract → Settings, the three permission levels.
2:30-3:15 Eval rigor: the eleven test conversations and what each proves; the guardrail tests; the model scoreboard with accuracy and cost per conversation; what failed and what changed.
3:15-3:45 Impact: the metric (correct update within 24 hours), attribution, review time, cost.
3:45-4:00 Launch plan: the four-week pilot, the shadow week, permissions that open as trust grows."""
    F[44] = "Yes. Every grading-critical decision is written in this sheet: the user, workflow, trigger, boundaries, fields, stage rules, permissions, tools, memory, output, escalation, approval, eval cases and results, limitations, risks, operating model, monitoring, pilot and video. File names are mentioned only to locate the prototype's parts; nothing requires opening them to assess the work."
    F[45] = "Yes. F29 and F30 describe the loop and what the user does, F36 describes what the prototype shows step by step, and the video demo follows the same steps (Explore, add a conversation, review, new client, WhatsApp, permissions)."
    F[46] = "Planned as outlined in F43: four minutes, with the demo at the centre and the eval rigor shown with the real scoreboard. To be confirmed once the video is recorded."
    return C, F


def main():
    run_tests = "--no-tests" not in sys.argv
    tests = {"guardrails": node_count("eval/guardrail_tests.mjs") if run_tests else (49, 49),
             "granola": node_count("eval/granola_live_test.mjs") if run_tests else (7, 7)}
    shutil.copyfile(SRC, OUT)
    wb = openpyxl.load_workbook(OUT)
    ws = wb.worksheets[0]
    model = ws.cell(10, 6)
    C, F = answers(tests)
    for r, v in C.items():
        ws.cell(r, 3).value = v
    for r, text in F.items():
        cell = ws.cell(r, 6)
        cell.value = text
        cell.font = copy(model.font)
        cell.alignment = copy(model.alignment)
        cell.border = copy(model.border)
        cell.fill = copy(model.fill)
        # the v3 heights fit 92 characters per line and 13.2 pt per line in column F (width 80, Roboto 10)
        lines = sum(max(1, -(-len(par) // 92)) for par in text.split("\n"))
        height = round(lines * 13.2 + 10, 1)
        if height > 409:  # Excel's maximum row height: the rest of the text would be hidden
            print("WARNING: F%d needs %.0f pt and Excel stops at 409; shorten it" % (r, height))
        ws.row_dimensions[r].height = min(409.0, max(46.5, height))
    wb.save(OUT)
    print("PRD v4 written: %s (%d answers; guardrails %d/%d, granola %d/%d)" % (OUT, len(F), *tests["guardrails"], *tests["granola"]))


if __name__ == "__main__":
    main()
