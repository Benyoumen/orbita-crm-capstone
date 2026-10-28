// Orbita CRM agent: reference pipeline (Node 22+, one dependency: @anthropic-ai/sdk, loaded only for live calls).
//
//   node agent/pipeline.mjs --case T1                    one eval case (needs ANTHROPIC_API_KEY, e.g. in capstone/.env)
//   node agent/pipeline.mjs --all [--model <id>]         every eval case -> eval/outputs/<model>/
//   node agent/pipeline.mjs --all --mock                 no API call: reference answers through the same validator -> eval/outputs/mock/
//   node agent/pipeline.mjs --all --dry-run              pre-checks and prompt size only
//   node agent/pipeline.mjs --meeting MTG-2001 --user U01   app-style run on a meeting's linked opportunity
//   node agent/pipeline.mjs --file samples/acme-logistics_discovery-call.vtt --user U01   any transcript or chat export
//
// Env (or capstone/.env): ANTHROPIC_API_KEY, ORBITA_MODEL (default claude-sonnet-5-5), ORBITA_EFFORT (low, medium or high; default medium).
// The rules live in agent/core.mjs (pure, shared with the server and the mockup page). This file reads the
// kit's files, builds the prompt (static part cached, per-run part compact) and calls the model.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as core from "./core.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
if (fs.existsSync(path.join(KIT, ".env")) && typeof process.loadEnvFile === "function") process.loadEnvFile(path.join(KIT, ".env"));
const rd = (p) => fs.readFileSync(path.join(KIT, p), "utf8");
const rj = (p) => JSON.parse(rd(p));

export const SCHEMA = rj("agent/field_schema.json");
export const DEFAULT_MODEL = process.env.ORBITA_MODEL || "claude-sonnet-5-5";
// ORBITA_* and not CLAUDE_*: Claude Code sets CLAUDE_EFFORT in its own shell, and the kit must not inherit it
export const EFFORT = ["low", "medium", "high"].includes(process.env.ORBITA_EFFORT) ? process.env.ORBITA_EFFORT : "medium";
// Server-side refusal fallback (Claude API): Sonnet 5.5 and Opus 5.5 take the "default" form; Haiku 5.5 has none.
const FALLBACK_MODELS = new Set(["claude-sonnet-5-5", "claude-opus-5-5"]);

// ------------------------------------------------------------------ data access (swap for your CRM store)
export function loadData(crm) {
  const cache = path.join(KIT, ".granola-cache", "meetings.json");
  return {
    team: rj("data/team.json"),
    clients: (crm && crm.clients) || rj("data/clients.json"),
    opportunities: (crm && crm.opportunities) || rj("data/opportunities.json"),
    meetings: [...rj("data/meetings.json"), ...rj("data/channel_meetings.json"), ...(fs.existsSync(cache) ? JSON.parse(fs.readFileSync(cache, "utf8")) : [])],
  };
}
export function readTranscript(meeting) {
  if (!meeting || !meeting.transcript_file) return null;
  const p = path.join(KIT, meeting.transcript_file);
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null;
}

// ------------------------------------------------------------------ prompt
let SYSTEM = null;
function renderExamples(team) {
  return ["EX1", "EX2"].map((x) => {
    const ctx = rj(`examples/${x}_context.json`);
    const lines = core.transcriptLines(rd(`examples/${x}_transcript.txt`));
    const input = core.buildUserMessage({ meeting: ctx.meeting, opp: ctx.opportunity, client: ctx.client, team, lines, schema: SCHEMA });
    const { meeting_id, ...output } = rj(`examples/${x}_expected_output.json`);
    return `### Example ${x}\nINPUT\n${input}\n\nOUTPUT\n${JSON.stringify(output)}`;
  }).join("\n\n");
}
/** The static system prompt: identical for every run, so it is cached (prefix match). */
export function systemPrompt(team = rj("data/team.json")) {
  if (SYSTEM) return SYSTEM;
  let s = rd("agent/system_prompt.md").split("\n---\n")[0].replace(/^> .*\n/gm, "");
  s = s.replace("{{policies/agent_policy.md}}", rd("policies/agent_policy.md").trim())
    .replace("{{field_dictionary}}", core.renderFieldDictionary(SCHEMA))
    .replace("{{policies/stage_rules.md}}", rd("policies/stage_rules.md").trim())
    .replace("{{examples}}", renderExamples(team));
  return (SYSTEM = s);
}
export function buildPrompt({ meeting, opp, client, lines, data, permissions = null }) {
  return { system: systemPrompt(data.team), user: core.buildUserMessage({ meeting, opp, client, team: data.team, lines, schema: SCHEMA, permissions }) };
}

// ------------------------------------------------------------------ model call
let anthropic = null;
async function api() {
  if (!anthropic) {
    const { default: Anthropic } = await import("@anthropic-ai/sdk");
    anthropic = new Anthropic(); // ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN or an `ant auth login` profile
  }
  return anthropic;
}
/** One structured call: cached system block, JSON schema enforced by the API, usage returned for the log. */
export async function callJson({ system, user, schema, model = DEFAULT_MODEL, effort = EFFORT, maxTokens = 16000 }) {
  const client = await api();
  const params = {
    model,
    max_tokens: maxTokens,
    system: [{ type: "text", text: system, cache_control: { type: "ephemeral" } }],
    messages: [{ role: "user", content: user }],
    output_config: { effort, format: { type: "json_schema", schema } },
  };
  const res = FALLBACK_MODELS.has(model)
    ? await client.beta.messages.create({ ...params, betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" })
    : await client.messages.create(params);
  if (res.stop_reason === "refusal") throw new Error(`The model declined the request (${(res.stop_details && res.stop_details.category) || "no category"}).`);
  if (res.stop_reason === "max_tokens") throw new Error("The model output hit max_tokens before the JSON was complete.");
  const text = res.content.filter((b) => b.type === "text").map((b) => b.text).join("");
  const u = res.usage || {};
  const usage = { input_tokens: u.input_tokens || 0, output_tokens: u.output_tokens || 0,
    cache_read_input_tokens: u.cache_read_input_tokens || 0, cache_creation_input_tokens: u.cache_creation_input_tokens || 0 };
  return { raw: JSON.parse(text), usage, model: res.model || model };
}
export async function callModel({ system, user }, model = DEFAULT_MODEL, effort = EFFORT) {
  return callJson({ system, user, schema: core.buildOutputSchema(SCHEMA), model, effort });
}

// ------------------------------------------------------------------ mock model (reference answers; never put these in the prompt)
// A transcript dropped in the page carries its own id: it is recognised by its spoken text (conversationKey).
function mockOutput(meetingId, lines) {
  const dir = path.join(KIT, "eval", "reference_outputs");
  const refs = fs.readdirSync(dir).filter((x) => x.endsWith(".json")).map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")))
    .filter((o) => o.run_status !== "Blocked");
  const byId = refs.find((o) => o.meeting_id === meetingId);
  if (byId) return byId;
  const key = core.conversationKey(lines || []);
  const kit = [...rj("data/meetings.json"), ...rj("data/channel_meetings.json")].find((m) => core.conversationKey(core.transcriptLines(readTranscript(m) || "")) === key);
  const byKey = kit && refs.find((o) => o.meeting_id === kit.meeting_id);
  if (byKey) return byKey;
  throw Object.assign(new Error("No saved result for this transcript: without a Claude key, only the sample transcripts can be read."), { status: 409 });
}

// ------------------------------------------------------------------ orchestration
// meeting/transcript: a conversation that is not in the kit (a dropped file, a pasted text), already normalised.
export async function runAgent({ meetingId, opportunityId, userId, dryRun = false, mock = false, crm, model = DEFAULT_MODEL,
  effort = EFFORT, permissions = null, meeting: given = null, transcript: givenText = null }) {
  const data = loadData(crm);
  const runId = `RUN-${Date.now()}`;
  const log = core.newLog(runId);
  let meeting = given || data.meetings.find((m) => m.meeting_id === meetingId);
  const transcript = givenText ?? readTranscript(meeting);
  if (meeting) {
    // a conversation that arrived without a link is attributed the way the platform does it (match, or a new opportunity)
    meeting = core.attribute({ meeting, lines: core.transcriptLines(transcript || ""), data, user: data.team.find((u) => u.user_id === userId), schema: SCHEMA });
    data.meetings = [meeting, ...data.meetings.filter((m) => m.meeting_id !== meeting.meeting_id)];
    meetingId = meeting.meeting_id;
  }
  const pre = core.prepareRun({ meetingId, opportunityId, userId, data, transcript, log, schema: SCHEMA, permissions });
  if (pre.output) { log.add("system", "run_blocked", meetingId, "blocked", pre.output.block_reason); return { runId, output: pre.output, log: log.events }; }
  const prompt = buildPrompt({ ...pre, data, permissions });
  if (dryRun) return { runId, output: { dry_run: true, system_chars: prompt.system.length, user_chars: prompt.user.length, lines: pre.lines.length }, log: log.events };
  let raw; let usage = null; let served = null;
  if (mock) {
    log.add("system", "agent_called", meetingId, "ok", "MOCK (reference output)");
    raw = mockOutput(meetingId, pre.lines);
  } else {
    log.add("system", "agent_called", meetingId, "ok", `${model} · effort ${effort}`);
    const r = await callModel(prompt, model, effort);
    raw = r.raw; usage = r.usage; served = r.model;
    const cost = core.costOf(usage, model);
    log.add("system", "agent_answered", meetingId, "ok",
      `in=${usage.input_tokens} cache_read=${usage.cache_read_input_tokens} cache_write=${usage.cache_creation_input_tokens} out=${usage.output_tokens}${cost != null ? ` cost=$${cost.toFixed(4)}` : ""}${served !== model ? ` served_by=${served}` : ""}`);
  }
  const output = core.validateOutput(raw, { ...pre, team: data.team }, SCHEMA);
  output.usage = usage ? { ...usage, model, served_by: served, cost_usd: core.costOf(usage, model) } : null;
  log.add("system", "output_validated", meetingId, "ok", `${output.validation_notes.length} correction(s)`);
  log.add("agent", "proposals_generated", pre.opp.opportunity_id || "new opportunity", "ok", output.fields.map((f) => `${f.field}=${f.status}`).join(", "));
  return { runId, output, log: log.events };
}

// ------------------------------------------------------------------ CLI
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const arg = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
  const dryRun = args.includes("--dry-run");
  const mock = args.includes("--mock");
  const model = arg("--model") || DEFAULT_MODEL;
  const cases = rj("eval/expected_results.json").cases;
  const jobs = args.includes("--all") ? cases : arg("--case") ? cases.filter((c) => c.case_id === arg("--case")) : [];
  if (arg("--meeting")) jobs.push({ case_id: arg("--meeting"), meeting_id: arg("--meeting"), opportunity_id: undefined, run_as_user_id: arg("--user") || "U01" });
  if (arg("--file")) {
    // any transcript or chat export, read and attributed exactly as the page does it
    const file = path.resolve(arg("--file"));
    const parsed = core.parseConversation(fs.readFileSync(file, "utf8"), { now: new Date().toISOString() });
    const lines = core.labelSpeakers(parsed.lines, { team: rj("data/team.json") });
    jobs.push({ case_id: path.basename(file).replace(/\.[a-z0-9]+$/i, ""), meeting_id: "MTG-FILE", run_as_user_id: arg("--user") || "U01", opportunity_id: undefined,
      meeting: { meeting_id: "MTG-FILE", title: path.basename(file), start: parsed.start || new Date().toISOString(), chat: parsed.chat,
        recorded_minutes: parsed.minutes, ends_mid_sentence: parsed.ends_mid_sentence, source: { system: parsed.kind === "whatsapp" ? "whatsapp" : "file", file: path.basename(file), format: parsed.kind },
        participants: [...new Set(lines.map((l) => l.speaker))], transcript_status: "complete" },
      transcript: core.conversationText(lines) });
  }
  if (!jobs.length) { console.log("Usage: --case T1 | --all | --meeting MTG-2001 --user U01 | --file <transcript>  [--mock] [--dry-run] [--model <id>]"); process.exit(1); }
  const label = mock ? "mock" : model;
  const outDir = arg("--out") ? path.resolve(arg("--out")) : path.join(KIT, "eval", "outputs", label);
  if (!dryRun) fs.mkdirSync(outDir, { recursive: true });
  let spent = 0; let calls = 0;
  for (const c of jobs) {
    try {
      // every case starts from the seed CRM: crm undefined -> loadData reads data/*.json again
      const { output, log } = await runAgent({ meetingId: c.meeting_id, opportunityId: c.opportunity_id, userId: c.run_as_user_id, dryRun, mock, model,
        meeting: c.meeting || null, transcript: c.transcript ?? null });
      if (!dryRun) {
        fs.writeFileSync(path.join(outDir, `${c.case_id}.json`), JSON.stringify(output, null, 2));
        fs.writeFileSync(path.join(outDir, `${c.case_id}.log.json`), JSON.stringify(log, null, 2));
      }
      if (output.usage) { calls++; spent += output.usage.cost_usd || 0; }
      const fresh = output.target && output.target.kind === "new" ? `new opportunity for ${output.target.client_name || "a new client"} · ` : "";
      const summary = output.run_status === "Blocked" ? `Blocked (${output.source_status})`
        : output.dry_run ? `Ready -> would call ${model} (${output.lines} lines, system ${output.system_chars} chars, user ${output.user_chars} chars)`
        : fresh + output.fields.filter((f) => f.status !== "no_evidence").map((f) => `${f.field}:${f.status}`).join(" ");
      const u = output.usage;
      console.log(`${c.case_id.padEnd(4)} ${summary}${u ? `  [in ${u.input_tokens} + cache ${u.cache_read_input_tokens}r/${u.cache_creation_input_tokens}w, out ${u.output_tokens}, $${(u.cost_usd || 0).toFixed(4)}]` : ""}`);
    } catch (e) {
      console.error(`${c.case_id}  ERROR ${e.message}`);
      process.exitCode = 1;
    }
  }
  if (calls) console.log(`\n${calls} model call(s) on ${model}, total $${spent.toFixed(4)}. Outputs: ${path.relative(KIT, outDir)}`);
}
