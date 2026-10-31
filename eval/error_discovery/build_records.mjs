// Error discovery, step 1: one review record per (case, model) from eval/outputs/<model>/, with the conversation
// and the CRM context the reviewer needs to judge it. A blocked case never reaches the model, so it gets one record.
//   node eval/error_discovery/build_records.mjs          -> eval/error_discovery/error_discovery_data/records.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { transcriptLines } from "../../agent/core.mjs";
import { scoreCase } from "../score.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const KIT = path.resolve(HERE, "..", "..");
const rj = (p) => JSON.parse(fs.readFileSync(path.join(KIT, p), "utf8"));
const schema = rj("agent/field_schema.json");
const cases = rj("eval/expected_results.json").cases;
const meetings = [...rj("data/meetings.json"), ...rj("data/channel_meetings.json")];
const opps = rj("data/opportunities.json");
const clients = rj("data/clients.json");
const team = rj("data/team.json");
const MODELS = [["claude-sonnet-5-5", "Sonnet 5.5"], ["claude-opus-5-5", "Opus 5.5"], ["claude-haiku-5-5", "Haiku 5.5"]];
const groupLabel = Object.fromEntries(schema.groups.map((g) => [g.id, g.label]));
const fieldDef = Object.fromEntries(schema.fields.map((f) => [f.key, f]));
const side = (speaker) => (/\(orbita\)/i.test(speaker) ? "seller" : /unattributed/i.test(speaker) ? "unattributed" : "customer");

const records = [];
for (const c of cases) {
  const m = meetings.find((x) => x.meeting_id === c.meeting_id) || null;
  const file = m && m.transcript_file ? path.join(KIT, m.transcript_file) : null;
  const lines = file && fs.existsSync(file) ? transcriptLines(fs.readFileSync(file, "utf8")) : [];
  const opp = opps.find((o) => o.opportunity_id === (c.opportunity_id || (m && m.linked_opportunity_id))) || null;
  const client = clients.find((x) => x.client_id === (opp ? opp.client_id : m && m.client_id)) || null;
  const user = team.find((u) => u.user_id === c.run_as_user_id) || null;
  let platformDone = false;
  for (const [model, short] of MODELS) {
    const outFile = path.join(KIT, "eval", "outputs", model, `${c.case_id}.json`);
    if (!fs.existsSync(outFile)) continue;
    const out = JSON.parse(fs.readFileSync(outFile, "utf8"));
    const blocked = out.run_status === "Blocked";
    if (blocked && platformDone) continue;
    platformDone = platformDone || blocked;
    const stage = (out.fields || []).find((f) => f.field === "stage");
    const src = (m && m.source) || {};
    records.push({
      id: `${c.case_id}-${blocked ? "platform" : model}`,
      case_id: c.case_id,
      case_name: c.name,
      proves: c.proves || null,
      model: blocked ? "platform" : model,
      model_short: blocked ? "No model call" : short,
      client: client ? client.name : (out.target && out.target.client_name) || null,
      opportunity: opp ? opp.name : (out.target && out.target.opportunity_name) || null,
      stage_before: stage ? stage.current_value : null,
      seller: user ? user.name : c.run_as_user_id,
      source: [src.system, src.format].filter(Boolean).join(" · ") || null,
      chat: !!(m && (m.chat || src.system === "whatsapp")),
      scheduled_minutes: m ? m.scheduled_minutes ?? null : null,
      recorded_minutes: m ? m.recorded_minutes ?? null : null,
      run_status: out.run_status,
      source_status: out.source_status,
      block_reason: out.block_reason || null,
      warnings: out.warnings || [],
      target: out.target || null,
      fields: (out.fields || []).map((f) => ({ ...f, label: (fieldDef[f.field] || {}).label || f.field, group_label: groupLabel[f.group] || f.group })),
      validation_notes: out.validation_notes || [],
      ignored_out_of_scope: out.ignored_out_of_scope || [],
      usage: out.usage || null,
      scorer: scoreCase(c, out, { lines, schema }),
      lines: lines.map((l) => ({ n: l.n, ts: l.timestamp, speaker: l.speaker, side: side(l.speaker), text: l.text })),
    });
  }
}

const dir = path.join(HERE, "error_discovery_data");
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, "records.json"), JSON.stringify(records, null, 1));
console.log(`${records.length} records (${records.filter((r) => r.model !== "platform").length} model traces, ${records.filter((r) => r.model === "platform").length} blocked in code) -> ${path.relative(KIT, path.join(dir, "records.json"))}`);
