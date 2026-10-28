// Adversarial tests of the guardrails in code: each test feeds a deliberately wrong answer (or a wrong
// seller decision) through the same functions the product uses, and checks that the guard catches it.
// A guard that never fails protects nothing, so every check here is written to fail without its guard.
//   node eval/guardrail_tests.mjs        exit code 0 only when every guard catches its defect

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as core from "../agent/core.mjs";
import { scoreCase } from "./score.mjs";
import { exploreContext, answerQuestion } from "../agent/explore.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const rj = (p) => JSON.parse(fs.readFileSync(path.join(KIT, p), "utf8"));
const schema = rj("agent/field_schema.json");
const fresh = () => ({ team: rj("data/team.json"), clients: rj("data/clients.json"), opportunities: rj("data/opportunities.json"), meetings: [...rj("data/meetings.json"), ...rj("data/channel_meetings.json")] });
const cases = rj("eval/expected_results.json").cases;

function context(meetingId, userId = "U01", patch) {
  const data = fresh();
  if (patch) patch(data);
  const meeting = data.meetings.find((m) => m.meeting_id === meetingId);
  const transcript = fs.readFileSync(path.join(KIT, meeting.transcript_file), "utf8");
  const pre = core.prepareRun({ meetingId, userId, data, transcript, log: core.newLog("TEST"), schema });
  return { data, pre };
}
const ref = (c) => rj(`eval/reference_outputs/${c}.json`);
const withField = (raw, key, fn) => ({ ...raw, fields: raw.fields.map((f) => (f.field === key ? fn({ ...f }) : f)) });
const statusOf = (out, key) => out.fields.find((f) => f.field === key).status;

let pass = 0; let fail = 0;
function check(name, ok, detail = "") {
  if (ok) pass++; else fail++;
  console.log(`${ok ? "OK  " : "FAIL"} ${name}${ok || !detail ? "" : `  (${detail})`}`);
}
const validate = (meetingId, raw) => { const { data, pre } = context(meetingId); return core.validateOutput(raw, { ...pre, team: data.team }, schema); };

// ------------------------------------------------------------------ validator
{
  const out = validate("MTG-2001", withField(ref("T1"), "customer_need", (f) => ({ ...f, evidence: [{ line: 11, quote: "We want the cheapest CRM on the market." }] })));
  check("a quote that is not in the transcript downgrades the field", statusOf(out, "customer_need") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "customer_need", (f) => ({ ...f, evidence: [{ line: 1, quote: f.evidence[0].quote }] })));
  const f = out.fields.find((x) => x.field === "customer_need");
  check("a quote cited on the wrong line is moved to the line that holds it", f.status === "proposed" && f.evidence[0].line !== 1 && out.validation_notes.some((n) => /found on L/.test(n)));
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "stage", (f) => ({ ...f, value: "Proposal" })));
  check("a stage two steps forward is refused", statusOf(out, "stage") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "stage", (f) => ({ ...f, value: "Closed Won" })));
  check("Closed Won is refused", statusOf(out, "stage") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "stage", (f) => ({ ...f, value: "New Lead" })));
  check("a backward stage move is refused", statusOf(out, "stage") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "follow_up_owner", (f) => ({ ...f, value: "Marina Lopes" })));
  check("a follow-up owner outside the roster is refused", statusOf(out, "follow_up_owner") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "follow_up_due_date", (f) => ({ ...f, value: "06/11/2026" })));
  check("a date that is not YYYY-MM-DD is refused", statusOf(out, "follow_up_due_date") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "follow_up_due_date", (f) => ({ ...f, value: "2026-02-30" })));
  check("a date that does not exist is refused", statusOf(out, "follow_up_due_date") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "go_live_target", (f) => ({ ...f, value: "March 2027" })));
  check("a go-live that is not YYYY-MM is refused", statusOf(out, "go_live_target") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "seats", (f) => ({ ...f, value: "sixty" })));
  check("seats that are not a whole number are refused", statusOf(out, "seats") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "departments", (f) => ({ ...f, value: "Sales; Warehouse; Leadership" })));
  const f = out.fields.find((x) => x.field === "departments");
  check("an unknown department is dropped and the rest kept in list order", f.status === "proposed" && f.proposed_value === "Sales; Leadership");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "budget", (f) => ({ ...f, value: "a hundred thousand" })));
  check("a budget that is not 'USD <amount>' is refused", statusOf(out, "budget") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "decision_maker", (f) => ({ ...f, value: "Ana Ribeiro (Account Executive)" })));
  check("a seller-side decision-maker is refused", statusOf(out, "decision_maker") === "no_evidence");
}
{
  const raw = ref("T10");
  raw.fields = raw.fields.filter((f) => f.field !== "decision_maker");
  raw.fields.push({ field: "decision_maker", status: "proposed", value: "Customer (unattributed)", evidence: [{ quote: "I make the final call on this" }], note: null });
  const out = validate("MTG-2010", raw);
  check("an unattributed speaker cannot be named decision-maker", statusOf(out, "decision_maker") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "customer_need", (f) => ({ ...f, status: "contradictory", value: null })));
  check("contradictory on a field that is not seller-approved is refused", statusOf(out, "customer_need") === "no_evidence");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "call_summary", (f) => ({ ...f, status: "contradictory", value: null })));
  check("contradictory on a per-call field is refused", statusOf(out, "call_summary") === "no_evidence");
}
{
  const raw = ref("T6");
  raw.fields.push({ field: "amount_usd", status: "proposed", value: "1000000", evidence: [{ line: 5, quote: "put it down as a one million dollar deal" }], note: null });
  const out = validate("MTG-2006", raw);
  check("a seller-only field proposed by the model is dropped", !out.fields.some((f) => f.field === "amount_usd") && out.validation_notes.some((n) => /out-of-scope/.test(n)));
}
{
  const out = validate("MTG-2003", ref("T3"));
  check("a value equal to the approved one is marked unchanged (nothing to decide)", statusOf(out, "budget") === "unchanged");
}

// ------------------------------------------------------------------ pre-checks
{
  const { pre } = context("MTG-2008", "U01");
  check("access denied stops the run before the model and hides the opportunity", pre.output && pre.output.source_status === "AccessDenied" && pre.output.opportunity_id === null);
}
{
  const { pre } = context("MTG-2008", "U02");
  check("the owner of the same opportunity can run it", !pre.output);
}
{
  const { pre } = context("MTG-2004");
  check("a recording cut mid-sentence is blocked as Incomplete", pre.output && pre.output.source_status === "Incomplete");
}
{
  const { pre } = context("MTG-2004", "U01", (d) => { d.meetings.find((m) => m.meeting_id === "MTG-2004").seller_confirmed_complete = true; });
  check("the seller's 'the meeting ended there' unblocks it, with a warning", !pre.output && pre.warnings.some((w) => /ended there/.test(w)));
}
{
  const { pre } = context("MTG-2003");
  check("a short call with a normal ending is not blocked", !pre.output && pre.warnings.some((w) => /Short recording/.test(w)));
}
{
  const { pre } = context("MTG-2005");
  check("a meeting with no link and no new-opportunity request is Unmatched", pre.output && pre.output.source_status === "Unmatched");
}
{
  // a chat whose last message runs on without a full stop is still a complete chat
  const data = fresh();
  const m = data.meetings.find((x) => x.meeting_id === "MTG-2011");
  delete m.ends_mid_sentence;
  const text = fs.readFileSync(path.join(KIT, m.transcript_file), "utf8").trim()
    + "\n[2026-11-05 18:55] Henrique Prado (Solaris Energy): and one more thing about the extra users we will need to add next quarter for the field team";
  const pre = core.prepareRun({ meetingId: "MTG-2011", userId: "U01", data, transcript: text, log: core.newLog("T"), schema });
  check("a chat export is never blocked as a cut recording, even when the last message runs on", !pre.output && !pre.warnings.length);
}
{
  const data = fresh();
  const m = data.meetings.find((x) => x.meeting_id === "MTG-2005");
  const lines = core.transcriptLines(fs.readFileSync(path.join(KIT, m.transcript_file), "utf8"));
  const linked = core.attribute({ meeting: m, lines, data, user: data.team[0], schema });
  data.meetings = [linked];
  const off = core.prepareRun({ meetingId: "MTG-2005", userId: "U01", data, transcript: fs.readFileSync(path.join(KIT, m.transcript_file), "utf8"), log: core.newLog("T"), schema,
    permissions: { ...core.defaultPermissions(schema), create_opportunity: "off" } });
  check("with 'create opportunities' set to Never, a new client is blocked instead of created", off.output && off.output.source_status === "Unmatched" && /turned off/.test(off.output.block_reason));
}

// ------------------------------------------------------------------ write path
{
  const { data, pre } = context("MTG-2001");
  const out = core.validateOutput(ref("T1"), { ...pre, team: data.team }, schema);
  let threw = false;
  try { core.applyApprovedFields({ output: out, decisions: { call_summary: { decision: "approve" } }, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team }); } catch { threw = true; }
  check("Submit without a decision on every actionable field is refused", threw && !core.fieldOf(data.opportunities.find((o) => o.opportunity_id === "OPP-0142"), "call_summary").value);
}
{
  const { data, pre } = context("MTG-2001");
  const out = core.validateOutput(ref("T1"), { ...pre, team: data.team }, schema);
  const decisions = Object.fromEntries(out.fields.filter((f) => core.ACTIONABLE.includes(f.status)).map((f) => [f.field, { decision: "approve" }]));
  decisions.seats = { decision: "edit", value: "about sixty" };
  let threw = false;
  try { core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team }); } catch { threw = true; }
  check("an invalid seller edit is refused and nothing is written", threw && !core.fieldOf(data.opportunities.find((o) => o.opportunity_id === "OPP-0142"), "budget").value);
}
{
  const { data, pre } = context("MTG-2001");
  const out = core.validateOutput(ref("T1"), { ...pre, team: data.team }, schema);
  const decisions = Object.fromEntries(out.fields.filter((f) => core.ACTIONABLE.includes(f.status)).map((f) => [f.field, { decision: "approve" }]));
  decisions.employee_count = { decision: "reject", reason: "check with Marina" };
  const record = core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team });
  const client = data.clients.find((c) => c.client_id === "CLI-001");
  check("approved client fields go to the client record, a rejected one is not written",
    core.fieldOf(client, "current_solution").approved && !core.fieldOf(client, "employee_count").value && record.find((r) => r.field === "employee_count").write_result === "Not written");
}

// ------------------------------------------------------------------ scorer (it must fail a wrong answer)
{
  const c = cases.find((x) => x.case_id === "T6");
  const { data, pre } = context("MTG-2006");
  const bad = withField(ref("T6"), "budget", (f) => ({ ...f, value: "USD 1,000,000 per year", evidence: [{ line: 5, quote: "put it down as a one million dollar deal" }] }));
  const out = core.validateOutput(bad, { ...pre, team: data.team }, schema);
  const lines = core.transcriptLines(fs.readFileSync(path.join(KIT, pre.meeting.transcript_file), "utf8"));
  check("the scorer fails a budget taken from the spoken deal amount", scoreCase(c, out, { lines, schema }).verdict === "FAIL");
}
{
  const c = cases.find((x) => x.case_id === "T10");
  const { data, pre } = context("MTG-2010");
  const raw = ref("T10");
  const out = core.validateOutput(withField(raw, "stage", (f) => ({ ...f, status: "proposed", value: "Solution", evidence: [{ line: 19, quote: "I make the final call on this" }] })), { ...pre, team: data.team }, schema);
  const lines = core.transcriptLines(fs.readFileSync(path.join(KIT, pre.meeting.transcript_file), "utf8"));
  check("the scorer fails a stage moved on an unattributed decision", scoreCase(c, out, { lines, schema }).verdict === "FAIL");
}

// ------------------------------------------------------------------ any source: reading, attribution, creation, permissions
{
  const p = core.parseConversation("05/11/2026, 18:02 - Ana Ribeiro: Hi\n05/11/2026, 18:40 - Henrique Prado: <Media omitted>\n05/11/2026, 18:41 - Henrique Prado: We agree.", { now: "2026-11-06" });
  check("a WhatsApp date that reads both ways is settled by the closest date, and media placeholders are dropped", p.kind === "whatsapp" && p.lines.length === 2 && p.lines[1].timestamp === "2026-11-05 18:41");
}
{
  const p = core.parseConversation("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Marina Lopes>We track everything in</v>\n\n00:00:04.100 --> 00:00:07.000\n<v Marina Lopes>spreadsheets today.</v>\n\n00:00:08.000 --> 00:00:09.000\n<v Ana Ribeiro>Got it.</v>");
  check("WebVTT cues split mid-sentence are glued back into one turn", p.lines.length === 2 && p.lines[0].text === "We track everything in spreadsheets today.");
}
{
  const data = fresh();
  const sample = (f) => core.parseConversation(fs.readFileSync(path.join(KIT, "samples", f), "utf8"), { now: "2026-11-06" });
  const match = (f, user) => { const p = sample(f); return core.matchConversation({ lines: core.labelSpeakers(p.lines, { team: data.team }), filename: f, clients: data.clients, opportunities: data.opportunities, team: data.team, user, schema }); };
  const ana = data.team.find((u) => u.user_id === "U01");
  const acme = match("acme-logistics_discovery-call.vtt", ana);
  check("a transcript with the client's contacts is attributed to the client's one open opportunity", acme.kind === "opportunity" && acme.opportunity_id === "OPP-0142");
  const delta = match("delta-pharma_intro-call.vtt", ana);
  check("a company the CRM does not know becomes a new client, named from the file", delta.kind === "new_client" && delta.client_name_guess === "Delta Pharma");
  const horizonte = match("horizonte-foods_solution-walkthrough.vtt", ana);
  check("another seller's opportunity is denied, and its name is not part of the answer", horizonte.kind === "denied" && !JSON.stringify(horizonte.reasons).includes("Horizonte"));
  const chat = match("WhatsApp Chat with Henrique Prado.txt", ana);
  check("a WhatsApp chat is attributed by its contact, without a company in the file name", chat.kind === "opportunity" && chat.opportunity_id === "OPP-0149");
}
{
  const data = fresh();
  data.opportunities.push({ opportunity_id: "OPP-9001", client_id: "CLI-001", name: "Second Acme deal", owner_id: "U01", fields: { stage: { value: "New Lead", approved: true } } });
  const p = core.parseConversation(fs.readFileSync(path.join(KIT, "samples", "acme-logistics_discovery-call.vtt"), "utf8"));
  const m = core.matchConversation({ lines: p.lines, filename: "acme-logistics_discovery-call.vtt", clients: data.clients, opportunities: data.opportunities, team: data.team, user: data.team[0], schema });
  check("a client with two open opportunities asks the seller to choose", m.kind === "choose" && m.candidates.length === 2);
}
function newClientRun(createDecision) {
  const data = fresh();
  const m = data.meetings.find((x) => x.meeting_id === "MTG-2005");
  const text = fs.readFileSync(path.join(KIT, m.transcript_file), "utf8");
  data.meetings = [core.attribute({ meeting: m, lines: core.transcriptLines(text), data, user: data.team[0], schema })];
  const pre = core.prepareRun({ meetingId: "MTG-2005", userId: "U01", data, transcript: text, log: core.newLog("T"), schema });
  const out = core.validateOutput(ref("T5"), { ...pre, team: data.team }, schema);
  const decisions = Object.fromEntries(out.fields.filter((f) => core.ACTIONABLE.includes(f.status)).map((f) => [f.field, { decision: "approve" }]));
  if (createDecision) decisions.__create__ = createDecision;
  return { data, out, decisions, pre };
}
{
  const { data, out, decisions } = newClientRun(null);
  let why = "";
  try { core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team }); } catch (e) { why = e.message; }
  check("fields of a new opportunity cannot be written before the seller decides on creating it", /new opportunity/.test(why) && data.opportunities.length === fresh().opportunities.length, why);
}
{
  const { data, out, decisions } = newClientRun({ decision: "reject", reason: "not a real prospect" });
  const record = core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team });
  check("a rejected new opportunity creates nothing and writes nothing", data.clients.length === fresh().clients.length && record.every((r) => r.write_result === "Not written"));
}
{
  const { data, out, decisions } = newClientRun({ decision: "approve", client_name: "Delta Pharma" });
  const record = core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team });
  const opp = data.opportunities.find((o) => o.opportunity_id === out.opportunity_id);
  const client = data.clients.find((c) => c.client_id === out.client_id);
  check("an approved new opportunity creates the client (with its contact) and the opportunity at New Lead, owned by the seller",
    client && client.name === "Delta Pharma" && client.contacts.some((c) => c.name === "Livia Prado") && opp && opp.owner_id === "U01"
    && core.fieldOf(opp, "stage").value === "New Lead" && core.fieldOf(opp, "customer_need").approved && record.every((r) => r.write_result === "Succeeded"));
}
{
  const { data, pre } = context("MTG-2001");
  const perms = core.defaultPermissions(schema);
  perms.fields.budget = "off";
  const out = core.validateOutput(ref("T1"), { ...pre, team: data.team, permissions: perms }, schema);
  check("a field set to Never is dropped even when the model proposes it", statusOf(out, "budget") === "off" && !core.ACTIONABLE.includes(statusOf(out, "budget")));
}
{
  const { data, pre } = context("MTG-2003");
  const perms = core.defaultPermissions(schema);
  for (const k of Object.keys(perms.fields)) perms.fields[k] = "auto";
  const out = core.validateOutput(ref("T3"), { ...pre, team: data.team, permissions: perms }, schema);
  const auto = core.autoFields(out, schema, perms);
  check("Always allow never covers a contradiction: it still waits for the seller", !auto.includes("next_step") && out.fields.find((f) => f.field === "next_step").status === "contradictory");
  let threw = false;
  try { core.applyApprovedFields({ output: out, decisions: { next_step: { decision: "keep", auto: true } }, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team, only: ["next_step"] }); } catch { threw = true; }
  check("the write path refuses an automatic decision on a contradictory field", threw);
}
{
  const { data, pre } = context("MTG-2001");
  const out = core.validateOutput(ref("T1"), { ...pre, team: data.team }, schema);
  const auto = core.autoFields(out, schema, core.defaultPermissions(schema));
  const decisions = Object.fromEntries(auto.map((k) => [k, { decision: "approve", auto: true }]));
  const record = core.applyApprovedFields({ output: out, decisions, crm: data, reviewerId: "U01", log: core.newLog("T"), schema, team: data.team, only: auto });
  const opp = data.opportunities.find((o) => o.opportunity_id === "OPP-0142");
  const wrote = record.length === auto.length && record.every((r) => r.decided_by === "permission") && core.fieldOf(opp, "call_summary").value;
  core.revertWrite({ item: record.find((r) => r.field === "call_summary"), output: out, crm: data, reviewerId: "U01", log: core.newLog("T") });
  check("Always allow writes only its fields, and Undo brings the previous value back",
    wrote && !core.fieldOf(opp, "call_summary").value && !core.fieldOf(opp, "budget").value && core.statusAfterSubmit(record) === "Written automatically");
}
{
  const out = validate("MTG-2001", withField(ref("T1"), "champion", (f) => ({ ...f, value: "Ana Ribeiro (Account Executive)" })));
  check("a seller-side champion is refused", statusOf(out, "champion") === "no_evidence");
}
{
  const raw = ref("T10");
  raw.fields = raw.fields.filter((f) => f.field !== "champion");
  raw.fields.push({ field: "champion", status: "proposed", value: "Customer (unattributed)", evidence: [{ quote: "I'm the one pushing for this inside the company." }], note: null });
  const out = validate("MTG-2010", raw);
  check("an unattributed speaker cannot be named champion", statusOf(out, "champion") === "no_evidence");
}
{
  const data = fresh();
  const ask = (q, user) => answerQuestion(q, exploreContext({ crm: data, team: data.team, user: data.team.find((u) => u.user_id === user), schema, now: "2026-11-06" }));
  const mine = ask("What's the status of Acme Logistics?", "U01");
  check("Explore answers the status of an opportunity from the CRM", mine.kind === "status" && mine.opportunity_ids.includes("OPP-0142") && /Qualified Opportunity/.test(mine.verdict));
  const other = ask("What's the status of Acme Logistics?", "U02");
  check("Explore never answers about an opportunity the user cannot read", other.kind === "none" && !JSON.stringify(other).includes("OPP-0142"));
}

console.log(`\n${pass} guards caught their defect, ${fail} did not.`);
process.exitCode = fail ? 1 : 0;
