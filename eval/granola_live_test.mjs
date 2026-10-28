// Tests the LIVE Granola path without a key: syncLive() against a fake public API built from the fixtures.
// It covers what a real account will hit: cursor pagination, a transcript too large to inline (413 ->
// paged /transcript), a rate limit (429 -> wait and retry), the incremental re-sync, and the guards on the
// key and the folder id. The normalised transcripts must equal the ones the fixtures produce.
//   node eval/granola_live_test.mjs

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { syncLive } from "../agent/granola.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const NOTES = path.join(KIT, "data", "granola", "notes");
const files = fs.readdirSync(NOTES).filter((f) => f.endsWith(".json")).sort();
const notes = files.map((f) => ({ meetingId: f.replace(/\.json$/, ""), note: JSON.parse(fs.readFileSync(path.join(NOTES, f), "utf8")) }));
const FOLDER = "fol_CRMsyncFolder1";
const BIG = notes.find((n) => n.meetingId === "MTG-2009").note.id; // answers 413 on include=transcript

let calls = 0; let throttled = false;
const json = (status, body, headers = {}) => ({ ok: status < 400, status, headers: { get: (k) => headers[k.toLowerCase()] ?? null }, json: async () => body, text: async () => JSON.stringify(body) });
async function fakeFetch(url, opts) {
  calls++;
  if (!String(opts.headers.Authorization).startsWith("Bearer grn_")) return json(401, { error: "unauthorized" });
  const u = new URL(url);
  const p = u.pathname.replace(/^\/v1/, "");
  if (p === "/notes") {
    if (!throttled) { throttled = true; return json(429, { error: "slow down" }, { "retry-after": "0" }); }
    if (u.searchParams.get("folder_id") !== FOLDER) return json(200, { notes: [], hasMore: false, cursor: null });
    const start = Number(u.searchParams.get("cursor") || 0);
    const page = notes.slice(start, start + 4).map(({ note }) => ({ id: note.id, object: "note", title: note.title, owner: note.owner, created_at: note.created_at, updated_at: note.updated_at, deleted_at: null }));
    const next = start + 4 < notes.length ? String(start + 4) : null;
    return json(200, { notes: page, hasMore: !!next, cursor: next });
  }
  let m = p.match(/^\/notes\/(not_\w+)\/transcript$/);
  if (m) {
    const n = notes.find((x) => x.note.id === m[1]).note;
    const start = Number(u.searchParams.get("cursor") || 0);
    const next = start + 10 < n.transcript.length ? String(start + 10) : null;
    return json(200, { transcript: n.transcript.slice(start, start + 10), hasMore: !!next, cursor: next });
  }
  m = p.match(/^\/notes\/(not_\w+)$/);
  if (m) {
    const n = notes.find((x) => x.note.id === m[1]).note;
    const include = u.searchParams.get("include") === "transcript";
    if (include && n.id === BIG) return json(413, { error: "TRANSCRIPT_TOO_LARGE" });
    const { transcript, ...rest } = n;
    return json(200, include ? n : { ...rest, transcript: null });
  }
  return json(404, { error: "not found" });
}

let pass = 0; let fail = 0;
const check = (name, ok, detail = "") => { ok ? pass++ : fail++; console.log(`${ok ? "OK  " : "FAIL"} ${name}${ok || !detail ? "" : `  (${detail})`}`); };
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "granola-live-"));
try {
  const r1 = await syncLive({ key: "grn_test", folder: FOLDER, fetchImpl: fakeFetch, cacheDir: tmp });
  check("first sync brings every note of the folder, across pages", r1.added.length === notes.length, JSON.stringify(r1.added));
  check("a 429 is retried instead of failing the sync", throttled);
  const cached = JSON.parse(fs.readFileSync(path.join(tmp, "meetings.json"), "utf8"));
  let same = 0;
  for (const { meetingId, note } of notes) {
    const live = cached.find((x) => x.source.note_id === note.id);
    const a = fs.readFileSync(path.join(KIT, live.transcript_file), "utf8");
    const b = fs.readFileSync(path.join(KIT, "transcripts", `${meetingId}.txt`), "utf8");
    if (a === b && live.linked_opportunity_id === JSON.parse(fs.readFileSync(path.join(KIT, "data", "meetings.json"), "utf8")).find((x) => x.meeting_id === meetingId).linked_opportunity_id) same++;
  }
  check("live transcripts and matches equal the fixtures' (including the paged 413 transcript)", same === notes.length, `${same}/${notes.length}`);
  check("live meetings get their own ids (MTG-3001...)", cached.every((x) => /^MTG-3\d{3}$/.test(x.meeting_id)));
  const before = calls;
  const r2 = await syncLive({ key: "grn_test", folder: FOLDER, fetchImpl: fakeFetch, cacheDir: tmp });
  check("a second sync with nothing new opens no note", r2.added.length === 0 && r2.updated.length === 0 && calls - before <= 3, `${calls - before} calls`);
  let e1 = null; try { await syncLive({ key: "", folder: FOLDER, fetchImpl: fakeFetch, cacheDir: tmp }); } catch (e) { e1 = e; }
  check("no API key: refused with instructions", e1 && /GRANOLA_API_KEY/.test(e1.message));
  let e2 = null; try { await syncLive({ key: "grn_test", folder: "CRM sync", fetchImpl: fakeFetch, cacheDir: tmp }); } catch (e) { e2 = e; }
  check("a folder name instead of an id: refused before listing anything", e2 && /fol_/.test(e2.message));
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log(`\n${pass} ok, ${fail} failed.`);
process.exitCode = fail ? 1 : 0;
