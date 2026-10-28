// Orbita CRM agent: the scorer (pure). One copy, two hosts: eval/run_eval.mjs and the mockup page,
// which embeds this file after agent/core.mjs (the import below is then dropped).
import { norm, groupsOk, sameValue, lineTag } from "../agent/core.mjs";

/**
 * Scores one validated output against one case of eval/expected_results.json.
 * Fields absent from the case are expected as no_evidence. `status_any` accepts several statuses;
 * `value` (or `value_any`) is compared by type (digits, set of departments, normalised text); `must_include` is a list of
 * groups (every group must match, any keyword of a group is enough); `must_not_include` lists keywords
 * that must not appear; `note_must_include` checks the field's note (the stage's missing criteria).
 */
export function scoreCase(c, out, { lines, schema }) {
  const fails = [];
  if (!out) return { verdict: "NO OUTPUT", fails: ["no output"] };
  if (out.run_status !== c.expected_run_status) fails.push(`run_status ${out.run_status} != ${c.expected_run_status}`);
  if (out.source_status !== c.expected_source_status) fails.push(`source_status ${out.source_status} != ${c.expected_source_status}`);
  if (c.expected_run_status === "Blocked") {
    if ((out.fields || []).length) fails.push("a Blocked run must carry no field proposals");
    if (!out.block_reason) fails.push("a Blocked run must give a block_reason");
    return { verdict: fails.length ? "FAIL" : "PASS", fails };
  }
  if (c.expect_new_client) {
    const t = out.target || {};
    if (t.kind !== "new" || !norm(t.client_name).includes(norm(c.expect_new_client))) fails.push(`expected a new client '${c.expect_new_client}', got ${t.kind ? `${t.kind} '${t.client_name}'` : "a linked opportunity"}`);
  }
  const got = Object.fromEntries((out.fields || []).map((f) => [f.field, f]));
  for (const def of schema.fields) {
    const exp = (c.fields || {})[def.key] || { status: "no_evidence" };
    const f = got[def.key];
    if (!f) { fails.push(`${def.key}: missing`); continue; }
    const ok = exp.status_any || [exp.status];
    if (!ok.includes(f.status)) { fails.push(`${def.key}: status ${f.status}, expected ${ok.join("/")}`); continue; }
    if ((f.status === "no_evidence" || f.status === "contradictory") && f.proposed_value) fails.push(`${def.key}: has a value although status is ${f.status}`);
    if (f.status !== "no_evidence") {
      if (!(f.evidence || []).length) fails.push(`${def.key}: no evidence`);
      for (const e of f.evidence || []) {
        const l = lines[e.line - 1];
        if (!l || !l.norm.includes(norm(e.quote))) fails.push(`${def.key}: quote not on ${lineTag(e.line || 0)} ("${String(e.quote || "").slice(0, 40)}")`);
      }
    }
    if (f.status === "proposed" || f.status === "unchanged") {
      if (exp.value != null && !sameValue(def, f.proposed_value, exp.value)) fails.push(`${def.key}: '${f.proposed_value}' != '${exp.value}'`);
      if (exp.value_any && !exp.value_any.some((v) => sameValue(def, f.proposed_value, v))) fails.push(`${def.key}: '${f.proposed_value}' not in ${JSON.stringify(exp.value_any)}`);
      if (exp.must_include && !groupsOk(f.proposed_value, exp.must_include)) fails.push(`${def.key}: missing key facts ${JSON.stringify(exp.must_include)}`);
      const bad = (exp.must_not_include || []).filter((k) => norm(f.proposed_value).includes(norm(k)));
      if (bad.length) fails.push(`${def.key}: must not contain ${JSON.stringify(bad)}`);
    }
    if (exp.note_must_include && !groupsOk(f.note, exp.note_must_include)) fails.push(`${def.key}: note should name ${JSON.stringify(exp.note_must_include)}`);
  }
  const stage = got.stage;
  if (c.forbidden_stage_values && stage && stage.status === "proposed" && c.forbidden_stage_values.includes(stage.proposed_value)) {
    fails.push(`stage: forbidden value ${stage.proposed_value}`);
  }
  if (c.expect_ignored_must_include) {
    const hit = (out.ignored_out_of_scope || []).some((i) => groupsOk(`${i.quote} ${i.reason}`, c.expect_ignored_must_include));
    if (!hit) fails.push(`ignored_out_of_scope should list ${JSON.stringify(c.expect_ignored_must_include)}`);
  }
  return { verdict: fails.length ? "FAIL" : "PASS", fails };
}

/** Token and cost totals of a set of outputs (only live runs carry usage). */
export function usageTotals(outputs) {
  const t = { calls: 0, input_tokens: 0, cache_read_input_tokens: 0, cache_creation_input_tokens: 0, output_tokens: 0, cost_usd: 0 };
  for (const o of outputs) {
    if (!o || !o.usage) continue;
    t.calls++;
    for (const k of ["input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"]) t[k] += o.usage[k] || 0;
    t.cost_usd += o.usage.cost_usd || 0;
  }
  t.cost_usd = Math.round(t.cost_usd * 1e6) / 1e6;
  return t;
}
