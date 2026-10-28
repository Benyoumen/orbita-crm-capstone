// Rebuilds the kit's synthetic data from the authored sources, in order:
//   1. data/granola/authoring/MTG-*.txt -> data/granola/notes/MTG-*.json   notes in the exact Granola API shape
//   2. agent/granola.mjs (fixtures)     -> data/meetings.json + transcripts/MTG-*.txt   what the agent reads
//      data/channels/*.txt (chat exports) -> data/channel_meetings.json + transcripts/     read and attributed by agent/core.mjs
//      samples/                             the same conversations as files to drop in the page (WebVTT, SRT, Otter,
//                                           plain text, WhatsApp); each must read back to the exact spoken text
//   3. eval/reference_outputs/*.json, examples/EX*_expected_output.json  -> line numbers filled from the quotes
//      (every quote must exist on exactly the line it lands on; a missing quote stops the build)
//   4. policies/field_dictionary.md + agent/output_schema.json             generated from agent/field_schema.json
//   5. data/csv/*.csv                                                      the CRM seed for a spreadsheet
//
//   node scripts/build_data.mjs
// Authoring format: '# key: value' header lines, then '[hh:mm:ss] Speaker (Company): text' lines.
// The note owner's lines become microphone/"me"; 'Customer (unattributed)' becomes a nameless system-audio voice.

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import { transcriptLines, tsToSec, secToTs, norm, renderFieldDictionary, buildOutputSchema, fieldOf, parseConversation, labelSpeakers,
  conversationText, conversationKey, attribute } from "../agent/core.mjs";
import { syncFixtures } from "../agent/granola.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const P = (...a) => path.join(KIT, ...a);
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const wj = (p, o) => fs.writeFileSync(p, JSON.stringify(o, null, 2) + "\n");
const schema = rj(P("agent", "field_schema.json"));
const team = rj(P("data", "team.json"));
const fail = (msg) => { console.error("BUILD FAILED: " + msg); process.exit(1); };

// ------------------------------------------------------------------ 1. authoring -> Granola notes
const AUTH = P("data", "granola", "authoring");
const NOTES = P("data", "granola", "notes");
fs.mkdirSync(NOTES, { recursive: true });
const FOLDER = { id: "fol_CRMsyncFolder1", object: "folder", name: "CRM sync", parent_folder_id: null, space_id: null };
const isoAt = (startMs, sec) => new Date(startMs + sec * 1000).toISOString().replace(".000Z", "Z");

function parseAuthoring(text, file) {
  const head = {}; const lines = [];
  for (const raw of text.split(/\r?\n/)) {
    const h = raw.match(/^# (\w+): (.*)$/);
    if (h) { head[h[1]] = h[2].trim(); continue; }
    if (!raw.trim()) continue;
    const m = raw.match(/^\[(\d{2}:\d{2}:\d{2})\] ([^:]+?): (.*)$/);
    if (!m) fail(`${file}: unreadable line "${raw.slice(0, 60)}"`);
    lines.push({ sec: tsToSec(m[1]), who: m[2].trim(), text: m[3].trim() });
  }
  for (const k of ["title", "start", "scheduled_minutes", "owner", "attendees"]) if (!head[k]) fail(`${file}: header '${k}' missing`);
  return { head, lines };
}

const authored = fs.existsSync(AUTH) ? fs.readdirSync(AUTH).filter((f) => /^MTG-[\w-]+\.txt$/.test(f)).sort() : [];
for (const f of authored) {
  const { head, lines } = parseAuthoring(fs.readFileSync(path.join(AUTH, f), "utf8"), f);
  const meetingId = f.replace(/\.txt$/, "");
  const owner = team.find((u) => u.email === head.owner);
  if (!owner) fail(`${f}: owner ${head.owner} is not in the team roster`);
  const attendees = head.attendees.split(";").map((s) => s.trim()).filter(Boolean).map((s) => {
    const m = s.match(/^(.*?)\s*<([^>]+)>$/);
    if (!m) fail(`${f}: attendee "${s}" is not 'Name <email>'`);
    return { name: m[1].trim(), email: m[2].trim().toLowerCase() };
  });
  const startMs = Date.parse(head.start);
  const sched = Number(head.scheduled_minutes);
  const id = "not_" + crypto.createHash("sha1").update(meetingId + head.title).digest("hex").slice(0, 14);
  const transcript = lines.map((l, i) => {
    const next = lines[i + 1];
    const words = l.text.split(/\s+/).length;
    let dur = Math.max(1, Math.round(words / 2.6));
    if (next) dur = Math.max(1, Math.min(dur, next.sec - l.sec - 1));
    let speaker;
    if (l.who === `${owner.name} (Orbita)`) speaker = { source: "microphone", attribution: "me" };
    else if (/^Customer \(unattributed\)$/.test(l.who)) speaker = { source: "speaker", attribution: "them" };
    else speaker = { source: "speaker", attribution: "them", name: l.who.replace(/\s*\([^)]*\)\s*$/, "") };
    return { speaker, text: l.text, start_time: isoAt(startMs, l.sec), end_time: isoAt(startMs, l.sec + dur) };
  });
  const lastEnd = transcript.length ? Date.parse(transcript[transcript.length - 1].end_time) : startMs;
  const note = {
    id, object: "note", title: head.title,
    owner: { name: owner.name, email: owner.email },
    created_at: isoAt(startMs, 0), updated_at: new Date(lastEnd + 120000).toISOString().replace(".000Z", "Z"), deleted_at: null,
    web_url: `https://notes.granola.ai/d/${id}`,
    calendar_event: { event_title: head.title, invitees: attendees.map((a) => ({ email: a.email })), organiser: owner.email,
      calendar_event_id: `evt_${id.slice(4)}`, scheduled_start_time: isoAt(startMs, 0), scheduled_end_time: isoAt(startMs, sched * 60) },
    attachments: [], attendees, folder_membership: [FOLDER], space_membership: [],
    summary_text: head.summary || "", summary_markdown: head.summary || null, private_notes_text: null, private_notes_markdown: null,
    transcript,
  };
  wj(path.join(NOTES, `${meetingId}.json`), note);
}
console.log(`1. ${authored.length} Granola notes -> data/granola/notes/`);

// ------------------------------------------------------------------ 2. connector (fixtures mode)
const granolaMeetings = syncFixtures();
console.log(`2. ${granolaMeetings.length} meetings -> data/meetings.json (+ transcripts/)`);

// chat exports: parsed, labelled and attributed by the same core the page and the server use
const CH = P("data", "channels");
const clientsSeed = rj(P("data", "clients.json"));
const oppsSeed = rj(P("data", "opportunities.json"));
const channelMeetings = [];
for (const c of fs.existsSync(P("data", "channels", "channels.json")) ? rj(P("data", "channels", "channels.json")) : []) {
  const owner = team.find((u) => u.email === c.owner);
  if (!owner) fail(`channels.json: owner ${c.owner} is not in the team roster`);
  const parsed = parseConversation(fs.readFileSync(path.join(CH, c.file), "utf8"));
  if (parsed.kind !== "whatsapp" || parsed.lines.length < 2) fail(`${c.file}: not read as a WhatsApp export (${parsed.kind}, ${parsed.lines.length} lines)`);
  const bare = { meeting_id: c.meeting_id, source: { system: "whatsapp", file: c.file, format: parsed.kind }, title: c.file.replace(/\.txt$/i, "").replace(/^WhatsApp Chat with/i, "WhatsApp chat with"),
    start: `${parsed.start}:00${c.tz}`, scheduled_minutes: null, recorded_minutes: null, chat: true, organiser_id: owner.user_id, owner_email: owner.email,
    transcript_status: "complete", ends_mid_sentence: false, granola_summary: null };
  const data = { team, clients: clientsSeed, opportunities: oppsSeed, meetings: [] };
  const linked = attribute({ meeting: bare, lines: labelSpeakers(parsed.lines, { team }), data, user: owner, schema });
  const client = clientsSeed.find((x) => x.client_id === linked.client_id) || null;
  const lines = labelSpeakers(parsed.lines, { team, client });
  const rel = `transcripts/${c.meeting_id}.txt`;
  fs.writeFileSync(P(rel), conversationText(lines) + "\n");
  channelMeetings.push({ ...linked, participants: [...new Set(lines.map((l) => l.speaker))], transcript_file: rel });
}
wj(P("data", "channel_meetings.json"), channelMeetings);
const meetings = [...granolaMeetings, ...channelMeetings];
console.log(`   ${channelMeetings.length} chat export(s) -> data/channel_meetings.json (+ transcripts/)`);

// samples: the eleven conversations as the files a seller would drop (name, format, the voice labels a tool would use)
const SAMPLES = [
  ["MTG-2001", "acme-logistics_discovery-call.vtt", "teams"],
  ["MTG-2002", "verde-retail_intro-call.txt", "kit"],
  ["MTG-2003", "nimbus-health_demo-planning.txt", "otter"],
  ["MTG-2004", "verde-retail_pos-data-questions.vtt", "zoom"],
  ["MTG-2005", "delta-pharma_intro-call.vtt", "teams"],
  ["MTG-2006", "atlas-manufacturing_proposal-check-in.srt", "srt"],
  ["MTG-2007", "cedro-construtora_discovery-call.txt", "plain"],
  ["MTG-2008", "horizonte-foods_solution-walkthrough.vtt", "zoom"],
  ["MTG-2009", "lumen-education_scope-session.vtt", "teams"],
  ["MTG-2010", "pampa-agro_discovery-call.txt", "kit"],
];
const SD = P("samples");
fs.mkdirSync(SD, { recursive: true });
for (const f of fs.readdirSync(SD)) if (!/\.md$/i.test(f)) fs.rmSync(path.join(SD, f));
const vttTs = (sec) => `${secToTs(Math.floor(sec))}.${String(Math.round((sec % 1) * 1000)).padStart(3, "0")}`;
const bareName = (s) => (/^Customer \(unattributed\)$/.test(s) ? "Speaker 2" : s.replace(/\s*\([^)]*\)\s*$/, ""));
for (const [id, file, style] of SAMPLES) {
  const m = granolaMeetings.find((x) => x.meeting_id === id);
  if (!m) fail(`samples: meeting ${id} not found`);
  const lines = transcriptLines(fs.readFileSync(P(m.transcript_file), "utf8"));
  const sec = (l) => tsToSec(l.timestamp);
  const end = (i) => Math.max(sec(lines[i]) + 1, Math.min(sec(lines[i]) + Math.max(1.5, lines[i].text.split(/\s+/).length / 2.6), i + 1 < lines.length ? sec(lines[i + 1]) - 0.2 : Infinity));
  let out;
  if (style === "teams" || style === "zoom") {
    out = "WEBVTT\n\n" + lines.map((l, i) => `${i + 1}\n${vttTs(sec(l))} --> ${vttTs(end(i))}\n${style === "teams" ? `<v ${bareName(l.speaker)}>${l.text}</v>` : `${bareName(l.speaker)}: ${l.text}`}\n`).join("\n");
  } else if (style === "srt") {
    out = lines.map((l, i) => `${i + 1}\n${vttTs(sec(l)).replace(".", ",")} --> ${vttTs(end(i)).replace(".", ",")}\n${bareName(l.speaker)}: ${l.text}\n`).join("\n");
  } else if (style === "otter") {
    const clock = (t) => { const s2 = tsToSec(t); const h = Math.floor(s2 / 3600), mi = Math.floor((s2 % 3600) / 60), se = s2 % 60; return h ? `${h}:${String(mi).padStart(2, "0")}:${String(se).padStart(2, "0")}` : `${mi}:${String(se).padStart(2, "0")}`; };
    out = lines.map((l) => `${bareName(l.speaker)}  ${clock(l.timestamp)}\n${l.text}\n`).join("\n");
  } else if (style === "plain") {
    out = lines.map((l) => `${bareName(l.speaker)}: ${l.text}`).join("\n") + "\n";
  } else {
    out = lines.map((l) => `[${l.timestamp}] ${bareName(l.speaker)}: ${l.text}`).join("\n") + "\n";
  }
  fs.writeFileSync(path.join(SD, file), out);
  const back = parseConversation(out);
  if (conversationKey(back.lines) !== conversationKey(lines)) fail(`samples/${file}: reads back to different text (${back.kind}, ${back.lines.length} of ${lines.length} lines)`);
}
for (const c of channelMeetings) {
  fs.copyFileSync(path.join(CH, c.source.file), path.join(SD, c.source.file));
  if (conversationKey(parseConversation(fs.readFileSync(path.join(SD, c.source.file), "utf8")).lines) !== conversationKey(transcriptLines(fs.readFileSync(P(c.transcript_file), "utf8"))))
    fail(`samples/${c.source.file}: reads back to different text`);
}
console.log(`   ${SAMPLES.length + channelMeetings.length} sample files -> samples/ (each reads back to the same spoken text)`);

// ------------------------------------------------------------------ 3. line numbers of the reference answers
function fillLines(obj, lines, where) {
  const place = (item, what) => {
    const q = norm(String(item.quote || "").replace(/^["']+|["']+$/g, ""));
    const hits = lines.filter((l) => l.norm.includes(q));
    if (!hits.length) fail(`${where}: ${what} quote not found in the transcript: "${item.quote}"`);
    if (hits.length > 1 && !(item.line && hits.some((h) => h.n === item.line))) console.warn(`   ${where}: ${what} quote appears on ${hits.length} lines, using L${hits[0].n}: "${item.quote}"`);
    item.line = item.line && hits.some((h) => h.n === item.line) ? item.line : hits[0].n;
  };
  for (const f of obj.fields || []) for (const e of f.evidence || []) place(e, f.field);
  for (const i of obj.ignored_out_of_scope || []) place(i, "ignored_out_of_scope");
}
let refs = 0;
for (const f of fs.readdirSync(P("eval", "reference_outputs")).filter((x) => x.endsWith(".json"))) {
  const file = P("eval", "reference_outputs", f);
  const o = rj(file);
  const m = meetings.find((x) => x.meeting_id === o.meeting_id);
  if (!m) fail(`${f}: meeting ${o.meeting_id} not found`);
  if (o.run_status === "Blocked") continue;
  fillLines(o, transcriptLines(fs.readFileSync(P(m.transcript_file), "utf8")), f);
  wj(file, o); refs++;
}
for (const x of ["EX1", "EX2"]) {
  const file = P("examples", `${x}_expected_output.json`);
  if (!fs.existsSync(file)) continue;
  const o = rj(file);
  fillLines(o, transcriptLines(fs.readFileSync(P("examples", `${x}_transcript.txt`), "utf8")), `${x}_expected_output.json`);
  wj(file, o); refs++;
}
console.log(`3. line numbers filled in ${refs} reference answers`);

// ------------------------------------------------------------------ 4. generated policy files
fs.writeFileSync(P("policies", "field_dictionary.md"), "<!-- Generated by scripts/build_data.mjs from agent/field_schema.json. Do not edit by hand. -->\n\n" + renderFieldDictionary(schema) + "\n");
wj(P("agent", "output_schema.json"), { $schema: "https://json-schema.org/draft/2020-12/schema", title: "Call-to-CRM agent output (sparse, line-cited). Generated from agent/field_schema.json by scripts/build_data.mjs.", ...buildOutputSchema(schema) });
console.log("4. policies/field_dictionary.md + agent/output_schema.json regenerated");

// ------------------------------------------------------------------ 5. CSVs
const csvCell = (v) => { const s = v == null ? "" : String(v); return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
const csv = (rows) => rows.map((r) => r.map(csvCell).join(",")).join("\n") + "\n";
fs.mkdirSync(P("data", "csv"), { recursive: true });
const clients = rj(P("data", "clients.json"));
const opps = rj(P("data", "opportunities.json"));
const oppDefs = schema.fields.filter((d) => d.record === "opportunity");
const cliDefs = schema.fields.filter((d) => d.record === "client");
fs.writeFileSync(P("data", "csv", "opportunities.csv"), csv([
  ["opportunity_id", "client_id", "client", "name", "owner_id", "amount_usd", "close_date", "last_updated", ...oppDefs.flatMap((d) => [d.key, `${d.key}_approved`])],
  ...opps.map((o) => [o.opportunity_id, o.client_id, (clients.find((c) => c.client_id === o.client_id) || {}).name, o.name, o.owner_id, o.amount_usd, o.close_date, o.last_updated,
    ...oppDefs.flatMap((d) => { const f = fieldOf(o, d.key); return [f.value, f.approved]; })]),
]));
fs.writeFileSync(P("data", "csv", "clients.csv"), csv([
  ["client_id", "name", "domain", "industry", "hq", ...cliDefs.flatMap((d) => [d.key, `${d.key}_approved`]), "contacts"],
  ...clients.map((c) => [c.client_id, c.name, c.domain, c.industry, c.hq, ...cliDefs.flatMap((d) => { const f = fieldOf(c, d.key); return [f.value, f.approved]; }),
    c.contacts.map((p) => `${p.name} (${p.title}, ${p.email}, ${p.buying_role})`).join("; ")]),
]));
fs.writeFileSync(P("data", "csv", "team.csv"), csv([["user_id", "name", "role", "email", "access"], ...team.map((u) => [u.user_id, u.name, u.role, u.email, u.access])]));
fs.writeFileSync(P("data", "csv", "meetings.csv"), csv([
  ["meeting_id", "source", "granola_note_id", "title", "start", "scheduled_minutes", "recorded_minutes", "organiser_id", "client_id", "linked_opportunity_id", "match_reason", "transcript_status", "transcript_file"],
  ...meetings.map((m) => [m.meeting_id, m.source.system, m.source.note_id, m.title, m.start, m.scheduled_minutes, m.recorded_minutes, m.organiser_id, m.client_id, m.linked_opportunity_id, m.match_reason, m.transcript_status, m.transcript_file]),
]));
const cases = fs.existsSync(P("eval", "expected_results.json")) ? rj(P("eval", "expected_results.json")).cases : [];
fs.writeFileSync(P("data", "csv", "expected.csv"), csv([
  ["case_id", "prd_case", "name", "meeting_id", "opportunity_id", "run_as_user_id", "expected_run_status", "expected_source_status", "proposed", "contradictory", "unchanged"],
  ...cases.map((c) => {
    const by = (s) => Object.entries(c.fields || {}).filter(([, e]) => (e.status_any || [e.status]).includes(s)).map(([k]) => k).join(" ");
    return [c.case_id, c.prd_case, c.name, c.meeting_id, c.opportunity_id, c.run_as_user_id, c.expected_run_status, c.expected_source_status, by("proposed"), by("contradictory"), by("unchanged")];
  }),
]));
console.log("5. data/csv/ regenerated (opportunities, clients, team, meetings, expected)");
