// LLM-as-judge for one failure mode: is each value the agent proposes (and its note) SUPPORTED by what the speakers said?
// Schema v4: picklist values are categories; the specifics sit in the note, so the judge reads both.
// Binary (Pass / Fail) per proposed field, critique before the result. The code checks (eval/score.mjs and the
// validator) already prove that every quote sits on the line it cites; they cannot tell whether the VALUE says more
// than the quotes do (an added number, the wrong person, a date nobody agreed). That is what this judge reads.
//
//   node eval/judge.mjs                              every label in eval/outputs/ except mock -> eval/judge_results.json
//   node eval/judge.mjs --label claude-haiku-5-5     one label (merged into the file)
//   node eval/judge.mjs --model claude-opus-5-5      the judge model (default Sonnet 5.5: a narrower task than the agent's,
//                                                    about USD 0.13 per experiment of 9 conversations; Opus is ~4x)
//   node eval/judge.mjs --budget 3                   stop before spending more than USD 3 in this run (default 3)
//
// Not validated yet: the few-shot examples below are author-written on a conversation that is NOT in the eval set
// (no leakage). Alignment with a human is measured in the CRM (Evals › Trace review: agree / disagree on each verdict)
// and shown as TPR / TNR in Evals › Dashboard. Trust the judge only once that agreement is high.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import * as P from "../agent/pipeline.mjs";
import * as core from "../agent/core.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const KIT = path.resolve(HERE, "..");
const rj = (rel) => JSON.parse(fs.readFileSync(path.join(KIT, rel), "utf8"));
const args = process.argv.slice(2);
const arg = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const JUDGE = arg("--model") || "claude-sonnet-5-5";
const BUDGET = Number(arg("--budget") || 3);
const OUT = path.join(HERE, "judge_results.json");

const SYSTEM = `You are an evaluator for a CRM agent that reads a sales conversation (a meeting transcript or a chat) and proposes values for CRM fields, each with quotes from numbered lines. Many fields are picklists: the value is one or more categories from a fixed list (several joined by '; ', or 'Other: <few words>'), and the specifics (names, figures, systems) are in the agent's note. You check exactly one thing: whether each proposed value, together with its note, is supported by what the speakers said in this conversation.

## Definitions

PASS: every fact in the value and in its note is said in the conversation or follows directly from it. For a picklist, every option chosen is supported: what the speakers said falls into that category. Paraphrase and summary are fine; so is combining several lines. Names, roles, companies, numbers, currencies, quantities and dates match what was said. A relative date ("Friday", "tomorrow") resolved from the meeting date is fine when the resolution is correct. A person named as economic buyer or champion is the speaker the conversation shows in that role. Facts from the CRM context the agent was given (a contact's job title, the client's name) count as supported, and so do options a list field already holds in the current CRM values when the agent keeps them in an updated list.

FAIL: the value or its note adds a fact nobody said, a picklist names an option the conversation does not support, (a number, an amount, a role, a date, a product, a commitment), changes one (a different figure, person or date), states as decided something that was only discussed or hoped for, or attributes words or a role to the wrong person. A value is judged on its content, not on its style or length; a missing detail is not a failure unless the value says something false.

Judge each field on its own. Read the whole conversation, not only the quoted lines: support may sit elsewhere. Write the critique first (what the value claims, where the conversation says it or does not), in one to three sentences, then the result.

## Examples (a conversation that is not one you will judge)

Conversation (meeting on Tue 2026-03-10):
L001 [00:00:05] Paula Reis (Orbita): Thanks for joining, Marcos, Carla.
L002 [00:01:10] Marcos Lima (Ferro Steel): We have forty thousand a year for this, that's the line in next year's budget.
L003 [00:02:40] Carla Souza (Ferro Steel): I'll take it to our CFO, he signs anything above twenty-five thousand.
L004 [00:03:15] Marcos Lima (Ferro Steel): We lost two renewals last quarter because nobody saw the dates.
L005 [00:05:02] Carla Souza (Ferro Steel): Let's show it to the six regional managers next Tuesday.

Field: Budget · value: "USD 40,000 per year" · quotes: L002
Critique: Marcos says "forty thousand a year" for this line of the budget. The value restates the amount and the period. The currency is not said, but the CRM records amounts in USD and the figure and period match; nothing is added that changes the meaning.
Result: Pass

Field: Economic buyer · value: "Carla Souza (CFO)" · quotes: L003
Critique: Carla says she will take it to "our CFO, he signs anything above twenty-five thousand". The CFO is someone else, and is not named; Carla is not the CFO. The value attributes the economic-buyer role and the CFO title to the wrong person.
Result: Fail

Field: Pain · value: "Lost two renewals worth USD 200,000 last quarter because nobody saw the renewal dates" · quotes: L004
Critique: L004 supports two lost renewals last quarter and the reason. No amount is mentioned anywhere in the conversation; "worth USD 200,000" is an added fact.
Result: Fail

Field: Budget (picklist) · value: "Under USD 50k per year" · note: "USD 40,000 per year." · quotes: L002
Critique: Marcos says forty thousand a year; the band under USD 50k holds it and the note restates the figure. Both are supported.
Result: Pass

Field: Paper process (picklist) · value: "Signature by the economic buyer; Procurement review" · note: "The CFO signs above USD 25,000." · quotes: L003
Critique: L003 supports that the CFO signs anything above twenty-five thousand, so the first option and the note hold. Nobody mentions procurement; "Procurement review" is an option the conversation does not support.
Result: Fail

Field: Next step · value: "Demo for the 6 regional managers on Tue 17 Mar" · quotes: L005
Critique: Carla proposes showing it to "the six regional managers next Tuesday". The meeting is on Tue 2026-03-10, so next Tuesday is 17 March. "Demo" paraphrases "show it". Every fact is supported.
Result: Pass`;

const SCHEMA_OUT = {
  type: "object", additionalProperties: false, required: ["fields"],
  properties: { fields: { type: "array", items: { type: "object", additionalProperties: false, required: ["field", "critique", "result"],
    properties: { field: { type: "string" }, critique: { type: "string" }, result: { type: "string", enum: ["Pass", "Fail"] } } } } },
};
const PROMPT_SHA = crypto.createHash("sha256").update(SYSTEM).digest("hex").slice(0, 8);

function caseInputs(c) {
  const meetings = rj("data/meetings.json").concat(rj("data/channel_meetings.json"));
  const m = meetings.find((x) => x.meeting_id === c.meeting_id);
  const lines = core.transcriptLines(P.readTranscript(m) || "");
  // the CRM context the agent itself was given: the client and its contacts with their titles
  const opp = c.opportunity_id ? rj("data/opportunities.json").find((o) => o.opportunity_id === c.opportunity_id) : null;
  const client = opp ? rj("data/clients.json").find((x) => x.client_id === opp.client_id) : null;
  return { m, lines, opp, client };
}
function userMessage(c, out, { m, lines, opp, client }) {
  const def = Object.fromEntries(P.SCHEMA.fields.map((d) => [d.key, d]));
  const fields = out.fields.filter((f) => f.status === "proposed" && f.proposed_value != null && f.proposed_value !== "");
  const conv = lines.map((l) => `L${String(l.n).padStart(3, "0")} [${l.timestamp}] ${l.speaker}: ${l.text}`).join("\n");
  const list = fields.map((f) => `Field: ${def[f.field].label} (key ${f.field})${def[f.field].options ? " · picklist" : ""} · definition: ${def[f.field].definition}\nValue: ${JSON.stringify(String(f.proposed_value))}\nQuotes: ${(f.evidence || []).map((x) => `L${String(x.line).padStart(3, "0")}`).join(", ") || "none"}${f.note ? `\nAgent note: ${f.note}` : ""}`).join("\n\n");
  // the current CRM values too: a list field keeps its approved options when the conversation adds one (policy)
  const cur = [];
  for (const d of P.SCHEMA.fields) {
    const rec = d.record === "client" ? client : opp;
    const v = rec && rec.fields && rec.fields[d.key] && rec.fields[d.key].value;
    if (v != null && v !== "") cur.push(`${d.key}: ${v}`);
  }
  const ctx = client ? `CRM context the agent was given: client ${client.name}; opportunity ${opp.name}; contacts: ${(client.contacts || []).map((p) => `${p.name}${p.title ? " (" + p.title + ")" : ""}`).join("; ") || "none"}.\nCurrent CRM values: ${cur.join(" | ") || "none"}.`
    : "CRM context the agent was given: none (a company that is not in the CRM yet).";
  return { fields, text: `${ctx}\n\nConversation (${m.chat ? "chat" : "meeting"} on ${String(m.start).slice(0, 10)}, ${m.title}):\n${conv}\n\nJudge each of these ${fields.length} proposed values. Use the field key in "field".\n\n${list}` };
}

const prev = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, "utf8")) : null;
const result = prev && prev.judge && prev.judge.prompt_sha === PROMPT_SHA && prev.judge.model === JUDGE ? prev : { judge: {}, labels: {} };
result.judge = { model: JUDGE, prompt_sha: PROMPT_SHA, criterion: "Each proposed value and its note are supported by what the speakers said (every picklist option chosen fits; no added or changed fact, right person, right date).", validated: false, at: new Date().toISOString() };
const root = path.join(HERE, "outputs");
const only = arg("--label");
const labels = fs.readdirSync(root).filter((d) => d !== "mock" && fs.statSync(path.join(root, d)).isDirectory() && (!only || d === only)).sort();
const cases = rj("eval/expected_results.json").cases;
let spent = 0;
for (const label of labels) {
  const L = result.labels[label] = { cases: {}, judged: 0, passed: 0, cost_usd: 0 };
  for (const c of cases) {
    const f = path.join(root, label, `${c.case_id}.json`);
    if (!fs.existsSync(f)) continue;
    const out = JSON.parse(fs.readFileSync(f, "utf8"));
    if (out.run_status === "Blocked") continue;
    const inp = caseInputs(c);
    const { fields, text } = userMessage(c, out, inp);
    if (!fields.length) continue;
    if (spent >= BUDGET) { console.log(`budget reached (USD ${spent.toFixed(4)}): stopping before ${label} ${c.case_id}`); break; }
    try {
      const r = await P.callJson({ system: SYSTEM, user: text, schema: SCHEMA_OUT, model: JUDGE, effort: "medium", maxTokens: 12000 });
      const cost = core.costOf(r.usage, JUDGE);
      spent += cost; L.cost_usd += cost;
      const by = Object.fromEntries((r.raw.fields || []).map((x) => [x.field, x]));
      // a field the judge skipped has no verdict: it is left out of the counts, never scored as a failure
      const rows = fields.filter((fd) => by[fd.field]).map((fd) => ({ field: fd.field, value: String(fd.proposed_value), result: by[fd.field].result, critique: by[fd.field].critique }));
      const skipped = fields.filter((fd) => !by[fd.field]).map((fd) => fd.field);
      if (skipped.length) console.log(`  ${label} ${c.case_id}: no verdict for ${skipped.join(", ")} (left out)`);
      L.cases[c.case_id] = { fields: rows, skipped };
      L.judged += rows.length; L.passed += rows.filter((x) => x.result === "Pass").length;
      const fails = rows.filter((x) => x.result === "Fail");
      console.log(`${label.padEnd(26)} ${c.case_id.padEnd(4)} ${rows.length - fails.length}/${rows.length} supported${fails.length ? "  FAIL: " + fails.map((x) => x.field).join(", ") : ""}  [$${cost.toFixed(4)}]`);
    } catch (e) {
      console.error(`${label} ${c.case_id} ERROR ${e.message}`);
      process.exitCode = 1;
    }
  }
}
fs.writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log(`\njudge ${JUDGE} (prompt ${PROMPT_SHA}) · USD ${spent.toFixed(4)} this run · ${path.relative(KIT, OUT)}`);
for (const [k, v] of Object.entries(result.labels)) console.log(`${k.padEnd(26)} ${v.passed}/${v.judged} values supported`);
