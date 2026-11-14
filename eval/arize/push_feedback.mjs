// Sends seller thumbs from the CRM (.feedback/feedback.jsonl, written by mockups/server.mjs) to Arize as annotations on
// the run's root span: `thumbs up/down` (label), `seller_feedback_reason` (the reason picked on a thumbs down) and `notes`
// (the seller's optional note). Only ratings that carry the run's `span_id` can be linked; the others are counted and
// skipped (the server must keep runAgent's spanId on the run and copy it into the rating).
//
//   node eval/arize/push_feedback.mjs [--file .feedback/feedback.jsonl] [--dry-run]
//
// Run it daily (or on every rating) so the Arize dashboard shows the thumbs-up rate next to the evals.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const args = process.argv.slice(2);
const file = path.resolve(args.includes("--file") ? args[args.indexOf("--file") + 1] : process.env.ORBITA_FEEDBACK_FILE || path.join(KIT, ".feedback", "feedback.jsonl"));
const dry = args.includes("--dry-run");
const SPACE = process.env.ARIZE_SPACE || "Digithall Evals";
const PROJECT = process.env.ARIZE_PROJECT_NAME || "orbita-crm-agent";
const REASONS = ["wrong_opportunity", "wrong_values", "missed_stage", "wrong", "incomplete", "off_topic", "other"];

if (!fs.existsSync(file)) { console.log(`No feedback file at ${file}.`); process.exit(0); }
// the latest line of a rating wins (the same rule as the server)
const latest = new Map();
for (const line of fs.readFileSync(file, "utf8").split("\n")) { try { const f = JSON.parse(line); latest.set(f.uid, f); } catch { /* torn line */ } }
const all = [...latest.values()];
const linked = all.filter((f) => /^[0-9a-f]{16}$/.test(f.span_id || ""));
const records = linked.map((f) => {
  const values = [{ name: "thumbs up/down", label: f.rating === "up" ? "thumbs up" : "thumbs down" }];
  if (f.rating === "down" && REASONS.includes(f.reason)) values.push({ name: "seller_feedback_reason", label: f.reason });
  if (f.note) values.push({ name: "notes", text: String(f.note).slice(0, 280) });
  return { record_id: f.span_id, values };
});
console.log(`${all.length} rating(s): ${linked.length} linked to a trace, ${all.length - linked.length} without span_id (skipped).`);
if (dry || !records.length) process.exit(0);
const tmp = path.join(path.dirname(file), "feedback.annotations.json");
fs.writeFileSync(tmp, JSON.stringify(records, null, 1));
console.log(execFileSync("ax", ["spans", "annotate", PROJECT, "--space", SPACE, "--file", tmp, "--days", "30"], { encoding: "utf8" }).trim().split("\n").pop());
