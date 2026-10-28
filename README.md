# Orbita CRM agent v5: prototype kit (Product Faculty capstone)

Orbita CRM is a fictional B2B software company that sells a CRM to mid-sized companies. Its CRM has an agent inside: the seller adds a sales conversation (a meeting transcript from any notetaker, or a WhatsApp chat export), the agent **attributes it to the right opportunity** (or proposes a new one) and proposes an update of **22 fields**, each with the transcript line it comes from. The seller decides what is written, field by field or through per-field permissions (Always allow, Needs approval, Never). **Explore** answers questions about the pipeline from the CRM. All data is synthetic.

This folder is the kit: field schema, synthetic CRM and conversations, policies, the pure core (reading, attribution, pre-checks, validator, write path), Explore, the pipeline that calls Claude, the eval with its scorer, and `samples/` (the conversations as files to drop). The mockup that uses it lives in `mockups/` (see `mockups/LEIAME.md`).

## Quick start (Node 22+)
```bash
npm install                                   # one dependency: @anthropic-ai/sdk (loaded only for live calls)
node agent/pipeline.mjs --all --dry-run       # pre-checks only: T4 and T8 blocked before the model; the others Ready
node agent/pipeline.mjs --all --mock          # offline: saved answers through the same validator -> eval/outputs/mock/
node eval/run_eval.mjs                        # scores every label in eval/outputs/ -> eval/results.md + eval/results.json
npm test                                      # adversarial guardrail tests + the Granola connector against a fake API

# any transcript or chat export, read and attributed exactly as the page does it
node agent/pipeline.mjs --file "samples/WhatsApp Chat with Henrique Prado.txt" --mock

# live, with the real model (key in capstone/.env, see .env.example)
node agent/pipeline.mjs --all --model claude-sonnet-5-5
node agent/pipeline.mjs --all --model claude-haiku-5-5
node agent/pipeline.mjs --all --model claude-opus-5-5
node eval/run_eval.mjs                        # one row per model: passed, tokens, cost per meeting
python scripts/fill_prd.py                    # PRD v4 (row F33 regenerated from eval/results.json and the tests)

node scripts/build_data.mjs                   # rebuild every synthetic file, the samples and the reference line numbers
```

## Architecture: one agent call inside a deterministic pipeline
```
any conversation (file or pasted text; Teams/Zoom .vtt, .srt, Otter, Granola, WhatsApp export)
  -> parseConversation + labelSpeakers (code): lines, speakers, seller side from the roster
  -> matchConversation (code): contacts, client in the title, domain, mentions -> one opportunity, a new one, or ask
  -> pre-checks (code): access, completeness, permissions (a new opportunity may be off)
  -> ONE model call (cached system prompt + compact per-conversation message)
  -> typed validator (code) -> permissions: Always allow written now (with Undo), the rest waits for the seller
  -> applyApprovedFields (code, the only write; also creates the client and opportunity) -> activity log
```
No multi-agent setup: one conversation produces one structured answer. Splitting fields across agents would resend the transcript N times, add a merge step and allow answers that disagree, while every guardrail already runs in code. Explore is a separate, read-only job over the validated CRM.

**Token optimisations** (measured by `eval/run_eval.mjs`, which records input, cache and output tokens and the cost of every live call):
- **Prompt caching**: the static system block (policy, the generated field dictionary, stage rules, two examples, ~7k tokens) is identical for every run and cached; from the second call it is read at ~0.1x.
- **Numbered transcript**: evidence is `{line, quote}`; the validator fills the timestamp and speaker from the line.
- **Sparse output**: the model returns only fields with evidence (plus the stage), never echoes current values; fields the seller turned off are listed in the message and dropped in code.
- **Compact input**: current values as `field: value [approved]`, empty ones omitted.
- **Structured outputs** (`output_config.format`, JSON schema generated from the field schema): no parsing failures, no retries.
- **Effort** `medium` by default (`ORBITA_EFFORT`); model set by `ORBITA_MODEL` (default `claude-sonnet-5-5`) or per request from the page's Settings. The variables are `ORBITA_*` on purpose: Claude Code sets `CLAUDE_EFFORT` in its own shell.
- Sonnet 5.5 and Opus 5.5 calls carry the server-side refusal fallback (`fallbacks: "default"`).

## One core, three hosts
`agent/core.mjs`, `eval/score.mjs` and `agent/explore.mjs` are pure (no file system, no network). The CLI, the local server (`mockups/server.mjs`) and the generated mockup page (which embeds the three files verbatim) run the same code.

## Folder map
| Path | What it is |
|---|---|
| `capstone-prd_v4.xlsx` | The PRD, written by `scripts/fill_prd.py` from `capstone-prd_v3.xlsx` (kept intact); F33 comes from `eval/results.json` |
| `agent/field_schema.json` | **Single source of truth** for the 22 fields: group, record (opportunity or client), kind, type, format, evidence rule, examples, MEDDPICC letter and question, default permission |
| `agent/core.mjs` | Pure rules: `parseConversation`, `labelSpeakers`, `matchConversation`, `attribute`, `prepareRun`, `buildUserMessage`, `validateOutput`, `applyApprovedFields`, `revertWrite`, `meddpiccOf`, permissions |
| `agent/explore.mjs` | Explore: `exploreContext` (only what the user can read), `answerQuestion`, `exploreSuggestions` |
| `agent/pipeline.mjs` | Reads the kit, builds the prompt, calls Claude through the SDK (`callJson`), logs usage and cost; `--file` reads any transcript |
| `agent/granola.mjs` | Optional Granola connector: fixtures and live sync of one folder (polling, pagination, 413, 429) |
| `agent/system_prompt.md` | Prompt template; `agent/output_schema.json` is generated |
| `agent/run_log_schema.json` | Run record (with the permission behind every write) and the append-only event log |
| `policies/` | Agent policy and stage rules (hand-written); `field_dictionary.md` is generated from the schema |
| `data/clients.json`, `data/opportunities.json` | CRM seed: 14 clients (domain, industry, contacts, profile fields) and 16 opportunities across the six stages |
| `data/team.json` | 3 account executives, 1 sales manager, 1 solutions engineer, 1 implementation lead, with access rules |
| `data/granola/authoring/`, `data/channels/` | The ten meetings as written, and the WhatsApp export |
| `data/meetings.json`, `data/channel_meetings.json`, `transcripts/` | What the agent reads (generated) |
| `samples/` | The eleven conversations as files to drop in the page (WebVTT, SRT, Otter, timestamped lines, plain text, WhatsApp; generated, each checked to read back to the same text) |
| `examples/EX1, EX2` | Few-shot examples used in the prompt (Mar Azul Hotels, Bela Vista Clinics); never part of the eval |
| `eval/expected_results.json` | Expected outcome per case and field (the oracle) |
| `eval/reference_outputs/` | Correct answers in the model's format; used by `--mock` and as the page's saved results. **Never put them in the prompt** |
| `eval/score.mjs`, `eval/run_eval.mjs` | Scorer and results by label (mock, each model) |
| `eval/guardrail_tests.mjs`, `eval/granola_live_test.mjs` | Every guardrail fed a deliberate defect; the Granola connector against a fake API |

## The 22 fields
| Group | Fields |
|---|---|
| Conversation (per-conversation) | call_summary, objection, commitment |
| Next step | next_step, follow_up_owner (roster), follow_up_due_date (YYYY-MM-DD) |
| Qualification (MEDDPICC) | metrics (M), decision_maker = economic buyer (E), decision_criteria (D), decision_process (D), paper_process (P), customer_need = pain (I), champion (C), competitors = competition (C) |
| Scope and budget | seats (integer), departments (from a list), integrations, budget (USD, customer-stated), go_live_target (YYYY-MM) |
| Company profile (client record) | employee_count (integer), current_solution |
| Stage | stage (one step forward at most, never Closed) |

Seller-only, never proposed: deal amount, close date, probability, discount, price, contract term, owner, contacts. **Budget is not the deal amount.** Economic buyer and champion must be identified customer-side people, never an unattributed voice.

Default permissions: the conversation notes are **Always allow**; everything else **Needs approval**; a new opportunity **Needs approval**. A contradiction with an approved value always waits for the seller, whatever the permission.

Stages: `New Lead → Qualified Opportunity → Solution → Proposal → Negotiation → Contract`, then `Closed Won` / `Closed Lost` (seller only). Exit criteria in `policies/stage_rules.md`.

## Test cases
| Case | Conversation | Scenario | Expected |
|---|---|---|---|
| T1 | Acme Logistics (.vtt) | Complete discovery call | Every MEDDPICC element; Qualified Opportunity → Solution; due 2026-11-06 |
| T2 | Verde Retail | Intro, no date | Due date and stage = no evidence; "No budget allocated" |
| T3 | Nimbus Health (Otter) | The approved demo is cancelled | Next step and due date contradictory; budget unchanged |
| T4 | Verde Retail (.vtt) | Recording cut mid-sentence | Blocked: Incomplete |
| T5 | Delta Pharma (.vtt) | Company not in the CRM | New client and opportunity proposed; nothing created before the decision |
| T6 | Atlas Manufacturing (.srt) | "Let's sign" before the CFO has the proposal; "one million deal"; budget stated | No stage change (note names the CFO); amount ignored; champion and paper process proposed |
| T7 | Cedro Construtora (pasted text) | Seller edits a proposal | Edited value written; both versions kept |
| T8 | Horizonte Foods (.vtt) | Another seller's opportunity | Blocked: AccessDenied, nothing shown |
| T9 | Lumen Education (.vtt) | Scope session | Typed fields valid; Solution → Proposal |
| T10 | Pampa Agro | Voices the notetaker could not name | No economic buyer, no champion, no stage change |
| T11 | Solaris Energy (WhatsApp) | Terms agreed in a chat | Negotiation → Contract; "tomorrow" from the message date |

## How the guardrails work
1. **Before the model** (code): the conversation is read and attributed (one open opportunity, a new one, or the seller chooses); the seller can read the opportunity; the transcript is usable (with a booked length: under 60% **and** cut mid-sentence; without one: cut mid-sentence; chats are never cut); creating an opportunity is allowed by the permissions.
2. **Model**: proposes per field with line-cited quotes, following `policies/`.
3. **After the model** (code): each quote must sit on the line it cites; contradictory only on seller-approved state fields; owner in the roster; dates, months, integers, departments and budget in format; economic buyer and champion on the customer side and never unattributed; the stage one step forward and never Closed; seller-only and turned-off fields dropped; a value equal to the approved one marked unchanged. Every correction is listed in `validation_notes`.
4. **Write**: only `applyApprovedFields`, for the fields the seller decided or that are under Always allow (never a contradiction); it re-checks the seller's own values, creates the client and opportunity only after that decision, and writes each field to the opportunity or the client record. `revertWrite` undoes an automatic write.

## Granola (optional)
The connector reads the **public API** (`https://public-api.granola.ai/v1`) with a personal API key (`grn_…`, Business plan). Only one folder is read (`GRANOLA_FOLDER`), new or updated notes are fetched incrementally, and real notes stay in `.granola-cache/`. Without a key, export the transcript from Granola and drop it in the page.

Reset the CRM to the seed before each eval case: expected results assume the seed state.
