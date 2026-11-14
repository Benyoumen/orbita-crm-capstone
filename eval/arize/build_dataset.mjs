// Builds the Arize dataset of the 11 eval cases: one example per case, with the exact per-run message the agent reads
// (CRM context + numbered conversation), the oracle from eval/expected_results.json and the case metadata.
// Experiments replay these examples on a model or prompt version and score them with the same code scorer.
//
//   node eval/arize/build_dataset.mjs > eval/arize/orbita_eval_cases.json
//   ax datasets create --name "orbita-eval-cases" --space "Digithall Evals" --file eval/arize/orbita_eval_cases.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as core from "../../agent/core.mjs";
import * as P from "../../agent/pipeline.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const cases = JSON.parse(fs.readFileSync(path.join(KIT, "eval", "expected_results.json"), "utf8")).cases;

const examples = cases.map((c) => {
  const data = P.loadData();
  let meeting = data.meetings.find((m) => m.meeting_id === c.meeting_id);
  const transcript = P.readTranscript(meeting);
  meeting = core.attribute({ meeting, lines: core.transcriptLines(transcript || ""), data, user: data.team.find((u) => u.user_id === c.run_as_user_id), schema: P.SCHEMA });
  data.meetings = [meeting, ...data.meetings.filter((m) => m.meeting_id !== meeting.meeting_id)];
  const pre = core.prepareRun({ meetingId: meeting.meeting_id, opportunityId: c.opportunity_id, userId: c.run_as_user_id, data, transcript,
    log: core.newLog("DATASET"), schema: P.SCHEMA });
  const blocked = Boolean(pre.output);
  return {
    case_id: c.case_id,
    prd_case: c.prd_case,
    scenario: c.name,
    proves: c.proves || "",
    meeting_id: c.meeting_id,
    run_as_user_id: c.run_as_user_id,
    opportunity_id: c.opportunity_id || "",
    // what the model reads for this case; blocked cases stop in code, so they carry the transcript instead
    input: blocked ? (transcript || "") : P.buildPrompt({ ...pre, data }).user,
    blocked_in_code: blocked,
    expected_run_status: c.expected_run_status,
    expected_source_status: c.expected_source_status,
    expected: JSON.stringify({ fields: c.fields || {}, expect_new_client: c.expect_new_client || null,
      forbidden_stage_values: c.forbidden_stage_values || null, expect_ignored_must_include: c.expect_ignored_must_include || null }),
  };
});
process.stdout.write(JSON.stringify(examples, null, 1));
