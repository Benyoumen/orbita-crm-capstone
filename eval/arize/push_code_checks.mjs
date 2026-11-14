// Scores one traced run folder with the code scorer (eval/score.mjs) and writes each verdict to Arize as the
// `code_checks` annotation (pass / fail, the failed checks as text) on that run's root span.
// The dashboard can then chart the code checks next to seller thumbs and LLM-judge scores, per model and prompt version.
//
//   node eval/arize/push_code_checks.mjs eval/arize_runs/2026-10-31_run2/claude-sonnet-5-5 [--dry-run]
//
// Needs the `ax` CLI with a profile on the space (the run folder's outputs carry trace_id, written by agent/pipeline.mjs
// when tracing is on). Never writes eval/results.* (those feed the PRD).
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { transcriptLines } from "../../agent/core.mjs";
import { scoreCase } from "../score.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const SPACE = process.env.ARIZE_SPACE || "Digithall Evals";
const PROJECT = process.env.ARIZE_PROJECT_NAME || "orbita-crm-agent";
const dir = path.resolve(process.argv[2] || "");
const dry = process.argv.includes("--dry-run");
if (!fs.existsSync(dir)) { console.error("Usage: node eval/arize/push_code_checks.mjs <run folder> [--dry-run]"); process.exit(1); }

const schema = rj(path.join(KIT, "agent", "field_schema.json"));
const cases = rj(path.join(KIT, "eval", "expected_results.json")).cases;
const meetings = [...rj(path.join(KIT, "data", "meetings.json")), ...rj(path.join(KIT, "data", "channel_meetings.json"))];
const linesOf = (id) => { const m = meetings.find((x) => x.meeting_id === id); return m && m.transcript_file ? transcriptLines(fs.readFileSync(path.join(KIT, m.transcript_file), "utf8")) : []; };
// `ax` prints a status line before its JSON on stdout: keep from the first bracket on
const ax = (args) => { const out = execFileSync("ax", args, { encoding: "utf8", maxBuffer: 64 << 20 }); return JSON.parse(out.slice(out.search(/[[{]/))); };

const records = []; let pass = 0;
for (const c of cases) {
  const f = path.join(dir, `${c.case_id}.json`);
  if (!fs.existsSync(f)) continue;
  const out = rj(f);
  const r = scoreCase(c, out, { lines: linesOf(c.meeting_id), schema });
  if (r.verdict === "PASS") pass++;
  if (!out.trace_id) { console.log(`${c.case_id} ${r.verdict} (no trace_id: run it with tracing on)`); continue; }
  const spans = ax(["spans", "export", PROJECT, "--space", SPACE, "--trace-id", out.trace_id, "--stdout"]);
  const root = spans.find((s) => !s.parent_id);
  if (!root) { console.log(`${c.case_id} trace ${out.trace_id} not found in Arize yet`); continue; }
  records.push({ record_id: root.context.span_id, values: [{ name: "code_checks", label: r.verdict === "PASS" ? "pass" : "fail",
    // no score: on a categorical config Arize derives it from the label (labels made with the CLI carry none)
    text: r.fails.join(" | ").slice(0, 1000) || "all checks passed" }] });
  console.log(`${c.case_id.padEnd(4)} ${r.verdict.padEnd(4)} span ${root.context.span_id}${r.fails.length ? `  ${r.fails.join(" | ").slice(0, 120)}` : ""}`);
}
console.log(`\n${pass}/${records.length} pass. ${dry ? "Dry run: nothing written." : "Writing to Arize..."}`);
if (!dry && records.length) {
  const tmp = path.join(dir, "code_checks.annotations.json");
  fs.writeFileSync(tmp, JSON.stringify(records, null, 1));
  const res = execFileSync("ax", ["spans", "annotate", PROJECT, "--space", SPACE, "--file", tmp, "--days", "30"], { encoding: "utf8" });
  console.log(res.trim().split("\n").slice(-3).join("\n"));
}
