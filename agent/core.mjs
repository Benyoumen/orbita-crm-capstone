// Orbita CRM agent: the pure core (no file system, no network, no Node APIs).
//
// One copy of the rules, three hosts: agent/pipeline.mjs (CLI and eval), mockups/server.mjs
// (live mode) and the generated mockup page, which embeds this file verbatim. Every host runs
// the same parser, the same matching, the same pre-checks, the same validator and the same write.
//
//   parseConversation     any transcript or chat export (kit, WebVTT, SRT, Otter, WhatsApp, plain) -> lines
//   labelSpeakers         seller side from the roster, customer side from the client, generic voices unattributed
//   matchConversation     the conversation -> the right opportunity (or a new one), with the reasons
//   prepareRun            deterministic pre-checks: opportunity match, seller access, transcript completeness
//   buildUserMessage      the per-run part of the prompt (conversation, client, opportunity, roster, numbered lines)
//   renderFieldDictionary the field dictionary of the prompt, generated from agent/field_schema.json
//   buildOutputSchema     the JSON schema the model must return (structured outputs)
//   validateOutput        guardrails applied in code to the model's sparse answer
//   applyApprovedFields   the only write path: after the seller's decisions, or a field's "Always allow"
//
// Every CRM value is a string or null. agent/field_schema.json says how each string is checked.

export const ACTIONABLE = ["proposed", "contradictory"];
export const AGENT_STATUSES = ["proposed", "no_evidence", "contradictory"];

// USD per million tokens (Claude API list prices, Oct 2026): input, output, cache read, cache write (5-minute TTL)
export const PRICES = {
  "claude-sonnet-5-5": { input: 2, output: 10, cache_read: 0.2, cache_write: 2.5 },
  "claude-haiku-5-5": { input: 0.1, output: 0.5, cache_read: 0.01, cache_write: 0.125 },
  "claude-opus-5-5": { input: 4, output: 20, cache_read: 0.2, cache_write: 5 },
};

export function costOf(usage, model) {
  const p = PRICES[model];
  if (!usage || !p) return null;
  const usd = ((usage.input_tokens || 0) * p.input + (usage.output_tokens || 0) * p.output
    + (usage.cache_read_input_tokens || 0) * p.cache_read + (usage.cache_creation_input_tokens || 0) * p.cache_write) / 1e6;
  return Math.round(usd * 1e6) / 1e6;
}

// ------------------------------------------------------------------ schema helpers
export function fieldDef(schema, key) { return schema.fields.find((d) => d.key === key) || null; }
export function fieldKeys(schema) { return schema.fields.map((d) => d.key); }
export function fieldOf(rec, key) {
  const f = rec && rec.fields ? rec.fields[key] : null;
  return f ? { value: f.value ?? null, approved: !!f.approved, written_by: f.written_by ?? null, written_at: f.written_at ?? null }
    : { value: null, approved: false, written_by: null, written_at: null };
}
export function currentOf(def, opp, client) { return fieldOf(def.record === "client" ? client : opp, def.key); }
export const isClosed = (schema, stage) => schema.closed_stages.includes(stage);

/** MEDDPICC coverage of one opportunity: which of the eight elements hold a value, and the gaps by leverage. */
export function meddpiccOf(schema, opp) {
  const items = schema.fields.filter((d) => d.meddpicc).map((d) => {
    const f = fieldOf(opp, d.key);
    return { key: d.key, letter: d.meddpicc, label: d.label, known: f.value != null && f.value !== "", value: f.value, approved: f.approved, ask: d.ask, priority: d.priority };
  });
  return { items, known: items.filter((i) => i.known).length, total: items.length, gaps: items.filter((i) => !i.known).sort((a, b) => a.priority - b.priority) };
}

// ------------------------------------------------------------------ permissions ("Always allow" / "Needs approval" / "Never")
export function defaultPermissions(schema) {
  return { fields: Object.fromEntries(schema.fields.map((d) => [d.key, d.permission || "ask"])),
    create_opportunity: (schema.permissions && schema.permissions.create_opportunity) || "ask" };
}
export function permissionOf(schema, permissions, key) {
  const p = permissions && permissions.fields ? permissions.fields[key] : null;
  return p || (fieldDef(schema, key) || {}).permission || "ask";
}
/** Fields the platform may write without asking: proposed (never contradictory) and set to "Always allow". */
export function autoFields(output, schema, permissions) {
  return (output.fields || []).filter((f) => f.status === "proposed" && permissionOf(schema, permissions, f.field) === "auto").map((f) => f.field);
}

// ------------------------------------------------------------------ text helpers
export const norm = (s) => String(s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/[‘’`]/g, "'").replace(/[“”]/g, '"').replace(/[–—]/g, "-").replace(/\s+/g, " ").trim();
const words = (s) => String(s || "").trim().split(/\s+/).filter(Boolean).length;
const cleanQuote = (q) => String(q ?? "").trim().replace(/^["'“”‘’]+|["'“”‘’]+$/g, "").trim();
const escapeRe = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
export const groupsOk = (text, groups) => (groups || []).every((g) => g.some((k) => norm(text).includes(norm(k))));

// ------------------------------------------------------------------ transcript lines (the normalised text every host stores)
// "[hh:mm:ss] Speaker: text" for meetings, "[YYYY-MM-DD hh:mm] Speaker: text" for chats.
const LINE_RE = /^\[(\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] ([^:\n]+?): (.*)$/;
export const tsToSec = (t) => { const [h, m, s] = String(t).split(":").map(Number); return h * 3600 + m * 60 + s; };
export const secToTs = (sec) => {
  const s = Math.max(0, Math.round(sec));
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60].map((n) => String(n).padStart(2, "0")).join(":");
};

/** Normalised lines, numbered from 1 (the L-number the agent cites). */
export function transcriptLines(text) {
  const out = [];
  for (const raw of String(text || "").split(/\r?\n/)) {
    const m = raw.match(LINE_RE);
    if (m) out.push({ n: out.length + 1, timestamp: m[1], speaker: m[2].trim(), text: m[3].trim(), norm: norm(m[3]) });
  }
  return out;
}
export const lineTag = (n) => "L" + String(n).padStart(3, "0");
const untimed = (lines) => lines.length > 0 && lines.every((l) => l.timestamp === "00:00:00");
export function numberedTranscript(lines) {
  const bare = untimed(lines);
  return lines.map((l) => `${lineTag(l.n)} ${bare ? "" : `[${l.timestamp}] `}${l.speaker}: ${l.text}`).join("\n");
}
/** A long last line without a closing mark. Short closings ("Thanks", "Talk soon") and emoji are normal endings. */
export function endsMidSentence(lines) {
  const last = lines[lines.length - 1];
  if (!last) return false;
  const t = last.text.trim();
  if (/[.!?…"')\]]$/.test(t) || words(t) <= 4 || /\p{Extended_Pictographic}$/u.test(t)) return false;
  return true;
}
/** Recorded share of the scheduled slot. ratio null when there is no booked length or no usable timestamp. */
export function coverageOf(meeting, lines) {
  const sched = Number(meeting.scheduled_minutes) || null;
  let rec = meeting.recorded_minutes != null ? Number(meeting.recorded_minutes) : null;
  const timed = lines.filter((l) => /^\d{2}:\d{2}:\d{2}$/.test(l.timestamp));
  if (rec == null && timed.length && !untimed(lines)) rec = tsToSec(timed[timed.length - 1].timestamp) / 60;
  if (!sched || rec == null) return { recorded: rec, scheduled: sched, ratio: null };
  return { recorded: rec, scheduled: sched, ratio: rec / sched };
}
/** A short, stable key of the spoken text (format and speaker labels ignored): FNV-1a over the normalised lines. */
export function conversationKey(lines) {
  let h = 0x811c9dc5;
  const s = lines.map((l) => norm(l.text)).join("\n");
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return h.toString(16).padStart(8, "0");
}

// ------------------------------------------------------------------ any conversation -> lines
const pad2 = (n) => String(n).padStart(2, "0");
const clockToSec = (t) => { const p = String(t).split(":").map(Number); return p.length === 3 ? p[0] * 3600 + p[1] * 60 + p[2] : p[0] * 60 + p[1]; };
const NAME_RE = /^[\p{L}][\p{L}\p{N} .'’()&-]{0,58}$/u;
const looksLikeName = (s) => { const t = String(s || "").trim(); return NAME_RE.test(t) && words(t) <= 6 && !/[.!?;,]$/.test(t); };
const GENERIC_SPEAKER = /^(speaker|participant|guest|unknown( speaker)?|unidentified( speaker)?|attendee|caller|user)\s*#?\s*\d*$|^\d+$/i;
const KIT_RE = /^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:\n]{1,60}?):\s+(.*)$/;
const CHAT_KIT_RE = /^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*([^:\n]{1,60}?):\s+(.*)$/;
const WA_HEAD = String.raw`^\[?(\d{1,2})[./-](\d{1,2})[./-](\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*([AaPp])\.?\s?[Mm]\.?)?\]?`;
const WA_RE = new RegExp(WA_HEAD + String.raw`\s*(?:[-–]\s+)?([^:]{1,60}?):\s+(.*)$`);
const WA_SYS_RE = new RegExp(WA_HEAD);
const WA_SKIP = /^(<media omitted>|(image|video|audio|sticker|gif|document|contact card) omitted|this message was deleted|you deleted this message|null|<this message was edited>)$/i;
const CUE_RE = /^((?:\d{1,2}:)?\d{2}:\d{2})[.,]\d{3}\s+-->\s+/;
const OTTER_RE = /^(.{2,60}?)(?:\s{2,}|\t)(\d{1,2}:\d{2}(?::\d{2})?)\s*$/;
const PLAIN_RE = /^\**\s*([\p{L}][^:\n]{0,58}?)\s*\**\s*:\s+(.+)$/u;
const SENTENCE_END = /[.!?…]["')\]]?$/;

const clean = (s) => String(s).replace(/[‎‏‪-‮﻿]/g, "").replace(/[  ]/g, " ");
const countRe = (rows, re) => rows.reduce((n, r) => n + (re.test(r.trim()) ? 1 : 0), 0);

function parseKit(rows, re, chat) {
  const lines = [];
  for (const r of rows) {
    const t = r.trim();
    const m = t.match(re);
    if (m) {
      lines.push(chat ? { timestamp: m[1], sec: null, speaker: m[2].trim(), text: m[3].trim() }
        : { timestamp: secToTs(clockToSec(m[1])), sec: clockToSec(m[1]), speaker: m[2].trim(), text: m[3].trim() });
    } else if (lines.length && t && !/^[#[]/.test(t)) lines[lines.length - 1].text += " " + t;
  }
  return lines;
}

function parseCues(raw) {
  const lines = [];
  for (const block of raw.split(/\n\s*\n/)) {
    const ls = block.split("\n").map((s) => s.trim()).filter(Boolean);
    const ci = ls.findIndex((l) => CUE_RE.test(l));
    if (ci < 0) continue;
    const start = clockToSec(ls[ci].match(CUE_RE)[1]);
    let text = ls.slice(ci + 1).join(" ");
    let speaker = null;
    const v = text.match(/<v(?:\.[^\s>]+)?\s+([^>]+)>/);
    if (v) speaker = v[1].trim();
    text = text.replace(/<[^>]+>/g, "").trim();
    if (!speaker) {
      const m = text.match(/^([^:]{1,60}?):\s+(.*)$/);
      if (m && looksLikeName(m[1])) { speaker = m[1].trim(); text = m[2].trim(); }
    }
    if (!text) continue;
    const prev = lines[lines.length - 1];
    // Teams and Zoom split long turns into several cues: glue a cue to the previous one of the same voice
    // when the previous text stops mid-sentence
    if (prev && (speaker == null || speaker === prev.speaker) && !SENTENCE_END.test(prev.text)) { prev.text += " " + text; continue; }
    lines.push({ timestamp: secToTs(start), sec: start, speaker: speaker || (prev ? prev.speaker : "Unknown speaker"), text });
  }
  return lines;
}

function parseWhatsApp(rows, now) {
  const raw = [];
  for (const r of rows) {
    const m = r.match(WA_RE);
    if (m) { raw.push({ a: +m[1], b: +m[2], y: +m[3], h: +m[4], mi: +m[5], ap: m[7] || "", name: m[8].trim(), text: m[9].trim() }); continue; }
    if (WA_SYS_RE.test(r)) continue; // a system line ("Messages and calls are end-to-end encrypted...")
    if (raw.length && r.trim()) raw[raw.length - 1].text += " " + r.trim();
  }
  // day/month order: any part above 12 settles it; otherwise the reading closest to today wins
  let dmy = raw.some((x) => x.a > 12) ? true : raw.some((x) => x.b > 12) ? false : null;
  const year = (y) => (y < 100 ? 2000 + y : y);
  const iso = (x, d) => `${year(x.y)}-${pad2(d ? x.b : x.a)}-${pad2(d ? x.a : x.b)}`;
  if (dmy == null) {
    const last = raw[raw.length - 1];
    const ref = now ? Date.parse(String(now).slice(0, 10)) : null;
    dmy = !last || ref == null ? true : Math.abs(Date.parse(iso(last, true)) - ref) <= Math.abs(Date.parse(iso(last, false)) - ref);
  }
  const lines = [];
  for (const x of raw) {
    if (WA_SKIP.test(x.text)) continue;
    let h = x.h;
    if (/p/i.test(x.ap) && h < 12) h += 12;
    if (/a/i.test(x.ap) && h === 12) h = 0;
    lines.push({ timestamp: `${iso(x, dmy)} ${pad2(h)}:${pad2(x.mi)}`, sec: null, speaker: x.name, text: x.text });
  }
  return lines;
}

function parseOtter(rows) {
  const lines = []; let cur = null;
  for (const r of rows) {
    const m = r.match(OTTER_RE);
    if (m && looksLikeName(m[1])) { cur = { timestamp: secToTs(clockToSec(m[2])), sec: clockToSec(m[2]), speaker: m[1].trim(), text: "" }; lines.push(cur); continue; }
    if (cur && r.trim()) cur.text = (cur.text ? cur.text + " " : "") + r.trim();
  }
  return lines.filter((l) => l.text);
}

function parsePlain(rows) {
  const lines = []; let cur = null;
  for (const r of rows) {
    const t = r.trim();
    if (!t || /^\(?\d{1,2}:\d{2}(?::\d{2})?\)?$/.test(t)) continue; // blank, or a bare timestamp between paragraphs
    const m = t.match(PLAIN_RE);
    if (m && looksLikeName(m[1])) { cur = { timestamp: "00:00:00", sec: null, speaker: m[1].trim(), text: m[2].trim() }; lines.push(cur); continue; }
    if (cur) cur.text += " " + t;
  }
  return lines;
}

/**
 * Reads a meeting transcript or a chat export in any of the common shapes and returns the spoken lines.
 * kind: kit ("[hh:mm:ss] Name: text", Granola and this kit), vtt (Teams, Zoom, Google Meet), srt, otter
 * ("Name  0:14" then the text: Otter, Fathom), whatsapp (Android or iPhone export), chat (this kit's
 * normalised chats), plain ("Name: text" lines, pasted). now (ISO date) settles ambiguous chat dates.
 */
export function parseConversation(text, { now = null } = {}) {
  const raw = clean(String(text || "")).replace(/\r\n?/g, "\n");
  const rows = raw.split("\n");
  const filled = rows.filter((r) => r.trim());
  let kind, lines;
  if (/^\s*WEBVTT/.test(raw)) { kind = "vtt"; lines = parseCues(raw); }
  else if (/^\s*\d+\s*\n\s*(?:\d{1,2}:)?\d{2}:\d{2},\d{3}\s+-->/m.test(raw)) { kind = "srt"; lines = parseCues(raw); }
  else if (countRe(filled, WA_RE) >= 2 && countRe(filled, WA_SYS_RE) >= filled.length * 0.3) { kind = "whatsapp"; lines = parseWhatsApp(filled, now); }
  else if (countRe(filled, CHAT_KIT_RE) >= 2) { kind = "chat"; lines = parseKit(filled, CHAT_KIT_RE, true); }
  else if (countRe(filled, KIT_RE) >= 2) { kind = "kit"; lines = parseKit(filled, KIT_RE, false); }
  else if (countRe(rows, OTTER_RE) >= 2) { kind = "otter"; lines = parseOtter(rows); }
  else { kind = "plain"; lines = parsePlain(rows); }
  lines = lines.filter((l) => l.text && l.speaker);
  const chat = kind === "whatsapp" || kind === "chat";
  const timed = lines.filter((l) => l.sec != null);
  return {
    kind, chat, lines,
    speakers: [...new Set(lines.map((l) => l.speaker))],
    start: chat && lines.length ? lines[0].timestamp.replace(" ", "T") : null,
    date: chat && lines.length ? lines[lines.length - 1].timestamp.slice(0, 10) : null,
    minutes: !chat && timed.length ? Math.max(1, Math.round(timed[timed.length - 1].sec / 60)) : null,
    ends_mid_sentence: chat ? false : endsMidSentence(lines),
  };
}

/** The normalised text that every host stores and the agent reads (see transcriptLines). */
export function conversationText(lines) {
  return lines.map((l) => `[${/^\d{4}-/.test(l.timestamp) ? l.timestamp : secToTs(l.sec ?? (l.timestamp ? tsToSec(l.timestamp) : 0))}] ${l.speaker}: ${l.text}`).join("\n");
}

/**
 * Names each voice the way the agent needs it: roster people as "Name (Orbita)", generic voices
 * ("Speaker 2") as unattributed, everyone else on the customer side "Name (Client)". Labels that
 * already carry a company are kept.
 */
export function labelSpeakers(lines, { team, client = null, clientName = "" }) {
  const map = {};
  for (const s of new Set(lines.map((l) => l.speaker))) {
    const t = String(s).trim();
    if (/\([^)]*\)\s*$/.test(t)) { map[s] = t; continue; }
    const u = team.find((x) => norm(x.name) === norm(t));
    if (u) map[s] = `${u.name} (Orbita)`;
    else if (GENERIC_SPEAKER.test(t)) map[s] = `${t} (unattributed)`;
    else map[s] = `${t} (${(client && client.name) || clientName || "Customer"})`;
  }
  return lines.map((l) => ({ ...l, speaker: map[l.speaker] }));
}

// ------------------------------------------------------------------ which opportunity is this conversation about
const STOP_WORDS = new Set(["the", "group", "grupo", "company", "global", "brasil", "brazil", "sales", "first", "general", "national", "international", "green", "blue", "north", "south"]);
export const clientKeyWord = (name) => { const w = norm(name).split(/\s+/)[0]; return w && w.length >= 4 && !STOP_WORDS.has(w) ? w : null; };
const wordRe = (w) => new RegExp(`(^|[^a-z0-9])${escapeRe(w)}(?=[^a-z0-9]|$)`, "g");
const MEETING_WORDS = /\b(intro(duction)?|discovery|demo|planning|call|meeting|transcript|notes?|chat|kick ?off|check ?in|follow ?up|session|scope|review|sync|weekly|catch ?up|whatsapp|with|walkthrough|solution|proposal|questions|data|pos|vtt|srt|txt|pasted|text|conversation)\b/gi;

/** A client name read from a title or a file name ("delta-pharma_intro-call.vtt" -> "Delta Pharma"). */
export function guessClientName(title, filename, speakers = []) {
  const people = new Set(speakers.map((s) => norm(String(s).replace(/\s*\([^)]*\)\s*$/, ""))));
  for (const src of [title, String(filename || "").replace(/\.[a-z0-9]{2,4}$/i, "")]) {
    for (const part of String(src || "").split(/\s+[-–|·]\s+|_/)) {
      const rest = part.replace(/-/g, " ").replace(MEETING_WORDS, " ").replace(/\s+/g, " ").trim();
      if (!rest || words(rest) > 4 || !/\p{L}/u.test(rest) || people.has(norm(rest))) continue;
      return rest.split(" ").map((w) => (w === w.toLowerCase() ? w.charAt(0).toUpperCase() + w.slice(1) : w)).join(" ");
    }
  }
  return "";
}

/**
 * Attributes a conversation to the CRM. Signals per client: a speaker who is a contact (+3), a speaker
 * labelled with the client (+3), the client named in the title or file name (+4), the client's web
 * domain in the text (+4), mentions of the client in the text (+1 each, at most +2). One client must
 * lead clearly; then exactly one open opportunity the user can read is linked.
 * kind: opportunity | choose (the seller picks) | new_opportunity (known client, no open opportunity)
 *       | new_client | denied (the opportunity belongs to someone else; nothing about it is returned)
 */
export function matchConversation({ lines, title = "", filename = "", clients, opportunities, team, user, schema }) {
  const text = norm(lines.map((l) => l.text).join(" "));
  const head = norm(`${title} ${String(filename || "").replace(/\.[a-z0-9]{2,4}$/i, "")}`.replace(/[_.-]+/g, " "));
  const voices = [...new Set(lines.map((l) => l.speaker))].map((s) => ({
    name: norm(String(s).replace(/\s*\([^)]*\)\s*$/, "")), company: norm((String(s).match(/\(([^)]*)\)\s*$/) || [])[1] || "") }));
  const scored = clients.map((c) => {
    let score = 0; const reasons = [];
    const cn = norm(c.name), kw = clientKeyWord(c.name);
    for (const p of c.contacts || []) if (voices.some((v) => v.name === norm(p.name))) { score += 3; reasons.push(`${p.name} is a contact at ${c.name}`); }
    if (voices.some((v) => v.company === cn)) { score += 3; reasons.push(`a speaker is from ${c.name}`); }
    if (head && (head.includes(cn) || (kw && wordRe(kw).test(head)))) { score += 4; reasons.push(`the title names ${c.name}`); }
    if (c.domain && text.includes(norm(c.domain))) { score += 4; reasons.push(`the conversation mentions ${c.domain}`); }
    const hits = (text.match(wordRe(kw || cn)) || []).length;
    if (hits) { score += Math.min(2, hits); reasons.push(`the conversation mentions ${c.name}`); }
    return { c, score, reasons };
  }).filter((x) => x.score > 0).sort((a, b) => b.score - a.score);
  const openOf = (c) => opportunities.filter((o) => o.client_id === c.client_id && !isClosed(schema, fieldOf(o, "stage").value));
  const cand = (o) => ({ opportunity_id: o.opportunity_id, client_id: o.client_id, name: o.name });
  if (!scored.length) {
    return { kind: "new_client", client_id: null, opportunity_id: null, candidates: [], reasons: ["no client in the CRM matches the speakers, the title or the conversation"],
      client_name_guess: guessClientName(title, filename, lines.map((l) => l.speaker)) };
  }
  const [best, second] = scored;
  if (best.score < 3 || (second && second.score * 2 > best.score)) {
    const close = scored.filter((x) => x.score * 2 >= best.score);
    return { kind: "choose", client_id: null, opportunity_id: null, reasons: close.flatMap((x) => x.reasons).slice(0, 4),
      candidates: close.flatMap((x) => openOf(x.c).filter((o) => canRead(user, o))).map(cand), client_name_guess: guessClientName(title, filename, lines.map((l) => l.speaker)) };
  }
  const open = openOf(best.c);
  const mine = open.filter((o) => canRead(user, o));
  if (!open.length) return { kind: "new_opportunity", client_id: best.c.client_id, opportunity_id: null, candidates: [], reasons: [...best.reasons, `${best.c.name} has no open opportunity`] };
  // denied: the ids stay with the platform (so the run is logged and blocked as AccessDenied); the screen shows only the reason
  if (!mine.length) return { kind: "denied", client_id: best.c.client_id, opportunity_id: open[0].opportunity_id, candidates: [], reasons: ["this conversation belongs to an opportunity you do not have access to"] };
  if (mine.length === 1) return { kind: "opportunity", client_id: best.c.client_id, opportunity_id: mine[0].opportunity_id, candidates: [cand(mine[0])], reasons: best.reasons };
  return { kind: "choose", client_id: best.c.client_id, opportunity_id: null, candidates: mine.map(cand), reasons: [...best.reasons, `${best.c.name} has ${mine.length} open opportunities`] };
}

/** The new-opportunity request a match turns into (contacts: the identified customer-side voices). */
export function targetFromMatch(m, { lines, clients }) {
  if (m.kind === "new_opportunity") {
    const c = clients.find((x) => x.client_id === m.client_id);
    return { kind: "new", client_id: c.client_id, client_name: c.name, opportunity_name: `${c.name} - CRM`, contacts: [] };
  }
  const people = [...new Set(lines.map((l) => l.speaker).filter((s) => !/\((Orbita|unattributed)\)\s*$/.test(s))
    .map((s) => s.replace(/\s*\([^)]*\)\s*$/, "").trim()).filter((s) => s && !GENERIC_SPEAKER.test(s)))];
  const name = m.client_name_guess || "";
  return { kind: "new", client_id: null, client_name: name, opportunity_name: name ? `${name} - CRM` : "", contacts: people };
}

/**
 * A conversation that arrived without a link gets one the way the platform would do it: linked when one
 * opportunity matches, a new-opportunity request when the company or the opportunity is new, the hidden
 * link of someone else's opportunity when access is denied (blocked later), and nothing when the seller must choose.
 */
export function attribute({ meeting, lines, data, user, schema }) {
  if (meeting.linked_opportunity_id || meeting.target) return meeting;
  const m = matchConversation({ lines, title: meeting.title, filename: (meeting.source || {}).file, clients: data.clients,
    opportunities: data.opportunities, team: data.team, user, schema });
  const why = m.reasons.join("; ");
  if (m.kind === "opportunity" || m.kind === "denied") return { ...meeting, linked_opportunity_id: m.opportunity_id, client_id: m.client_id, match_reason: why };
  if (m.kind === "new_client" || m.kind === "new_opportunity") return { ...meeting, target: targetFromMatch(m, { lines, clients: data.clients }), match_reason: why };
  return { ...meeting, match_reason: why };
}

// ------------------------------------------------------------------ log
export function newLog(runId, clock = () => new Date().toISOString()) {
  const events = [];
  return {
    events,
    add(actor, action, object_id, outcome, detail = "") {
      events.push({ run_id: runId, seq: events.length + 1, timestamp: clock(), actor, action, object_id, outcome, detail });
    },
  };
}

// ------------------------------------------------------------------ access
export function canRead(user, opp) {
  if (!user || !opp) return false;
  return user.access === "all_opportunities_read" || (user.access === "own_opportunities" && opp.owner_id === user.user_id);
}

export function blocked(meeting_id, opportunity_id, source_status, block_reason) {
  return { meeting_id, opportunity_id: source_status === "AccessDenied" ? null : opportunity_id ?? null, source_status,
    run_status: "Blocked", block_reason, warnings: [], fields: [], ignored_out_of_scope: [], validation_notes: [] };
}

// ------------------------------------------------------------------ 1. deterministic pre-checks (no LLM)
// Order: meeting exists -> opportunity (linked, or a new one) -> seller access -> transcript usable.
// data: { team, clients, opportunities, meetings }; transcript: the normalised text, already read by the host (or null).
// meeting.target = { kind: "new", client_id | null, client_name, opportunity_name, contacts } asks for a new opportunity.
export function prepareRun({ meetingId, opportunityId, userId, data, transcript, log, schema, permissions = null }) {
  const meeting = data.meetings.find((m) => m.meeting_id === meetingId);
  log.add("system", "run_created", meetingId, "ok", `user=${userId}`);
  if (!meeting) return { output: blocked(meetingId, opportunityId ?? null, "Missing", "Meeting not found.") };
  const user = data.team.find((u) => u.user_id === userId);
  const target = meeting.target && meeting.target.kind === "new" ? meeting.target : null;
  let opp, client;
  if (target) {
    const create = (permissions && permissions.create_opportunity) || (schema.permissions && schema.permissions.create_opportunity) || "ask";
    if (create === "off") {
      log.add("system", "run_blocked", meetingId, "blocked", "new opportunity needed; creating opportunities is off");
      return { output: blocked(meetingId, null, "Unmatched", "No opportunity in the CRM matches this conversation, and creating opportunities is turned off in Settings > Permissions.") };
    }
    client = target.client_id ? data.clients.find((c) => c.client_id === target.client_id) : null;
    if (target.client_id && !client) return { output: blocked(meetingId, null, "Missing", "Client not found.") };
    if (!client) client = { client_id: null, name: target.client_name || "New client", contacts: [], industry: null, fields: {} };
    opp = { opportunity_id: null, client_id: client.client_id, name: target.opportunity_name || `${client.name} - CRM`, owner_id: userId,
      fields: { stage: { value: schema.stages[0], approved: true } } };
    log.add("system", "opportunity_matched", meetingId, "ok", `new opportunity for ${client.client_id ? client.name : "new client " + client.name}`);
  } else {
    const oppId = opportunityId === undefined ? meeting.linked_opportunity_id : opportunityId;
    if (!meeting.linked_opportunity_id || !oppId || meeting.linked_opportunity_id !== oppId) {
      log.add("system", "run_blocked", meetingId, "blocked", "meeting not linked to exactly this opportunity");
      return { output: blocked(meetingId, oppId ?? null, "Unmatched",
        "This conversation is not linked to an opportunity in the CRM. Choose one in Meetings, or create a new one.") };
    }
    opp = data.opportunities.find((o) => o.opportunity_id === oppId);
    const hasAccess = canRead(user, opp);
    log.add("system", "access_checked", oppId, hasAccess ? "ok" : "blocked", `user=${userId}`);
    if (!hasAccess) return { output: blocked(meetingId, oppId, "AccessDenied", "You do not have access to this opportunity. No data has been shown.") };
    client = data.clients.find((c) => c.client_id === opp.client_id) || null;
    log.add("system", "opportunity_read", oppId, "ok", `stage=${fieldOf(opp, "stage").value}`);
  }

  const status = meeting.transcript_status || "complete";
  const ref = opp.opportunity_id;
  if (status === "pending") {
    log.add("system", "transcript_checked", meetingId, "blocked", "pending");
    return { output: blocked(meetingId, ref, "Missing", "The transcript is still being processed. It will be picked up on the next sync.") };
  }
  const lines = status === "missing" || transcript == null ? [] : transcriptLines(transcript);
  if (!lines.length) {
    log.add("system", "transcript_checked", meetingId, "blocked", "missing");
    return { output: blocked(meetingId, ref, "Missing", "No readable transcript is available for this conversation. Update the CRM manually.") };
  }
  const warnings = [];
  if (meeting.chat) {
    log.add("system", "transcript_checked", meetingId, "ok", `chat; ${lines.length} messages`);
  } else {
    const cov = coverageOf(meeting, lines);
    const mid = meeting.ends_mid_sentence ?? endsMidSentence(lines);
    const marker = /\[Transcript ended/i.test(transcript);
    const pct = cov.ratio == null ? "unknown" : `${Math.round(cov.ratio * 100)}%`;
    // with a booked length: under 60% of it and cut mid-sentence; without one, a mid-sentence ending alone
    const cut = cov.ratio != null ? cov.ratio < 0.6 && mid : mid;
    const incomplete = !meeting.seller_confirmed_complete && (status === "incomplete" || marker || cut);
    log.add("system", "transcript_checked", meetingId, incomplete ? "blocked" : "ok",
      `status=${status}; coverage=${pct} of ${cov.scheduled ?? "?"} min; ends_mid_sentence=${mid}`);
    if (incomplete) {
      const how = cov.ratio != null ? `the recording covers ${pct} of the scheduled ${cov.scheduled} min and stops mid-sentence` : "it stops mid-sentence";
      return { output: blocked(meetingId, ref, "Incomplete",
        `The transcript looks incomplete: ${how}. No update will be proposed. If the meeting really ended there, confirm it and prepare the update again.`) };
    }
    if (meeting.seller_confirmed_complete) warnings.push("You confirmed that the meeting ended there.");
    else if (cov.ratio != null && cov.ratio < 0.6) warnings.push(`Short recording: ${pct} of the scheduled ${cov.scheduled} min, with a normal ending.`);
  }
  return { meeting, opp, client, user, transcript, lines, warnings, target, permissions };
}

// ------------------------------------------------------------------ 2. prompt parts that depend on data
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
export function weekdayOf(isoDate) {
  const [y, m, d] = String(isoDate).slice(0, 10).split("-").map(Number);
  return WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
}

export function renderFieldDictionary(schema) {
  const perCall = schema.fields.filter((d) => d.kind === "per_call").map((d) => "`" + d.key + "`").join(", ");
  const out = [
    `# Field dictionary: the ${schema.fields.length} in-scope fields`,
    "",
    `**Per-conversation fields** describe this conversation only: ${perCall}. **State fields** describe the opportunity or the client now; only state fields can be \`contradictory\`.`,
    `**Seller-only, never proposed:** ${schema.seller_only_note}`,
    "Values are plain strings. Respect each format exactly: the platform rejects values that do not match it.",
  ];
  for (const g of schema.groups) {
    out.push("", `## ${g.label}`);
    for (const d of schema.fields.filter((f) => f.group === g.id)) {
      const where = d.record === "client" ? "client record" : "opportunity";
      const tag = d.meddpicc ? `, MEDDPICC ${d.meddpicc}` : "";
      out.push(`- \`${d.key}\` (${d.label}; ${d.kind === "per_call" ? "per-conversation" : "state"}, ${where}${tag}): ${d.definition} Evidence: ${d.evidence} Format: ${d.format} Good: "${d.good}". Bad: ${d.bad}.`);
    }
  }
  return out.join("\n");
}

export function buildOutputSchema(schema) {
  const strOrNull = { anyOf: [{ type: "string" }, { type: "null" }] };
  const cite = { type: "object", additionalProperties: false, required: ["line", "quote"],
    properties: { line: { type: "integer" }, quote: { type: "string" } } };
  return {
    type: "object", additionalProperties: false,
    required: ["run_status", "source_status", "block_reason", "fields", "ignored_out_of_scope"],
    properties: {
      run_status: { type: "string", enum: ["Awaiting review", "Blocked"] },
      source_status: { type: "string", enum: ["Ready", "Unmatched"] },
      block_reason: strOrNull,
      fields: { type: "array", items: { type: "object", additionalProperties: false,
        required: ["field", "status", "value", "evidence", "note"],
        properties: { field: { type: "string", enum: fieldKeys(schema) }, status: { type: "string", enum: AGENT_STATUSES },
          value: strOrNull, evidence: { type: "array", items: cite }, note: strOrNull } } },
      ignored_out_of_scope: { type: "array", items: { type: "object", additionalProperties: false, required: ["line", "quote", "reason"],
        properties: { line: { type: "integer" }, quote: { type: "string" }, reason: { type: "string" } } } },
    },
  };
}

const SOURCE_LABEL = { granola: "Granola", whatsapp: "WhatsApp chat export", file: "transcript file", paste: "pasted transcript" };
export function sourceLabel(meeting) {
  const s = meeting.source || {};
  return SOURCE_LABEL[s.system] || s.system || "transcript file";
}

/** The per-run user message: compact text, empty CRM values omitted, transcript numbered. */
export function buildUserMessage({ meeting, opp, client, team, lines, schema, permissions = null }) {
  const date = String(meeting.start || "").slice(0, 10);
  const time = String(meeting.start || "").slice(11, 16);
  const owner = (team.find((u) => u.user_id === opp.owner_id) || {}).name || opp.owner_id;
  const out = [
    "CONVERSATION",
    `id: ${meeting.meeting_id} | source: ${sourceLabel(meeting)} | title: ${meeting.title}`,
    meeting.chat
      ? `chat from ${lines[0].timestamp} to ${lines[lines.length - 1].timestamp} (each message carries its own date and time; resolve "tomorrow" from the message that says it)`
      : `date: ${date ? `${date} (${weekdayOf(date)})` : "unknown"} ${time} | scheduled: ${meeting.scheduled_minutes ?? "?"} min | recorded: ${meeting.recorded_minutes ?? "?"} min`,
    `participants: ${(meeting.participants || []).join("; ")}`,
    "",
    "CLIENT",
    !client ? "(none)" : client.client_id
      ? `${client.name} (${client.client_id}) | industry: ${client.industry} | contacts: ${(client.contacts || []).map((c) => `${c.name} (${c.title})`).join("; ")}`
      : `${client.name} (new client: not in the CRM yet, no known contacts)`,
    "",
    "OPPORTUNITY",
    opp.opportunity_id ? `${opp.opportunity_id} | ${opp.name} | owner: ${owner}`
      : `new opportunity (not in the CRM yet) | owner: ${owner} | it starts at ${schema.stages[0]}`,
    "",
    "CURRENT VALUES (empty fields are omitted; [approved] = approved by the seller)",
  ];
  let any = false;
  for (const d of schema.fields) {
    const cur = currentOf(d, opp, client);
    if (cur.value == null || cur.value === "") continue;
    any = true;
    out.push(`${d.key}: ${cur.value}${cur.approved ? " [approved]" : ""}`);
  }
  if (!any) out.push("(all empty)");
  const off = schema.fields.filter((d) => permissionOf(schema, permissions, d.key) === "off").map((d) => d.key);
  if (off.length) out.push("", `FIELDS TURNED OFF BY THE SELLER (do not return them): ${off.join(", ")}`);
  out.push("", "TEAM ROSTER (allowed follow-up owners)", team.map((u) => `${u.name} (${u.role})`).join("; "),
    "", "TRANSCRIPT (cite evidence by line number)", numberedTranscript(lines));
  return out.join("\n");
}

// ------------------------------------------------------------------ 3. value checks (shared by the validator and the seller's edits)
function canonicalStage(schema, v) { return schema.stages.find((s) => norm(s) === norm(v)) || null; }

/**
 * Check and normalise one value. seller=true is the seller's own edit: the stage may then be any stage
 * (Closed Won/Lost included); the agent's proposal must be exactly one step forward.
 */
export function checkValue(def, value, { schema, team, current, seller = false }) {
  const v = typeof value === "string" ? value.trim() : value == null ? "" : String(value).trim();
  if (!v) return { ok: false, why: "proposed without a value" };
  const note = (s) => ({ ok: true, value: s.value, note: s.note });
  switch (def.type) {
    case "roster": {
      const u = team.find((x) => norm(x.name) === norm(v));
      return u ? { ok: true, value: u.name } : { ok: false, why: `owner '${v}' is not in the team roster` };
    }
    case "date": {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return { ok: false, why: `date '${v}' is not YYYY-MM-DD` };
      const [y, m, d] = v.split("-").map(Number); const dt = new Date(Date.UTC(y, m - 1, d));
      return dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d ? { ok: true, value: v } : { ok: false, why: `date '${v}' does not exist` };
    }
    case "month": {
      const m = v.match(/^(\d{4})-(\d{2})$/);
      return m && +m[2] >= 1 && +m[2] <= 12 ? { ok: true, value: v } : { ok: false, why: `go-live '${v}' is not YYYY-MM` };
    }
    case "integer": {
      const s = v.replace(/[,\s]/g, "");
      return /^\d+$/.test(s) && +s > 0 ? { ok: true, value: String(+s) } : { ok: false, why: `'${v}' is not a whole number` };
    }
    case "multi": {
      const opts = schema.departments;
      const parts = v.split(/[;,]/).map((p) => p.trim()).filter(Boolean);
      const hit = opts.filter((o) => parts.some((p) => norm(p) === norm(o)));
      const miss = parts.filter((p) => !opts.some((o) => norm(o) === norm(p)));
      if (!hit.length) return { ok: false, why: `'${v}' has no department from the list` };
      return note({ value: hit.join("; "), note: miss.length ? `dropped unknown department(s): ${miss.join(", ")}` : null });
    }
    case "budget": {
      if (/^no budget allocated\.?$/i.test(v)) return { ok: true, value: "No budget allocated" };
      return /^usd\s*\d/i.test(v) ? { ok: true, value: v.replace(/^usd\s*/i, "USD ") } : { ok: false, why: `budget '${v}' is not 'USD <amount> per <period>'` };
    }
    case "person": {
      const role = def.label.toLowerCase();
      if (/unattributed/i.test(v)) return { ok: false, why: `an unattributed speaker cannot be named as ${role}` };
      if (team.some((u) => norm(v).startsWith(norm(u.name)))) return { ok: false, why: `'${v}' is on the seller side, not the customer's ${role}` };
      return { ok: true, value: v };
    }
    case "stage": {
      const to = canonicalStage(schema, v);
      if (!to) return { ok: false, why: `unknown stage '${v}'` };
      if (seller) return { ok: true, value: to };
      if (isClosed(schema, to)) return { ok: false, why: "Closed Won/Lost can only be set by the seller" };
      const from = schema.stages.indexOf(current), toI = schema.stages.indexOf(to);
      return toI === from + 1 ? { ok: true, value: to } : { ok: false, why: `stage move ${current} -> ${to} is not one step forward` };
    }
    default: {
      const n = words(v);
      return note({ value: v, note: def.max_words && n > def.max_words ? `${n} words, over the ${def.max_words}-word limit` : null });
    }
  }
}

export function sameValue(def, a, b) {
  if (a == null || b == null) return a == null && b == null;
  if (def.type === "integer") return String(a).replace(/[,\s]/g, "") === String(b).replace(/[,\s]/g, "");
  if (def.type === "multi") {
    const set = (s) => String(s).split(/[;,]/).map(norm).filter(Boolean).sort().join("|");
    return set(a) === set(b);
  }
  return norm(a).replace(/[.\s]+$/, "") === norm(b).replace(/[.\s]+$/, "");
}

// ------------------------------------------------------------------ 4. validator (guardrails in code, not trusted to the model)
function resolveCite(item, lines) {
  const q = cleanQuote(item && item.quote);
  if (norm(q).length <= 3) return { why: "empty quote" };
  const nq = norm(q);
  const cited = Number.isInteger(item.line) ? lines[item.line - 1] : null;
  if (cited && cited.norm.includes(nq)) return { line: cited };
  const hits = lines.filter((l) => l.norm.includes(nq));
  if (!hits.length) return { why: `quote not found ("${q.slice(0, 40)}")` };
  const near = cited ? hits.reduce((a, b) => (Math.abs(b.n - cited.n) < Math.abs(a.n - cited.n) ? b : a)) : hits[0];
  return { line: near, moved: item.line };
}

function resolveEvidence(list, lines, key, notes) {
  const out = [];
  for (const item of Array.isArray(list) ? list : []) {
    const r = resolveCite(item, lines);
    if (!r.line) { notes.push(`${key}: removed a quote (${r.why})`); continue; }
    if (r.moved !== undefined && r.moved !== r.line.n) notes.push(`${key}: quote cited on ${lineTag(r.moved || 0)} found on ${lineTag(r.line.n)}`);
    if (out.some((e) => e.line === r.line.n && norm(e.quote) === norm(cleanQuote(item.quote)))) continue;
    out.push({ line: r.line.n, timestamp: r.line.timestamp, speaker: r.line.speaker, quote: cleanQuote(item.quote) });
  }
  return out.slice(0, 3);
}

/**
 * The model returns only fields with evidence (plus the stage). The validator rebuilds the full table:
 * every field of the schema, in schema order, each with its current value, a checked status, a
 * normalised value and evidence resolved to real transcript lines. Every correction is listed in
 * validation_notes. "unchanged" = proposed value equal to the approved value: no decision, no write.
 * "off" = the seller turned the field off in Settings: whatever the model said is dropped.
 */
export function validateOutput(raw, ctx, schema) {
  const { meeting, opp, client, lines, team, target = null, permissions = null } = ctx;
  const notes = [];
  if (raw && raw.run_status === "Blocked") {
    return { ...blocked(meeting.meeting_id, opp.opportunity_id, "Unmatched", raw.block_reason || "Blocked by the agent: the conversation is about a different company."), validation_notes: notes };
  }
  const keys = fieldKeys(schema);
  const given = raw && Array.isArray(raw.fields) ? raw.fields : [];
  const extra = given.filter((f) => !keys.includes(f && f.field));
  if (extra.length) notes.push(`dropped out-of-scope fields: ${extra.map((f) => f && f.field).join(", ")}`);
  const byKey = {};
  for (const f of given) {
    if (!f || !keys.includes(f.field)) continue;
    if (byKey[f.field]) { notes.push(`${f.field}: duplicate entry ignored`); continue; }
    byKey[f.field] = f;
  }
  const fields = schema.fields.map((def) => {
    const cur = currentOf(def, opp, client);
    const g = byKey[def.key];
    const f = { field: def.key, group: def.group, record: def.record, current_value: cur.value, current_approved: cur.approved,
      status: "no_evidence", proposed_value: null, evidence: [], note: null };
    if (permissionOf(schema, permissions, def.key) === "off") { f.status = "off"; f.note = "Turned off in Settings > Permissions."; return f; }
    if (!g) {
      if (def.type === "stage") { notes.push("stage: missing in the agent output -> no_evidence"); f.note = "The agent did not assess the stage."; }
      return f;
    }
    f.status = g.status;
    f.note = g.note ?? null;
    const down = (why) => { notes.push(`${def.key}: ${why} -> no_evidence`); f.status = "no_evidence"; f.proposed_value = null; f.evidence = []; f.note = `Validator: ${why}`; return f; };
    if (!AGENT_STATUSES.includes(f.status)) return down(`invalid status '${g.status}'`);
    if (f.status === "no_evidence") return f; // keeps the note (for the stage: the missing criteria)
    f.evidence = resolveEvidence(g.evidence, lines, def.key, notes);
    if (!f.evidence.length) return down("no evidence quote found verbatim in the transcript");
    if (f.status === "contradictory") {
      if (def.kind !== "state" || !cur.approved || cur.value == null) return down("contradictory is only allowed on a seller-approved state field");
      f.proposed_value = null;
      return f;
    }
    const c = checkValue(def, g.value, { schema, team, current: fieldOf(opp, "stage").value });
    if (!c.ok) return down(c.why);
    if (c.note) notes.push(`${def.key}: ${c.note}`);
    f.proposed_value = c.value;
    if (cur.approved && sameValue(def, cur.value, c.value)) f.status = "unchanged";
    return f;
  });
  const ignored = [];
  for (const item of raw && Array.isArray(raw.ignored_out_of_scope) ? raw.ignored_out_of_scope : []) {
    const r = resolveCite(item, lines);
    if (!r.line) { notes.push(`ignored_out_of_scope: removed an item (${r.why})`); continue; }
    ignored.push({ line: r.line.n, timestamp: r.line.timestamp, speaker: r.line.speaker, quote: cleanQuote(item.quote), reason: String(item.reason || "") });
  }
  return { meeting_id: meeting.meeting_id, opportunity_id: opp.opportunity_id, client_id: client ? client.client_id : null,
    target: target ? { ...target } : null,
    source_status: "Ready", run_status: "Awaiting review", block_reason: null, warnings: ctx.warnings || [],
    fields, ignored_out_of_scope: ignored, validation_notes: notes };
}

// ------------------------------------------------------------------ 5. write (platform only)
// decisions: { field: { decision: "approve"|"edit"|"reject"|"keep"|"replace"|"clear", value?, reason?, auto? },
//              __create__: { decision: "approve"|"reject", client_name?, opportunity_name?, auto? } for a new opportunity }
// crm: { opportunities, clients } (mutated in place). only: the fields to write in this call (default: every
// actionable field). Throws when a decision is missing or a seller value is invalid; nothing is written then.
const ALLOWED = { proposed: ["approve", "edit", "reject"], contradictory: ["keep", "replace", "clear"] };
export function nextId(list, key, prefix, width) {
  const max = list.reduce((m, x) => Math.max(m, Number(String(x[key] || "").replace(/\D/g, "")) || 0), 0);
  return prefix + String(max + 1).padStart(width, "0");
}

function createRecords({ output, d, crm, reviewerId, log, schema, runId, now }) {
  const t = output.target;
  const today = String(now).slice(0, 10);
  let client = t.client_id ? crm.clients.find((c) => c.client_id === t.client_id) : null;
  if (t.client_id && !client) throw new Error(`Client ${t.client_id} not found in the CRM`);
  const name = String(d.client_name || t.client_name || "").trim();
  if (!client) {
    if (!name) throw new Error("The new client needs a name");
    client = { client_id: nextId(crm.clients, "client_id", "CLI-", 3), name, domain: null, industry: null, hq: null, fields: {},
      contacts: (t.contacts || []).map((n) => ({ name: n, title: "", email: "", buying_role: "" })), created: today, created_by: reviewerId };
    crm.clients.push(client);
    log.add(d.auto ? "system" : reviewerId, "client_created", client.client_id, "ok", `${client.name}${client.contacts.length ? `; contacts: ${client.contacts.map((c) => c.name).join(", ")}` : ""}`);
  }
  const opp = { opportunity_id: nextId(crm.opportunities, "opportunity_id", "OPP-", 4), client_id: client.client_id,
    name: String(d.opportunity_name || t.opportunity_name || `${client.name} - CRM`).trim(), owner_id: reviewerId,
    amount_usd: null, close_date: null, created: today, last_updated: today,
    fields: { stage: { value: schema.stages[0], approved: true, written_by: runId, written_at: now } } };
  crm.opportunities.push(opp);
  log.add(d.auto ? "system" : reviewerId, "opportunity_created", opp.opportunity_id, "ok", `${opp.name} (${client.name}), stage ${schema.stages[0]}`);
  output.opportunity_id = opp.opportunity_id;
  output.client_id = client.client_id;
  output.target = { ...t, created: { client_id: client.client_id, opportunity_id: opp.opportunity_id, new_client: !t.client_id, auto: !!d.auto } };
}

export function applyApprovedFields({ output, decisions, crm, reviewerId, log, schema, team, runId = null, now = new Date().toISOString(), only = null }) {
  const scope = output.fields.filter((f) => ACTIONABLE.includes(f.status) && (!only || only.includes(f.field)));
  const missing = scope.filter((f) => !decisions[f.field]);
  if (missing.length) throw new Error(`Decision required for: ${missing.map((f) => f.field).join(", ")}`);
  const isNew = !output.opportunity_id && output.target && output.target.kind === "new";
  if (isNew && !decisions.__create__) throw new Error("Decision required for: the new opportunity");
  const stageNow = isNew ? schema.stages[0] : fieldOf(crm.opportunities.find((o) => o.opportunity_id === output.opportunity_id), "stage").value;
  const plan = scope.map((f) => {
    const def = fieldDef(schema, f.field);
    const d = decisions[f.field];
    if (!ALLOWED[f.status].includes(d.decision)) throw new Error(`${def.label}: '${d.decision}' is not a valid decision for a ${f.status} field`);
    if (d.auto && !(f.status === "proposed" && d.decision === "approve")) throw new Error(`${def.label}: only a proposed value can be written without asking`);
    let final = null; let write = false;
    if (d.decision === "approve") { final = f.proposed_value; write = true; }
    else if (d.decision === "edit" || d.decision === "replace") {
      const c = checkValue(def, d.value, { schema, team, current: stageNow, seller: true });
      if (!c.ok) throw new Error(`${def.label}: ${c.why}`);
      final = c.value; write = true;
    } else if (d.decision === "clear") { final = null; write = true; }
    else if (d.decision === "keep") { final = f.current_value; }
    return { f, def, d, final, write };
  });
  const record = [];
  if (isNew) {
    const d = decisions.__create__;
    if (d.decision !== "approve") {
      log.add(reviewerId, "opportunity_not_created", output.meeting_id, "ok", d.reason || "rejected by the seller");
      for (const { f, def, d: fd } of plan) record.push(entry(f, def, fd, null, "Not written"));
      return record;
    }
    createRecords({ output, d, crm, reviewerId, log, schema, runId, now });
  }
  const opp = crm.opportunities.find((o) => o.opportunity_id === output.opportunity_id);
  if (!opp) throw new Error(`Opportunity ${output.opportunity_id} not found in the CRM`);
  const client = crm.clients.find((c) => c.client_id === opp.client_id) || null;
  let wrote = 0;
  function entry(f, def, d, final, result) {
    return { field: f.field, record: def.record, previous_value: f.current_value, previous_approved: f.current_approved, agent_status: f.status,
      agent_proposal: f.proposed_value, evidence: f.evidence, seller_decision: d.decision, decided_by: d.auto ? "permission" : "seller",
      final_value: final, rejection_reason: d.reason ?? null, reviewer_id: reviewerId, decided_at: now, write_result: result };
  }
  for (const { f, def, d, final, write } of plan) {
    const target = def.record === "client" ? client : opp;
    const objectId = `${def.record === "client" ? (client && client.client_id) : opp.opportunity_id}.${f.field}`;
    log.add(d.auto ? "system" : reviewerId, "field_decided", objectId, "ok", d.auto ? "approve (Always allow)" : d.decision);
    let result = "Not written";
    if (write && target) {
      log.add("system", "crm_write_attempted", objectId, "ok");
      target.fields = target.fields || {};
      target.fields[f.field] = { value: final, approved: true, written_by: runId, written_at: now };
      result = "Succeeded";
      wrote++;
      log.add("system", "crm_write_result", objectId, "ok", result);
    }
    record.push(entry(f, def, d, final, result));
  }
  if (wrote || isNew) opp.last_updated = String(now).slice(0, 10);
  return record;
}

/** Undo of one write (an "Always allow" field the seller did not want): the previous value comes back. */
export function revertWrite({ item, output, crm, reviewerId, log, now = new Date().toISOString() }) {
  if (item.write_result !== "Succeeded" || item.reverted_at) throw new Error(`${item.field}: nothing to undo`);
  const opp = crm.opportunities.find((o) => o.opportunity_id === output.opportunity_id);
  const target = item.record === "client" ? crm.clients.find((c) => c.client_id === (opp && opp.client_id)) : opp;
  if (!target) throw new Error(`${item.field}: record not found`);
  target.fields = target.fields || {};
  if (item.previous_value == null) delete target.fields[item.field];
  else target.fields[item.field] = { value: item.previous_value, approved: !!item.previous_approved, written_by: "undo", written_at: now };
  item.reverted_at = now;
  item.reverted_by = reviewerId;
  log.add(reviewerId, "crm_write_reverted", `${item.record === "client" ? target.client_id : target.opportunity_id}.${item.field}`, "ok", "undo");
  return item;
}

/** Run status after the last decision, in the vocabulary of agent/run_log_schema.json. */
export function statusAfterSubmit(record) {
  if (!record.length) return "Approved"; // nothing to decide: the seller confirmed the record as it is
  if (record.every((r) => r.decided_by === "permission")) return "Written automatically";
  if (!record.some((r) => r.write_result === "Succeeded")) return record.every((r) => r.seller_decision === "keep") ? "Approved" : "Rejected";
  return record.some((r) => ["edit", "replace", "clear"].includes(r.seller_decision)) ? "Edited and approved" : "Approved";
}
