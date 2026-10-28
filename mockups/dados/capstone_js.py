# -*- coding: utf-8 -*-
"""O JavaScript do mockup Orbita CRM (v5: qualquer conversa -> CRM). Stdlib pura; o
renderizador troca os marcadores __FOTO__ (o JSON congelado por coleta.py), __ICO__
(os SVG que a tela desenha em tempo de execucao) e __CORE__ (o nucleo do kit:
agent/core.mjs + eval/score.mjs + agent/explore.mjs, embutidos tal como estao).

O que mora aqui, em ordem:

  store       o estado em localStorage (`orbita.crm.v3`): o CRM semeado do kit, as
              reunioes que a vendedora adicionou, as rodadas, as decisoes, os chats
              do Explore e os ajustes (permissoes por campo, modelo, esforco).
  entrada     "Select your opportunity" + arquivo ou texto colado: o nucleo le o
              formato (WebVTT, SRT, Otter, WhatsApp, linhas "Nome: texto"), rotula as
              vozes e atribui a conversa a uma oportunidade (ou propoe uma nova).
  rodada      pre-checagens do nucleo; o servidor local chama o Claude quando existe;
              sem servidor, so as transcricoes de exemplo tem resultado salvo. Os
              campos em "Always allow" sao escritos na hora (com Undo); o resto espera.
  vistas      explore · meetings · review/<run> · opportunities[/<opp>] ·
              clients[/<cliente>] · settings[/<aba>]; as rotas antigas redirecionam.

Regra que a sonda confere: nada escreve no CRM fora de CORE.applyApprovedFields, e
so o que a vendedora aprovou ou deixou em "Always allow".
"""

JS = r"""
'use strict';
const FOTO = __FOTO__;
const ICO = __ICO__;
// The kit's rules, embedded verbatim from agent/core.mjs, eval/score.mjs and agent/explore.mjs by
// render_capstone.py: the same parser, matching, pre-checks, validator, write path, scorer and Explore
// answers as the command line and the local server.
const CORE = (function () {
__CORE__
})();
const SCHEMA = FOTO.schema;
const FIELDS = SCHEMA.fields.map(d => d.key);
const DEF = Object.fromEntries(SCHEMA.fields.map(d => [d.key, d]));
const STAGES = SCHEMA.stages;
const OPEN_STAGES = STAGES.filter(s => !SCHEMA.closed_stages.includes(s));
const MDP = SCHEMA.fields.filter(d => d.meddpicc);
const LEVELS = SCHEMA.permissions.levels;
const KEY = 'orbita.crm.v3';
const API = window.CAPSTONE_API != null ? window.CAPSTONE_API : (location.protocol.startsWith('http') ? '' : 'http://localhost:8787');
const DEMO_USERS = ['U01', 'U02', 'U04'];
const TODAY = FOTO.data_da_foto; // "overdue" is measured against the snapshot, never against a constant
const MODELS = [
  {id: 'claude-sonnet-5-5', name: 'Claude Sonnet 5.5', note: 'balanced: the default'},
  {id: 'claude-haiku-5-5', name: 'Claude Haiku 5.5', note: 'fastest and lowest cost'},
  {id: 'claude-opus-5-5', name: 'Claude Opus 5.5', note: 'most careful reading, highest cost'},
];
const KIND_LABEL = {vtt: 'WebVTT (Teams, Zoom, Google Meet)', srt: 'subtitles (SRT)', otter: 'Otter / Fathom export', whatsapp: 'WhatsApp chat export',
  chat: 'chat', kit: 'timestamped transcript', plain: 'speaker lines'};

// ------------------------------------------------------------------ utils
const e = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
const deep = o => JSON.parse(JSON.stringify(o));
const pad = n => String(n).padStart(2, '0');
const WD = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], MO = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function fmtDate(iso, withTime) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(iso || '');
  if (!m) return iso || '';
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  let s = `${WD[d.getUTCDay()]} ${+m[3]} ${MO[+m[2] - 1]} ${m[1]}`;
  if (withTime !== false && m[4]) s += ` · ${m[4]}:${m[5]}`;
  return s;
}
const fmtShort = iso => fmtDate(iso, false).replace(/ \d{4}$/, '');
function fmtUSD(n) {
  if (n == null) return 'no amount';
  if (n >= 1e6) return 'USD ' + (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1e3) return 'USD ' + Math.round(n / 1e3) + 'k';
  return 'USD ' + n;
}
function isoLocal(d) {
  d = d || new Date();
  const off = -d.getTimezoneOffset(), sg = off >= 0 ? '+' : '-', a = Math.abs(off);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${sg}${pad(a / 60 | 0)}:${pad(a % 60)}`;
}
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
function ico(name, cls) { return (ICO[name] || '').replace('class="ni"', 'class="' + (cls || 'ico-s') + '"'); }
const MONO_COLORS = ['#4F46A5', '#0F6E78', '#7C4A1E', '#5B3F8C', '#2F5D8A', '#5E5E1C'];
function mono(name) {
  if (FOTO.monos[name]) return FOTO.monos[name];
  let h = 0; for (const ch of String(name || '?')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return {letter: (String(name || '?').match(/[A-Za-z0-9]/) || ['?'])[0].toUpperCase(), color: MONO_COLORS[h % MONO_COLORS.length]};
}
function logo(name, size) {
  if (!name) return '';
  const m = mono(name);
  const cls = size === 32 ? 'lg lg-32' : size === 20 ? 'lg lg-20' : 'lg';
  return `<span class="${cls}" style="background:${m.color}" aria-hidden="true">${e(m.letter)}</span>`;
}
function initials(name) {
  const p = (name || '').split(/\s+/).filter(x => /^[A-Za-zÀ-ɏ]/.test(x));
  return p.length ? (p[0][0] + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase() : '';
}
const modelName = id => (MODELS.find(m => m.id === id) || {name: id || 'Claude'}).name;

// ------------------------------------------------------------------ store
let S;
function freshSettings() { return {permissions: CORE.defaultPermissions(SCHEMA), model: MODELS[0].id, effort: 'medium'}; }
function fresh(settings) {
  return {v: 3, user: 'U01', crm: {clients: deep(FOTO.clients), opportunities: deep(FOTO.opportunities)},
    meetings: [], transcripts: {}, runs: {}, runOrder: [], events: [], confirmed: {}, chats: [], chatCurrent: null,
    settings: settings || freshSettings(), granola: {synced: false, lastSync: null},
    seq: {run: 0, mtg: 0, chat: 0}, lastRun: null, evalRows: null, evalAt: null};
}
function load() {
  try { const j = localStorage.getItem(KEY); if (j) { const s = JSON.parse(j); if (s && s.v === 3) return s; } } catch (_) {}
  return null;
}
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (_) {} }
function resetAll() { S = fresh(S ? S.settings : null); save(); }

const userById = id => FOTO.team.find(u => u.user_id === id);
const me = () => userById(S.user);
const isManager = () => me().access === 'all_opportunities_read';
const opps = () => S.crm.opportunities;
const clients = () => S.crm.clients;
const oppById = id => opps().find(o => o.opportunity_id === id);
const clientById = id => clients().find(c => c.client_id === id);
const clientOf = o => (o ? clientById(o.client_id) : null);
const canRead = (o, u) => CORE.canRead(u || me(), o);
const myOpps = () => opps().filter(o => canRead(o));
const isOpen = o => !SCHEMA.closed_stages.includes(stageOf(o));
const myOpenOpps = () => myOpps().filter(isOpen);
const myClients = () => clients().filter(c => opps().some(o => o.client_id === c.client_id && canRead(o)));
const fv = (rec, key) => CORE.fieldOf(rec, key);
const stageOf = o => fv(o, 'stage').value;
const ownerName = o => (userById(o.owner_id) || {}).name || o.owner_id;
const perms = () => S.settings.permissions;
const permOf = key => CORE.permissionOf(SCHEMA, perms(), key);

const allMeetings = () => S.meetings.map(m => (S.confirmed[m.meeting_id] ? Object.assign({}, m, {seller_confirmed_complete: true}) : m));
const meetingById = id => allMeetings().find(m => m.meeting_id === id) || null;
const isMine = m => m.organiser_id === S.user;
const myMeetings = () => allMeetings().filter(isMine);
const transcriptOf = m => (m ? (S.transcripts[m.meeting_id] != null ? S.transcripts[m.meeting_id] : null) : null);

const allRuns = () => S.runOrder.map(id => S.runs[id]);
const visibleRuns = () => allRuns().filter(r => isManager() || r.userId === S.user);
const runsOf = meetingId => allRuns().filter(r => r.meetingId === meetingId && r.userId === S.user);
const latestRun = meetingId => runsOf(meetingId)[0] || null;
const nextRunId = () => 'RUN-' + String(++S.seq.run).padStart(4, '0');
const nextMtgId = () => 'MTG-D' + String(++S.seq.mtg).padStart(3, '0');
const isNewTarget = o => !o.opportunity_id && o.target && o.target.kind === 'new';
const autoDone = run => (run.autoRecord || []).map(r => r.field);
/** The fields that still wait for the seller: actionable, not written by "Always allow", not waiting for the creation. */
function pendingFields(run) {
  if (run.record || run.status === 'Blocked') return [];
  const skip = new Set(autoDone(run).concat(run.autoPending || []));
  return run.output.fields.filter(f => CORE.ACTIONABLE.includes(f.status) && !skip.has(f.field));
}
const waiting = run => !run.record && run.status !== 'Blocked';
const awaitingFor = oppId => allRuns().find(r => r.output.opportunity_id === oppId && waiting(r) && r.userId === S.user) || null;

// saved results: the sample transcripts carry the kit's reference answers, found by their spoken text
const SAVED = {};
for (const [id, tx] of Object.entries(FOTO.transcripts)) if (FOTO.refs[id]) SAVED[CORE.conversationKey(CORE.transcriptLines(tx))] = id;
const savedFor = lines => { const id = SAVED[CORE.conversationKey(lines)]; return id ? FOTO.refs[id] : null; };

// ------------------------------------------------------------------ the local server (Claude for runs and Explore)
const LIVE = {ok: false, mode: null, key: false, checked: false, granola: null};
async function probeServer() {
  try {
    const r = await fetch(API + '/api/health', {cache: 'no-store'});
    if (r.ok) { const j = await r.json(); Object.assign(LIVE, {ok: true, mode: j.mode, key: !!j.key, granola: j.granola || null}); }
    else LIVE.ok = false;
  } catch (_) { LIVE.ok = false; }
  LIVE.checked = true;
  renderJob();
  const v = view();
  if (v === 'settings') renderSettings();
  if (v === 'explore') renderExplore();
}
const claudeOn = () => LIVE.ok && LIVE.mode === 'live';

// ------------------------------------------------------------------ adding a conversation (file or pasted text)
function ingest(text, name, pasted) {
  const parsed = CORE.parseConversation(text, {now: TODAY});
  if (parsed.lines.length < 2 || parsed.speakers.length < 1) {
    toast(`Could not read a conversation in ${name || 'the text'}: expected one speaker per line ("Name: text"), a WebVTT or SRT file, or a WhatsApp export`, 'bad');
    return false;
  }
  const base = String(name || '').replace(/\.[a-z0-9]{2,4}$/i, '');
  const cap = w => w.charAt(0).toUpperCase() + w.slice(1);
  const title = parsed.kind === 'whatsapp' ? base.replace(/^WhatsApp Chat with/i, 'WhatsApp chat with')
    : base.split('_').map(p => p.replace(/-/g, ' ').replace(/\s+/g, ' ').trim()).filter(Boolean)
      .map((p, i) => (i === 0 ? p.split(' ').map(cap).join(' ') : cap(p))).join(' - ');
  UI.draft = {name: name || 'pasted text', pasted: !!pasted, kind: parsed.kind, chat: parsed.chat, lines: parsed.lines, speakers: parsed.speakers,
    minutes: parsed.minutes, ends_mid_sentence: parsed.ends_mid_sentence, start: parsed.start, title: pasted ? '' : title,
    date: parsed.date || TODAY, newClient: null, newName: null};
  renderDraft();
  return true;
}
/** Where the draft goes: the seller's choice in "Select your opportunity", or what the core matched. */
function resolveDraft(d) {
  const choice = UI.oppChoice;
  const labeled = CORE.labelSpeakers(d.lines, {team: FOTO.team});
  if (choice && choice !== '__new__') {
    const o = oppById(choice);
    return {kind: 'chosen', opportunity_id: choice, client_id: o.client_id, reasons: ['chosen by you']};
  }
  if (choice === '__new__') {
    const guess = CORE.guessClientName(d.title, d.pasted ? '' : d.name, d.speakers);
    return {kind: 'new', client_name: d.newClient != null ? d.newClient : guess, reasons: ['new opportunity, chosen by you']};
  }
  const m = CORE.matchConversation({lines: labeled, title: d.title, filename: d.pasted ? '' : d.name, clients: clients(), opportunities: opps(), team: FOTO.team, user: me(), schema: SCHEMA});
  if (m.kind === 'new_client') return {kind: 'new', client_name: d.newClient != null ? d.newClient : m.client_name_guess, reasons: m.reasons};
  if (m.kind === 'new_opportunity') return {kind: 'new', client_name: d.newClient != null ? d.newClient : clientById(m.client_id).name, reasons: m.reasons};
  return m;
}
function draftTarget(d, r) {
  const name = String(r.client_name || '').trim();
  const known = clients().find(c => c.name.toLowerCase() === name.toLowerCase()) || null;
  const people = CORE.labelSpeakers(d.lines, {team: FOTO.team, clientName: name || 'Customer'}).map(l => l.speaker)
    .filter(s => !/\((Orbita|unattributed)\)\s*$/.test(s)).map(s => s.replace(/\s*\([^)]*\)\s*$/, ''));
  const oname = d.newName != null ? d.newName : (name ? `${known ? known.name : name} - CRM` : '');
  return {kind: 'new', client_id: known ? known.client_id : null, client_name: known ? known.name : name, opportunity_name: oname,
    contacts: known ? [] : [...new Set(people)]};
}
function renderDraft() {
  const box = $('#mt-draft'); if (!box) return;
  const d = UI.draft;
  if (!d) { box.hidden = true; box.innerHTML = ''; return; }
  const r = resolveDraft(d);
  const create = perms().create_opportunity;
  let att = '', ready = true;
  if (r.kind === 'opportunity' || r.kind === 'chosen') {
    const o = oppById(r.opportunity_id), c = clientOf(o);
    att = `<div class="dr-att ok">${ico('check')}<span><b>${e(c.name)} · ${e(o.name)}</b> <span class="t3">${e(stageOf(o))}</span><span class="mini">${e(r.reasons.join('; '))}</span></span><button class="lnk" type="button" data-change>Change</button></div>`;
  } else if (r.kind === 'new') {
    const t = draftTarget(d, r);
    const how = create === 'auto' ? 'Settings allow creating it as soon as the update is prepared.'
      : create === 'ask' ? 'You approve the creation in the review, together with the fields.'
      : 'Creating opportunities is turned off in Settings > Permissions: this conversation will be blocked.';
    att = `<div class="dr-att new">${ico('plus')}<span><b>New opportunity</b> · ${t.client_id ? `${e(t.client_name)} has no open opportunity` : 'no client in your CRM matches this conversation'}<span class="mini">${e(how)}</span></span><button class="lnk" type="button" data-change>Change</button></div>
      <div class="frow">
        <label class="fld"><span class="fld-l">Client</span><input class="inp" id="dr-client" list="dl-clients" value="${e(t.client_name)}" placeholder="Company name"></label>
        <label class="fld"><span class="fld-l">Opportunity name</span><input class="inp" id="dr-oname" value="${e(t.opportunity_name)}" placeholder="for example Field sales CRM"></label>
      </div>
      <datalist id="dl-clients">${clients().map(c => `<option value="${e(c.name)}">`).join('')}</datalist>
      ${t.contacts.length ? `<div class="mini">${t.client_id ? '' : `New contacts for the client: ${e(t.contacts.join(', '))}. `}Owner: you · starts at ${e(STAGES[0])}.</div>` : `<div class="mini">Owner: you · starts at ${e(STAGES[0])}.</div>`}`;
    ready = !!t.client_name;
  } else if (r.kind === 'denied') {
    att = `<div class="dr-att bad">${ico('circle-x')}<span><b>This conversation belongs to an opportunity you do not have access to.</b><span class="mini">Nothing about it will be shown. If you prepare the update, the attempt is recorded and blocked.</span></span></div>`;
  } else {
    att = `<div class="dr-att warn">${ico('circle-help')}<span><b>${r.candidates.length ? 'More than one opportunity could match' : 'No clear match'}</b>${r.candidates.length ? `: ${e(r.candidates.map(x => x.name).join(', '))}` : ''}<span class="mini">Pick it in <b>Select your opportunity</b> above, or choose New opportunity.</span></span></div>`;
    ready = false;
  }
  box.hidden = false;
  box.innerHTML = `
    <div class="dr-file">${ico(d.chat ? 'message-circle' : 'file-text')}<span><b>${e(d.name)}</b> · read as ${e(KIND_LABEL[d.kind] || d.kind)} · ${plural(d.lines.length, d.chat ? 'message' : 'line', d.chat ? 'messages' : 'lines')}${d.minutes ? ` · about ${d.minutes} min` : ''}
      <span class="mini">${plural(d.speakers.length, 'speaker', 'speakers')}: ${e(d.speakers.join(', '))}</span></span></div>
    ${att}
    <div class="frow">
      <label class="fld fld-w"><span class="fld-l">Meeting title</span><input class="inp" id="dr-title" value="${e(d.title)}" placeholder="for example Acme Logistics - Discovery call"></label>
      ${d.chat ? `<div class="fld"><span class="fld-l">Messages</span><span class="fld-v">${e(fmtDate(d.lines[0].timestamp))} to ${e(fmtDate(d.lines[d.lines.length - 1].timestamp))}</span></div>`
        : `<label class="fld"><span class="fld-l">Date</span><input class="inp" id="dr-date" type="date" value="${e(d.date)}"></label>`}
    </div>
    ${d.ends_mid_sentence ? `<div class="warnline">${ico('circle-help')}<span>The transcript stops mid-sentence. If the meeting really ended there, you can confirm it in the review.</span></div>` : ''}
    <div class="acts"><button class="b b-p" type="button" id="dr-go"${ready ? '' : ' disabled'}>Prepare CRM update</button><button class="b b-t" type="button" id="dr-cancel">Discard</button></div>`;
  const ci = $('#dr-client'); if (ci) ci.oninput = () => { d.newClient = ci.value; const on = $('#dr-oname'); if (on && d.newName == null) on.value = ci.value ? ci.value + ' - CRM' : ''; $('#dr-go').disabled = !ci.value.trim(); };
  const on = $('#dr-oname'); if (on) on.oninput = () => { d.newName = on.value; };
  $('#dr-title').oninput = ev => { d.title = ev.target.value; };
  const dt = $('#dr-date'); if (dt) dt.onchange = ev => { d.date = ev.target.value || TODAY; };
  $$('#mt-draft [data-change]').forEach(b => b.onclick = () => { const s = $('#mt-opp'); s.focus(); });
  $('#dr-cancel').onclick = () => { UI.draft = null; renderDraft(); };
  $('#dr-go').onclick = () => prepareDraft();
}
async function prepareDraft() {
  const d = UI.draft; if (!d) return;
  const r = resolveDraft(d);
  if (r.kind === 'choose') { toast('Pick the opportunity first', 'neu'); return; }
  const id = nextMtgId();
  let client = null, target = null, linked = null;
  if (r.kind === 'new') { target = draftTarget(d, r); client = target.client_id ? clientById(target.client_id) : null; if (!target.client_name) { toast('Name the client first', 'neu'); return; } }
  else { linked = r.opportunity_id; client = clientById(r.client_id); }
  const lines = CORE.labelSpeakers(d.lines, {team: FOTO.team, client, clientName: target ? target.client_name : ''});
  const who = target ? target.client_name : client ? client.name : '';
  const m = {meeting_id: id, title: (d.title || '').trim() || (who ? `${who} - ${d.chat ? 'chat' : 'conversation'}` : d.pasted ? 'Pasted conversation' : d.name), start: d.chat ? d.start : `${d.date}T10:00`, scheduled_minutes: null, recorded_minutes: d.minutes,
    chat: d.chat, ends_mid_sentence: d.ends_mid_sentence, source: {system: d.kind === 'whatsapp' ? 'whatsapp' : d.pasted ? 'paste' : 'file', file: d.name, format: d.kind},
    organiser_id: S.user, participants: [...new Set(lines.map(l => l.speaker))], client_id: client ? client.client_id : null,
    linked_opportunity_id: linked, target, match_reason: (r.reasons || []).join('; '), transcript_status: 'complete', added_at: isoLocal()};
  S.meetings.unshift(m); S.transcripts[id] = CORE.conversationText(lines);
  UI.draft = null; UI.oppChoice = ''; save();
  const runId = await startRun(id);
  if (!runId) renderMeetings();
}

// ------------------------------------------------------------------ run lifecycle
async function startRun(meetingId, opts) {
  opts = opts || {};
  const m = meetingById(meetingId);
  if (!m) return null;
  const runId = nextRunId();
  const log = CORE.newLog(runId, isoLocal);
  const data = {team: FOTO.team, clients: clients(), opportunities: opps(), meetings: allMeetings()};
  if (!opts.silent) setJob('rodando', 'Preparing the CRM update', e(m.title));
  const transcript = transcriptOf(m);
  const pre = CORE.prepareRun({meetingId, userId: S.user, data, transcript, log, schema: SCHEMA, permissions: perms()});
  let output, events, mode = 'saved', model = null;
  if (pre.output) {
    log.add('system', 'run_blocked', meetingId, 'blocked', pre.output.block_reason);
    output = pre.output; events = log.events; mode = 'checks';
  } else if (LIVE.ok) {
    try {
      const body = {meetingId, userId: S.user, crm: S.crm, meeting: m, transcript, permissions: perms(), model: S.settings.model, effort: S.settings.effort};
      const r = await fetch(API + '/api/runs', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || ('server ' + r.status));
      output = j.output; events = j.log.map((ev, i) => Object.assign({}, ev, {run_id: runId, seq: i + 1}));
      mode = j.mode; model = j.model || null;
    } catch (err) {
      S.seq.run--; if (!opts.silent) setJob('pronto'); toast('The agent could not read this conversation · ' + err.message, 'bad'); return null;
    }
  } else {
    const raw = savedFor(pre.lines);
    if (!raw) {
      S.seq.run--; if (!opts.silent) setJob('pronto');
      toast('The agent is offline: start the Orbita server with your Claude key to read new conversations. Offline, only the sample transcripts have a saved result.', 'neu', {label: 'Open Settings', hash: '#/settings/agent'});
      return null;
    }
    log.add('system', 'agent_called', meetingId, 'ok', 'saved result (agent offline)');
    output = CORE.validateOutput(deep(raw), Object.assign({}, pre, {team: FOTO.team}), SCHEMA);
    log.add('system', 'output_validated', meetingId, 'ok', `${output.validation_notes.length} correction(s)`);
    log.add('agent', 'proposals_generated', pre.opp.opportunity_id || 'new opportunity', 'ok', output.fields.map(f => `${f.field}=${f.status}`).join(', '));
    events = log.events;
  }
  const run = {id: runId, meetingId, userId: S.user, mode, model, createdAt: isoLocal(), stageAtRun: pre.opp ? stageOf(pre.opp) : null,
    output, log: events, decisions: {}, autoRecord: null, autoPending: [], record: null, status: output.run_status, submittedAt: null};
  S.runs[runId] = run; S.runOrder.unshift(runId); S.lastRun = runId;
  if (output.run_status !== 'Blocked') { autoApply(run); logTo(run, S.user, 'review_ready', output.opportunity_id || 'new opportunity', 'ok'); }
  save();
  if (!opts.silent) { setJob('pronto'); location.hash = '#/review/' + runId; }
  return runId;
}
/** "Always allow": those fields are written as soon as the update is prepared (or with the new opportunity, when it needs approval). */
function autoApply(run) {
  const out = run.output;
  const auto = CORE.autoFields(out, SCHEMA, perms());
  const fresh = isNewTarget(out);
  const createAuto = fresh && perms().create_opportunity === 'auto';
  if (fresh && !createAuto) { run.autoPending = auto; return; }
  if (!auto.length && !createAuto) return;
  const decisions = Object.fromEntries(auto.map(k => [k, {decision: 'approve', auto: true}]));
  if (createAuto) decisions.__create__ = {decision: 'approve', auto: true};
  const log = CORE.newLog(run.id, isoLocal);
  const now = isoLocal();
  const rec = CORE.applyApprovedFields({output: out, decisions, crm: S.crm, reviewerId: S.user, log, schema: SCHEMA, team: FOTO.team, runId: run.id, now, only: auto});
  log.events.forEach(ev => run.log.push(Object.assign({}, ev, {seq: run.log.length + 1})));
  run.autoRecord = rec; run.autoAt = now;
  if (createAuto) run.decisions.__create__ = decisions.__create__;
  if (!pendingFields(run).length) { run.record = rec.slice(); run.submittedAt = now; run.status = CORE.statusAfterSubmit(run.record); }
}
function logTo(run, actor, action, object_id, outcome, detail) {
  run.log.push({run_id: run.id, seq: run.log.length + 1, timestamp: isoLocal(), actor, action, object_id, outcome, detail: detail || ''});
}
function decide(runId, field, decision, value, reason) {
  const run = S.runs[runId];
  if (!run || run.record) return;
  run.decisions[field] = {decision, value: value == null ? undefined : value, reason: reason == null ? undefined : reason};
  UI.editing = null; save(); renderReview(runId);
}
function decideCreate(runId, decision) {
  const run = S.runs[runId];
  if (!run || run.record) return;
  const t = run.output.target;
  const client = ($('#no-client') || {}).value, name = ($('#no-name') || {}).value;
  if (decision === 'approve' && !t.client_id && !String(client || t.client_name || '').trim()) { toast('Name the client first', 'neu'); return; }
  run.decisions.__create__ = {decision, client_name: (client || t.client_name || '').trim(), opportunity_name: (name || t.opportunity_name || '').trim()};
  save(); renderReview(runId);
}
function decideGroup(runId, group) {
  const run = S.runs[runId];
  if (!run || run.record) return;
  pendingFields(run).filter(f => f.group === group && f.status === 'proposed' && !run.decisions[f.field]).forEach(f => { run.decisions[f.field] = {decision: 'approve'}; });
  UI.editing = null; save(); renderReview(runId);
}
function undecide(runId, field) {
  const run = S.runs[runId];
  if (!run || run.record) return;
  delete run.decisions[field]; UI.editing = null; save(); renderReview(runId);
}
function submitRun(runId) {
  const run = S.runs[runId];
  if (!run || run.record || run.status === 'Blocked') return;
  const pend = pendingFields(run);
  const missing = pend.filter(f => !run.decisions[f.field]);
  const fresh = isNewTarget(run.output);
  if (fresh && !run.decisions.__create__) { toast('Approve or reject the new opportunity first', 'neu'); return; }
  if (missing.length) { toast(`Decide on ${DEF[missing[0].field].label} first · ${plural(missing.length, 'decision', 'decisions')} left`, 'neu'); return; }
  const decisions = Object.assign({}, run.decisions);
  (run.autoPending || []).forEach(k => { decisions[k] = {decision: 'approve', auto: true}; });
  const only = pend.map(f => f.field).concat(run.autoPending || []);
  const now = isoLocal();
  const log = CORE.newLog(runId, isoLocal);
  let record;
  try {
    record = CORE.applyApprovedFields({output: run.output, decisions, crm: S.crm, reviewerId: S.user, log, schema: SCHEMA, team: FOTO.team, runId, now, only});
  } catch (err) { toast('Submit refused · ' + err.message, 'bad'); return; }
  log.events.forEach(ev => run.log.push(Object.assign({}, ev, {seq: run.log.length + 1})));
  run.record = (run.autoRecord || []).concat(record); run.submittedAt = now; run.status = CORE.statusAfterSubmit(run.record);
  if (fresh && run.output.opportunity_id) { const m = meetingById(run.meetingId); const sm = S.meetings.find(x => x.meeting_id === run.meetingId); if (sm) { sm.linked_opportunity_id = run.output.opportunity_id; sm.client_id = run.output.client_id; } if (m) m.linked_opportunity_id = run.output.opportunity_id; }
  save(); renderReview(runId); renderNav();
  const writes = record.filter(r => r.write_result === 'Succeeded').length;
  const created = fresh && run.output.opportunity_id;
  toast(created ? `Created ${clientOf(oppById(run.output.opportunity_id)).name} · ${oppById(run.output.opportunity_id).name} · ${plural(writes, 'field', 'fields')} written`
    : writes ? `Written to the CRM · ${plural(writes, 'field', 'fields')}` : 'Nothing written', writes || created ? 'ok' : 'neu',
  run.output.opportunity_id ? {label: 'Open the record', hash: '#/opportunities/' + run.output.opportunity_id} : null);
}
function undoAuto(runId, field) {
  const run = S.runs[runId];
  const item = run && (run.autoRecord || []).find(r => r.field === field);
  if (!item || item.reverted_at) return;
  const log = CORE.newLog(runId, isoLocal);
  try { CORE.revertWrite({item, output: run.output, crm: S.crm, reviewerId: S.user, log, now: isoLocal()}); } catch (err) { toast(err.message, 'bad'); return; }
  log.events.forEach(ev => run.log.push(Object.assign({}, ev, {seq: run.log.length + 1})));
  if (run.record) { const r2 = run.record.find(r => r.field === field); if (r2 && r2 !== item) Object.assign(r2, {reverted_at: item.reverted_at, reverted_by: item.reverted_by}); }
  save(); renderReview(runId);
  toast(`${DEF[field].label}: undone · the previous value is back`, 'ok');
}
function confirmEnded(meetingId) {
  const m = meetingById(meetingId);
  if (!m) return;
  S.confirmed[meetingId] = {by: me().name, at: isoLocal()};
  S.events.unshift({at: isoLocal(), user: S.user, kind: 'confirm', meetingId, text: `${me().name} confirmed that "${m.title}" ended there`});
  save();
}

// ------------------------------------------------------------------ job pill, toast, nav
function setJob(estado, t, s) {
  const job = $('#job'); if (!job) return;
  job.dataset.estado = estado;
  if (estado === 'rodando') { $('#job-t').textContent = t; $('#job-s').innerHTML = s || ''; return; }
  renderJob();
}
function renderJob() {
  const job = $('#job'); if (!job || job.dataset.estado === 'rodando') return;
  $('#job-t').textContent = 'Agent';
  job.dataset.on = claudeOn() ? '1' : '0';
  $('#job-s').textContent = !LIVE.checked ? 'checking the connection' : claudeOn() ? modelName(S.settings.model)
    : LIVE.ok ? 'server without a Claude key · sample transcripts only' : 'offline · sample transcripts only';
}
let toastTimer = null;
function toast(text, kind, action) {
  const t = $('#toast'); if (!t) return;
  $('#toast-k').className = 'tk' + (kind === 'bad' ? ' bad' : kind === 'neu' ? ' neu' : '');
  $('#toast-k').innerHTML = ico(kind === 'bad' ? 'x' : kind === 'neu' ? 'circle-minus' : 'check');
  $('#toast-tx').textContent = text;
  const b = $('#toast-act');
  if (action) { b.hidden = false; b.textContent = action.label; b.onclick = () => { location.hash = action.hash; hideToast(); }; }
  else { b.hidden = true; b.onclick = null; }
  t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(hideToast, 7000);
}
function hideToast() { const t = $('#toast'); if (t) t.hidden = true; }
function renderNav() {
  const u = me();
  $('#who').textContent = u.name;
  $('#uav-i').textContent = initials(u.name); $('#umenu-nm').textContent = u.name; $('#umenu-role').textContent = u.role;
  $('#umenubtn').setAttribute('aria-label', 'Account of ' + u.name); $('#umenubtn').title = u.name;
  const wait = allRuns().filter(r => r.userId === S.user && waiting(r)).length;
  const nm = $('#nav-meetings-n'); nm.textContent = wait || ''; nm.className = 'nav-n' + (wait ? ' hot' : '');
  nm.title = wait ? plural(wait, 'CRM update waiting for your review', 'CRM updates waiting for your review') : '';
  $('#nav-opps-n').textContent = myOpenOpps().length;
  $('#nav-clients-n').textContent = myClients().length;
  $$('.pi[data-user]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.user === S.user)));
  const mine = S.chats.filter(c => c.user === S.user).slice(0, 4);
  $('#nav-chats').innerHTML = mine.map(c => `<button class="nav-i nav-c${view() === 'explore' && S.chatCurrent === c.id ? ' on' : ''}" type="button" data-chat="${e(c.id)}" title="${e(c.title)}">${ico('message-circle', 'ni')}<span class="lb">${e(c.title)}</span></button>`).join('');
  $$('#nav-chats [data-chat]').forEach(b => b.onclick = () => { S.chatCurrent = b.dataset.chat; save(); if (view() === 'explore') { renderExplore(); renderNav(); } else location.hash = '#/explore'; });
}

// ------------------------------------------------------------------ router
const UI = {editing: null, oppsStage: 'all', oppsQ: '', oppsOwner: '', oppsSort: 'due', clQ: '', clSort: 'name', actFilter: 'all', expanded: {}, quiet: {},
  setTab: 'permissions', draft: null, oppChoice: '', src: 'file', drawerRoute: null, asking: false};
const VIEWS = ['explore', 'meetings', 'review', 'opportunities', 'clients', 'settings'];
const TABS = ['permissions', 'agent', 'sources', 'team', 'activity', 'quality', 'data'];
const ALIAS = {calls: ['meetings'], opps: ['opportunities'], opp: ['opportunities', null], audit: ['settings', 'activity'], activity: ['settings', 'activity'],
  eval: ['settings', 'quality'], agent: ['settings', 'agent'], sources: ['settings', 'sources']};
function parseHash() {
  const parts = (location.hash || '#/explore').replace(/^#\/?/, '').split('/');
  return {v: parts[0] || 'explore', id: parts[1] ? decodeURIComponent(parts[1]) : null};
}
function view() { const v = parseHash().v; return ALIAS[v] ? ALIAS[v][0] : (VIEWS.includes(v) ? v : 'explore'); }
function route() {
  let {v, id} = parseHash();
  if (ALIAS[v]) {
    const [nv, tab] = ALIAS[v];
    const nid = v === 'opp' ? id : v === 'agent' && id === 'quality' ? 'quality' : tab;
    location.replace('#/' + nv + (nid ? '/' + encodeURIComponent(nid) : ''));
    return;
  }
  if (!VIEWS.includes(v)) v = 'explore';
  if (v === 'review' && !id && S.lastRun) { location.replace('#/review/' + S.lastRun); return; }
  // a new view (or another update in Review) starts at the top; a drawer opening over a list keeps the scroll
  const page = v + (v === 'review' || v === 'settings' ? '/' + id : '');
  if (UI.page && UI.page !== page) window.scrollTo(0, 0);
  UI.page = page;
  $$('.view').forEach(sec => { sec.hidden = sec.dataset.view !== v; });
  $$('.nav-i[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === v || (v === 'review' && b.dataset.view === 'meetings')));
  if (v === 'explore') renderExplore();
  else if (v === 'meetings') renderMeetings();
  else if (v === 'review') renderReview(id);
  else if (v === 'opportunities') { renderOpps(); if (id) openOppDrawer(id, true); }
  else if (v === 'clients') { renderClients(); if (id) openClientDrawer(id, true); }
  else if (v === 'settings') { if (TABS.includes(id)) UI.setTab = id; renderSettings(); }
  renderNav();
  const sec = $(`.view[data-view="${v}"]`);
  document.title = (sec.dataset.title || v) + ' · Orbita CRM';
  // focus moves to the view (screen readers announce it) without scrolling it under the sticky bar
  if (UI.navigated && !(id && (v === 'opportunities' || v === 'clients'))) sec.focus({preventScroll: true});
  UI.navigated = true;
}

// ------------------------------------------------------------------ chips and small renderers
const CH = {
  run: s => s === 'Awaiting review' ? '<span class="ch ch-warn">Awaiting review</span>' : s === 'Blocked' ? '<span class="ch ch-bad">Blocked</span>'
    : s === 'Rejected' ? '<span class="ch ch-neu">Rejected</span>' : `<span class="ch ch-ok">${e(s)}</span>`,
  field: s => s === 'proposed' ? '<span class="ch ch-info">proposed</span>' : s === 'contradictory' ? '<span class="ch ch-warn">contradictory</span>'
    : s === 'unchanged' ? '<span class="ch ch-neu">unchanged</span>' : s === 'off' ? '<span class="ch ch-nd">off</span>' : '<span class="ch ch-nd">no evidence</span>',
  decision: (d, by) => (by === 'permission' ? '<span class="ch ch-ok">Always allow</span>' : ({approve: '<span class="ch ch-ok">Approved</span>', edit: '<span class="ch ch-info">Edited</span>', reject: '<span class="ch ch-bad">Rejected</span>',
    keep: '<span class="ch ch-neu">Kept</span>', replace: '<span class="ch ch-info">Replaced</span>', clear: '<span class="ch ch-warn">Cleared</span>'})[d] || ''),
  write: (w, reverted) => reverted ? '<span class="ch ch-neu">Undone</span>' : w === 'Succeeded' ? '<span class="ch ch-ok">Written</span>' : w === 'Failed' ? '<span class="ch ch-bad">Failed</span>' : '<span class="ch ch-neu">Not written</span>',
  stage: s => `<span class="ch ch-neu">${e(s || 'no stage')}</span>`,
  src: m => { const s = (m.source || {}).system; return s === 'whatsapp' ? 'WhatsApp chat' : s === 'paste' ? 'pasted text' : s === 'granola' ? 'Granola' : 'transcript file'; },
  perm: p => `<span class="ch ${p === 'auto' ? 'ch-ok' : p === 'off' ? 'ch-nd' : 'ch-neu'}">${e((LEVELS.find(l => l.id === p) || {}).label || p)}</span>`,
};
function dueChip(o) {
  const d = fv(o, 'follow_up_due_date').value;
  if (!d) return '<span class="nada">no follow-up</span>';
  if (d < TODAY) return `<span class="ch ch-bad">overdue · ${e(fmtShort(d))}</span>`;
  const days = (Date.parse(d) - Date.parse(TODAY)) / 86400000;
  return days <= 2 ? `<span class="ch ch-warn">due ${e(fmtShort(d))}</span>` : `<span class="ch ch-neu">due ${e(fmtShort(d))}</span>`;
}
function valueOr(v, cls) { return v == null || v === '' ? '<span class="nada">empty</span>' : `<span class="${cls || ''}">${e(v)}</span>`; }
function apprMark(f) {
  if (f.value == null || f.value === '') return '';
  return f.approved ? `<span class="appr">${ico('check')}seller-approved</span>` : `<span class="appr no">${ico('circle-dashed')}not approved</span>`;
}
function oppTitle(o) {
  const c = clientOf(o);
  return `<span class="ttl">${logo(c ? c.name : '')}<span><b>${e(c ? c.name : o.client_id)}</b><span class="sub">${e(o.name)} · ${e(o.opportunity_id)}</span></span></span>`;
}
/** MEDDPICC: the eight letters, filled when the CRM holds the element. extra = keys known after this update. */
function mdpStrip(o, size, extra) {
  const m = CORE.meddpiccOf(SCHEMA, o || {fields: {}});
  const add = new Set(extra || []);
  const known = m.items.filter(i => i.known || add.has(i.key)).length;
  const cells = m.items.map(i => `<span class="mdp-c${i.known ? ' on' : add.has(i.key) ? ' add' : ''}" title="${e(i.label)}: ${i.known ? e(i.value) : add.has(i.key) ? 'proposed in this update' : 'unknown'}">${e(i.letter)}</span>`).join('');
  return `<span class="mdp${size === 'lg' ? ' mdp-lg' : ''}" role="img" aria-label="MEDDPICC ${known} of ${m.total} known">${cells}<span class="mdp-n">${known}/${m.total}</span></span>`;
}
function blockShort(s) {
  return ({Incomplete: 'transcript cut off', Unmatched: 'no opportunity for this conversation', AccessDenied: 'no access to the opportunity', Missing: 'no readable transcript'})[s] || s;
}
function runTarget(r) {
  const o = r.output;
  if (o.source_status === 'AccessDenied') return '';
  const opp = o.opportunity_id ? oppById(o.opportunity_id) : null;
  if (opp) return `${clientOf(opp).name} · ${opp.name}`;
  if (isNewTarget(o)) return `${o.target.client_name || 'new client'} (new opportunity)`;
  return '';
}

// ------------------------------------------------------------------ view: explore (questions about your pipeline)
function greeting() {
  const h = new Date().getHours();
  return `${h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'}, ${me().name.split(' ')[0]}`;
}
function runSummaries() {
  return allRuns().filter(r => r.userId === S.user && r.status !== 'Blocked').map(r => {
    const m = meetingById(r.meetingId) || {title: r.meetingId, start: r.createdAt};
    return {run_id: r.id, opportunity_id: r.output.opportunity_id, label: runTarget(r), title: m.title, date: String(m.start || '').slice(0, 10),
      at: r.submittedAt || r.createdAt, pending: waiting(r) ? pendingFields(r).length : 0,
      written: (r.record || r.autoRecord || []).filter(x => x.write_result === 'Succeeded' && !x.reverted_at).length,
      created: !!(r.output.target && r.output.target.created)};
  });
}
const exploreCtx = () => CORE.exploreContext({crm: S.crm, team: FOTO.team, user: me(), schema: SCHEMA, runs: runSummaries(), now: TODAY});
const currentChat = () => S.chats.find(c => c.id === S.chatCurrent && c.user === S.user) || null;
function msgHtml(msg) {
  if (msg.role === 'user') return `<li class="msg eu"><p>${e(msg.text)}</p></li>`;
  if (msg.pending) return `<li class="msg nex wait"><div class="msg-who">Orbita</div><p class="msg-v">Reading your CRM…</p></li>`;
  const a = msg.answer;
  const sugs = a.kind === 'none' ? `<p class="msg-sgh">Try one of these</p><ul class="sg-l msg-sg">${CORE.exploreSuggestions(exploreCtx()).map(sgHtml).join('')}</ul>` : '';
  return `<li class="msg nex"><div class="msg-who">Orbita</div><p class="msg-v">${e(a.verdict)}</p>
    ${a.findings.length ? `<ol class="msg-a">${a.findings.map(f => `<li>${e(f.text)}${(f.src || []).map(n => `<sup class="ref">${n}</sup>`).join('')}</li>`).join('')}</ol>` : ''}
    ${a.open ? `<p class="msg-ab"><b>Not settled yet:</b> ${e(a.open)}</p>` : ''}${sugs}
    ${a.sources && a.sources.length ? `<ol class="msg-f" aria-label="sources of this answer">${a.sources.map(s => `<li>${e(s)}</li>`).join('')}</ol>` : ''}
    ${a.actions && a.actions.length ? `<div class="msg-acts">${a.actions.map(x => x.opp ? `<button class="b b-sm b-s" type="button" data-ex-opp="${e(x.opp)}">${e(x.label)}</button>` : `<a class="b b-sm b-s" href="#/review/${e(x.run)}">${e(x.label)}</a>`).join('')}</div>` : ''}
    <div class="msg-m">${msg.via === 'rules' ? 'answered from your CRM data' : `answered by ${e(modelName(msg.via))} from your CRM data`}</div></li>`;
}
function sgHtml(s) {
  return `<li><button class="sg" type="button" data-q="${e(s.q)}">${s.client ? logo(s.client) : `<span class="sg-i">${ico('compass')}</span>`}<span class="sg-t">${e(s.q)}</span><span class="sg-k">${e(s.when)}</span></button></li>`;
}
function renderExplore() {
  const chat = currentChat();
  const has = !!(chat && chat.messages.length);
  const box = $('.ex');
  box.classList.toggle('ex-on', has);
  $('#ex-t').textContent = has ? chat.title : greeting();
  const th = $('#ex-thread');
  th.hidden = !has;
  th.innerHTML = has ? chat.messages.map(msgHtml).join('') : '';
  $('#ex-sg-box').hidden = has;
  if (!has) $('#ex-sg').innerHTML = CORE.exploreSuggestions(exploreCtx()).map(sgHtml).join('');
  $('#ex-src-t').textContent = claudeOn() ? `Your CRM · ${modelName(S.settings.model)}` : 'Your CRM';
  $('#ex-in').placeholder = has ? 'Ask a follow-up about your pipeline' : 'Ask about a client, an opportunity or your pipeline';
  $$('.ex [data-q]').forEach(b => b.onclick = () => askExplore(b.dataset.q));
  $$('.ex [data-ex-opp]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.exOpp));
  if (has) { const last = th.lastElementChild; if (last && UI.scrollChat) { UI.scrollChat = false; last.scrollIntoView({block: 'nearest'}); } }
}
async function askExplore(question) {
  const q = String(question || '').trim();
  if (!q || UI.asking) return;
  let chat = currentChat();
  if (!chat) {
    chat = {id: 'CH-' + (++S.seq.chat), user: S.user, title: q.length > 48 ? q.slice(0, 46) + '…' : q, at: isoLocal(), messages: []};
    S.chats.unshift(chat); S.chatCurrent = chat.id;
  }
  chat.messages.push({role: 'user', text: q, at: isoLocal()});
  const slot = {role: 'agent', pending: true};
  chat.messages.push(slot);
  $('#ex-in').value = '';
  UI.asking = true; UI.scrollChat = true; renderExplore(); renderNav();
  let answer = null, via = 'rules';
  if (claudeOn()) {
    setJob('rodando', 'Asking Claude', e(q.slice(0, 60)));
    try {
      const r = await fetch(API + '/api/explore', {method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({question: q, userId: S.user, crm: S.crm, runs: runSummaries(), now: TODAY, model: S.settings.model})});
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || ('server ' + r.status));
      answer = j.answer; via = j.model || 'rules';
    } catch (err) { toast('Claude did not answer (' + err.message + ') · answered from the CRM rules instead', 'neu'); }
    setJob('pronto');
  }
  if (!answer) answer = CORE.answerQuestion(q, exploreCtx());
  Object.assign(slot, {pending: false, answer, via, at: isoLocal()});
  UI.asking = false; UI.scrollChat = true; save(); renderExplore();
}
function newChat() { S.chatCurrent = null; save(); if (view() === 'explore') { renderExplore(); renderNav(); } else location.hash = '#/explore'; setTimeout(() => $('#ex-in').focus(), 0); }

// ------------------------------------------------------------------ view: meetings
function renderMeetings() {
  const ms = myMeetings().slice().sort((a, b) => (String(a.added_at || a.start) < String(b.added_at || b.start) ? 1 : -1));
  const wait = allRuns().filter(r => r.userId === S.user && waiting(r)).length;
  const n = (v, hot) => `<span class="v${v ? (hot ? ' hot' : '') : ' zero'}">${v}</span>`;
  $('#mt-strip').innerHTML = `<div class="st">${n(ms.length)}<span class="l">${ms.length === 1 ? 'meeting of yours' : 'meetings of yours'}</span></div>
    <div class="st">${n(wait, true)}<span class="l">${wait === 1 ? 'CRM update waiting for your review' : 'CRM updates waiting for your review'}</span></div>`;
  // Select your opportunity: detect, your open opportunities by client, or a new one
  const sel = $('#mt-opp');
  const byClient = {};
  myOpenOpps().forEach(o => { const c = clientOf(o); (byClient[c.name] = byClient[c.name] || []).push(o); });
  sel.innerHTML = `<option value="">Detect it from the transcript</option>`
    + Object.keys(byClient).sort().map(cn => `<optgroup label="${e(cn)}">${byClient[cn].map(o => `<option value="${e(o.opportunity_id)}">${e(o.name)} · ${e(stageOf(o))}</option>`).join('')}</optgroup>`).join('')
    + `<optgroup label="Not in your CRM yet"><option value="__new__">New opportunity…</option></optgroup>`;
  sel.value = UI.oppChoice || '';
  $('#mt-opp-h').textContent = UI.oppChoice === '__new__' ? 'The agent fills the new opportunity from the conversation; you name the client below.'
    : UI.oppChoice ? 'The update goes to this opportunity, whatever the transcript says.'
    : 'Leave it on detect: the agent finds the opportunity from the speakers and the company named in the conversation.';
  $$('.src-tabs [data-src]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.src === UI.src)));
  $('#drop').hidden = UI.src !== 'file';
  $('#paste').hidden = UI.src !== 'paste';
  $('#mt-add').hidden = isManager() && !ms.length ? false : false;
  $('#mt-n').textContent = plural(ms.length, 'meeting', 'meetings');
  const empty = isManager() ? 'As a manager you read the team\'s CRM; meetings are added by each seller.'
    : 'No meeting yet. Add a transcript or a chat export above: the agent prepares the CRM update.';
  $('#tb-meetings tbody').innerHTML = ms.length ? ms.map(m => {
    const run = latestRun(m.meeting_id);
    const opp = run && run.output.opportunity_id && run.output.source_status !== 'AccessDenied' ? oppById(run.output.opportunity_id) : (m.linked_opportunity_id && canRead(oppById(m.linked_opportunity_id)) ? oppById(m.linked_opportunity_id) : null);
    let oppHtml;
    if (opp) oppHtml = oppTitle(opp);
    else if (run && run.output.source_status === 'AccessDenied') oppHtml = '<span class="ch ch-nd" title="the conversation belongs to an opportunity you cannot read">no access</span>';
    else if (m.target) oppHtml = `<span class="ttl">${logo(m.target.client_name)}<span><b>${e(m.target.client_name || 'New client')}</b><span class="sub">new opportunity${run && run.output.target && run.output.target.created ? ' · created' : ''}</span></span></span>`;
    else oppHtml = '<span class="ch ch-nd">not linked</span>';
    const pend = run ? pendingFields(run).length : 0;
    const runHtml = !run ? '<span class="nada">not prepared</span>'
      : run.status === 'Blocked' ? `${CH.run('Blocked')}<div class="sub">${e(blockShort(run.output.source_status))}</div>`
      : waiting(run) ? `${CH.run('Awaiting review')}<div class="sub">${plural(pend, 'field to decide', 'fields to decide')}${run.autoRecord && run.autoRecord.length ? ` · ${run.autoRecord.length} written automatically` : ''}</div>`
      : `${CH.run(run.status)}<div class="sub">${plural((run.record || []).filter(x => x.write_result === 'Succeeded' && !x.reverted_at).length, 'field written', 'fields written')}</div>`;
    const main = run ? `<a class="b b-sm b-row" href="#/review/${e(run.id)}">${run.status === 'Blocked' ? 'See reason' : waiting(run) ? 'Review update' : 'Open'}</a>`
      : `<button class="b b-sm b-row" type="button" data-run="${e(m.meeting_id)}">Prepare CRM update</button>`;
    return `<tr data-mtg="${e(m.meeting_id)}">
      <td><b>${e(m.title)}</b><div class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}${m.chat ? '' : m.recorded_minutes ? ` · ${e(m.recorded_minutes)} min` : ''}</div></td>
      <td class="mid">${oppHtml}</td>
      <td class="mid">${runHtml}</td>
      <td class="mid act-c"><span class="acts">${main}</span></td></tr>`;
  }).join('') : `<tr><td colspan="4"><div class="empty soft">${empty}</div></td></tr>`;
  $$('#tb-meetings [data-run]').forEach(b => b.onclick = () => startRun(b.dataset.run));
  renderDraft();
}
function readFile(file) {
  const rd = new FileReader();
  rd.onload = () => ingest(String(rd.result || ''), file.name, false);
  rd.readAsText(file);
}
function wireIntake() {
  const z = $('#drop'), inp = $('#drop-file');
  z.addEventListener('click', ev => { if (ev.target.closest('button,label,input')) return; inp.click(); });
  z.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); inp.click(); } });
  inp.addEventListener('change', () => { if (inp.files[0]) readFile(inp.files[0]); inp.value = ''; });
  ['dragenter', 'dragover'].forEach(k => z.addEventListener(k, ev => { ev.preventDefault(); z.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(k => z.addEventListener(k, ev => { ev.preventDefault(); z.classList.remove('over'); }));
  z.addEventListener('drop', ev => { const f = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0]; if (f) readFile(f); });
  $$('.src-tabs [data-src]').forEach(b => b.onclick = () => { UI.src = b.dataset.src; renderMeetings(); if (UI.src === 'paste') $('#paste-in').focus(); });
  const pin = $('#paste-in');
  pin.addEventListener('input', () => { const n = pin.value.split('\n').filter(x => x.trim()).length; $('#paste-n').textContent = n ? plural(n, 'line', 'lines') : ''; });
  $('#paste-go').onclick = () => { if (ingest(pin.value, 'pasted text', true)) { pin.value = ''; $('#paste-n').textContent = ''; } };
  $('#mt-opp').onchange = ev => { UI.oppChoice = ev.target.value; if (UI.draft) { UI.draft.newClient = null; UI.draft.newName = null; } renderMeetings(); };
}

// ------------------------------------------------------------------ view: review
function renderReview(runId) {
  const run = runId && S.runs[runId];
  const head = $('#rev-head'), body = $('#rev-body');
  body.dataset.run = run ? run.id : '';
  if (!run) {
    head.innerHTML = '<h1>Review</h1><div class="ph-c">no CRM update chosen</div>';
    body.innerHTML = '<div class="empty">Add a meeting in <a class="lk" href="#/meetings">Meetings</a>: the agent prepares the update, you review it here.</div>';
    return;
  }
  const o = run.output, m = meetingById(run.meetingId);
  const blocked = o.run_status === 'Blocked';
  const denied = blocked && o.source_status === 'AccessDenied';
  const opp = !denied && o.opportunity_id ? oppById(o.opportunity_id) : null;
  const cl = opp ? clientOf(opp) : null;
  const fresh = isNewTarget(o);
  const by = run.mode === 'live' ? `prepared by ${e(modelName(run.model))}` : run.mode === 'saved' ? 'saved result of a sample transcript' : 'stopped by the checks, before the agent';
  const known = o.fields.filter(f => DEF[f.field].meddpicc && (f.status === 'proposed' || f.status === 'unchanged')).map(f => f.field);
  const mdpBase = opp || {fields: {}};
  const mdp = blocked ? '' : (() => { const m2 = CORE.meddpiccOf(SCHEMA, mdpBase); const gaps = m2.gaps.filter(g => !known.includes(g.key));
    return `<div class="rev-mdp">${mdpStrip(mdpBase, 'lg', known)}<span class="mini">${gaps.length ? `Still unknown after this conversation: ${e(gaps.map(g => g.label).join(', '))}. Ask next: "${e(gaps[0].ask)}"` : 'Every MEDDPICC element is known after this conversation.'}</span></div>`; })();
  head.innerHTML = `
    <h1>${opp ? `${e(cl.name)} <span class="t3" style="font-weight:425">· ${e(opp.name)}</span>` : fresh ? `${e(o.target.client_name || 'New client')} <span class="t3" style="font-weight:425">· new opportunity</span>` : e(m ? m.title : run.meetingId)}</h1>
    <div class="hdr-facts">
      ${opp ? `<span class="kf">${logo(cl.name)}<b>${e(opp.opportunity_id)}</b></span><span class="kf">owner <b>${e(ownerName(opp))}</b></span><span class="kf">stage <b>${e(run.stageAtRun || stageOf(opp))}</b></span>` : ''}
      <span class="kf">${m ? `<b>${e(m.title)}</b> · ${e(fmtDate(m.start, false))} · ${e(CH.src(m))}` : e(run.meetingId)}</span>
      <span class="kf">${CH.run(run.status)}</span><span class="kf t3">${by}</span>
    </div>
    ${(o.warnings || []).map(w => `<div class="warnline">${ico('circle-help')}<span>${e(w)}</span></div>`).join('')}${mdp}`;
  if (blocked) {
    const act = o.source_status === 'Incomplete' ? `<button class="b b-sm b-s" type="button" id="rev-confirm">The meeting ended there: prepare the update</button>`
      : o.source_status === 'Unmatched' ? `<a class="b b-sm b-s" href="#/meetings">Choose the opportunity in Meetings</a>` : '';
    body.innerHTML = `
      <div class="pn"><div class="pn-h"><h2>Blocked before the agent</h2><span class="pn-n">${e(o.source_status)}</span></div>
        <div class="empty block soft" style="margin:14px 16px">${ico('circle-x', 'ico-b')}<div><b>${e(o.block_reason)}</b>
          <p>${denied ? 'The opportunity was not read and no field is shown. The attempt is recorded in the activity log.' : 'No proposal was generated and nothing was written. The check ran in code, before any call to the model.'}</p></div></div>
        <div class="pn-f row"><span>${plural(run.log.length, 'event', 'events')} recorded</span><span class="grow"></span>${act}<a class="b b-sm b-t" href="#/settings/activity">Activity log</a></div>
      </div>`;
    const c = $('#rev-confirm'); if (c) c.onclick = () => { confirmEnded(run.meetingId); startRun(run.meetingId); };
    return;
  }
  const done = !!run.record;
  const pend = pendingFields(run);
  const decided = pend.filter(f => run.decisions[f.field]).length;
  const createD = run.decisions.__create__;
  const needCreate = fresh && !createD;
  const groups = SCHEMA.groups.map(g => renderGroup(run, g, done)).join('');
  const stage = o.fields.find(f => f.field === 'stage');
  const autoN = (run.autoRecord || []).length + (run.autoPending || []).length;
  const notes = `
    <div class="notes">
      <div class="pn"><div class="pn-h"><h2>Stage note</h2></div><div class="pn-b">${stage && stage.note ? e(stage.note) : '<span class="nada">no note from the agent</span>'}</div></div>
      <div class="pn"><div class="pn-h"><h2>Ignored (out of scope)</h2><span class="pn-n">${o.ignored_out_of_scope.length}</span></div><div class="pn-b">${o.ignored_out_of_scope.length
        ? `<ul>${o.ignored_out_of_scope.map(x => `<li><span class="q">${e(x.quote)}</span><span class="why">${e(x.speaker)} · ${e(x.reason)}</span></li>`).join('')}</ul>`
        : '<span class="nada">nothing out of scope in this conversation</span>'}</div></div>
      <div class="pn"><div class="pn-h"><h2>Validator notes</h2><span class="pn-n">${o.validation_notes.length}</span></div><div class="pn-b">${o.validation_notes.length
        ? `<ul>${o.validation_notes.map(x => `<li>${e(x)}</li>`).join('')}</ul>` : '<span class="nada">0 corrections: every quote was found on its line and every value passed the field rules</span>'}</div></div>
    </div>`;
  const creation = fresh || (o.target && o.target.created) ? renderCreation(run, done) : '';
  const left = pend.length - decided + (needCreate ? 1 : 0);
  const foot = done
    ? `<div class="rev-foot"><span class="cnt"><b>${e(run.status)}</b> · ${e(fmtDate(run.submittedAt))} · ${plural(run.record.filter(r => r.write_result === 'Succeeded' && !r.reverted_at).length, 'field written', 'fields written')}</span><span class="grow"></span>
        ${o.opportunity_id ? `<a class="b b-sm b-s" href="#/opportunities/${e(o.opportunity_id)}">${ico('id-card')}Open the CRM record</a>` : ''}<a class="b b-sm b-t" href="#/settings/activity">Activity log</a></div>`
    : `<div class="rev-foot"><span class="cnt"><b>${decided + (fresh && createD ? 1 : 0)} of ${pend.length + (fresh ? 1 : 0)}</b> decisions made${left ? ` · ${plural(left, 'decision', 'decisions')} left` : ' · ready to submit'}${autoN ? ` · ${plural(autoN, 'field', 'fields')} under Always allow` : ''}</span><span class="grow"></span>
        <button class="b b-p" type="button" id="rev-submit"${left ? ' disabled' : ''} title="${left ? 'every field that waits for you needs a decision first' : 'write the approved values to the CRM'}">Submit to CRM</button></div>`;
  body.innerHTML = `${creation}
    <div class="pn"><div class="pn-h"><h2>Proposed update</h2><span class="pn-n">${plural(pend.length, 'field to decide', 'fields to decide')}${autoN ? ` · ${autoN} under Always allow` : ''}</span>
      <span class="pn-d">${done ? 'written values are marked seller-approved in the CRM' : 'fields that need approval are written only when you submit'}</span></div>
      <div class="tbw"><table class="tb" id="tb-rev"><thead><tr><th>Field</th><th>Current value</th><th>Proposed value</th><th>Evidence</th><th>${done ? 'Decision · result' : 'Decision'}</th></tr></thead>${groups}</table></div>
      ${foot}</div>
    ${notes}`;
  wireReview(run);
}
function renderCreation(run, done) {
  const o = run.output, t = o.target, d = run.decisions.__create__;
  const created = t && t.created;
  const perm = perms().create_opportunity;
  let dec;
  if (created) dec = `<div class="dres">${CH.decision(d && d.decision || 'approve', created.auto ? 'permission' : 'seller')}<span class="ch ch-ok">Created</span><a class="lk" href="#/opportunities/${e(created.opportunity_id)}">${e(created.opportunity_id)}</a></div>`;
  else if (done) dec = `<div class="dres">${CH.decision(d ? d.decision : 'reject')}<span class="ch ch-neu">Not created</span></div>`;
  else if (d) dec = `<div class="dres">${CH.decision(d.decision)}<button class="b b-t chg" type="button" data-undo-create title="take the decision back">change</button></div>`;
  else dec = `<span class="acts"><button class="b b-sm b-row" type="button" data-create="approve">Approve creation</button><button class="b b-sm b-t" type="button" data-create="reject">Reject</button></span>`;
  const editable = !created && !done && !d;
  const cname = d && d.client_name ? d.client_name : t.client_name, oname = d && d.opportunity_name ? d.opportunity_name : t.opportunity_name;
  return `<div class="pn newopp" id="rev-new"><div class="pn-h"><h2>${t.client_id ? 'New opportunity' : 'New client and opportunity'}</h2>
      <span class="pn-n">${created ? `created ${created.auto ? 'automatically (Always allow)' : 'on approval'}` : perm === 'ask' ? 'needs your approval · the fields are written only if you approve it' : ''}</span></div>
    <div class="no-b">
      ${editable && !t.client_id ? `<label class="fld"><span class="fld-l">Client</span><input class="inp" id="no-client" value="${e(cname)}"></label>` : `<div class="fld"><span class="fld-l">Client</span><span class="fld-v">${logo(cname)}${e(cname)}${t.client_id ? ' <span class="mini">already in the CRM</span>' : ''}</span></div>`}
      ${editable ? `<label class="fld"><span class="fld-l">Opportunity name</span><input class="inp" id="no-name" value="${e(oname)}"></label>` : `<div class="fld"><span class="fld-l">Opportunity</span><span class="fld-v">${e(oname)}</span></div>`}
      <div class="fld"><span class="fld-l">Owner · stage</span><span class="fld-v">${e(me().name)} · ${e(STAGES[0])}</span></div>
      ${(t.contacts || []).length ? `<div class="fld"><span class="fld-l">Contacts from the conversation</span><span class="fld-v">${e(t.contacts.join(', '))}</span></div>` : ''}
      <div class="no-dec">${dec}</div>
    </div></div>`;
}
function renderGroup(run, g, done) {
  const fs = run.output.fields.filter(f => f.group === g.id);
  if (!fs.length) return '';
  const pend = new Set(pendingFields(run).map(f => f.field));
  const autoSet = new Set(autoDone(run).concat(run.autoPending || []));
  const act = fs.filter(f => pend.has(f.field));
  const quiet = fs.filter(f => !CORE.ACTIONABLE.includes(f.status) && f.field !== 'stage');
  const open = UI.quiet[run.id + '|' + g.id];
  const pendingApprove = done ? 0 : act.filter(f => f.status === 'proposed' && !run.decisions[f.field]).length;
  const rows = fs.map(f => renderFieldRow(run, f, done, quiet.includes(f) && !open, autoSet.has(f.field))).join('');
  const sum = quiet.length ? `<tr class="qsum"><td colspan="5"><button class="lnk" type="button" data-quiet="${e(g.id)}" aria-expanded="${open ? 'true' : 'false'}">${open ? 'Hide' : 'Show'} ${quiet.length}: ${quiet.map(f => `${e(DEF[f.field].label)} (${f.status === 'unchanged' ? 'unchanged' : f.status === 'off' ? 'off' : 'no evidence'})`).join(', ')}</button></td></tr>` : '';
  const autoN = fs.filter(f => autoSet.has(f.field)).length;
  return `<tbody class="rg" data-group="${e(g.id)}">
    <tr class="grp"><th colspan="5"><div class="grp-in"><span class="grp-t">${e(g.label)}</span><span class="grp-n">${act.length ? plural(act.length, 'to decide', 'to decide') : 'nothing to decide'}${autoN ? ` · ${autoN} always allowed` : ''}${quiet.length ? ' · ' + quiet.length + ' quiet' : ''}</span><span class="grow"></span>${pendingApprove > 1 ? `<button class="b b-xs b-s" type="button" data-approve-group="${e(g.id)}">Approve ${pendingApprove} in ${e(g.label.replace(/ \(.*\)$/, ''))}</button>` : ''}</div></th></tr>
    ${rows}${sum}</tbody>`;
}
function renderFieldRow(run, f, done, hide, isAuto) {
  const def = DEF[f.field];
  const d = run.decisions[f.field];
  const rec = (run.record || run.autoRecord || []).find(r => r.field === f.field) || null;
  const kind = (def.meddpicc ? `MEDDPICC ${def.meddpicc} · ` : '') + (def.kind === 'per_call' ? 'this conversation' : 'state') + (def.record === 'client' ? ' · client record' : '');
  const cur = `<div class="cur"><span class="val${f.status === 'contradictory' ? ' kept' : ''}">${valueOr(f.current_value)}</span>${f.current_value != null
    ? (f.current_approved ? `<span class="appr">${ico('check')}seller-approved</span>` : `<span class="appr no">${ico('circle-dashed')}not approved</span>`) : ''}</div>`;
  let prop;
  if (f.status === 'proposed' || f.status === 'unchanged') {
    const edited = d && d.decision === 'edit' && d.value != null;
    prop = `<div class="prop">${CH.field(f.status)}${edited ? `<span class="val strike" title="agent proposal, replaced by the seller">${e(f.proposed_value)}</span><span class="lab"><b>edited by ${e(userById(run.userId).name)}</b></span><span class="val">${e(d.value)}</span>` : `<span class="val">${e(f.proposed_value)}</span>`}${f.note ? `<span class="lab">${e(f.note)}</span>` : ''}</div>`;
  } else if (f.status === 'contradictory') {
    const rep = d && d.decision === 'replace' ? `<span class="lab"><b>replacement by the seller</b></span><span class="val">${e(d.value)}</span>` : d && d.decision === 'clear' ? '<span class="lab"><b>cleared by the seller</b></span>' : '';
    prop = `<div class="prop">${CH.field(f.status)}<span class="lab">The conversation contradicts the approved value and agrees no new one. ${f.note ? e(f.note) : ''}</span>${rep}</div>`;
  } else {
    prop = `<div class="prop">${CH.field(f.status)}<span class="lab">${f.note ? e(f.note) : 'Not discussed, vague or only implied. The current value stays.'}</span></div>`;
  }
  const ev = f.evidence.length ? `<div class="ev">${f.evidence.map(x => `<button class="evb" type="button" data-ev="${e(run.meetingId)}|${e(x.line)}" title="show this line in the transcript"><q>${e(x.quote)}</q><span class="evm">${x.timestamp && x.timestamp !== '00:00:00' ? `<time>${e(/^\d{4}-/.test(x.timestamp) ? fmtShort(x.timestamp) + ' ' + x.timestamp.slice(11) : x.timestamp)}</time>` : ''}<span>${e(x.speaker)}</span></span></button>`).join('')}</div>`
    : '<span class="nada">no quote</span>';
  let dec;
  if (f.status === 'no_evidence') dec = '<div class="dec"><span class="ch ch-nd">No evidence</span><span class="note">nothing to decide</span></div>';
  else if (f.status === 'off') dec = '<div class="dec"><span class="ch ch-nd">Off</span><span class="note">turned off in Settings &gt; Permissions</span></div>';
  else if (f.status === 'unchanged') dec = '<div class="dec"><span class="ch ch-neu">Unchanged</span><span class="note">the conversation confirmed the approved value · nothing to write</span></div>';
  else if (isAuto && rec) dec = `<div class="dec"><div class="dres">${CH.decision('approve', 'permission')}${CH.write(rec.write_result, rec.reverted_at)}${!rec.reverted_at && rec.write_result === 'Succeeded' ? `<button class="b b-t chg" type="button" data-undo-auto title="put the previous value back">Undo</button>` : ''}</div></div>`;
  else if (isAuto) dec = `<div class="dec"><div class="dres">${CH.decision('approve', 'permission')}<span class="note">written with the new opportunity</span></div></div>`;
  else if (done && rec) dec = `<div class="dec"><div class="dres">${CH.decision(rec.seller_decision, rec.decided_by)}${CH.write(rec.write_result, rec.reverted_at)}${rec.rejection_reason ? `<span class="mini">reason: ${e(rec.rejection_reason)}</span>` : ''}</div></div>`;
  else dec = `<div class="dec">${renderDecision(run, f, d)}</div>`;
  return `<tr data-field="${e(f.field)}" data-status="${e(f.status)}"${isAuto ? ' data-auto="1"' : ''}${hide ? ' hidden' : ''}><td><span class="fname">${e(def.label)}</span><span class="fkind">${e(kind)}</span></td><td>${cur}</td><td>${prop}</td><td>${ev}</td><td>${dec}</td></tr>`;
}
function editorHtml(def, start) {
  const v = start == null ? '' : String(start);
  if (def.type === 'integer') return `<input class="inp" id="dec-text" type="number" min="1" step="1" value="${e(v)}">`;
  if (def.type === 'date') return `<input class="inp" id="dec-text" type="date" value="${e(v)}">`;
  if (def.type === 'month') return `<input class="inp" id="dec-text" type="month" value="${e(v)}">`;
  if (def.type === 'roster') return `<select class="inp" id="dec-text">${FOTO.team.map(u => `<option${u.name === v ? ' selected' : ''}>${e(u.name)}</option>`).join('')}</select>`;
  if (def.type === 'stage') return `<select class="inp" id="dec-text">${STAGES.map(s => `<option${s === v ? ' selected' : ''}>${e(s)}</option>`).join('')}</select>`;
  if (def.type === 'multi') {
    const on = v.split(/[;,]/).map(x => x.trim().toLowerCase());
    return `<div class="chkset" id="dec-multi" role="group" aria-label="${e(def.label)}">${SCHEMA.departments.map(o => `<label><input type="checkbox" value="${e(o)}"${on.includes(o.toLowerCase()) ? ' checked' : ''}>${e(o)}</label>`).join('')}</div>`;
  }
  if (def.type === 'budget' || def.type === 'person') return `<input class="inp" id="dec-text" value="${e(v)}">`;
  return `<textarea class="inp" id="dec-text" rows="3">${e(v)}</textarea>`;
}
function editorValue(def) {
  if (def.type === 'multi') return $$('#dec-multi input:checked').map(x => x.value).join('; ');
  return (($('#dec-text') || {}).value || '').trim();
}
function renderDecision(run, f, d) {
  const def = DEF[f.field];
  const ed = UI.editing && UI.editing.runId === run.id && UI.editing.field === f.field ? UI.editing.mode : null;
  if (ed === 'edit' || ed === 'replace') {
    const start = ed === 'edit' ? (d && d.value != null ? d.value : f.proposed_value) : (d && d.value != null ? d.value : (f.current_value || ''));
    return `<div class="edit"><span class="fld-l">${ed === 'edit' ? 'Edited value' : 'New value'} <i>${e(def.format)}</i></span>${editorHtml(def, start)}
      <span class="acts"><button class="b b-xs b-p" type="button" data-save="${ed}">Save</button><button class="b b-xs b-t" type="button" data-cancel>Cancel</button></span></div>`;
  }
  if (ed === 'reject') {
    return `<div class="edit"><label class="fld"><span class="fld-l">Reason <i>optional</i></span><input class="inp" id="dec-text" value="${e(d && d.reason || '')}" placeholder="why the proposal is wrong"></label>
      <span class="acts"><button class="b b-xs b-d" type="button" data-save="reject">Reject</button><button class="b b-xs b-t" type="button" data-cancel>Cancel</button></span></div>`;
  }
  if (d) {
    const extra = d.decision === 'reject' && d.reason ? `<span class="mini">reason: ${e(d.reason)}</span>` : '';
    return `<div class="dres">${CH.decision(d.decision)}${extra}<button class="b b-t chg" type="button" data-undo title="take the decision back">change</button></div>`;
  }
  if (f.status === 'proposed') {
    return '<span class="acts"><button class="b b-sm b-row" type="button" data-dec="approve">Approve</button><button class="b b-sm b-t" type="button" data-open="edit">Edit</button><button class="b b-sm b-t" type="button" data-open="reject">Reject</button></span>';
  }
  return '<span class="acts"><button class="b b-sm b-row" type="button" data-dec="keep" title="keep the current approved value">Keep</button><button class="b b-sm b-t" type="button" data-open="replace">Replace</button><button class="b b-sm b-t" type="button" data-dec="clear" title="clear the field in the CRM">Clear</button></span>';
}
function wireReview(run) {
  $$('#tb-rev tr[data-field]').forEach(tr => {
    const field = tr.dataset.field;
    $$('[data-dec]', tr).forEach(b => b.onclick = () => decide(run.id, field, b.dataset.dec));
    $$('[data-open]', tr).forEach(b => b.onclick = () => { UI.editing = {runId: run.id, field, mode: b.dataset.open}; renderReview(run.id); const x = $('#dec-text') || $('#dec-multi input'); if (x) x.focus(); });
    $$('[data-cancel]', tr).forEach(b => b.onclick = () => { UI.editing = null; renderReview(run.id); });
    $$('[data-undo]', tr).forEach(b => b.onclick = () => undecide(run.id, field));
    $$('[data-undo-auto]', tr).forEach(b => b.onclick = () => undoAuto(run.id, field));
    $$('[data-save]', tr).forEach(b => b.onclick = () => {
      const mode = b.dataset.save, def = DEF[field];
      if (mode === 'reject') { const v = (($('#dec-text') || {}).value || '').trim(); decide(run.id, field, 'reject', undefined, v || undefined); return; }
      const v = editorValue(def);
      const opp = run.output.opportunity_id ? oppById(run.output.opportunity_id) : null;
      const c = CORE.checkValue(def, v, {schema: SCHEMA, team: FOTO.team, current: opp ? stageOf(opp) : STAGES[0], seller: true});
      if (!c.ok) { toast(`${def.label}: ${c.why}`, 'bad'); return; }
      decide(run.id, field, mode, c.value);
    });
  });
  $$('#rev-body [data-create]').forEach(b => b.onclick = () => decideCreate(run.id, b.dataset.create));
  $$('#rev-body [data-undo-create]').forEach(b => b.onclick = () => { delete run.decisions.__create__; save(); renderReview(run.id); });
  $$('#tb-rev [data-approve-group]').forEach(b => b.onclick = () => decideGroup(run.id, b.dataset.approveGroup));
  $$('#tb-rev [data-quiet]').forEach(b => b.onclick = () => { const k = run.id + '|' + b.dataset.quiet; UI.quiet[k] = !UI.quiet[k]; renderReview(run.id); });
  $$('#tb-rev [data-ev]').forEach(b => b.onclick = () => { const [mtg, line] = b.dataset.ev.split('|'); openTranscript(mtg, +line); });
  const sb = $('#rev-submit'); if (sb) sb.onclick = () => submitRun(run.id);
}

// ------------------------------------------------------------------ transcript drawer
function openTranscript(meetingId, lineNo) {
  const m = meetingById(meetingId), dlg = $('#drw');
  if (!m || !dlg) return;
  const lines = CORE.transcriptLines(transcriptOf(m) || '');
  const bare = lines.every(l => l.timestamp === '00:00:00');
  $('#drw-t').textContent = m.title;
  $('#drw-m').textContent = `${fmtDate(m.start, false)} · ${CH.src(m)} · ${(m.participants || []).join(', ')}`;
  $('#drw-b').innerHTML = lines.length ? lines.map(l => {
    const hl = l.n === lineNo;
    const t = bare ? `L${l.n}` : m.chat ? l.timestamp.slice(11) : l.timestamp;
    return `<div class="tl${hl ? ' hl' : ''}"${hl ? ' id="tl-hl"' : ''}><time>${e(t)}</time><span><span class="who">${e(l.speaker)}${hl ? '<span class="tl-mark">evidence</span>' : ''}</span>${e(l.text)}</span></div>`;
  }).join('') : '<div class="empty">No transcript text for this meeting.</div>';
  if (!dlg.open) dlg.showModal();
  const hl = $('#tl-hl'); if (hl) { requestAnimationFrame(() => hl.scrollIntoView({block: 'center'})); setTimeout(() => hl.scrollIntoView({block: 'center'}), 60); }
}

// ------------------------------------------------------------------ view: opportunities (funnel by stage)
function lastWriteOf(oppId) {
  const by = {};
  allRuns().filter(r => r.output.opportunity_id === oppId).forEach(r => (r.record || r.autoRecord || []).forEach(x => { if (x.write_result === 'Succeeded' && !x.reverted_at && !by[x.field]) by[x.field] = r; }));
  return by;
}
function renderOpps() {
  const u = me();
  const readable = myOpenOpps();
  const q = UI.oppsQ.trim().toLowerCase();
  const owners = [...new Set(readable.map(o => o.owner_id))];
  const list = readable.filter(o => (!UI.oppsOwner || o.owner_id === UI.oppsOwner)
    && (!q || `${clientOf(o).name} ${o.name} ${o.opportunity_id}`.toLowerCase().includes(q)));
  const sortFn = {due: (a, b) => (fv(a, 'follow_up_due_date').value || '9999') < (fv(b, 'follow_up_due_date').value || '9999') ? -1 : 1,
    amount: (a, b) => (b.amount_usd || 0) - (a.amount_usd || 0), updated: (a, b) => (a.last_updated < b.last_updated ? 1 : -1),
    qual: (a, b) => CORE.meddpiccOf(SCHEMA, a).known - CORE.meddpiccOf(SCHEMA, b).known}[UI.oppsSort];
  const pipe = readable.reduce((s, o) => s + (o.amount_usd || 0), 0);
  const aw = readable.filter(o => awaitingFor(o.opportunity_id)).length;
  const overdue = readable.filter(o => { const d = fv(o, 'follow_up_due_date').value; return d && d < TODAY; }).length;
  const thin = readable.filter(o => CORE.meddpiccOf(SCHEMA, o).known < 4).length;
  const n = (v, hot) => `<span class="v${v ? (hot ? ' hot' : '') : ' zero'}">${v}</span>`;
  $('#opps-strip').innerHTML = `
    <div class="st">${n(readable.length)}<span class="l">${isManager() ? 'open opportunities (read access to all)' : 'open opportunities you own'}</span></div>
    <div class="st"><span class="v">${e(fmtUSD(pipe))}</span><span class="l">open pipeline <span class="t">(amount per year, set by the seller)</span></span></div>
    <div class="st">${n(overdue, true)}<span class="l">follow-ups overdue <span class="t">(on ${e(fmtShort(TODAY))})</span></span></div>
    <div class="st">${n(thin)}<span class="l">with fewer than 4 of 8 MEDDPICC elements known</span></div>`;
  $('#opps-ctx').innerHTML = `as <b>${e(u.name)}</b> · ${e(u.role)}${aw ? ` · ${plural(aw, 'update', 'updates')} waiting for your review` : ''}`;
  const byStage = Object.fromEntries(OPEN_STAGES.map(s => [s, list.filter(o => stageOf(o) === s).sort(sortFn)]));
  $('#opps-chips').innerHTML = `<button class="fchip" type="button" data-stage="all" aria-pressed="${UI.oppsStage === 'all'}">All <span class="n">${list.length}</span></button>`
    + OPEN_STAGES.map(s => `<button class="fchip" type="button" data-stage="${e(s)}" aria-pressed="${UI.oppsStage === s}">${e(s)} <span class="n">${byStage[s].length}</span></button>`).join('');
  $('#opps-owner-w').hidden = !isManager();
  $('#opps-owner').innerHTML = `<option value="">All owners</option>` + owners.map(id => `<option value="${e(id)}"${UI.oppsOwner === id ? ' selected' : ''}>${e(userById(id).name)}</option>`).join('');
  $('#opps-sort').value = UI.oppsSort;
  if ($('#opps-q').value !== UI.oppsQ) $('#opps-q').value = UI.oppsQ;
  $('#opps-groups').innerHTML = OPEN_STAGES.map((s, i) => {
    const rows = byStage[s];
    const sum = rows.reduce((t, o) => t + (o.amount_usd || 0), 0);
    return `<section class="fg" data-stage="${e(s)}"${UI.oppsStage !== 'all' && UI.oppsStage !== s ? ' data-fora="1"' : ''}>
      <h2 class="fg-h"><span class="mk mk-${i}" aria-hidden="true"></span>${e(s)}<span class="ch ch-neu fg-n" data-n>${rows.length}</span><span class="fg-sum">${rows.length ? e(fmtUSD(sum)) : 'no amount'}</span></h2>
      ${rows.length ? `<ul class="fg-l">${rows.map(o => oppRow(o)).join('')}</ul>` : `<p class="fg-empty">No opportunities in ${e(s)}.</p>`}</section>`;
  }).join('');
  $$('#opps-chips .fchip').forEach(b => b.onclick = () => { UI.oppsStage = b.dataset.stage; renderOpps(); });
  $$('#opps-groups [data-details]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.details));
}
function oppRow(o) {
  const aw = awaitingFor(o.opportunity_id);
  const byRun = Object.values(lastWriteOf(o.opportunity_id))[0];
  const ns = fv(o, 'next_step').value;
  return `<li class="fr rowh" data-opp="${e(o.opportunity_id)}">
    <span class="fr-c">${oppTitle(o)}</span>
    <span class="fr-c">${e(ownerName(o))}</span>
    <span class="fr-c fr-num"><b>${e(fmtUSD(o.amount_usd))}</b><span class="sub">${o.close_date ? 'closes ' + e(fmtShort(o.close_date)) : 'no close date'}</span></span>
    <span class="fr-c">${dueChip(o)}<span class="sub fr-ns">${ns ? e(ns) : 'no next step'}</span></span>
    <span class="fr-c">${mdpStrip(o)}<span class="sub">${byRun ? 'updated ' + e(fmtShort(o.last_updated)) + ' by an update' : 'updated ' + e(fmtShort(o.last_updated))}</span></span>
    <span class="fr-c fr-act">${aw ? `<a class="b b-sm b-t" href="#/review/${e(aw.id)}">Review update</a>` : ''}<button class="b b-sm b-row" type="button" data-details="${e(o.opportunity_id)}">Details</button></span>
  </li>`;
}
function csvCell(v) { v = v == null ? '' : String(v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
function exportCrm() {
  const od = SCHEMA.fields.filter(d => d.record === 'opportunity'), cd = SCHEMA.fields.filter(d => d.record === 'client');
  const head = ['opportunity_id', 'client_id', 'client', 'name', 'owner_id', 'owner', 'amount_usd', 'close_date', 'last_updated']
    .concat(od.flatMap(d => [d.key, d.key + '_approved']), cd.flatMap(d => ['client_' + d.key, 'client_' + d.key + '_approved']));
  const rows = opps().map(o => {
    const c = clientOf(o);
    return [o.opportunity_id, o.client_id, c.name, o.name, o.owner_id, ownerName(o), o.amount_usd, o.close_date, o.last_updated]
      .concat(od.flatMap(d => { const f = fv(o, d.key); return [f.value, f.approved ? 'TRUE' : 'FALSE']; }), cd.flatMap(d => { const f = fv(c, d.key); return [f.value, f.approved ? 'TRUE' : 'FALSE']; }))
      .map(csvCell).join(',');
  });
  download('orbita_crm_opportunities.csv', [head.join(',')].concat(rows).join('\n') + '\n', 'text/csv');
  toast('CRM exported · orbita_crm_opportunities.csv (one row per opportunity, with its client profile)', 'ok');
}
function download(name, text, type) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type: type || 'text/plain'})); a.download = name; document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
}

// ------------------------------------------------------------------ opportunity drawer (the record)
function fieldsDl(rec, defs, lw) {
  return `<dl class="kv">${defs.map(d => {
    const f = fv(rec, d.key), w = lw && lw[d.key];
    return `<div><dt>${d.meddpicc ? `<span class="mdp-l">${e(d.meddpicc)}</span>` : ''}${e(d.label)}</dt><dd>${valueOr(f.value)} ${apprMark(f)}${w ? `<span class="sub">written by update ${e(w.id)} · ${e(fmtDate(w.submittedAt || w.autoAt))}</span>` : ''}</dd></div>`;
  }).join('')}</dl>`;
}
function historyRows(oppId) {
  const rows = [];
  allRuns().filter(r => r.output.opportunity_id === oppId).forEach(r => (r.record || r.autoRecord || []).forEach(x => rows.push({r, x})));
  return rows;
}
function openOppDrawer(id, fromRoute) {
  const dlg = $('#opp-drw'), o = oppById(id);
  if (!dlg) return;
  if ($('#cli-drw').open) $('#cli-drw').close();
  UI.drawerRoute = fromRoute ? 'opportunities' : null;
  const idBox = $('#opp-drw-id'), body = $('#opp-drw-b');
  if (!o || !canRead(o)) {
    idBox.innerHTML = '<h2 id="opp-drw-t">Opportunity</h2>';
    body.innerHTML = `<div class="empty block">${ico('circle-x', 'ico-b')}<div><b>You do not have access to this opportunity.</b><p>${e(me().name)} can read ${me().access === 'own_opportunities' ? 'only the opportunities they own' : 'nothing in the CRM'}. No data has been shown.</p></div></div>`;
    if (!dlg.open) dlg.showModal();
    return;
  }
  const c = clientOf(o), lw = lastWriteOf(o.opportunity_id), aw = awaitingFor(o.opportunity_id);
  idBox.innerHTML = `<div class="ttl">${logo(c.name, 32)}<span><h2 id="opp-drw-t">${e(c.name)} · ${e(o.name)}</h2><span class="sub">${e(o.opportunity_id)} · owner ${e(ownerName(o))} · last updated ${e(fmtDate(o.last_updated))}</span></span></div>`;
  const due = fv(o, 'follow_up_due_date');
  const ms = myMeetings().filter(m => m.linked_opportunity_id === o.opportunity_id).sort((a, b) => (String(a.start) < String(b.start) ? 1 : -1));
  const hist = historyRows(o.opportunity_id);
  const mq = CORE.meddpiccOf(SCHEMA, o);
  body.innerHTML = `
    <div class="fid"><div class="facts">
      <div class="f"><div class="l">Stage</div><div class="v">${e(stageOf(o))}</div><div class="m">${fv(o, 'stage').approved ? 'seller-approved' : 'not approved'}</div></div>
      <div class="f"><div class="l">Amount</div><div class="v${o.amount_usd == null ? ' na' : ''}">${e(fmtUSD(o.amount_usd))}</div><div class="m">per year · set by the seller</div></div>
      <div class="f"><div class="l">Close date</div><div class="v${o.close_date ? '' : ' na'}">${o.close_date ? e(fmtShort(o.close_date)) : 'not set'}</div><div class="m">set by the seller</div></div>
      <div class="f"><div class="l">Next follow-up</div><div class="v${due.value ? '' : ' na'}">${due.value ? e(fmtShort(due.value)) : 'no date'}</div><div class="m">${e(fv(o, 'follow_up_owner').value || 'no owner')}</div></div></div></div>
    ${aw ? `<div class="pend">${ico('list-checks')}<span>A CRM update from <b>${e((meetingById(aw.meetingId) || {}).title || aw.meetingId)}</b> is waiting for your review.</span><a class="b b-sm b-row" href="#/review/${e(aw.id)}">Review update</a></div>` : ''}
    <section class="dsec dsec-mdp"><h3>Qualification · MEDDPICC <span class="mini">${mq.known} of ${mq.total} known</span></h3>
      <div class="mdp-row">${mdpStrip(o, 'lg')}</div>
      ${mq.gaps.length ? `<ol class="ask">${mq.gaps.slice(0, 3).map(g => `<li><b>${e(g.label)}</b> · ${e(g.ask)}</li>`).join('')}</ol>` : '<p class="mini pad">Every element holds a value. Coverage does not grade how strong each one is.</p>'}
      ${fieldsDl(o, MDP, lw)}</section>
    ${SCHEMA.groups.filter(g => g.id !== 'qualification').map(g => {
      const defs = SCHEMA.fields.filter(d => d.group === g.id && d.key !== 'stage');
      if (!defs.length) return '';
      const rec = defs[0].record === 'client' ? c : o;
      return `<section class="dsec"><h3>${e(g.label)}${defs[0].record === 'client' ? ' <span class="mini">client record</span>' : ''}</h3>${fieldsDl(rec, defs, lw)}</section>`;
    }).join('')}
    <section class="dsec"><h3>Meetings <span class="mini">transcripts and chats</span></h3>${ms.length ? `<ul class="mlist">${ms.map(m => { const r = latestRun(m.meeting_id); return `<li><span><b>${e(m.title)}</b><span class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}</span></span>${r ? CH.run(r.status) : '<span class="nada">not prepared</span>'}</li>`; }).join('')}</ul>` : '<p class="nada pad">No meeting added for this opportunity yet.</p>'}</section>
    <section class="dsec"><h3>History <span class="mini">changes written through CRM updates</span></h3>${hist.length ? `<table class="tb tb-hist"><thead><tr><th>Field</th><th>Before → after</th><th>Decision</th><th>Who · when</th></tr></thead><tbody>${hist.map(({r, x}) => `<tr><td><b>${e(DEF[x.field].label)}</b></td><td>${valueOr(x.previous_value)} → ${x.write_result === 'Succeeded' ? valueOr(x.final_value) : '<span class="nada">not written</span>'}${x.reverted_at ? '<div class="sub">undone</div>' : ''}</td><td>${CH.decision(x.seller_decision, x.decided_by)}</td><td>${e(userById(x.reviewer_id).name)}<div class="sub">${e(fmtDate(x.decided_at))} · ${e(r.id)}</div></td></tr>`).join('')}</tbody></table>` : '<p class="nada pad">No change written through a CRM update yet.</p>'}</section>`;
  if (!dlg.open) dlg.showModal();
}
function openClientDrawer(id, fromRoute) {
  const dlg = $('#cli-drw'), c = clientById(id);
  if (!dlg) return;
  if ($('#opp-drw').open) $('#opp-drw').close();
  UI.drawerRoute = fromRoute ? 'clients' : null;
  const idBox = $('#cli-drw-id'), body = $('#cli-drw-b');
  const readable = c ? opps().filter(o => o.client_id === c.client_id && canRead(o)) : [];
  if (!c || !readable.length) {
    idBox.innerHTML = '<h2 id="cli-drw-t">Client</h2>';
    body.innerHTML = `<div class="empty block">${ico('circle-x', 'ico-b')}<div><b>You do not have access to this client.</b><p>A client is visible when you can read at least one of its opportunities. No data has been shown.</p></div></div>`;
    if (!dlg.open) dlg.showModal();
    return;
  }
  idBox.innerHTML = `<div class="ttl">${logo(c.name, 32)}<span><h2 id="cli-drw-t">${e(c.name)}</h2><span class="sub">${[c.industry, c.hq, c.domain].filter(Boolean).map(e).join(' · ') || 'created from a conversation · profile to complete'}</span></span></div>`;
  const ms = myMeetings().filter(m => m.client_id === c.client_id).sort((a, b) => (String(a.start) < String(b.start) ? 1 : -1));
  body.innerHTML = `
    <section class="dsec"><h3>Company profile <span class="mini">client record</span></h3>${fieldsDl(c, SCHEMA.fields.filter(d => d.record === 'client'), null)}</section>
    <section class="dsec"><h3>Contacts <span class="mini">${plural(c.contacts.length, 'person', 'people')}</span></h3>${c.contacts.length ? `<table class="tb"><thead><tr><th>Name</th><th>Title</th><th>E-mail</th><th>Buying role</th></tr></thead><tbody>${c.contacts.map(p => `<tr><td><b>${e(p.name)}</b></td><td>${valueOr(p.title)}</td><td>${valueOr(p.email)}</td><td>${valueOr(p.buying_role)}</td></tr>`).join('')}</tbody></table>` : '<p class="nada pad">No contact yet.</p>'}</section>
    <section class="dsec"><h3>Opportunities <span class="mini">${readable.length}</span></h3><table class="tb"><thead><tr><th>Opportunity</th><th>Stage</th><th class="num">Amount</th><th>Owner</th><th></th></tr></thead><tbody>${readable.map(o => `<tr><td><b>${e(o.name)}</b><div class="sub">${e(o.opportunity_id)}</div></td><td>${CH.stage(stageOf(o))}</td><td class="num nw">${e(fmtUSD(o.amount_usd))}</td><td class="nw">${e(ownerName(o))}</td><td><button class="b b-sm b-row" type="button" data-details="${e(o.opportunity_id)}">Details</button></td></tr>`).join('')}</tbody></table></section>
    <section class="dsec"><h3>Recent meetings</h3>${ms.length ? `<ul class="mlist">${ms.map(m => `<li><span><b>${e(m.title)}</b><span class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}</span></span></li>`).join('')}</ul>` : '<p class="nada pad">No meeting of yours with this client yet.</p>'}</section>`;
  $$('#cli-drw-b [data-details]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.details));
  if (!dlg.open) dlg.showModal();
}
function onDrawerClose() {
  const back = UI.drawerRoute;
  UI.drawerRoute = null;
  const {v, id} = parseHash();
  if (back && id && (v === 'opportunities' || v === 'clients')) location.hash = '#/' + v;
}

// ------------------------------------------------------------------ view: clients (one card per client)
function lastMeetingOf(c) {
  const ms = myMeetings().filter(m => m.client_id === c.client_id).map(m => String(m.start || '').slice(0, 10)).sort();
  return ms.length ? ms[ms.length - 1] : null;
}
function renderClients() {
  const u = me();
  const q = UI.clQ.trim().toLowerCase();
  const openOf = c => opps().filter(o => o.client_id === c.client_id && canRead(o) && isOpen(o));
  const list = myClients().filter(c => !q || `${c.name} ${c.industry || ''} ${c.hq || ''} ${c.contacts.map(p => p.name + ' ' + p.title).join(' ')}`.toLowerCase().includes(q));
  const sorters = {name: (a, b) => a.name.localeCompare(b.name), pipeline: (a, b) => openOf(b).reduce((s, o) => s + (o.amount_usd || 0), 0) - openOf(a).reduce((s, o) => s + (o.amount_usd || 0), 0),
    recent: (a, b) => String(lastMeetingOf(b) || '').localeCompare(String(lastMeetingOf(a) || '')) || a.name.localeCompare(b.name)};
  list.sort(sorters[UI.clSort] || sorters.name);
  const openN = list.reduce((t, c) => t + openOf(c).length, 0);
  $('#cl-ctx').innerHTML = `${plural(list.length, 'client', 'clients')} · ${plural(openN, 'open opportunity', 'open opportunities')} · as <b>${e(u.name)}</b>${isManager() ? ' · reads all' : ' · clients where you own an opportunity'}`;
  if ($('#cl-q').value !== UI.clQ) $('#cl-q').value = UI.clQ;
  $('#cl-sort').value = UI.clSort;
  $('#cl-list').innerHTML = list.length ? list.map(c => {
    const os = opps().filter(o => o.client_id === c.client_id && canRead(o)).sort((a, b) => STAGES.indexOf(stageOf(b)) - STAGES.indexOf(stageOf(a)));
    const open = os.filter(isOpen), sum = open.reduce((s, o) => s + (o.amount_usd || 0), 0);
    const emp = fv(c, 'employee_count').value, cur = fv(c, 'current_solution').value, last = lastMeetingOf(c);
    const tags = [c.industry, c.hq, emp ? `${Number(emp).toLocaleString('en-US')} employees` : null, cur ? `today: ${cur}` : null].filter(Boolean);
    return `<article class="cl-card" data-client="${e(c.client_id)}" aria-labelledby="cl-h-${e(c.client_id)}">
      <header class="cl-h">${logo(c.name, 32)}<div class="cl-id"><h2 id="cl-h-${e(c.client_id)}">${e(c.name)}</h2>
        <div class="cl-f">${tags.length ? tags.map(t => `<span class="tag">${e(t)}</span>`).join('') : '<span class="nada">profile to complete</span>'}</div></div>
        <div class="cl-r"><span class="cl-sum"><b>${plural(open.length, 'open opportunity', 'open opportunities')}</b>${open.length ? ' · ' + e(fmtUSD(sum)) : ''}</span><span class="sub">${plural(c.contacts.length, 'contact', 'contacts')}${last ? ' · last meeting ' + e(fmtShort(last)) : ''}</span></div>
        <button class="b b-sm b-s" type="button" data-client-details="${e(c.client_id)}">Client details</button></header>
      <ul class="cl-ops">${os.map(o => `<li class="cl-op" data-opp="${e(o.opportunity_id)}">
        <span class="cl-on"><b>${e(o.name)}</b><span class="sub">${e(o.opportunity_id)}</span></span>
        <span>${CH.stage(stageOf(o))}</span>
        <span class="num"><b>${e(fmtUSD(o.amount_usd))}</b><span class="sub">${o.close_date ? 'closes ' + e(fmtShort(o.close_date)) : 'no close date'}</span></span>
        <span class="nw">${e(ownerName(o))}</span>
        <span>${dueChip(o)}</span>
        <span>${mdpStrip(o)}</span>
        <span class="cl-act"><button class="b b-sm b-row" type="button" data-details="${e(o.opportunity_id)}">Details</button></span></li>`).join('')}</ul>
    </article>`;
  }).join('') : '<div class="empty">No client matches.</div>';
  $$('#cl-list [data-details]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.details));
  $$('#cl-list [data-client-details]').forEach(b => b.onclick = () => openClientDrawer(b.dataset.clientDetails));
}

// ------------------------------------------------------------------ view: settings
function renderSettings() {
  $$('#set-tabs [data-tab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === UI.setTab)));
  ({permissions: renderPerms, agent: renderAgentTab, sources: renderSources, team: renderTeam, activity: renderActivity, quality: renderQuality, data: renderData})[UI.setTab]();
}
function pseg(name, value, attr) {
  return `<div class="pseg" role="radiogroup" aria-label="${e(name)}">${LEVELS.map(l => `<button type="button" role="radio" aria-checked="${String(value === l.id)}" ${attr}="${e(l.id)}" class="ps ps-${e(l.id)}" title="${e(l.help)}">${e(l.label)}</button>`).join('')}</div>`;
}
function renderPerms() {
  const P = perms();
  const count = id => FIELDS.filter(k => permOf(k) === id).length;
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><h2>What the agent may change in your CRM</h2><span class="pn-d">applies to every update the agent prepares for you · ${count('auto')} always allowed · ${count('ask')} need approval · ${count('off')} never</span></div>
      <div class="perm-legend">${LEVELS.map(l => `<div class="pl pl-${e(l.id)}"><b>${e(l.label)}</b><span>${e(l.help)}</span></div>`).join('')}</div>
      <div class="tbw"><table class="tb perm" id="tb-perm"><thead><tr><th>Field</th><th>What it holds</th><th>Permission</th></tr></thead>
      ${SCHEMA.groups.map(g => { const fs = SCHEMA.fields.filter(d => d.group === g.id); return `<tbody data-group="${e(g.id)}"><tr class="grp"><th colspan="3"><div class="grp-in"><span class="grp-t">${e(g.label)}</span><span class="grp-n">${LEVELS.map(l => { const n = fs.filter(d => permOf(d.key) === l.id).length; return n ? `${n} ${e(l.label.toLowerCase())}` : ''; }).filter(Boolean).join(' · ')}</span><span class="grow"></span><span class="grp-set">Set all ${pseg(g.label, fs.every(d => permOf(d.key) === permOf(fs[0].key)) ? permOf(fs[0].key) : null, 'data-pg-' + g.id)}</span></div></th></tr>
        ${fs.map(d => `<tr data-perm-field="${e(d.key)}"><td><span class="fname">${d.meddpicc ? `<span class="mdp-l">${e(d.meddpicc)}</span>` : ''}${e(d.label)}</span><span class="fkind">${d.kind === 'per_call' ? 'this conversation' : 'state'}${d.record === 'client' ? ' · client record' : ''}</span></td><td class="perm-d">${e(d.definition)}</td><td class="mid">${pseg(d.label, permOf(d.key), 'data-pf')}</td></tr>`).join('')}</tbody>`; }).join('')}
      </table></div>
      <div class="pn-f row"><span>Defaults: the conversation notes are always allowed; everything else needs your approval.</span><span class="grow"></span><button class="b b-sm b-t" type="button" id="perm-reset">Restore defaults</button></div></div>
    <div class="pn"><div class="pn-h"><h2>New opportunities</h2><span class="pn-d">when a conversation matches no open opportunity of yours</span></div>
      <div class="set-row"><div class="sl">Create the opportunity (and the client, when it is new)</div><div class="sv">${pseg('New opportunities', P.create_opportunity, 'data-pc')}
        <span class="mini">${P.create_opportunity === 'auto' ? 'Created as soon as the update is prepared, owned by you, at New Lead. Fields under Always allow are written into it.' : P.create_opportunity === 'ask' ? 'The review shows the new client and opportunity first; nothing is created until you approve it.' : 'The conversation is blocked: choose an existing opportunity in Meetings instead.'}</span></div></div></div>
    <div class="pn"><div class="pn-h"><h2>Always true, whatever you choose</h2></div><ul class="rules">${SCHEMA.permissions.fixed_rules.map(r => `<li>${ico('check')}<span>${e(r)}</span></li>`).join('')}<li>${ico('check')}<span>Every value carries the quote it comes from, and every write, automatic or not, is in the activity log with the time and the permission that allowed it.</span></li></ul></div>`;
  $$('#tb-perm [data-pf]').forEach(b => b.onclick = () => { const k = b.closest('tr').dataset.permField; P.fields[k] = b.dataset.pf; save(); renderPerms(); });
  SCHEMA.groups.forEach(g => $$(`#tb-perm [data-pg-${g.id}]`).forEach(b => b.onclick = () => { SCHEMA.fields.filter(d => d.group === g.id).forEach(d => { P.fields[d.key] = b.getAttribute('data-pg-' + g.id); }); save(); renderPerms(); }));
  $$('#set-body [data-pc]').forEach(b => b.onclick = () => { P.create_opportunity = b.dataset.pc; save(); renderPerms(); });
  $('#perm-reset').onclick = () => { S.settings.permissions = CORE.defaultPermissions(SCHEMA); save(); renderPerms(); toast('Permissions restored to the defaults', 'ok'); };
}
function renderAgentTab() {
  const res = FOTO.eval_results, labels = res ? res.labels : {};
  const conn = !LIVE.checked ? 'checking…' : LIVE.ok ? (LIVE.key ? 'connected · Claude key set on the server' : 'connected · no Claude key on the server (capstone/.env)') : 'not running';
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><h2>Connection</h2><span class="pn-d">the Claude key stays on the server; it never reaches this page</span></div>
      <div class="set-row"><div class="sl">Orbita server</div><div class="sv"><span><span class="dot ${LIVE.ok ? (LIVE.key ? 'ok' : 'warn') : 'bad'}" aria-hidden="true"></span>${e(conn)}</span>
        ${LIVE.ok ? '' : '<span class="mini">Start it from the capstone folder: <code>node mockups/server.mjs</code>, with <code>ANTHROPIC_API_KEY</code> in <code>capstone/.env</code>; then open <code>http://localhost:8787</code>.</span>'}
        <span class="acts"><button class="b b-sm b-s" type="button" id="ag-check">${ico('rotate-ccw')}Check again</button></span></div></div>
      <div class="set-row"><div class="sl">What happens now</div><div class="sv"><span>${claudeOn() ? `Every conversation you add is read by ${e(modelName(S.settings.model))}, and Explore answers with it.` : 'Without Claude, the agent reads only the sample transcripts (capstone/samples), from saved results, and Explore answers from rules over your CRM data.'}</span></div></div></div>
    <div class="pn"><div class="pn-h"><h2>Model</h2><span class="pn-d">used for new CRM updates and for Explore</span></div>
      <div class="set-row"><div class="sl">Claude model</div><div class="sv"><div class="radio" role="radiogroup" aria-label="model">${MODELS.map(m => { const l = labels[m.id]; return `<button class="seg" type="button" role="radio" aria-checked="${String(S.settings.model === m.id)}" data-model="${e(m.id)}">${e(m.name)}<span class="sub">${e(m.note)}${l ? ` · ${l.passed}/${l.total} test meetings · USD ${(l.cost_per_call_usd || 0).toFixed(3)} per meeting` : ''}</span></button>`; }).join('')}</div></div></div>
      <div class="set-row"><div class="sl">Effort</div><div class="sv"><div class="radio radio-row" role="radiogroup" aria-label="effort">${['low', 'medium', 'high'].map(x => `<button class="seg" type="button" role="radio" aria-checked="${String(S.settings.effort === x)}" data-effort="${x}">${x[0].toUpperCase() + x.slice(1)}</button>`).join('')}</div>
        <span class="mini">Higher effort reads more carefully, takes longer and costs more. Medium is the default.</span></div></div></div>`;
  $('#ag-check').onclick = () => { LIVE.checked = false; renderAgentTab(); probeServer(); };
  $$('#set-body [data-model]').forEach(b => b.onclick = () => { S.settings.model = b.dataset.model; save(); renderAgentTab(); renderJob(); });
  $$('#set-body [data-effort]').forEach(b => b.onclick = () => { S.settings.effort = b.dataset.effort; save(); renderAgentTab(); });
}
function renderSources() {
  const g = LIVE.granola, gLive = LIVE.ok && g && g.mode === 'live';
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><h2>Where conversations come from</h2><span class="pn-d">every source goes through the same reading, attribution and permissions</span></div>
      <div class="src-l">
        <div class="src-i"><span class="src-k">${ico('file-text', 'ico-b')}</span><div><b>Meeting transcripts</b><span class="mini">Upload or paste in Meetings: Teams, Zoom and Google Meet (.vtt), subtitles (.srt), Granola, Otter and Fathom (.txt), or plain "Name: text" lines.</span></div><span class="ch ch-ok">On</span></div>
        <div class="src-i"><span class="src-k">${ico('message-circle', 'ico-b')}</span><div><b>WhatsApp</b><span class="mini">In WhatsApp, open the chat, choose Export chat, Without media, and drop the .txt in Meetings. The agent finds the opportunity from the contact's name.</span></div><span class="ch ch-ok">On</span></div>
        <div class="src-i"><span class="src-k">${ico('audio-lines', 'ico-b')}</span><div><b>Granola</b><span class="mini">${gLive ? `Connected through the server · folder ${e(g.folder || 'not set')}${g.last_sync ? ' · last sync ' + e(fmtDate(g.last_sync)) : ''}` : 'Optional: syncs a Granola folder on its own. Needs the Business plan and, on the server, GRANOLA_API_KEY and GRANOLA_FOLDER (node mockups/server.mjs --granola-live). Without it, export the transcript from Granola and drop it in Meetings.'}</span></div>${gLive ? `<button class="b b-sm b-s" type="button" id="src-sync">${ico('rotate-ccw')}Sync now</button>` : '<span class="ch ch-nd">Not connected</span>'}</div>
        <div class="src-i soft"><span class="src-k">${ico('mail', 'ico-b')}</span><div><b>E-mail, Telegram, Messenger</b><span class="mini">Not available yet. They will go through the same reading and attribution.</span></div><span class="ch ch-nd">Later</span></div>
      </div></div>`;
  const sb = $('#src-sync'); if (sb) sb.onclick = syncGranola;
}
async function syncGranola() {
  if (!LIVE.ok) return;
  setJob('rodando', 'Syncing Granola', 'the folder of your account');
  try {
    const r = await fetch(API + '/api/granola/sync', {method: 'POST'});
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || ('server ' + r.status));
    let added = 0;
    for (const m of j.meetings || []) {
      if (S.meetings.some(x => x.meeting_id === m.meeting_id) || !j.transcripts[m.meeting_id]) continue;
      S.meetings.unshift(Object.assign({}, m, {organiser_id: S.user, added_at: isoLocal()})); S.transcripts[m.meeting_id] = j.transcripts[m.meeting_id]; added++;
    }
    S.granola = {synced: true, lastSync: isoLocal()}; save();
    toast(added ? `Granola · ${plural(added, 'meeting', 'meetings')} added to Meetings` : 'Granola is up to date', 'ok', added ? {label: 'Open Meetings', hash: '#/meetings'} : null);
  } catch (err) { toast('Granola sync failed · ' + err.message, 'bad'); }
  setJob('pronto');
}
function renderTeam() {
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><h2>Who is using Orbita CRM</h2><span class="pn-d">switch to see what each role can read</span></div>
      <div class="set-row"><div class="sl">Signed in as</div><div class="sv"><div class="radio" role="radiogroup" aria-label="user">${DEMO_USERS.map(id => userById(id)).map(u => `<button class="seg" type="button" role="radio" aria-checked="${String(u.user_id === S.user)}" data-user="${e(u.user_id)}">${e(u.name)}<span class="sub">${e(u.role)} · ${u.access === 'all_opportunities_read' ? 'reads every opportunity' : 'reads only their own opportunities'}</span></button>`).join('')}</div></div></div></div>
    <div class="pn"><div class="pn-h"><h2>Team roster</h2><span class="pn-d">the people the agent may name as follow-up owner</span></div>
      <div class="tbw"><table class="tb"><thead><tr><th>Name</th><th>Role</th><th>E-mail</th><th>Access</th></tr></thead><tbody>${FOTO.team.map(u => `<tr><td><b>${e(u.name)}</b></td><td>${e(u.role)}</td><td>${e(u.email)}</td><td>${u.access === 'all_opportunities_read' ? 'all opportunities' : 'own opportunities'}</td></tr>`).join('')}</tbody></table></div></div>`;
  $$('#set-body [data-user]').forEach(b => b.onclick = () => switchUser(b.dataset.user));
}
function runKind(r) { return r.status === 'Blocked' ? 'blocked' : r.record ? 'written' : 'awaiting'; }
function runSentence(r) {
  const m = meetingById(r.meetingId) || {title: r.meetingId}, u = userById(r.userId);
  const target = runTarget(r);
  if (r.status === 'Blocked') return {main: `Blocked: ${blockShort(r.output.source_status)}`, sub: `"${m.title}"${target ? ' · ' + target : ''} · ${u.name}`};
  if (!r.record) {
    const auto = (r.autoRecord || []).filter(x => x.write_result === 'Succeeded').length;
    return {main: `Agent prepared ${plural(pendingFields(r).length, 'field', 'fields')} for ${target}`, sub: `from "${m.title}"${auto ? ` · ${auto} written automatically` : ''} · waiting for review`};
  }
  const w = r.record.filter(x => x.write_result === 'Succeeded' && !x.reverted_at).length;
  const cnt = k => r.record.filter(x => x.seller_decision === k && x.decided_by !== 'permission').length;
  const autoW = r.record.filter(x => x.decided_by === 'permission' && x.write_result === 'Succeeded' && !x.reverted_at).length;
  const parts = [autoW && `${autoW} always allowed`, cnt('edit') + cnt('replace') && `${cnt('edit') + cnt('replace')} edited`, cnt('reject') && `${cnt('reject')} rejected`, cnt('keep') && `${cnt('keep')} kept`, r.record.some(x => x.reverted_at) && 'undo used'].filter(Boolean);
  const created = r.output.target && r.output.target.created ? 'created the opportunity and ' : '';
  return {main: `${u.name} ${created}wrote ${plural(w, 'field', 'fields')} to ${target}`, sub: `${parts.length ? parts.join(', ') : 'all approved'} · from "${m.title}"`};
}
function renderActivity() {
  const runs = visibleRuns();
  const evs = S.events.filter(x => isManager() || x.user === S.user);
  const counts = {all: runs.length, written: runs.filter(r => runKind(r) === 'written').length, awaiting: runs.filter(r => runKind(r) === 'awaiting').length, blocked: runs.filter(r => runKind(r) === 'blocked').length};
  const labels = {all: 'All', written: 'Written', awaiting: 'Waiting for review', blocked: 'Blocked'};
  const items = runs.filter(r => UI.actFilter === 'all' || runKind(r) === UI.actFilter).map(r => ({at: r.submittedAt || r.createdAt, r}))
    .concat(UI.actFilter === 'all' ? evs.map(x => ({at: x.at, x})) : []).sort((a, b) => (a.at < b.at ? 1 : -1));
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><span class="fgroup" id="act-filter" role="group" aria-label="filter">${Object.keys(labels).map(k => `<button class="fchip" type="button" data-f="${k}" aria-pressed="${UI.actFilter === k}">${labels[k]} <span class="n">${counts[k]}</span></button>`).join('')}</span><span class="grow"></span>
      <span class="acts"><button class="b b-sm b-t" type="button" id="act-export" title="every event of every run, in the format of agent/run_log_schema.json">${ico('download')}Download technical log (JSON)</button></span></div>
      <ol class="feed" id="act-list">${items.length ? items.map(it => {
        if (it.x) return `<li class="fi fi-ev"><time class="fi-t">${e(fmtDate(it.at))}</time><div class="fi-m"><span>${e(it.x.text)}</span><div class="sub">seller decision on a blocked conversation</div></div><span class="fi-s"><span class="ch ch-neu">Confirmed</span></span><span class="fi-a"></span></li>`;
        const r = it.r, s = runSentence(r), open = UI.expanded[r.id];
        const chip = runKind(r) === 'blocked' ? CH.run('Blocked') : CH.run(r.status);
        const rec = r.record || r.autoRecord || [];
        const changes = rec.length ? `<div class="fi-x"${open ? '' : ' hidden'}><table class="tb"><thead><tr><th>Field</th><th>Before</th><th>After</th><th>Decision</th></tr></thead><tbody>${rec.map(x => `<tr><td><b>${e(DEF[x.field].label)}</b>${DEF[x.field].record === 'client' ? '<div class="sub">client record</div>' : ''}</td><td>${valueOr(x.previous_value)}</td><td>${x.write_result === 'Succeeded' ? valueOr(x.final_value) : '<span class="nada">not written</span>'}${(x.seller_decision === 'edit' || x.seller_decision === 'replace') && x.agent_proposal ? `<div class="sub">Agent proposed: ${e(x.agent_proposal)}</div>` : ''}${x.reverted_at ? '<div class="sub">undone</div>' : ''}</td><td class="mid">${CH.decision(x.seller_decision, x.decided_by)}${x.rejection_reason ? `<div class="sub">${e(x.rejection_reason)}</div>` : ''}</td></tr>`).join('')}</tbody></table></div>` : '';
        return `<li class="fi" data-run="${e(r.id)}" data-kind="${runKind(r)}"><time class="fi-t">${e(fmtDate(it.at))}</time>
          <div class="fi-m"><b>${e(s.main)}</b><div class="sub">${e(s.sub)} · ${e(r.id)}</div></div>
          <span class="fi-s">${chip}</span>
          <span class="fi-a acts"><a class="b b-sm b-t" href="#/review/${e(r.id)}">${r.status === 'Blocked' ? 'See reason' : 'Open review'}</a>${rec.length ? `<button class="b b-sm b-t" type="button" data-expand="${e(r.id)}" aria-expanded="${open ? 'true' : 'false'}">${open ? 'Hide changes' : 'Changes'}</button>` : ''}</span>
          ${changes}</li>`;
      }).join('') : '<li class="fi-none"><span class="nada">Nothing yet. Add a meeting in Meetings: every CRM update, written or blocked, lands here.</span></li>'}</ol></div>`;
  $$('#act-filter .fchip').forEach(b => b.onclick = () => { UI.actFilter = b.dataset.f; renderActivity(); });
  $$('#act-list [data-expand]').forEach(b => b.onclick = () => { UI.expanded[b.dataset.expand] = !UI.expanded[b.dataset.expand]; renderActivity(); });
  $('#act-export').onclick = exportLog;
}
function exportLog() {
  const runs = visibleRuns().map(r => {
    const m = meetingById(r.meetingId);
    return {run_record: {run_id: r.id, meeting_id: r.meetingId, source: m && m.source || null, opportunity_id: r.output.source_status === 'AccessDenied' ? null : r.output.opportunity_id,
      run_as_user_id: r.userId, stage_at_run: r.stageAtRun, source_status: r.output.source_status, run_status: r.status, block_reason: r.output.block_reason,
      mode: r.mode, model: r.model, target: r.output.target || null, field_decisions: r.record || r.autoRecord || []}, events: r.log};
  });
  download('orbita_crm_activity_log.json', JSON.stringify({exported_at: isoLocal(), schema: 'agent/run_log_schema.json', permissions: perms(), runs, decisions: S.events}, null, 2), 'application/json');
}
function runEvalInPage() {
  const rows = [];
  for (const c of FOTO.expected.cases) {
    const crm = {clients: deep(FOTO.clients), opportunities: deep(FOTO.opportunities)};
    const data = {team: FOTO.team, clients: crm.clients, opportunities: crm.opportunities, meetings: deep(FOTO.meetings)};
    const log = CORE.newLog('EVAL-' + c.case_id, isoLocal);
    const tx = FOTO.transcripts[c.meeting_id] != null ? FOTO.transcripts[c.meeting_id] : null;
    const user = userById(c.run_as_user_id);
    const m0 = data.meetings.find(m => m.meeting_id === c.meeting_id);
    if (m0) data.meetings = [CORE.attribute({meeting: m0, lines: CORE.transcriptLines(tx || ''), data, user, schema: SCHEMA})].concat(data.meetings.filter(m => m !== m0));
    const pre = CORE.prepareRun({meetingId: c.meeting_id, opportunityId: c.opportunity_id === null ? undefined : c.opportunity_id, userId: c.run_as_user_id, data, transcript: tx, log, schema: SCHEMA});
    let out;
    if (pre.output) out = pre.output;
    else { const raw = FOTO.refs[c.meeting_id]; out = raw ? CORE.validateOutput(deep(raw), Object.assign({}, pre, {team: FOTO.team}), SCHEMA) : CORE.blocked(c.meeting_id, null, 'Missing', 'no reference output'); }
    const sc = CORE.scoreCase(c, out, {lines: CORE.transcriptLines(tx || ''), schema: SCHEMA});
    const platform = [];
    const all = () => Object.fromEntries(out.fields.filter(f => CORE.ACTIONABLE.includes(f.status)).map(f => [f.field, {decision: f.status === 'proposed' ? 'approve' : 'keep'}]));
    if (c.review_script && !pre.output) {
      const decisions = all();
      Object.entries(c.review_script.edit || {}).forEach(([k, v]) => { decisions[k] = {decision: 'edit', value: v}; });
      const rec = CORE.applyApprovedFields({output: out, decisions, crm, reviewerId: c.run_as_user_id, log, schema: SCHEMA, team: FOTO.team, runId: 'EVAL-' + c.case_id, now: isoLocal()});
      const [k, edited] = Object.entries(c.review_script.edit)[0];
      const r = rec.find(x => x.field === k), opp = crm.opportunities.find(o => o.opportunity_id === c.opportunity_id);
      platform.push(["The CRM receives the seller's edited text, not the agent's version", CORE.fieldOf(opp, k).value === edited && r.agent_proposal !== edited]);
      platform.push(['The record keeps both the agent proposal and the final value', !!r.agent_proposal && r.final_value === edited]);
      platform.push(['The record keeps the reviewer and the decision time', r.reviewer_id === c.run_as_user_id && /^\d{4}-\d{2}-\d{2}T/.test(r.decided_at)]);
    }
    if (c.expect_new_client && !pre.output) {
      const before = crm.clients.length;
      const decisions = Object.assign(all(), {__create__: {decision: 'approve'}});
      CORE.applyApprovedFields({output: out, decisions, crm, reviewerId: c.run_as_user_id, log, schema: SCHEMA, team: FOTO.team, runId: 'EVAL-' + c.case_id, now: isoLocal()});
      const o2 = crm.opportunities.find(o => o.opportunity_id === out.opportunity_id);
      platform.push(['Approving the new opportunity creates the client and the opportunity at New Lead', crm.clients.length === before + 1 && !!o2 && CORE.fieldOf(o2, 'stage').value === STAGES[0]]);
    }
    if (c.case_id === 'T1' && !pre.output) {
      const crm2 = {clients: deep(FOTO.clients), opportunities: deep(FOTO.opportunities)};
      const auto = CORE.autoFields(out, SCHEMA, CORE.defaultPermissions(SCHEMA));
      const rec = CORE.applyApprovedFields({output: out, decisions: Object.fromEntries(auto.map(k => [k, {decision: 'approve', auto: true}])), crm: crm2, reviewerId: 'U01', log, schema: SCHEMA, team: FOTO.team, runId: 'EVAL-T1A', now: isoLocal(), only: auto});
      const o2 = crm2.opportunities.find(o => o.opportunity_id === out.opportunity_id);
      platform.push(['Fields under Always allow are written without a click, and only those', rec.length === auto.length && auto.every(k => CORE.fieldOf(o2, k).value) && !CORE.fieldOf(o2, 'budget').value]);
    }
    if (c.expected_source_status === 'AccessDenied') {
      platform.push(['No opportunity or client data is returned', !out.fields.length && out.opportunity_id === null]);
      platform.push(['The access-denied attempt is in the run log', log.events.some(ev => ev.action === 'access_checked' && ev.outcome === 'blocked')]);
    }
    rows.push({case_id: c.case_id, pass: sc.verdict === 'PASS', fails: sc.fails, platform});
  }
  S.evalRows = rows; S.evalAt = isoLocal(); save();
  renderQuality();
}
function renderQuality() {
  const cases = FOTO.expected.cases, rows = S.evalRows;
  const passed = rows ? rows.filter(r => r.pass).length : null;
  const plat = rows ? rows.flatMap(r => r.platform) : [];
  const res = FOTO.eval_results;
  const labels = res ? Object.entries(res.labels) : [];
  const exp = c => c.expected_run_status === 'Blocked' ? `Blocked: ${c.expected_source_status}` : c.expect_new_client ? `New client: ${c.expect_new_client}`
    : `Ready · at least ${Object.values(c.fields).filter(x => !(x.status_any || [x.status]).includes('no_evidence')).length} fields with evidence`;
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-b purpose"><b>Why this page exists.</b> Before any change to the agent's rules, fields or model goes live, the agent must pass these ${cases.length} test conversations, whose correct answers we know. Each one covers one risk: a missing date, a contradiction, a cut recording, a company that is not in the CRM, a stage pushed too early, a seller edit, an access boundary, unnamed voices, a WhatsApp chat. This is a tool for whoever maintains the agent.</div></div>
    <div class="pn"><div class="pn-h"><h2>Test conversations</h2><span class="pn-n">${rows ? `${passed}/${rows.length} pass · replayed ${e(fmtDate(S.evalAt))}` : 'not replayed in this browser yet'}</span>
      <span class="acts"><button class="b b-sm b-s" type="button" id="eval-run">${ico('gauge')}Replay test conversations</button></span></div>
      <div class="tbw"><table class="tb" id="tb-eval"><thead><tr><th>Test</th><th>What it proves</th><th>Expected</th><th>Result</th></tr></thead><tbody>
      ${cases.map(c => { const r = rows && rows.find(x => x.case_id === c.case_id); return `<tr><td class="mid"><b>${e(c.case_id)}</b><div class="sub">${e(c.meeting_id)}</div></td><td>${e(c.proves || c.name)}</td><td class="mid">${e(exp(c))}</td>
        <td class="mid">${r ? `<span class="ev-res ${r.pass ? 'pass' : 'fail'}">${r.pass ? 'Pass' : 'Fail'}</span>${r.fails.length ? `<ul class="issues">${r.fails.map(f => `<li>${e(f)}</li>`).join('')}</ul>` : ''}` : '<span class="nada">not replayed</span>'}</td></tr>`; }).join('')}
      </tbody></table></div>
      <div class="pn-f">Replay runs the saved answers through the same checks, validator and scorer this page uses for real updates (agent/core.mjs and eval/score.mjs, embedded as they are). It proves the guardrails, not the model; the model is scored from the command line, below.</div></div>
    <div class="pn"><div class="pn-h"><h2>Write checks</h2><span class="pn-n">${rows ? `${plat.filter(p => p[1]).length}/${plat.length} pass` : 'run with the replay'}</span></div>
      <div class="checks">${rows ? rows.filter(r => r.platform.length).map(r => `<div class="case">${e(r.case_id)}</div>${r.platform.map(p => `<div class="chk"><span class="ev-res ${p[1] ? 'pass' : 'fail'}">${p[1] ? 'Pass' : 'Fail'}</span><span>${e(p[0])}</span></div>`).join('')}`).join('')
        : '<div class="chk"><span class="nada">Replay the test conversations to run the write checks.</span></div>'}</div></div>
    <div class="pn"><div class="pn-h"><h2>Scoreboard by model</h2><span class="pn-n">${res ? 'last command-line eval · ' + e(fmtDate((res.run_at || '').slice(0, 16).replace('Z', ''))) : 'no command-line eval in the snapshot'}</span></div>
      <div class="tbw"><table class="tb" id="tb-models"><thead><tr><th>Model</th><th>Passed</th><th class="num">Model calls</th><th class="num">Input tokens</th><th class="num">Cache read</th><th class="num">Output tokens</th><th class="num">Cost per meeting</th></tr></thead><tbody>
      ${labels.length ? labels.map(([k, r]) => `<tr><td><b>${e(k === 'mock' ? 'saved answers' : modelName(k))}</b><div class="sub">${k === 'mock' ? 'no model: proves the platform' : 'live model'}</div></td><td class="mid">${r.passed}/${r.total}</td><td class="num mid">${r.usage.calls || '-'}</td><td class="num mid">${r.usage.calls ? r.usage.input_tokens.toLocaleString('en-US') : '-'}</td><td class="num mid">${r.usage.calls ? r.usage.cache_read_input_tokens.toLocaleString('en-US') : '-'}</td><td class="num mid">${r.usage.calls ? r.usage.output_tokens.toLocaleString('en-US') : '-'}</td><td class="num mid">${r.cost_per_call_usd != null ? 'USD ' + r.cost_per_call_usd.toFixed(4) : '-'}</td></tr>`).join('')
        : '<tr><td colspan="7"><span class="nada">No result yet.</span></td></tr>'}
      </tbody></table></div>
      <div class="pn-f">Live scores come from <code>node agent/pipeline.mjs --all --model &lt;id&gt;</code> then <code>node eval/run_eval.mjs</code>; the blocked tests stop in code before the model. Run <code>python dados/coleta.py</code> to bring the latest results here.</div></div>`;
  $('#eval-run').onclick = runEvalInPage;
}
function renderData() {
  $('#set-body').innerHTML = `
    <div class="pn"><div class="pn-h"><h2>Your data in this browser</h2><span class="pn-d">this prototype keeps the CRM in the browser (localStorage)</span></div>
      <div class="set-row"><div class="sl">CRM</div><div class="sv"><span>${plural(clients().length, 'client', 'clients')} · ${plural(opps().length, 'opportunity', 'opportunities')} · ${plural(S.meetings.length, 'meeting', 'meetings')} · ${plural(S.runOrder.length, 'CRM update', 'CRM updates')}</span>
        <span class="acts"><button class="b b-sm b-s" type="button" id="dt-export">${ico('download')}Export CRM (CSV)</button><button class="b b-sm b-t" type="button" id="dt-log">${ico('download')}Technical log (JSON)</button></span></div></div>
      <div class="set-row"><div class="sl">Explore</div><div class="sv"><span>${plural(S.chats.filter(c => c.user === S.user).length, 'chat', 'chats')} of yours</span><span class="acts"><button class="b b-sm b-t" type="button" id="dt-chats">Clear my chats</button></span></div></div>
      <div class="set-row"><div class="sl">Start over</div><div class="sv"><span>Put the CRM back to the seed: ${FOTO.clients.length} clients and ${FOTO.opportunities.length} opportunities, no meetings. Permissions and agent settings stay.</span><span class="acts"><button class="b b-sm b-d" type="button" id="dt-reset">Reset to the seed</button></span></div></div></div>`;
  $('#dt-export').onclick = exportCrm;
  $('#dt-log').onclick = exportLog;
  $('#dt-chats').onclick = () => { S.chats = S.chats.filter(c => c.user !== S.user); S.chatCurrent = null; save(); renderData(); renderNav(); toast('Your chats were cleared', 'ok'); };
  $('#dt-reset').onclick = askReset;
}
function switchUser(id) {
  if (!userById(id)) return;
  S.user = id; S.chatCurrent = null; UI.editing = null; UI.draft = null; UI.oppChoice = ''; save(); renderNav(); renderJob();
  route();
  toast('Now signed in as ' + userById(id).name, 'ok');
}
function askReset() {
  const dlg = $('#dlg-reset'); if (!dlg) return;
  dlg.showModal();
  $('#dlg-reset-ok').onclick = () => { dlg.close(); resetAll(); UI.editing = null; UI.draft = null; UI.expanded = {}; UI.quiet = {}; location.hash = '#/meetings'; route(); renderJob();
    toast(`CRM reset to the seed · ${FOTO.clients.length} clients, ${FOTO.opportunities.length} opportunities, 0 meetings`, 'ok'); };
}

// ------------------------------------------------------------------ boot
function boot() {
  S = load() || fresh();
  if (!DEMO_USERS.includes(S.user)) S.user = 'U01';
  S.settings = Object.assign(freshSettings(), S.settings || {});
  S.settings.permissions = Object.assign(CORE.defaultPermissions(SCHEMA), S.settings.permissions || {});
  S.settings.permissions.fields = Object.assign(CORE.defaultPermissions(SCHEMA).fields, (S.settings.permissions || {}).fields || {});
  const um = $('#umenu'), ub = $('#umenubtn');
  ub.onclick = () => { const open = !um.classList.contains('open'); um.classList.toggle('open', open); ub.setAttribute('aria-expanded', String(open)); };
  document.addEventListener('click', ev => { if (!um.contains(ev.target)) { um.classList.remove('open'); ub.setAttribute('aria-expanded', 'false'); } });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && um.classList.contains('open')) { um.classList.remove('open'); ub.setAttribute('aria-expanded', 'false'); ub.focus(); } });
  $$('.pi[data-user]').forEach(b => b.onclick = () => { um.classList.remove('open'); switchUser(b.dataset.user); });
  $$('.pi[data-go]').forEach(b => b.onclick = () => { um.classList.remove('open'); location.hash = b.dataset.go; });
  $$('.nav-i[data-view]').forEach(b => b.onclick = () => { location.hash = '#/' + b.dataset.view + (b.dataset.view === 'settings' ? '/' + UI.setTab : ''); });
  $('#nav-newchat').onclick = newChat;
  $('#job').onclick = () => { location.hash = '#/settings/agent'; };
  $('#ex-cmp').addEventListener('submit', ev => { ev.preventDefault(); askExplore($('#ex-in').value); });
  $('#ex-in').addEventListener('keydown', ev => { if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); askExplore($('#ex-in').value); } });
  $('#opps-export').onclick = exportCrm;
  $('#opps-q').addEventListener('input', ev => { UI.oppsQ = ev.target.value; renderOpps(); const q = $('#opps-q'); q.focus(); q.setSelectionRange(q.value.length, q.value.length); });
  $('#opps-owner').onchange = ev => { UI.oppsOwner = ev.target.value; renderOpps(); };
  $('#opps-sort').onchange = ev => { UI.oppsSort = ev.target.value; renderOpps(); };
  $('#cl-q').addEventListener('input', ev => { UI.clQ = ev.target.value; renderClients(); const q = $('#cl-q'); q.focus(); q.setSelectionRange(q.value.length, q.value.length); });
  $('#cl-sort').onchange = ev => { UI.clSort = ev.target.value; renderClients(); };
  $$('#set-tabs [data-tab]').forEach(b => b.onclick = () => { location.hash = '#/settings/' + b.dataset.tab; });
  // the three ways out (x, click outside, Esc) restore the route themselves: the dialog's own
  // 'close' event can arrive late (or not at all in a background tab), so it is only a fallback
  for (const id of ['drw', 'opp-drw', 'cli-drw']) {
    const d = $('#' + id), rec = id !== 'drw';
    const shut = () => { if (d.open) d.close(); if (rec) onDrawerClose(); };
    $('#' + id + '-x').onclick = shut;
    d.addEventListener('click', ev => { if (ev.target === d) shut(); });
    if (rec) { d.addEventListener('cancel', onDrawerClose); d.addEventListener('close', onDrawerClose); }
  }
  const dr = $('#dlg-reset');
  $('#dlg-reset-x').onclick = () => dr.close();
  $('#dlg-reset-cancel').onclick = () => dr.close();
  dr.addEventListener('click', ev => { if (ev.target === dr) dr.close(); });
  $('#toast-x').onclick = hideToast;
  wireIntake();
  window.addEventListener('hashchange', route);
  UI.navigated = false;
  route(); renderJob();
  probeServer();
}
document.addEventListener('DOMContentLoaded', boot);
window.CRM = {ingest, prepareDraft, startRun, decide, decideCreate, decideGroup, submitRun, undoAuto, confirmEnded, askExplore, newChat, resetAll, switchUser,
  runEvalInPage, openOppDrawer, openClientDrawer, state: () => S, core: CORE, ui: () => UI, live: () => LIVE};
"""
