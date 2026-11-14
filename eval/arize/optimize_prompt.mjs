// Prompt optimization (arize-prompt-optimization skill, Phase 3): fills the skill's meta-prompt with the current system
// prompt and the failing runs of one or more run folders (code-scorer failures, with the oracle's expectation), asks
// Claude for a revised prompt, and saves it as a CANDIDATE. Nothing is promoted: the candidate must win an experiment
// first (ORBITA_SYSTEM_PROMPT_FILE=<candidate .txt> node agent/pipeline.mjs --all --model ... --out ...).
//
//   node eval/arize/optimize_prompt.mjs eval/arize_runs/2026-10-31_run1/claude-haiku-5-5 eval/arize_runs/2026-10-31_run2/claude-haiku-5-5
//
// Output: eval/arize/prompt_candidate.txt (system prompt), eval/arize/prompt_candidate.md (reasoning and the diff summary).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as core from "../../agent/core.mjs";
import * as P from "../../agent/pipeline.mjs";
import { scoreCase } from "../score.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const KIT = path.resolve(HERE, "..", "..");
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const MODEL = process.env.OPTIMIZER_MODEL || "claude-sonnet-5-5";
const dirs = process.argv.slice(2).map((d) => path.resolve(d));
if (!dirs.length) { console.error("Usage: node eval/arize/optimize_prompt.mjs <run folder> [<run folder>...]"); process.exit(1); }

const cases = rj(path.join(KIT, "eval", "expected_results.json")).cases;
const meetings = [...rj(path.join(KIT, "data", "meetings.json")), ...rj(path.join(KIT, "data", "channel_meetings.json"))];
const linesOf = (id) => { const m = meetings.find((x) => x.meeting_id === id); return m && m.transcript_file ? core.transcriptLines(fs.readFileSync(path.join(KIT, m.transcript_file), "utf8")) : []; };
const examples = rj(path.join(HERE, "orbita_eval_cases.json"));

// records: one per failing run, with only what the meta-prompt needs (the input, the failing fields, the expectation)
const records = [];
for (const dir of dirs) for (const c of cases) {
  const f = path.join(dir, `${c.case_id}.json`);
  if (!fs.existsSync(f)) continue;
  const out = rj(f);
  const v = scoreCase(c, out, { lines: linesOf(c.meeting_id), schema: P.SCHEMA });
  if (v.verdict === "PASS") continue;
  const bad = [...new Set(v.fails.map((x) => x.split(":")[0]))];
  records.push({ run: `${path.basename(path.dirname(dir))}/${path.basename(dir)}`, case: c.case_id, scenario: c.name,
    input: examples.find((e) => e.case_id === c.case_id).input,
    output_failing_fields: out.fields.filter((x) => bad.includes(x.field)).map(({ field, status, proposed_value, evidence, note }) => ({ field, status, proposed_value, evidence, note })),
    expected: Object.fromEntries(bad.map((k) => [k, (c.fields || {})[k] || { status: "no_evidence" }])),
    eval_label: "fail", eval_explanation: v.fails.join(" | ") });
}
console.log(`${records.length} failing run(s): ${records.map((r) => `${r.case}`).join(", ")}`);
if (!records.length) process.exit(0);

const original = P.systemPrompt();
const meta = fs.readFileSync(path.join(process.env.USERPROFILE || process.env.HOME, ".claude", "skills", "arize-prompt-optimization", "references", "optimization-meta-prompt.md"), "utf8")
  .split("````")[1].trim();
const prompt = meta.replace("{PASTE_ORIGINAL_PROMPT_HERE}", `SYSTEM:\n${original}\n\nUSER:\n{{run_input}}`).replace("{PASTE_RECORDS_HERE}", JSON.stringify(records, null, 1))
  + `\n\nCONTEXT FOR THIS PROMPT (read before editing)
- The same prompt scored 11/11 on Sonnet 5.5 in two runs; these failures come from Haiku 5.5 and vary between runs, so prefer clarifying rules over adding content.
- The "expected" block is an oracle written by a person: a failure can mean the oracle is too narrow. Only change the prompt where the rule itself is unclear; otherwise say in reasoning that the oracle should be reviewed.
- Keep the template variable {{run_input}} exactly. Keep every JSON example, field name, status name and the output contract unchanged. Change as little as possible; return the WHOLE system prompt.
Return JSON with "reasoning" (bullets) and "system" (the full revised system prompt text).`;

const schema = { type: "object", additionalProperties: false, required: ["reasoning", "system"],
  properties: { reasoning: { type: "array", items: { type: "string" } }, system: { type: "string" } } };
const r = await P.callJson({ system: "You are an expert in prompt optimization for production LLM agents.", user: prompt, schema, model: MODEL, effort: "medium", maxTokens: 20000 }); // under the SDK's non-streaming ceiling; the whole prompt is ~8k tokens
const cand = r.raw.system;
const lenDelta = cand.length - original.length;
const changed = original.split("\n").filter((l) => !cand.includes(l)).length;
fs.writeFileSync(path.join(HERE, "prompt_candidate.txt"), cand);
fs.writeFileSync(path.join(HERE, "prompt_candidate.md"), `# Prompt candidate (not promoted)\n\nOptimizer: ${MODEL} · cost USD ${(core.costOf(r.usage, MODEL) || 0).toFixed(4)} · ${records.length} failing runs as input\n\nLength ${original.length} -> ${cand.length} chars (${lenDelta >= 0 ? "+" : ""}${lenDelta}); ${changed} original lines changed or removed; {{run_input}} untouched in the user message.\n\n## Reasoning\n\n${r.raw.reasoning.map((x) => `- ${x}`).join("\n")}\n`);
console.log(`candidate: ${cand.length} chars (${lenDelta >= 0 ? "+" : ""}${lenDelta}), ${changed} original lines changed · USD ${(core.costOf(r.usage, MODEL) || 0).toFixed(4)}`);
console.log(r.raw.reasoning.map((x) => `- ${x}`).join("\n"));
