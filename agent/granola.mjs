// Granola connector: Granola notes -> meetings and transcripts the pipeline can run.
// Node 18+, no dependencies. The API key never leaves the server.
//
//   node agent/granola.mjs sync                 fixtures: data/granola/notes/MTG-*.json -> data/meetings.json + transcripts/
//   node agent/granola.mjs sync --live          GRANOLA_API_KEY + GRANOLA_FOLDER: the notes of one folder -> .granola-cache/
//   node agent/granola.mjs status [--live]      what the connector sees, without writing
//   node agent/granola.mjs folder-of <note>     prints the folders of ONE note (a not_… id or its link): how to find GRANOLA_FOLDER
//
// Granola public API (docs.granola.ai, Business plan and up): GET /v1/notes (created_after, updated_after,
// folder_id, cursor, page_size <= 30) and GET /v1/notes/{id}?include=transcript; a transcript too large to
// inline answers 413 TRANSCRIPT_TOO_LARGE and is read page by page from /v1/notes/{id}/transcript.
// There are no webhooks, so the server polls. Rate limit: 25 requests per 5 s, 5 per second sustained.
//
// Only the chosen folder is read: the connector never lists or opens notes outside it, and the cache of
// real notes (.granola-cache/) is kept out of the mockup snapshot, the eval outputs and the hand-in.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { norm, secToTs, transcriptLines, endsMidSentence, isClosed } from "./core.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const API = "https://public-api.granola.ai/v1";
export const CACHE = path.join(KIT, ".granola-cache");
const FIXTURES = path.join(KIT, "data", "granola", "notes");
const TZ = process.env.ORBITA_TZ || "America/Sao_Paulo";
const rj = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const eq = (a, b) => !!a && !!b && String(a).trim().toLowerCase() === String(b).trim().toLowerCase();
const domainOf = (email) => (String(email || "").toLowerCase().split("@")[1] || "").trim();

if (fs.existsSync(path.join(KIT, ".env")) && typeof process.loadEnvFile === "function") process.loadEnvFile(path.join(KIT, ".env"));

/** ISO date-time -> local "YYYY-MM-DDTHH:MM:SS±HH:MM" in the CRM's time zone. */
export function localIso(iso, tz = TZ) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23", timeZoneName: "longOffset" }).formatToParts(d).map((x) => [x.type, x.value]));
  const off = String(p.timeZoneName || "GMT").replace("GMT", "") || "+00:00";
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}${off}`;
}

export function loadBase() {
  return {
    schema: rj(path.join(KIT, "agent", "field_schema.json")),
    team: rj(path.join(KIT, "data", "team.json")),
    clients: rj(path.join(KIT, "data", "clients.json")),
    opportunities: rj(path.join(KIT, "data", "opportunities.json")),
  };
}

// ------------------------------------------------------------------ matching (code, no LLM)
/**
 * Meeting -> client -> opportunity. Client: the domain of the external attendees' e-mails, else the client
 * name in the title. Opportunity: the client's only open opportunity. Anything else is Unmatched, and the
 * seller links it by hand (the choice is logged).
 */
export function matchMeeting({ title, attendees, clients, opportunities, schema }) {
  const external = [...new Set(attendees.map((a) => domainOf(a.email)).filter((d) => d && d !== schema.seller_domain))];
  const byDomain = clients.filter((c) => external.includes(c.domain));
  let client = null; let reason = null;
  if (byDomain.length === 1) { client = byDomain[0]; reason = `attendee e-mail domain ${client.domain}`; }
  else if (!byDomain.length) {
    const t = norm(title);
    const byTitle = clients.filter((c) => t.includes(norm(c.name)));
    if (byTitle.length === 1) { client = byTitle[0]; reason = "client name in the meeting title"; }
  }
  if (!client) {
    return { client_id: null, linked_opportunity_id: null,
      reason: byDomain.length > 1 ? "attendees from more than one client" : "no client found for the attendees or the title" };
  }
  const open = opportunities.filter((o) => o.client_id === client.client_id && !isClosed(schema, (o.fields.stage || {}).value));
  if (open.length === 1) return { client_id: client.client_id, linked_opportunity_id: open[0].opportunity_id, reason };
  return { client_id: client.client_id, linked_opportunity_id: null,
    reason: open.length ? `${open.length} open opportunities for ${client.name}: pick one` : `no open opportunity for ${client.name}` };
}

// ------------------------------------------------------------------ normalisation
/**
 * One Granola note -> { meeting, transcript }. Speakers: the note owner's microphone is the seller from the
 * roster; other voices keep the name Granola resolved, with their company from the attendee e-mail; voices
 * without a name become "Customer (unattributed)". Consecutive blocks of the same speaker, less than 3 s
 * apart, become one line. Granola's own AI summary travels with the meeting for the seller to read, but it
 * is never evidence: the agent only cites the transcript.
 */
export function normalizeNote(note, { meetingId, team, clients, opportunities, schema, now = Date.now() }) {
  const owner = team.find((u) => eq(u.email, note.owner && note.owner.email)) || null;
  const attendees = (note.attendees || []).map((a) => ({ name: a.name || null, email: String(a.email || "").toLowerCase() }));
  const orgOf = (email) => {
    const dom = domainOf(email);
    if (!dom) return null;
    if (dom === schema.seller_domain) return "Orbita";
    const c = clients.find((x) => x.domain === dom);
    return c ? c.name : null;
  };
  const label = (sp = {}) => {
    if (sp.source === "microphone" || sp.attribution === "me") return owner ? `${owner.name} (Orbita)` : `${(note.owner && note.owner.name) || "Note owner"} (note owner)`;
    if (sp.name) {
      const u = team.find((x) => eq(x.name, sp.name));
      if (u) return `${u.name} (Orbita)`;
      const a = attendees.find((x) => eq(x.name, sp.name));
      const org = a ? orgOf(a.email) : null;
      return org ? `${sp.name} (${org})` : sp.name;
    }
    return sp.diarization_label ? `${sp.diarization_label} (unattributed)` : "Customer (unattributed)";
  };

  const items = (Array.isArray(note.transcript) ? note.transcript : [])
    .filter((t) => t && String(t.text || "").trim() && !Number.isNaN(Date.parse(t.start_time)))
    .sort((a, b) => Date.parse(a.start_time) - Date.parse(b.start_time));
  const t0 = items.length ? Date.parse(items[0].start_time) : null;
  const merged = [];
  for (const it of items) {
    const who = label(it.speaker);
    const st = Date.parse(it.start_time);
    const en = Number.isNaN(Date.parse(it.end_time)) ? st : Date.parse(it.end_time);
    const last = merged[merged.length - 1];
    if (last && last.who === who && st - last.end <= 3000) { last.text += " " + String(it.text).trim(); last.end = Math.max(last.end, en); }
    else merged.push({ who, start: st, end: en, text: String(it.text).trim().replace(/\s+/g, " ") });
  }
  const transcript = merged.map((l) => `[${secToTs((l.start - t0) / 1000)}] ${l.who}: ${l.text}`).join("\n");

  const ev = note.calendar_event || null;
  const startIso = (ev && ev.scheduled_start_time) || note.created_at;
  const scheduled = ev && ev.scheduled_start_time && ev.scheduled_end_time
    ? Math.round((Date.parse(ev.scheduled_end_time) - Date.parse(ev.scheduled_start_time)) / 60000) : null;
  const recorded = merged.length ? Math.max(1, Math.round((merged[merged.length - 1].end - t0) / 60000)) : 0;
  let status = "complete";
  if (!merged.length) status = note.transcript == null && now - Date.parse(note.updated_at || note.created_at) < 30 * 60000 ? "pending" : "missing";
  const participants = attendees.map((a) => {
    const u = team.find((x) => eq(x.email, a.email));
    if (u) return `${u.name} (Orbita)`;
    const org = orgOf(a.email);
    const nm = a.name || a.email;
    return org ? `${nm} (${org})` : nm;
  });
  const title = note.title || (ev && ev.event_title) || "(untitled meeting)";
  const match = matchMeeting({ title, attendees, clients, opportunities, schema });
  const meeting = {
    meeting_id: meetingId,
    source: { system: "granola", note_id: note.id, web_url: note.web_url || null,
      folder: (note.folder_membership || []).map((f) => f.name).filter(Boolean).join(", ") || null },
    title,
    start: localIso(startIso),
    scheduled_minutes: scheduled,
    recorded_minutes: recorded,
    organiser_id: owner ? owner.user_id : null,
    owner_email: note.owner ? note.owner.email : null,
    participants,
    client_id: match.client_id,
    linked_opportunity_id: match.linked_opportunity_id,
    match_reason: match.reason,
    transcript_status: status,
    ends_mid_sentence: endsMidSentence(transcriptLines(transcript)),
    granola_summary: note.summary_text || null,
    transcript_file: null,
  };
  return { meeting, transcript };
}

// ------------------------------------------------------------------ fixtures
/** Synthetic notes in the exact API shape -> data/meetings.json + transcripts/<meeting>.txt. */
export function syncFixtures({ write = true } = {}) {
  const base = loadBase();
  const files = fs.existsSync(FIXTURES) ? fs.readdirSync(FIXTURES).filter((f) => /^MTG-[\w-]+\.json$/.test(f)).sort() : [];
  const meetings = [];
  for (const f of files) {
    const meetingId = f.replace(/\.json$/, "");
    const { meeting, transcript } = normalizeNote(rj(path.join(FIXTURES, f)), { meetingId, ...base });
    meeting.transcript_file = transcript ? `transcripts/${meetingId}.txt` : null;
    if (write && transcript) fs.writeFileSync(path.join(KIT, meeting.transcript_file), transcript + "\n");
    meetings.push(meeting);
  }
  if (write) {
    fs.mkdirSync(path.join(KIT, "transcripts"), { recursive: true });
    fs.writeFileSync(path.join(KIT, "data", "meetings.json"), JSON.stringify(meetings, null, 2) + "\n");
  }
  return meetings;
}

// ------------------------------------------------------------------ live (public API)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let lastCall = 0;
async function call(url, key, fetchImpl, tries = 4) {
  for (let i = 0; i < tries; i++) {
    const wait = lastCall + 220 - Date.now(); // <= 5 requests per second
    if (wait > 0) await sleep(wait);
    lastCall = Date.now();
    const res = await fetchImpl(url, { headers: { Authorization: `Bearer ${key}`, Accept: "application/json" } });
    if (res.status === 429) { await sleep((Number(res.headers.get("retry-after")) || 2 ** i) * 1000); continue; }
    if (res.status === 413) return { tooLarge: true };
    if (!res.ok) throw Object.assign(new Error(`Granola API ${res.status}: ${(await res.text()).slice(0, 300)}`), { status: res.status });
    return { body: await res.json() };
  }
  throw new Error("Granola API: still rate-limited after retries");
}

async function fullTranscript(noteId, key, fetchImpl) {
  const items = [];
  let cursor = null;
  do {
    const r = await call(`${API}/notes/${noteId}/transcript${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`, key, fetchImpl);
    const b = r.body || {};
    items.push(...(b.transcript || b.items || b.data || []));
    cursor = b.hasMore ? b.cursor : null;
  } while (cursor);
  return items;
}

const readIndex = (cacheDir = CACHE) => (fs.existsSync(path.join(cacheDir, "index.json")) ? rj(path.join(cacheDir, "index.json")) : { last_sync: null, next_seq: 3001, notes: {} });

/** The notes of ONE folder, new or updated since the last sync -> .granola-cache/meetings.json + transcripts/. */
export async function syncLive({ key = process.env.GRANOLA_API_KEY, folder = process.env.GRANOLA_FOLDER, fetchImpl = fetch, cacheDir = CACHE } = {}) {
  if (!key) throw Object.assign(new Error("GRANOLA_API_KEY is not set (create it in the Granola desktop app: Settings > Connectors > API keys)."), { status: 409 });
  if (!/^fol_[a-zA-Z0-9]{14}$/i.test(String(folder || ""))) {
    throw Object.assign(new Error("GRANOLA_FOLDER must be the id of the Granola folder to sync (fol_…). Put one meeting in that folder and run: node agent/granola.mjs folder-of <note link>."), { status: 409 });
  }
  const base = loadBase();
  const idx = readIndex(cacheDir);
  fs.mkdirSync(path.join(cacheDir, "transcripts"), { recursive: true });
  const startedAt = new Date().toISOString();
  const since = idx.last_sync || new Date(Date.now() - 30 * 86400000).toISOString();
  const summaries = [];
  let cursor = null;
  do {
    const q = new URLSearchParams({ folder_id: folder, updated_after: since, page_size: "30" });
    if (cursor) q.set("cursor", cursor);
    const { body } = await call(`${API}/notes?${q}`, key, fetchImpl);
    summaries.push(...(body.notes || []));
    cursor = body.hasMore ? body.cursor : null;
  } while (cursor);
  const meetings = fs.existsSync(path.join(cacheDir, "meetings.json")) ? rj(path.join(cacheDir, "meetings.json")) : [];
  const added = []; const updated = [];
  for (const s of summaries) {
    if (s.deleted_at) continue;
    const known = idx.notes[s.id];
    if (known && known.updated_at === s.updated_at) continue;
    let r = await call(`${API}/notes/${s.id}?include=transcript`, key, fetchImpl);
    let note = r.body;
    if (r.tooLarge) { note = (await call(`${API}/notes/${s.id}`, key, fetchImpl)).body; note.transcript = await fullTranscript(s.id, key, fetchImpl); }
    const meetingId = known ? known.meeting_id : `MTG-${idx.next_seq++}`;
    const { meeting, transcript } = normalizeNote(note, { meetingId, ...base });
    meeting.transcript_file = transcript ? path.relative(KIT, path.join(cacheDir, "transcripts", `${meetingId}.txt`)).replace(/\\/g, "/") : null;
    if (transcript) fs.writeFileSync(path.join(KIT, meeting.transcript_file), transcript + "\n");
    meeting.synced_at = startedAt;
    const at = meetings.findIndex((m) => m.meeting_id === meetingId);
    if (at >= 0) meetings[at] = meeting; else meetings.push(meeting);
    idx.notes[s.id] = { meeting_id: meetingId, updated_at: s.updated_at };
    (known ? updated : added).push(meetingId);
  }
  idx.last_sync = startedAt;
  fs.writeFileSync(path.join(cacheDir, "meetings.json"), JSON.stringify(meetings, null, 2) + "\n");
  fs.writeFileSync(path.join(cacheDir, "index.json"), JSON.stringify(idx, null, 2) + "\n");
  return { mode: "live", folder, added, updated, total: meetings.length, last_sync: startedAt };
}

export function status({ live = false } = {}) {
  const idx = readIndex();
  return live
    ? { mode: "live", key: !!process.env.GRANOLA_API_KEY, folder: process.env.GRANOLA_FOLDER || null, last_sync: idx.last_sync, notes: Object.keys(idx.notes).length }
    : { mode: "fixtures", key: false, folder: "CRM sync (fixtures)", last_sync: null, notes: fs.existsSync(FIXTURES) ? fs.readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).length : 0 };
}

async function folderOf(ref, key = process.env.GRANOLA_API_KEY) {
  const id = (String(ref).match(/not_[a-zA-Z0-9]{14}/) || [])[0];
  if (!id) throw new Error("Pass a note id (not_…) or a Granola note link that contains it.");
  if (!key) throw new Error("GRANOLA_API_KEY is not set.");
  const { body } = await call(`${API}/notes/${id}`, key, fetch);
  return (body.folder_membership || []).map((f) => ({ id: f.id, name: f.name }));
}

// ------------------------------------------------------------------ CLI
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [cmd, ...rest] = process.argv.slice(2);
  const live = rest.includes("--live");
  try {
    if (cmd === "sync" && !live) {
      const ms = syncFixtures();
      for (const m of ms) console.log(`${m.meeting_id}  ${m.linked_opportunity_id || "unmatched".padEnd(8)}  ${String(m.recorded_minutes).padStart(3)}/${m.scheduled_minutes} min  ${m.transcript_status}${m.ends_mid_sentence ? " (ends mid-sentence)" : ""}  ${m.title}`);
      console.log(`${ms.length} meetings from fixtures -> data/meetings.json`);
    } else if (cmd === "sync") {
      console.log(JSON.stringify(await syncLive(), null, 2));
    } else if (cmd === "status") {
      console.log(JSON.stringify(status({ live }), null, 2));
    } else if (cmd === "folder-of") {
      console.log(JSON.stringify(await folderOf(rest[0]), null, 2));
    } else {
      console.log("Usage: node agent/granola.mjs sync [--live] | status [--live] | folder-of <note>");
      process.exitCode = 1;
    }
  } catch (e) {
    console.error(e.message);
    process.exitCode = 1;
  }
}
