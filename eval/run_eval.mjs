// Scores agent outputs against eval/expected_results.json, per label (mock, or one model id).
//   node eval/run_eval.mjs                       every label found in eval/outputs/
//   node eval/run_eval.mjs --label claude-haiku-5-5
// Writes eval/results.md (paste into PRD rows F32-F34) and eval/results.json (read by the mockup's
// Agent > Quality checks). Outputs come from: node agent/pipeline.mjs --all [--mock | --model <id>].

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { transcriptLines } from "../agent/core.mjs";
import { scoreCase, usageTotals } from "./score.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const KIT = path.resolve(HERE, "..");
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const schema = rj(path.join(KIT, "agent", "field_schema.json"));
const cases = rj(path.join(HERE, "expected_results.json")).cases;
const meetings = [...rj(path.join(KIT, "data", "meetings.json")), ...rj(path.join(KIT, "data", "channel_meetings.json"))];
const outRoot = path.join(HERE, "outputs");
const args = process.argv.slice(2);
const only = args.includes("--label") ? args[args.indexOf("--label") + 1] : null;
const labels = fs.existsSync(outRoot)
  ? fs.readdirSync(outRoot).filter((d) => fs.statSync(path.join(outRoot, d)).isDirectory() && (!only || d === only)).sort((a, b) => (a === "mock" ? -1 : b === "mock" ? 1 : a.localeCompare(b)))
  : [];
if (!labels.length) { console.error("No outputs: run node agent/pipeline.mjs --all --mock (or --model <id>) first."); process.exit(1); }

const linesOf = (meetingId) => {
  const m = meetings.find((x) => x.meeting_id === meetingId);
  const p = m && m.transcript_file ? path.join(KIT, m.transcript_file) : null;
  return p && fs.existsSync(p) ? transcriptLines(fs.readFileSync(p, "utf8")) : [];
};

const result = { run_at: new Date().toISOString(), cases: cases.map((c) => ({ case_id: c.case_id, prd_case: c.prd_case, name: c.name, proves: c.proves || null })), labels: {} };
for (const label of labels) {
  const dir = path.join(outRoot, label);
  const outs = []; const rows = [];
  for (const c of cases) {
    const file = path.join(dir, `${c.case_id}.json`);
    const out = fs.existsSync(file) ? rj(file) : null;
    outs.push(out);
    rows.push({ case_id: c.case_id, ...scoreCase(c, out, { lines: linesOf(c.meeting_id), schema }) });
  }
  const usage = usageTotals(outs);
  result.labels[label] = { passed: rows.filter((r) => r.verdict === "PASS").length, total: cases.length, usage,
    cost_per_call_usd: usage.calls ? Math.round((usage.cost_usd / usage.calls) * 1e6) / 1e6 : null, rows };
}

const fmt = (n) => (n == null ? "-" : Number(n).toLocaleString("en-US"));
let md = `# Eval results\n\nRun: ${result.run_at}  \nCases: ${cases.length} (eval/expected_results.json); outputs: eval/outputs/<label>/\n\n`;
md += "## Score by model\n\n| Label | Passed | Model calls | Input tokens | Cache read | Cache write | Output tokens | Cost (USD) | Cost per call |\n|---|---|---|---|---|---|---|---|---|\n";
for (const [label, r] of Object.entries(result.labels)) {
  const u = r.usage;
  md += `| ${label} | ${r.passed}/${r.total} | ${u.calls} | ${fmt(u.input_tokens)} | ${fmt(u.cache_read_input_tokens)} | ${fmt(u.cache_creation_input_tokens)} | ${fmt(u.output_tokens)} | ${u.calls ? u.cost_usd.toFixed(4) : "-"} | ${r.cost_per_call_usd != null ? r.cost_per_call_usd.toFixed(4) : "-"} |\n`;
}
const blocked = cases.filter((c) => c.expected_run_status === "Blocked").map((c) => c.case_id);
md += `\nBlocked cases (${blocked.join(", ")}) stop in code before any model call, so a full live run makes ${cases.length - blocked.length} calls. \`mock\` replays the reference answers through the same validator: it proves the platform, not the model.\n`;
for (const [label, r] of Object.entries(result.labels)) {
  md += `\n## Cases: ${label}\n\n| Case | PRD case | Scenario | Result | Issues |\n|---|---|---|---|---|\n`;
  for (const row of r.rows) {
    const c = cases.find((x) => x.case_id === row.case_id);
    md += `| ${row.case_id} | ${c.prd_case} | ${c.name} | ${row.verdict} | ${row.fails.join("; ").replace(/\|/g, "/") || "-"} |\n`;
  }
}
const manual = cases.filter((c) => c.platform_checks);
md += "\n## Platform checks (run in the mockup: Agent > Quality checks, and by the mockup gate)\n";
for (const c of manual) { md += `\n**${c.case_id}: ${c.name}**\n`; for (const p of c.platform_checks) md += `- ${p}\n`; }
fs.writeFileSync(path.join(HERE, "results.md"), md);
fs.writeFileSync(path.join(HERE, "results.json"), JSON.stringify(result, null, 2));

for (const [label, r] of Object.entries(result.labels)) {
  console.log(`${label.padEnd(20)} ${r.passed}/${r.total}${r.usage.calls ? `  ${r.usage.calls} calls  $${r.usage.cost_usd.toFixed(4)}` : ""}`);
  for (const row of r.rows.filter((x) => x.verdict !== "PASS")) console.log(`   ${row.case_id} ${row.verdict}: ${row.fails.join(" | ")}`);
}
console.log("Details: eval/results.md");
