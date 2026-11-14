// Uploads one run folder (real outputs of agent/pipeline.mjs on the 11 eval cases) as an Arize experiment on the
// `orbita-eval-cases` dataset, then attaches the code scorer's verdict to every run (`code_checks`: pass / fail, with the
// failed checks as text). Two experiments on the same dataset can then be compared side by side in Arize.
//
//   node eval/arize/push_experiment.mjs eval/arize_runs/2026-10-31_run2/claude-haiku-5-5 "haiku-5.5 · run2"
//
// Order imposed by Arize: create (example_id + output) -> export (to learn each run's id) -> annotate-runs.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { transcriptLines } from "../../agent/core.mjs";
import { scoreCase } from "../score.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const SPACE = process.env.ARIZE_SPACE || "Digithall Evals";
const DATASET = process.env.ARIZE_DATASET || "orbita-eval-cases";
const [dirArg, name] = process.argv.slice(2);
const dir = path.resolve(dirArg || "");
if (!fs.existsSync(dir) || !name) { console.error('Usage: node eval/arize/push_experiment.mjs <run folder> "<experiment name>"'); process.exit(1); }
const ax = (args, input) => { const out = execFileSync("ax", args, { encoding: "utf8", maxBuffer: 64 << 20, input }); const i = out.search(/[[{]/); return i >= 0 ? JSON.parse(out.slice(i)) : out; };

const schema = rj(path.join(KIT, "agent", "field_schema.json"));
const cases = rj(path.join(KIT, "eval", "expected_results.json")).cases;
const meetings = [...rj(path.join(KIT, "data", "meetings.json")), ...rj(path.join(KIT, "data", "channel_meetings.json"))];
const linesOf = (id) => { const m = meetings.find((x) => x.meeting_id === id); return m && m.transcript_file ? transcriptLines(fs.readFileSync(path.join(KIT, m.transcript_file), "utf8")) : []; };

// 1. dataset example ids (the top-level `id` of each exported example), by case
const examples = ax(["datasets", "export", DATASET, "--space", SPACE, "--all", "--stdout"]);
// the user fields come back under additional_properties; the row id Arize wants is the top-level `id`
const exampleOf = Object.fromEntries(examples.map((e) => [(e.additional_properties || e).case_id, e.id]));

// 2. runs: the real output of each case, plus what the scorer needs later
const runs = []; const verdicts = {};
for (const c of cases) {
  const f = path.join(dir, `${c.case_id}.json`);
  if (!fs.existsSync(f) || !exampleOf[c.case_id]) continue;
  const out = rj(f);
  verdicts[c.case_id] = scoreCase(c, out, { lines: linesOf(c.meeting_id), schema });
  const { trace_id, ...rest } = out;
  runs.push({ example_id: exampleOf[c.case_id], output: JSON.stringify(rest, null, 2), case_id: c.case_id, trace_id: trace_id || "",
    model: (out.usage && out.usage.model) || path.basename(dir), cost_usd: out.usage ? out.usage.cost_usd : 0,
    output_tokens: out.usage ? out.usage.output_tokens : 0, run_status: out.run_status });
}
const tmp = path.join(dir, "experiment.runs.json");
fs.writeFileSync(tmp, JSON.stringify(runs));
ax(["experiments", "create", "--name", name, "--dataset", DATASET, "--space", SPACE, "--file", tmp]);

// 3. learn each run's id, 4. attach the code verdict to it
const exported = ax(["experiments", "export", name, "--dataset", DATASET, "--space", SPACE, "--stdout"]);
const caseOfExample = Object.fromEntries(Object.entries(exampleOf).map(([k, v]) => [v, k]));
const ann = exported.map((r) => { const v = verdicts[caseOfExample[r.example_id]]; return v && { record_id: r.id, values: [
  { name: "code_checks", label: v.verdict === "PASS" ? "pass" : "fail", text: v.fails.join(" | ").slice(0, 1000) || "all checks passed" }] }; }).filter(Boolean);
const annFile = path.join(dir, "experiment.annotations.json");
fs.writeFileSync(annFile, JSON.stringify(ann, null, 1));
ax(["experiments", "annotate-runs", name, "--dataset", DATASET, "--space", SPACE, "--file", annFile]);
const pass = Object.values(verdicts).filter((v) => v.verdict === "PASS").length;
console.log(`Experiment "${name}": ${exported.length} runs, code_checks ${pass}/${Object.keys(verdicts).length} pass, ${ann.length} annotated.`);
