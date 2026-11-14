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
  vistas      explore[/<chat>] · meetings · review/<run> · opportunities[/<opp>] ·
              clients[/<cliente>] · evals[/<aba>] · settings[/<aba>]; as rotas antigas
              redirecionam (settings/quality -> evals/evalset).
  evals       o ciclo de melhoria do agente: avaliacao da vendedora, revisao de traces
              (Pass/Fail e nota, no metodo de analise de erros de Husain e Shankar),
              modos de falha e o conjunto de testes; os rotulos vao para os mesmos
              arquivos do app de revisao (eval/error_discovery), pelo servidor.

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
    meetings: [], transcripts: {}, runs: {}, runOrder: [], events: [], confirmed: {}, chats: [], chatCurrent: null, feedback: [],
    settings: settings || freshSettings(), granola: {synced: false, lastSync: null},
    seq: {run: 0, mtg: 0, chat: 0, fb: 0}, lastRun: null, evalRows: null, evalAt: null, evals: freshEvals()};
}
function load() {
  try { const j = localStorage.getItem(KEY); if (j) { const s = JSON.parse(j); if (s && s.v === 3) return s; } } catch (_) {}
  return null;
}
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (_) {} }
// the trace review is about the agent, not the CRM: a reset keeps the labels, notes and failure modes
function resetAll() { const ev = S && S.evals; S = fresh(S ? S.settings : null); if (ev) S.evals = ev; save(); }

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
  if (v === 'evals') renderEvals();
  evPull();
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
  let output, events, mode = 'saved', model = null, trace = {traceId: null, spanId: null};
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
      mode = j.mode; model = j.model || null; trace = {traceId: j.traceId || null, spanId: j.spanId || null};
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
    output, log: events, decisions: {}, autoRecord: null, autoPending: [], record: null, status: output.run_status, submittedAt: null,
    traceId: trace.traceId, spanId: trace.spanId};
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
  const rated = fbOf('update', runId);
  if (rated) { Object.assign(rated, fbContext('update', runId), {synced: false}); save(); fbSync(rated); }
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

// ------------------------------------------------------------------ seller feedback (thumbs up / down)
// One rating per CRM update and per Explore answer, by the seller who saw it. It stays with the CRM and, when the local
// server runs, goes to its feedback file for the agent owner. A rating keeps ids, the reason, the model and the decision
// counts: never the transcript and never a field value.
const FB_REASONS = {
  update: [['wrong_opportunity', 'Wrong opportunity'], ['wrong_values', 'Wrong or missing values'], ['missed_stage', 'Wrong stage or next step'], ['other', 'Something else']],
  explore: [['wrong', 'Wrong answer'], ['incomplete', 'Missing something'], ['off_topic', 'Not what I asked'], ['other', 'Something else']],
};
const FB_ASK = {update: ['Was this update right?', 'Right', 'Not right'], explore: ['Was this answer useful?', 'Useful', 'Not useful']};
const fbKey = (surface, ref) => surface + '|' + ref;
const fbBox = k => $$('[data-fb]').find(x => x.dataset.fb === k) || null;
const fbOf = (surface, ref) => S.feedback.find(f => f.surface === surface && f.ref === ref && f.user === S.user) || null;
const visibleFeedback = () => S.feedback.filter(f => isManager() || f.user === S.user);
const reasonLabel = f => (FB_REASONS[f.surface].find(r => r[0] === f.reason) || [null, 'no reason given'])[1];
const fbModel = f => f.model === 'rules' ? 'CRM rules' : f.model === 'saved' ? 'saved result' : modelName(f.model);
/** What the owner needs to triage a rating: where it came from, the model, what the seller did. */
function fbContext(surface, ref) {
  if (surface === 'update') {
    const r = S.runs[ref];
    if (!r || r.status === 'Blocked') return null;
    const rec = r.record || r.autoRecord || [];
    const n = k => rec.filter(x => x.seller_decision === k && x.decided_by !== 'permission').length;
    return {label: runTarget(r), model: r.mode === 'live' ? r.model : r.mode, run_id: r.id, meeting_id: r.meetingId, opportunity_id: r.output.opportunity_id || null,
      submitted: !!r.record, decisions: {approved: n('approve') + n('keep'), edited: n('edit') + n('replace'), rejected: n('reject') + n('clear'), undone: rec.filter(x => x.reverted_at).length},
      trace_id: r.traceId || null, span_id: r.spanId || null}; // Arize ids, when the server traced the run
  }
  const [chatId, i] = ref.split(':');
  const chat = S.chats.find(c => c.id === chatId), msg = chat && chat.messages[+i], asked = chat && chat.messages[+i - 1];
  if (!msg || !msg.answer) return null;
  return {label: asked ? asked.text : chat.title, model: msg.via, question: asked ? asked.text : '', answer: msg.answer.verdict, answer_kind: msg.answer.kind,
    trace_id: msg.traceId || null, span_id: msg.spanId || null};
}
function fbHtml(surface, ref) {
  const f = fbOf(surface, ref), k = fbKey(surface, ref), [ask, yes, no] = FB_ASK[surface];
  const open = UI.fbOpen === k && f && f.rating === 'down' && !f.sent;
  const btn = (r, label) => `<button class="fb-b" type="button" data-rate="${r}" aria-pressed="${f && f.rating === r ? 'true' : 'false'}" aria-label="${label}" title="${label}">${ico(r === 'up' ? 'thumbs-up' : 'thumbs-down')}</button>`;
  const said = !f ? '' : f.rating === 'up' ? 'Thanks · counted for the agent owner' : f.sent ? `Sent to the agent owner · ${e(reasonLabel(f))}` : '';
  const form = open ? `<div class="fb-f"><span class="fb-l" id="fb-l-${e(f.uid)}">What was wrong?</span>
      <div class="fb-rs" role="radiogroup" aria-labelledby="fb-l-${e(f.uid)}">${FB_REASONS[surface].map(([id, l]) => `<label class="fb-r"><input type="radio" name="fb-r-${e(f.uid)}" value="${id}">${e(l)}</label>`).join('')}</div>
      <input class="inp fb-note" type="text" maxlength="280" placeholder="Optional: what should it have said?" aria-label="Optional note for the agent owner">
      <span class="acts"><button class="b b-xs b-s" type="button" data-fb-send>Send</button><button class="b b-xs b-t" type="button" data-fb-skip>Skip</button></span></div>` : '';
  return `<div class="fb" data-fb="${e(k)}"><span class="fb-q">${ask}</span>${btn('up', yes)}${btn('down', no)}${said ? `<span class="fb-s">${said}</span>` : ''}${form}</div>`;
}
function fbRefresh(surface, ref) {
  const k = fbKey(surface, ref), box = fbBox(k);
  if (box) {
    box.outerHTML = fbHtml(surface, ref);
    const nb = fbBox(k), first = nb && $('input[type="radio"]', nb);
    if (first) first.focus(); else if (nb) ($('[aria-pressed="true"]', nb) || $('[data-rate]', nb)).focus();
  }
  if (view() === 'evals' && (UI.ev.tab === 'feedback' || UI.ev.tab === 'dashboard')) renderEvals();
  renderNav();
}
async function fbSync(f) {
  if (!LIVE.ok) return;
  const v = f.v = (f.v || 0) + 1; // only the answer to the latest send marks the rating synced
  try {
    const r = await fetch(API + '/api/feedback', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({feedback: f})});
    if (r.ok && f.v === v) { f.synced = true; save(); }
  } catch (_) {}
}
/** A thumbs up is recorded at once; a thumbs down opens the reason, which the seller may skip. A pressed thumb stays pressed. */
function rate(surface, ref, rating) {
  const ctx = fbContext(surface, ref);
  if (!ctx) return;
  let f = fbOf(surface, ref);
  if (f && f.rating === rating) return;
  if (!f) { f = {id: 'FB-' + String(++S.seq.fb).padStart(4, '0'), uid: Math.random().toString(36).slice(2, 12).padEnd(10, '0'), surface, ref, user: S.user}; S.feedback.unshift(f); }
  Object.assign(f, ctx, {rating, at: isoLocal(), reason: null, note: '', sent: rating === 'up', synced: false});
  UI.fbOpen = rating === 'down' ? fbKey(surface, ref) : null;
  save(); fbRefresh(surface, ref);
  fbSync(f);
}
function sendReason(surface, ref, skip) {
  const f = fbOf(surface, ref), box = fbBox(fbKey(surface, ref));
  if (!f || f.rating !== 'down') return;
  const pick = !skip && box && $('input[type="radio"]:checked', box);
  f.reason = pick ? pick.value : null;
  f.note = skip || !box ? '' : (($('.fb-note', box) || {}).value || '').trim().slice(0, 280);
  f.sent = true; f.synced = false; UI.fbOpen = null;
  save(); fbRefresh(surface, ref);
  fbSync(f);
}
function wireFeedback() {
  // one listener for every rating on the page: the views redraw with innerHTML, the feedback box keeps working
  const target = ev => { const box = ev.target.closest('[data-fb]'); if (!box) return null; const i = box.dataset.fb.indexOf('|'); return [box.dataset.fb.slice(0, i), box.dataset.fb.slice(i + 1)]; };
  document.addEventListener('click', ev => {
    const t = target(ev), b = t && ev.target.closest('[data-rate],[data-fb-send],[data-fb-skip]');
    if (!b) return;
    if (b.dataset.rate) rate(t[0], t[1], b.dataset.rate);
    else sendReason(t[0], t[1], b.hasAttribute('data-fb-skip'));
  });
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Enter' || !ev.target.matches('.fb-note')) return;
    const t = target(ev); if (t) { ev.preventDefault(); sendReason(t[0], t[1], false); }
  });
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
  const mine = S.chats.filter(c => c.user === S.user).slice(0, 8);
  const cur = view() === 'explore' ? S.chatCurrent : null;
  $('#nav-chats').innerHTML = mine.map(c => `<button class="nav-i nav-c${cur === c.id ? ' on' : ''}" type="button" data-chat="${e(c.id)}" title="${e(c.title)}"${cur === c.id ? ' aria-current="page"' : ''}><span class="lb">${e(c.title)}</span></button>`).join('');
  $$('#nav-chats [data-chat]').forEach(b => b.onclick = () => openChat(b.dataset.chat));
  // Explore is lit only on a new chat; an open chat lights its own line
  const ex = $('.nav-i[data-view="explore"]'); if (ex) ex.classList.toggle('on', view() === 'explore' && !cur);
  const toReview = EVD.traces.filter(t => EVD.sample.includes(t.id) && !evLabel(t.id)).length + prodTraces().filter(t => !evLabel(t.id)).length;
  const en = $('#nav-evals-n'); en.textContent = toReview || ''; en.title = toReview ? plural(toReview, 'trace to review', 'traces to review') : '';
}

// ------------------------------------------------------------------ router
const UI = {editing: null, oppsStage: 'all', oppsQ: '', oppsOwner: '', oppsSort: 'due', clQ: '', clSort: 'name', actFilter: 'all', expanded: {}, quiet: {},
  setTab: 'permissions', draft: null, oppChoice: '', src: 'file', drawerRoute: null, asking: false, fbOpen: null, mtQ: '', mtg: null,
  ev: {tab: 'dashboard', filter: 'all', all: false, cur: null, undo: [], saved: null, nt: null}};
const VIEWS = ['explore', 'meetings', 'review', 'opportunities', 'clients', 'evals', 'settings'];
const TABS = ['permissions', 'agent', 'sources', 'team', 'activity', 'data'];
const ALIAS = {calls: ['meetings'], opps: ['opportunities'], opp: ['opportunities', null], audit: ['settings', 'activity'], activity: ['settings', 'activity'],
  eval: ['evals', 'evalset'], quality: ['evals', 'evalset'], agent: ['settings', 'agent'], sources: ['settings', 'sources']};
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
  // Quality checks moved from Settings to the Evals tab (the eval set)
  if (v === 'settings' && id === 'quality') { location.replace('#/evals/evalset'); return; }
  // a new view (or another update in Review) starts at the top; a drawer opening over a list keeps the scroll
  const page = v + (v === 'review' || v === 'settings' || v === 'evals' || v === 'explore' ? '/' + id : '');
  if (UI.page && UI.page !== page) window.scrollTo(0, 0);
  UI.page = page;
  $$('.view').forEach(sec => { sec.hidden = sec.dataset.view !== v; });
  $$('.nav-i[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === v || (v === 'review' && b.dataset.view === 'meetings')));
  if (v === 'explore') {
    // like a chat app: Explore alone is a new chat; #/explore/<chat> reopens that chat at its last message
    const c = id && S.chats.find(x => x.id === id && x.user === S.user);
    S.chatCurrent = c ? c.id : null;
    renderExplore();
    if (c) chatToEnd();
  }
  else if (v === 'meetings') renderMeetings();
  else if (v === 'review') renderReview(id);
  else if (v === 'opportunities') { renderOpps(); if (id) openOppDrawer(id, true); }
  else if (v === 'clients') { renderClients(); if (id) openClientDrawer(id, true); }
  else if (v === 'evals') { if (id === 'overview') { location.replace('#/evals/dashboard'); return; } if (EV_TABS.includes(id)) UI.ev.tab = id; renderEvals(); }
  else if (v === 'settings') { if (TABS.includes(id)) UI.setTab = id; renderSettings(); }
  renderNav();
  const sec = $(`.view[data-view="${v}"]`);
  document.title = (sec.dataset.title || v) + ' · Orbita CRM';
  // focus moves to the view (screen readers announce it) without scrolling it under the sticky bar
  if (UI.navigated && !(id && (v === 'opportunities' || v === 'clients' || v === 'explore'))) sec.focus({preventScroll: true});
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
  stage: s => `<span class="ch st-${Math.max(0, STAGES.indexOf(s))}">${e(s || 'no stage')}</span>`, // one hue per stage of the funnel
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
  return `<span class="ttl">${logo(c ? c.name : '', 20)}<span><button class="rec" type="button" data-open-opp="${e(o.opportunity_id)}" title="open the CRM record">${e(c ? c.name : o.client_id)}</button><span class="sub">${e(o.name)} · ${e(o.opportunity_id)}</span></span></span>`;
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
function msgHtml(msg, ref) {
  if (msg.role === 'user') return `<li class="msg eu"><p>${e(msg.text)}</p></li>`;
  if (msg.pending) return `<li class="msg nex wait"><div class="msg-who">Orbita</div><p class="msg-v">Reading your CRM…</p></li>`;
  const a = msg.answer;
  const sugs = a.kind === 'none' ? `<p class="msg-sgh">Try one of these</p><ul class="sg-l msg-sg">${CORE.exploreSuggestions(exploreCtx()).map(sgHtml).join('')}</ul>` : '';
  return `<li class="msg nex"><div class="msg-who">Orbita</div><p class="msg-v">${e(a.verdict)}</p>
    ${a.findings.length ? `<ol class="msg-a">${a.findings.map(f => `<li>${e(f.text)}${(f.src || []).map(n => `<sup class="ref">${n}</sup>`).join('')}</li>`).join('')}</ol>` : ''}
    ${a.open ? `<p class="msg-ab"><b>Not settled yet:</b> ${e(a.open)}</p>` : ''}${sugs}
    ${a.sources && a.sources.length ? `<ol class="msg-f" aria-label="sources of this answer">${a.sources.map(s => `<li>${e(s)}</li>`).join('')}</ol>` : ''}
    ${a.actions && a.actions.length ? `<div class="msg-acts">${a.actions.map(x => x.opp ? `<button class="b b-sm b-s" type="button" data-ex-opp="${e(x.opp)}">${e(x.label)}</button>` : `<a class="b b-sm b-s" href="#/review/${e(x.run)}">${e(x.label)}</a>`).join('')}</div>` : ''}
    <div class="msg-m">${msg.via === 'rules' ? 'answered from your CRM data' : `answered by ${e(modelName(msg.via))} from your CRM data`}</div>${ref ? fbHtml('explore', ref) : ''}</li>`;
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
  $('#ex-t').classList.toggle('sr', has); // in a chat the first question is already on screen
  const th = $('#ex-thread');
  th.hidden = !has;
  th.innerHTML = has ? chat.messages.map((m, i) => msgHtml(m, chat.id + ':' + i)).join('') : '';
  $('#ex-sg-box').hidden = has;
  if (!has) $('#ex-sg').innerHTML = CORE.exploreSuggestions(exploreCtx()).map(sgHtml).join('');
  $('#ex-src-t').textContent = claudeOn() ? `Your CRM · ${modelName(S.settings.model)}` : 'Your CRM';
  $('#ex-in').placeholder = has ? 'Ask a follow-up about your pipeline' : 'Ask about a client, an opportunity or your pipeline';
  $$('.ex [data-q]').forEach(b => b.onclick = () => askExplore(b.dataset.q));
  $$('.ex [data-ex-opp]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.exOpp));
  if (has && UI.scrollChat) { UI.scrollChat = false; chatToEnd(); }
}
async function askExplore(question) {
  const q = String(question || '').trim();
  if (!q || UI.asking) return;
  let chat = currentChat();
  if (!chat) {
    chat = {id: 'CH-' + (++S.seq.chat), user: S.user, title: q.length > 48 ? q.slice(0, 46) + '…' : q, at: isoLocal(), messages: []};
    S.chats.unshift(chat); S.chatCurrent = chat.id;
    // the address names the chat, as in a chat app; replaceState does not re-render the view
    if (view() === 'explore') { history.replaceState(null, '', '#/explore/' + chat.id); UI.page = 'explore/' + chat.id; }
  }
  chat.messages.push({role: 'user', text: q, at: isoLocal()});
  const slot = {role: 'agent', pending: true};
  chat.messages.push(slot);
  $('#ex-in').value = '';
  UI.asking = true; UI.scrollChat = true; renderExplore(); renderNav();
  let answer = null, via = 'rules', ids = {};
  if (claudeOn()) {
    setJob('rodando', 'Asking Claude', e(q.slice(0, 60)));
    try {
      const r = await fetch(API + '/api/explore', {method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({question: q, userId: S.user, crm: S.crm, runs: runSummaries(), now: TODAY, model: S.settings.model})});
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || ('server ' + r.status));
      answer = j.answer; via = j.model || 'rules'; ids = {traceId: j.traceId || null, spanId: j.spanId || null};
    } catch (err) { toast('Claude did not answer (' + err.message + ') · answered from the CRM rules instead', 'neu'); }
    setJob('pronto');
  }
  if (!answer) answer = CORE.answerQuestion(q, exploreCtx());
  Object.assign(slot, {pending: false, answer, via, at: isoLocal()}, ids);
  UI.asking = false; UI.scrollChat = true; save(); renderExplore();
}
function newChat() {
  S.chatCurrent = null; save();
  if (location.hash === '#/explore') { renderExplore(); renderNav(); window.scrollTo(0, 0); } else location.hash = '#/explore';
  setTimeout(() => $('#ex-in').focus({preventScroll: true}), 0);
}
function openChat(id) {
  if (location.hash === '#/explore/' + id) { S.chatCurrent = id; renderExplore(); renderNav(); chatToEnd(); } else location.hash = '#/explore/' + encodeURIComponent(id);
}
/** An open chat lands on its last message, with the composer right below it. */
function chatToEnd() {
  const go = () => window.scrollTo(0, document.documentElement.scrollHeight);
  go(); requestAnimationFrame(go); setTimeout(go, 60);
  setTimeout(() => { const i = $('#ex-in'); if (i && view() === 'explore') i.focus({preventScroll: true}); }, 0);
}

// ------------------------------------------------------------------ view: meetings
const srcIcon = m => (m.chat || (m.source || {}).system === 'whatsapp' ? 'message-circle' : (m.source || {}).system === 'paste' ? 'file-text' : 'audio-lines');
// the channel shows by color too: transcripts in indigo, WhatsApp in green, pasted text in slate
const srcHue = m => (m.chat || (m.source || {}).system === 'whatsapp' ? 'green' : (m.source || {}).system === 'paste' ? 'slate' : 'indigo');
function renderMeetings() {
  const ms = myMeetings();
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
    : 'The agent finds the opportunity from the speakers and the company named in the conversation.';
  $$('.src-tabs [data-src]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.src === UI.src)));
  $('#drop').hidden = UI.src !== 'file';
  $('#paste').hidden = UI.src !== 'paste';
  if ($('#mt-q').value !== UI.mtQ) $('#mt-q').value = UI.mtQ;
  renderMeetingRows();
  renderDraft();
}
/** Search: every word must appear in the title, the people, the client or opportunity, or what was said. */
function meetingHit(m, toks) {
  if (!toks.length) return {ok: true};
  const opp = meetingOpp(m);
  const meta = [m.title, (m.participants || []).join(' '), opp ? clientOf(opp).name + ' ' + opp.name + ' ' + opp.opportunity_id : '', m.target ? m.target.client_name : '', CH.src(m)].join(' ').toLowerCase();
  const lines = CORE.transcriptLines(transcriptOf(m) || '');
  const said = lines.map(l => (l.speaker || '') + ' ' + (l.text || '')).join('\n').toLowerCase();
  if (!toks.every(t => meta.includes(t) || said.includes(t))) return {ok: false};
  const inSaid = toks.filter(t => !meta.includes(t));
  const look = inSaid.length ? inSaid : toks;
  const line = lines.find(l => look.every(t => ((l.text || '') + ' ' + (l.speaker || '')).toLowerCase().includes(t))) || lines.find(l => look.some(t => (l.text || '').toLowerCase().includes(t)));
  return {ok: true, line: inSaid.length ? line : null};
}
function renderMeetingRows() {
  const all = myMeetings().slice().sort((a, b) => (String(a.added_at || a.start) < String(b.added_at || b.start) ? 1 : -1));
  const toks = toksOf(UI.mtQ);
  const rows = all.map(m => ({m, hit: meetingHit(m, toks)})).filter(x => x.hit.ok);
  $('#mt-n').textContent = toks.length ? `${rows.length} of ${plural(all.length, 'meeting', 'meetings')}` : plural(all.length, 'meeting', 'meetings');
  const empty = toks.length ? `No meeting matches “${e(UI.mtQ.trim())}”. The search reads titles, people, clients and every line of the transcripts.`
    : isManager() ? 'As a manager you read the team\'s CRM; meetings are added by each seller.'
    : 'No meeting yet. Add a transcript or a chat export above: the agent prepares the CRM update.';
  $('#tb-meetings tbody').innerHTML = rows.length ? rows.map(({m, hit}) => {
    const run = latestRun(m.meeting_id);
    const opp = meetingOpp(m);
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
    const main = run ? `<a class="b b-sm ${waiting(run) ? 'b-p' : 'b-row'}" href="#/review/${e(run.id)}">${run.status === 'Blocked' ? 'See reason' : waiting(run) ? 'Review update' : 'Open'}</a>`
      : `<button class="b b-sm b-row" type="button" data-run="${e(m.meeting_id)}">Prepare CRM update</button>`;
    const n = (m.participants || []).length;
    const snip = hit.line ? `<button class="snip" type="button" data-open-mtg="${e(m.meeting_id)}" data-find="${e(UI.mtQ.trim())}" title="open the transcript at this line"><b>${e(spkName(hit.line.speaker))}</b> ${markTxt(clipAround(hit.line.text, toks[0]), toks)}</button>` : '';
    return `<tr data-mtg="${e(m.meeting_id)}" data-row-mtg="${e(m.meeting_id)}">
      <td><div class="mt-t"><span class="mt-ic hue-${srcHue(m)}" title="${e(CH.src(m))}">${ico(srcIcon(m), 'ico-b')}</span><div class="mt-tx"><button class="rec rec-b" type="button" data-open-mtg="${e(m.meeting_id)}" title="read the transcript">${toks.length ? markTxt(m.title, toks) : e(m.title)}</button>
        <span class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}${m.chat ? '' : m.recorded_minutes ? ` · ${e(m.recorded_minutes)} min` : ''}${n ? ` · ${plural(n, 'person', 'people')}` : ''}</span>${snip}</div></div></td>
      <td class="mid">${oppHtml}</td>
      <td class="mid">${runHtml}</td>
      <td class="mid act-c"><span class="acts">${main}</span></td></tr>`;
  }).join('') : `<tr><td colspan="4"><div class="empty soft">${empty}</div></td></tr>`;
  $$('#tb-meetings [data-run]').forEach(b => b.onclick = () => startRun(b.dataset.run));
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
// One card per group of the schema, so the kinds of information never run together; one row per field with
// what changes (now and new), the quote that proves it and the decision. The decision bar stays in view.
const GROUP_INFO = {
  conversation: ['message-circle', 'Logged with this conversation. It never overwrites the opportunity.', 'blue'],
  next_step: ['calendar-clock', 'The next step, who owns it and by when.', 'amber'],
  qualification: ['list-checks', 'What the buyer revealed: metrics, economic buyer, decision criteria and process, paper process, pain, champion and competition.', 'violet'],
  scope: ['users', 'How big the deal is: seats, teams, integrations, budget and go-live.', 'teal'],
  company: ['building-2', 'The client record, shared by every opportunity of this client.', 'slate'],
  stage: ['briefcase', 'Where the deal sits in the funnel. The agent moves it only on explicit evidence.', 'green'],
};
const REV_COLS = '<colgroup><col class="k-f"><col class="k-v"><col class="k-e"><col class="k-d"></colgroup>';
/** A value as people read it: dates and months in words; data-v keeps the stored value. */
function showVal(def, v, cls) {
  const c = cls || 'val';
  if (v == null || v === '') return '<span class="nada">empty</span>';
  let shown = String(v);
  if (def && def.type === 'date' && /^\d{4}-\d{2}-\d{2}$/.test(shown)) shown = fmtDate(shown, false);
  else if (def && def.type === 'month' && /^\d{4}-\d{2}$/.test(shown)) shown = MO[+shown.slice(5) - 1] + ' ' + shown.slice(0, 4);
  if (def && (def.type === 'select' || def.type === 'multiselect')) {
    const parts = shown.split(';').map(x => x.trim()).filter(Boolean);
    return `<span class="${c} opts" data-v="${e(v)}">${parts.map((x, i) => `${i ? '<span class="sep">; </span>' : ''}<span class="opt${/^Other:/i.test(x) ? ' oth' : ''}">${e(x)}</span>`).join('')}</span>`;
  }
  return `<span class="${c}" data-v="${e(v)}">${e(shown)}</span>`;
}
/** "Felipe Nunes (Acme Logistics)" -> name and organisation, so the name reads first. */
function spk(s) { const m = /^(.*?)\s*\(([^)]*)\)\s*$/.exec(s || ''); return m ? {name: m[1], org: m[2]} : {name: s || 'Unknown speaker', org: ''}; }
const spkName = s => spk(s).name;
const isSeller = s => { const p = spk(s); return /orbita/i.test(p.org) || FOTO.team.some(u => u.name === p.name); };
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
    return `<div class="rev-mdp">${mdpStrip(mdpBase, 'lg', known)}<span class="rev-mdp-t">${gaps.length ? `<b>Still unknown after this conversation:</b> ${e(gaps.map(g => g.label).join(', '))}. <b>Ask next:</b> “${e(gaps[0].ask)}”` : 'Every MEDDPICC element is known after this conversation.'}</span></div>`; })();
  head.innerHTML = `
    <nav class="crumbs" aria-label="you are here"><a href="#/meetings">Meetings</a>${ico('chevron-right')}${m ? `<button class="rec" type="button" data-open-mtg="${e(m.meeting_id)}" title="read the transcript">${e(m.title)}</button>` : `<span>${e(run.meetingId)}</span>`}</nav>
    <h1>${opp ? `<button class="rec rec-h" type="button" data-open-opp="${e(opp.opportunity_id)}" title="open the CRM record">${e(cl.name)}</button> <span class="h1-s">· ${e(opp.name)}</span>` : fresh ? `${e(o.target.client_name || 'New client')} <span class="h1-s">· new opportunity</span>` : e(m ? m.title : run.meetingId)}</h1>
    <div class="hdr-facts">
      ${opp ? `<span class="kf">${logo(cl.name)}<b>${e(opp.opportunity_id)}</b></span><span class="kf"><span class="k">Owner</span><b>${e(ownerName(opp))}</b></span><span class="kf"><span class="k">Stage</span>${CH.stage(run.stageAtRun || stageOf(opp))}</span>` : ''}
      ${m ? `<span class="kf"><span class="k">${e(CH.src(m))}</span><b>${e(fmtDate(m.start, false))}</b></span>` : ''}
      <span class="kf">${CH.run(run.status)}</span><span class="kf k">${by}</span>
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
      <div class="pn"><div class="pn-h"><h2>Why the stage moved, or not</h2></div><div class="pn-b">${stage && stage.note ? e(stage.note) : '<span class="nada">no note from the agent</span>'}</div></div>
      <div class="pn"><div class="pn-h"><h2>Left out of the CRM</h2><span class="pn-n">${o.ignored_out_of_scope.length}</span></div><div class="pn-b">${o.ignored_out_of_scope.length
        ? `<ul>${o.ignored_out_of_scope.map(x => `<li><span class="q">${e(x.quote)}</span><span class="why">${e(x.speaker)} · ${e(x.reason)}</span></li>`).join('')}</ul>`
        : '<span class="nada">nothing out of scope in this conversation</span>'}</div></div>
      <div class="pn"><div class="pn-h"><h2>Fixed by the checks</h2><span class="pn-n">${o.validation_notes.length}</span></div><div class="pn-b">${o.validation_notes.length
        ? `<ul>${o.validation_notes.map(x => `<li>${e(x)}</li>`).join('')}</ul>` : '<span class="nada">nothing to fix: every quote was found on its line and every value passed the field rules</span>'}</div></div>
    </div>`;
  const creation = fresh || (o.target && o.target.created) ? renderCreation(run, done) : '';
  const left = pend.length - decided + (needCreate ? 1 : 0);
  const made = decided + (fresh && createD ? 1 : 0), total = pend.length + (fresh ? 1 : 0);
  const written = done ? run.record.filter(r => r.write_result === 'Succeeded' && !r.reverted_at).length : 0;
  const bar = done
    ? `<div class="rv-bar is-done" id="rev-bar"><span class="rv-st">${ico('circle-check', 'ico-b')}<span><b>${e(run.status)}</b> · ${e(fmtDate(run.submittedAt))} · ${plural(written, 'field written', 'fields written')}</span></span><span class="grow"></span>
        ${o.opportunity_id ? `<a class="b b-sm b-s" href="#/opportunities/${e(o.opportunity_id)}">${ico('id-card')}Open the CRM record</a>` : ''}<a class="b b-sm b-t" href="#/settings/activity">Activity log</a></div>`
    : `<div class="rv-bar" id="rev-bar"><div class="rv-p"><span class="rv-c"><b>${made} of ${total}</b> decisions made</span><span class="rv-m" aria-hidden="true"><i style="transform:scaleX(${total ? (made / total).toFixed(3) : 1})"></i></span>
        <span class="rv-l">${left ? plural(left, 'decision', 'decisions') + ' left' : 'Ready to submit'}${autoN ? ` · ${plural(autoN, 'field', 'fields')} already written under Always allow` : ''}</span></div><span class="grow"></span>
        <button class="b b-p" type="button" id="rev-submit"${left ? ' disabled' : ''} title="${left ? 'every field that waits for you needs a decision first' : 'write the approved values to the CRM'}">Submit to CRM</button></div>`;
  body.innerHTML = `${bar}${creation}
    <div class="rv" id="tb-rev">
      <table class="tb rvt rv-cols" aria-hidden="true">${REV_COLS}<thead><tr><th>Field</th><th>What changes</th><th>Evidence from the conversation</th><th>${done ? 'Decision · result' : 'Your decision'}</th></tr></thead></table>
      ${groups}</div>
    <div class="rev-fb">${fbHtml('update', run.id)}</div>
    ${notes}`;
  wireReview(run);
}
function renderCreation(run, done) {
  const o = run.output, t = o.target, d = run.decisions.__create__;
  const created = t && t.created;
  const perm = perms().create_opportunity;
  let dec;
  if (created) dec = `<div class="dres">${CH.decision(d && d.decision || 'approve', created.auto ? 'permission' : 'seller')}<span class="ch ch-ok">Created</span><button class="rec" type="button" data-open-opp="${e(created.opportunity_id)}">${e(created.opportunity_id)}</button></div>`;
  else if (done) dec = `<div class="dres">${CH.decision(d ? d.decision : 'reject')}<span class="ch ch-neu">Not created</span></div>`;
  else if (d) dec = `<div class="dres">${CH.decision(d.decision)}<button class="b b-t chg" type="button" data-undo-create title="take the decision back">${ico('rotate-ccw')}Change</button></div>`;
  else dec = `<div class="dseg" role="group" aria-label="create the new opportunity"><button class="ds ds-ok" type="button" data-create="approve">${ico('check')}Approve creation</button><button class="ds" type="button" data-create="reject">${ico('x')}Reject</button></div>`;
  const editable = !created && !done && !d;
  const cname = d && d.client_name ? d.client_name : t.client_name, oname = d && d.opportunity_name ? d.opportunity_name : t.opportunity_name;
  return `<div class="pn newopp" id="rev-new"><div class="pn-h"><span class="rvg-i hue-blue">${ico('plus', 'ico-b')}</span><h2>${t.client_id ? 'New opportunity' : 'New client and opportunity'}</h2>
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
  const left = done ? 0 : act.filter(f => !run.decisions[f.field]).length;
  const rows = fs.map(f => renderFieldRow(run, f, done, quiet.includes(f) && !open, autoSet.has(f.field))).join('');
  const sum = quiet.length ? `<tr class="qsum"><td colspan="4"><button class="qbtn" type="button" data-quiet="${e(g.id)}" aria-expanded="${open ? 'true' : 'false'}">${ico(open ? 'chevron-down' : 'chevron-right')}<span class="qb-t">${open ? 'Hide' : 'Show'} ${plural(quiet.length, 'field', 'fields')} with nothing new</span><span class="qn">${quiet.map(f => e(DEF[f.field].label)).join(' · ')}</span></button></td></tr>` : '';
  const autoN = fs.filter(f => autoSet.has(f.field)).length;
  const info = GROUP_INFO[g.id] || ['list-checks', '', 'slate'];
  const count = done ? `${plural(act.length + autoN, 'field', 'fields')} decided` : act.length ? (left ? `${left} of ${act.length} to decide` : `all ${act.length} decided`) : 'nothing to decide';
  return `<section class="rvg${!done && left ? ' has-left' : ''}" data-group="${e(g.id)}" aria-labelledby="rvg-${e(g.id)}">
    <header class="rvg-h"><span class="rvg-i hue-${info[2]}">${ico(info[0], 'ico-b')}</span><div class="rvg-t"><h2 id="rvg-${e(g.id)}">${e(g.label)}</h2><p>${e(info[1])}</p></div>
      <span class="rvg-n"><b>${count}</b>${autoN ? `<span>${autoN} written under Always allow</span>` : ''}</span>${pendingApprove > 1 ? `<button class="b b-sm b-s" type="button" data-approve-group="${e(g.id)}">${ico('check')}Approve ${pendingApprove} in ${e(g.label.replace(/ \(.*\)$/, ''))}</button>` : ''}</header>
    <table class="tb rvt">${REV_COLS}<thead class="vh"><tr><th>Field</th><th>What changes</th><th>Evidence</th><th>Decision</th></tr></thead><tbody class="rg" data-group="${e(g.id)}">${rows}${sum}</tbody></table></section>`;
}
function evidenceHtml(run, list) {
  const one = x => { const p = spk(x.speaker); return `<button class="evb" type="button" data-ev="${e(run.meetingId)}|${e(x.line)}" title="show this line in the transcript"><q>${e(x.quote)}</q><span class="evm">${x.timestamp && x.timestamp !== '00:00:00' ? `<time>${e(/^\d{4}-/.test(x.timestamp) ? fmtShort(x.timestamp) + ' ' + x.timestamp.slice(11) : x.timestamp)}</time>` : ''}<span class="evw"><b>${e(p.name)}</b>${p.org ? ` · ${e(p.org)}` : ''}</span></span></button>`; };
  if (!list.length) return '<span class="nada">no quote</span>';
  return `<div class="ev">${one(list[0])}${list.length > 1 ? `<details class="evx"><summary>${plural(list.length - 1, 'more quote', 'more quotes')}</summary>${list.slice(1).map(one).join('')}</details>` : ''}</div>`;
}
function renderFieldRow(run, f, done, hide, isAuto) {
  const def = DEF[f.field];
  const d = run.decisions[f.field];
  const rec = (run.record || run.autoRecord || []).find(r => r.field === f.field) || null;
  const kind = def.kind === 'per_call' ? 'this conversation' : def.record === 'client' ? 'client record' : '';
  const hasCur = f.current_value != null && f.current_value !== '';
  const now = hasCur ? `<div class="dl"><span class="dk">Now</span><span class="dv">${showVal(def, f.current_value, 'cv')}${f.current_approved ? '' : `<span class="appr no">${ico('circle-dashed')}not approved</span>`}</span></div>` : '';
  let prop;
  if (f.status === 'proposed' || f.status === 'unchanged') {
    const edited = d && d.decision === 'edit' && d.value != null;
    const nv = edited ? `${showVal(def, d.value)}<span class="ed">edited by ${e(userById(run.userId).name)} · the agent proposed <s>${e(f.proposed_value)}</s></span>` : showVal(def, f.proposed_value);
    prop = `<div class="prop${hasCur ? ' two' : ''}">${f.status === 'unchanged' ? CH.field('unchanged') : ''}${now}<div class="dl dn">${hasCur ? '<span class="dk">New</span>' : ''}<span class="dv">${nv}</span></div>${f.note ? `<span class="lab">${e(f.note)}</span>` : ''}</div>`;
  } else if (f.status === 'contradictory') {
    const rep = d && d.decision === 'replace' ? `<div class="dl dn"><span class="dk">New</span><span class="dv">${showVal(def, d.value)}<span class="ed">replacement by the seller</span></span></div>` : d && d.decision === 'clear' ? '<span class="lab"><b>Cleared by the seller</b></span>' : '';
    prop = `<div class="prop two">${CH.field(f.status)}${now}<span class="lab">The conversation contradicts the approved value and agrees no new one.${f.note ? ' ' + e(f.note) : ''}</span>${rep}</div>`;
  } else {
    prop = `<div class="prop">${CH.field(f.status)}<span class="lab">${f.note ? e(f.note) : 'Not discussed, vague or only implied. The current value stays.'}</span></div>`;
  }
  let dec;
  if (f.status === 'no_evidence') dec = '<div class="dec"><span class="ch ch-nd">No evidence</span><span class="note">nothing to decide</span></div>';
  else if (f.status === 'off') dec = '<div class="dec"><span class="ch ch-nd">Off</span><span class="note">turned off in Settings › Permissions</span></div>';
  else if (f.status === 'unchanged') dec = '<div class="dec"><span class="ch ch-neu">Unchanged</span><span class="note">the conversation confirmed the approved value</span></div>';
  else if (isAuto && rec) dec = `<div class="dec"><div class="dres">${CH.decision('approve', 'permission')}${CH.write(rec.write_result, rec.reverted_at)}${!rec.reverted_at && rec.write_result === 'Succeeded' ? `<button class="b b-t chg" type="button" data-undo-auto title="put the previous value back">${ico('rotate-ccw')}Undo</button>` : ''}</div></div>`;
  else if (isAuto) dec = `<div class="dec"><div class="dres">${CH.decision('approve', 'permission')}<span class="note">written with the new opportunity</span></div></div>`;
  else if (done && rec) dec = `<div class="dec"><div class="dres">${CH.decision(rec.seller_decision, rec.decided_by)}${CH.write(rec.write_result, rec.reverted_at)}${rec.rejection_reason ? `<span class="mini">reason: ${e(rec.rejection_reason)}</span>` : ''}</div></div>`;
  else dec = `<div class="dec">${renderDecision(run, f, d)}</div>`;
  const st = isAuto ? 'auto' : d ? d.decision : '';
  const tag = def.meddpicc ? `<span class="mdp-l" title="MEDDPICC · ${e(def.label)}">${e(def.meddpicc)}</span>` : '';
  return `<tr data-field="${e(f.field)}" data-status="${e(f.status)}"${isAuto ? ' data-auto="1"' : ''}${st ? ` data-d="${e(st)}"` : ''}${hide ? ' hidden' : ''}><td class="c-f"><span class="fname">${tag}<span>${e(def.label)}</span></span>${kind ? `<span class="fkind">${e(kind)}</span>` : ''}</td><td class="c-v">${prop}</td><td class="c-e">${evidenceHtml(run, f.evidence)}</td><td class="c-d">${dec}</td></tr>`;
}
function editorHtml(def, start, run) {
  const v = start == null ? '' : String(start);
  if (def.type === 'integer') return `<input class="inp" id="dec-text" type="number" min="1" step="1" value="${e(v)}">`;
  if (def.type === 'date') return `<input class="inp" id="dec-text" type="date" value="${e(v)}">`;
  if (def.type === 'month') return `<input class="inp" id="dec-text" type="month" value="${e(v)}">`;
  if (def.type === 'roster') return `<select class="inp" id="dec-text">${FOTO.team.map(u => `<option${u.name === v ? ' selected' : ''}>${e(u.name)}</option>`).join('')}</select>`;
  if (def.type === 'stage') return `<select class="inp" id="dec-text">${STAGES.map(s => `<option${s === v ? ' selected' : ''}>${e(s)}</option>`).join('')}</select>`;
  // picklists (schema v4): one option, or several, and "Other: <text>" where the field allows it
  if (def.type === 'select') {
    const other = /^Other: /.test(v) ? v.slice(7) : '';
    return `<select class="inp" id="dec-text" aria-label="${e(def.label)}">${def.options.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}${def.allow_other ? `<option value="__other__"${other ? ' selected' : ''}>Other…</option>` : ''}</select>${def.allow_other ? `<input class="inp" id="dec-other" placeholder="Other: a few words" aria-label="other ${e(def.label)}" value="${e(other)}">` : ''}`;
  }
  if (def.type === 'multiselect') {
    const parts = v.split(';').map(x => x.trim()).filter(Boolean), on = new Set(parts.map(x => x.toLowerCase()));
    const others = parts.filter(x => /^Other:/i.test(x)).map(x => x.replace(/^Other:\s*/i, ''));
    return `<div class="chkset" id="dec-multi" role="group" aria-label="${e(def.label)}">${def.options.map(o => `<label><input type="checkbox" value="${e(o)}"${on.has(o.toLowerCase()) ? ' checked' : ''}>${e(o)}</label>`).join('')}</div>${def.allow_other ? `<input class="inp" id="dec-other" placeholder="Other (several separated by ;)" aria-label="other ${e(def.label)}" value="${e(others.join('; '))}">` : ''}`;
  }
  if (def.type === 'person') {
    // a contact of the client from the CRM, or another name typed in
    const opp = run && run.output.opportunity_id ? oppById(run.output.opportunity_id) : null, cl = opp ? clientOf(opp) : null;
    return `<input class="inp" id="dec-text" list="dec-contacts" value="${e(v)}" placeholder="Full name (job title)"><datalist id="dec-contacts">${((cl && cl.contacts) || []).map(c => `<option value="${e(c.name + (c.title ? ' (' + c.title + ')' : ''))}">`).join('')}</datalist>`;
  }
  return `<textarea class="inp" id="dec-text" rows="3">${e(v)}</textarea>`;
}
function editorValue(def) {
  const other = () => (($('#dec-other') || {}).value || '').split(';').map(x => x.trim()).filter(Boolean).map(x => 'Other: ' + x);
  if (def.type === 'multiselect') return $$('#dec-multi input:checked').map(x => x.value).concat(other()).join('; ');
  if (def.type === 'select' && ($('#dec-text') || {}).value === '__other__') return other()[0] || '';
  return (($('#dec-text') || {}).value || '').trim();
}
function renderDecision(run, f, d) {
  const def = DEF[f.field];
  const ed = UI.editing && UI.editing.runId === run.id && UI.editing.field === f.field ? UI.editing.mode : null;
  if (ed === 'edit' || ed === 'replace') {
    const start = ed === 'edit' ? (d && d.value != null ? d.value : f.proposed_value) : (d && d.value != null ? d.value : (f.current_value || ''));
    return `<div class="edit"><span class="fld-l">${ed === 'edit' ? 'Edited value' : 'New value'} <i>${e(def.format)}</i></span>${editorHtml(def, start, run)}
      <span class="acts"><button class="b b-xs b-p" type="button" data-save="${ed}">Save</button><button class="b b-xs b-t" type="button" data-cancel>Cancel</button></span></div>`;
  }
  if (ed === 'reject') {
    return `<div class="edit"><label class="fld"><span class="fld-l">Reason <i>optional</i></span><input class="inp" id="dec-text" value="${e(d && d.reason || '')}" placeholder="why the proposal is wrong"></label>
      <span class="acts"><button class="b b-xs b-d" type="button" data-save="reject">Reject</button><button class="b b-xs b-t" type="button" data-cancel>Cancel</button></span></div>`;
  }
  if (d) {
    const extra = d.decision === 'reject' && d.reason ? `<span class="mini">reason: ${e(d.reason)}</span>` : '';
    return `<div class="dres">${CH.decision(d.decision)}${extra}<button class="b b-t chg" type="button" data-undo title="take the decision back">${ico('rotate-ccw')}Change</button></div>`;
  }
  if (f.status === 'proposed') {
    return `<div class="dseg" role="group" aria-label="decision on ${e(def.label)}"><button class="ds ds-ok" type="button" data-dec="approve">${ico('check')}Approve</button><button class="ds" type="button" data-open="edit">Edit</button><button class="ds" type="button" data-open="reject">Reject</button></div>`;
  }
  return `<div class="dseg" role="group" aria-label="decision on ${e(def.label)}"><button class="ds ds-ok" type="button" data-dec="keep" title="keep the current approved value">Keep</button><button class="ds" type="button" data-open="replace">Replace</button><button class="ds" type="button" data-dec="clear" title="clear the field in the CRM">Clear</button></div>`;
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

// ------------------------------------------------------------------ the meeting reader (drawer): what came of it, who spoke, the transcript
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const toksOf = q => String(q || '').toLowerCase().split(/\s+/).filter(t => t.length > 1 || /\d/.test(t));
/** Escapes the text, then marks each search word in it. */
function markTxt(text, toks) {
  const safe = e(text);
  if (!toks || !toks.length) return safe;
  return safe.replace(new RegExp('(' + toks.map(t => reEsc(e(t))).join('|') + ')', 'gi'), '<mark>$1</mark>');
}
function clipAround(text, tok, n) {
  const s = String(text || ''), w = n || 150;
  if (s.length <= w) return s;
  const i = Math.max(0, s.toLowerCase().indexOf(tok || '') - 50);
  return (i > 0 ? '…' : '') + s.slice(i, i + w).trim() + (i + w < s.length ? '…' : '');
}
/** The opportunity a meeting landed on, if the user can read it. */
function meetingOpp(m) {
  const run = latestRun(m.meeting_id);
  if (run && run.output.source_status === 'AccessDenied') return null;
  if (run && run.output.opportunity_id) return oppById(run.output.opportunity_id) || null;
  const o = m.linked_opportunity_id && oppById(m.linked_opportunity_id);
  return o && canRead(o) ? o : null;
}
function openMeeting(meetingId, opts) {
  opts = opts || {};
  const m = meetingById(meetingId), dlg = $('#drw');
  if (!m || !dlg) return;
  UI.mtg = {id: meetingId, line: opts.line || null, find: opts.find || '', k: -1};
  const lines = CORE.transcriptLines(transcriptOf(m) || '');
  const run = latestRun(m.meeting_id), opp = meetingOpp(m);
  $('#drw-t').textContent = m.title;
  $('#drw-m').textContent = [fmtDate(m.start, false), CH.src(m), !m.chat && m.recorded_minutes ? m.recorded_minutes + ' min' : null, plural(lines.length, 'line', 'lines')].filter(Boolean).join(' · ');
  const who = [...new Set(lines.map(l => l.speaker).filter(Boolean))];
  const people = (who.length ? who : (m.participants || [])).map(s => { const p = spk(s); return `<span class="pp${isSeller(s) ? ' us' : ''}"><b>${e(p.name)}</b>${p.org ? `<span>${e(p.org)}</span>` : ''}</span>`; }).join('');
  const pend = run ? pendingFields(run).length : 0;
  const upd = !run ? '<span class="nada">not prepared yet</span>'
    : run.status === 'Blocked' ? `${CH.run('Blocked')}<span class="ms-x">${e(blockShort(run.output.source_status))}</span>`
    : waiting(run) ? `${CH.run('Awaiting review')}<span class="ms-x">${plural(pend, 'field to decide', 'fields to decide')}</span>`
    : `${CH.run(run.status)}<span class="ms-x">${plural((run.record || []).filter(x => x.write_result === 'Succeeded' && !x.reverted_at).length, 'field written', 'fields written')}</span>`;
  const act = run ? `<a class="b b-sm ${waiting(run) ? 'b-p' : 'b-s'}" href="#/review/${e(run.id)}">${run.status === 'Blocked' ? 'See why it stopped' : waiting(run) ? 'Review update' : 'Open the review'}</a>`
    : `<button class="b b-sm b-p" type="button" data-run-mtg="${e(m.meeting_id)}">Prepare CRM update</button>`;
  const oppHtml = opp ? oppTitle(opp) : m.target ? `<span class="ttl">${logo(m.target.client_name)}<span><b>${e(m.target.client_name || 'New client')}</b><span class="sub">new opportunity</span></span></span>`
    : run && run.output.source_status === 'AccessDenied' ? '<span class="ch ch-nd">no access</span>' : '<span class="nada">not linked to an opportunity</span>';
  $('#drw-b').innerHTML = `
    <section class="mtg-sum" aria-label="what came of this meeting">
      <div class="ms-r"><span class="ms-k">Opportunity</span><span class="ms-v">${oppHtml}</span></div>
      <div class="ms-r"><span class="ms-k">CRM update</span><span class="ms-v">${upd}</span><span class="ms-a">${act}</span></div>
      <div class="ms-r"><span class="ms-k">People</span><span class="ms-v pps">${people || '<span class="nada">no speaker named</span>'}</span></div>
    </section>
    <div class="tl-bar"><label class="srch tl-find">${ico('search')}<input id="tl-q" type="search" placeholder="Find in this transcript" aria-label="find in this transcript" value="${e(UI.mtg.find)}"></label><span class="tl-n" id="tl-n" aria-live="polite"></span></div>
    <div class="tl-list" id="tl-list"></div>`;
  renderLines(m, lines);
  const fq = $('#tl-q');
  fq.addEventListener('input', () => { UI.mtg.find = fq.value; UI.mtg.k = -1; renderLines(m, lines); });
  fq.addEventListener('keydown', ev => { if (ev.key === 'Enter') { ev.preventDefault(); nextHit(ev.shiftKey ? -1 : 1); } });
  $$('#drw-b a[href^="#/"]').forEach(a => a.addEventListener('click', () => dlg.close()));
  const rb = $('#drw-b [data-run-mtg]'); if (rb) rb.onclick = () => { dlg.close(); startRun(rb.dataset.runMtg); };
  if (!dlg.open) dlg.showModal();
  const target = $('#tl-hl') || (UI.mtg.find ? $('#tl-list .tl.hit') : null);
  if (target) { const go = () => target.scrollIntoView({block: 'center'}); requestAnimationFrame(go); setTimeout(go, 60); }
  else $('#drw-b').scrollTop = 0;
}
function renderLines(m, lines) {
  const toks = toksOf(UI.mtg.find);
  const bare = lines.length && lines.every(l => l.timestamp === '00:00:00');
  let prev = null, hits = 0;
  $('#tl-list').innerHTML = lines.length ? lines.map(l => {
    const hl = l.n === UI.mtg.line;
    const low = ((l.text || '') + ' ' + (l.speaker || '')).toLowerCase();
    const hit = toks.length && toks.every(t => low.includes(t));
    if (hit) hits++;
    const cont = prev === l.speaker && !hl; prev = l.speaker;
    const t = bare ? `L${l.n}` : m.chat ? l.timestamp.slice(11) : l.timestamp;
    const p = spk(l.speaker);
    return `<div class="tl${isSeller(l.speaker) ? ' us' : ''}${hl ? ' hl' : ''}${hit ? ' hit' : ''}${cont ? ' cont' : ''}" data-n="${l.n}"${hl ? ' id="tl-hl"' : ''}><time>${e(t)}</time><div class="tl-c">${cont ? '' : `<span class="who"><b>${e(p.name)}</b>${p.org ? `<span class="org">${e(p.org)}</span>` : ''}${hl ? '<span class="tl-mark">evidence</span>' : ''}</span>`}<p class="tl-x">${hit ? markTxt(l.text, toks) : e(l.text)}</p></div></div>`;
  }).join('') : '<div class="empty">No transcript text for this meeting.</div>';
  $('#tl-n').textContent = toks.length ? (hits ? plural(hits, 'line matches', 'lines match') + ' · Enter for the next' : 'no line matches') : '';
}
function nextHit(d) {
  const hs = $$('#tl-list .tl.hit');
  if (!hs.length) return;
  hs.forEach(h => h.classList.remove('cur'));
  UI.mtg.k = (UI.mtg.k + d + hs.length) % hs.length;
  hs[UI.mtg.k].classList.add('cur');
  hs[UI.mtg.k].scrollIntoView({block: 'center'});
}
/** Evidence: the transcript opens on the quoted line. */
function openTranscript(meetingId, lineNo) { openMeeting(meetingId, {line: lineNo}); }

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
  $('#opps-groups').classList.toggle('own', !isManager()); // a seller owns every row: no owner column
  $('#opps-groups').innerHTML = `<div class="fr fr-h" aria-hidden="true"><span>Client · opportunity</span><span>Owner</span><span>Amount</span><span>Next follow-up</span><span>Qualification</span><span></span></div>` + OPEN_STAGES.map((s, i) => {
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
  return `<li class="fr rowh" data-opp="${e(o.opportunity_id)}" data-row-opp="${e(o.opportunity_id)}">
    <span class="fr-c">${oppTitle(o)}</span>
    <span class="fr-c">${e(ownerName(o))}</span>
    <span class="fr-c fr-num"><b>${e(fmtUSD(o.amount_usd))}</b><span class="sub">${o.close_date ? 'closes ' + e(fmtShort(o.close_date)) : 'no close date'}</span></span>
    <span class="fr-c">${dueChip(o)}<span class="sub fr-ns">${ns ? e(ns) : 'no next step'}</span></span>
    <span class="fr-c">${mdpStrip(o)}<span class="sub">${byRun ? 'updated ' + e(fmtShort(o.last_updated)) + ' by an update' : 'updated ' + e(fmtShort(o.last_updated))}</span></span>
    <span class="fr-c fr-act">${aw ? `<a class="b b-sm b-s" href="#/review/${e(aw.id)}">Review update</a>` : ''}<button class="b b-sm b-t go" type="button" data-details="${e(o.opportunity_id)}" aria-label="open ${e(clientOf(o).name)} · ${e(o.name)}" title="open the record">${ico('chevron-right')}</button></span>
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
    return `<div><dt>${d.meddpicc ? `<span class="mdp-l">${e(d.meddpicc)}</span>` : ''}${e(d.label)}</dt><dd>${d.options ? showVal(d, f.value, 'kvv') : valueOr(f.value)} ${apprMark(f)}${w ? `<span class="sub">written by update ${e(w.id)} · ${e(fmtDate(w.submittedAt || w.autoAt))}</span>` : ''}</dd></div>`;
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
    <section class="dsec"><h3>Conversations <span class="mini">transcripts and chats that fed this record</span></h3>${ms.length ? `<ul class="mlist">${ms.map(m => { const r = latestRun(m.meeting_id); return `<li class="rowh" data-row-mtg="${e(m.meeting_id)}"><span class="mt-ic hue-${srcHue(m)}">${ico(srcIcon(m), 'ico-s')}</span><span class="ml-x"><button class="rec" type="button" data-open-mtg="${e(m.meeting_id)}" title="read the transcript">${e(m.title)}</button><span class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}</span></span>${r ? CH.run(r.status) : '<span class="nada">not prepared</span>'}</li>`; }).join('')}</ul>` : '<p class="nada pad">No conversation added for this opportunity yet.</p>'}</section>
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
    <section class="dsec"><h3>Opportunities <span class="mini">${readable.length}</span></h3><table class="tb"><thead><tr><th>Opportunity</th><th>Stage</th><th class="num">Amount</th><th>Owner</th><th></th></tr></thead><tbody>${readable.map(o => `<tr class="rowh" data-row-opp="${e(o.opportunity_id)}"><td><button class="rec" type="button" data-open-opp="${e(o.opportunity_id)}">${e(o.name)}</button><div class="sub">${e(o.opportunity_id)}</div></td><td>${CH.stage(stageOf(o))}</td><td class="num nw">${e(fmtUSD(o.amount_usd))}</td><td class="nw">${e(ownerName(o))}</td><td><button class="b b-sm b-t go" type="button" data-details="${e(o.opportunity_id)}" aria-label="open ${e(o.name)}" title="open the record">${ico('chevron-right')}</button></td></tr>`).join('')}</tbody></table></section>
    <section class="dsec"><h3>Recent conversations</h3>${ms.length ? `<ul class="mlist">${ms.map(m => `<li class="rowh" data-row-mtg="${e(m.meeting_id)}"><span class="mt-ic hue-${srcHue(m)}">${ico(srcIcon(m), 'ico-s')}</span><span class="ml-x"><button class="rec" type="button" data-open-mtg="${e(m.meeting_id)}" title="read the transcript">${e(m.title)}</button><span class="sub">${e(fmtDate(m.start, false))} · ${e(CH.src(m))}</span></span></li>`).join('')}</ul>` : '<p class="nada pad">No conversation of yours with this client yet.</p>'}</section>`;
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
    const tags = [c.industry, c.hq, emp ? `${emp} employees` : null, cur ? `today: ${cur}` : null].filter(Boolean);
    return `<article class="cl-card" data-client="${e(c.client_id)}" aria-labelledby="cl-h-${e(c.client_id)}">
      <header class="cl-h">${logo(c.name, 32)}<div class="cl-id"><h2 id="cl-h-${e(c.client_id)}"><button class="rec rec-h2" type="button" data-open-client="${e(c.client_id)}" title="open the client record">${e(c.name)}</button></h2>
        <div class="cl-f">${tags.length ? tags.map(t => `<span class="tag">${e(t)}</span>`).join('') : '<span class="nada">profile to complete</span>'}</div></div>
        <div class="cl-r"><span class="cl-sum"><b>${plural(open.length, 'open opportunity', 'open opportunities')}</b>${open.length ? ' · ' + e(fmtUSD(sum)) : ''}</span><span class="sub">${plural(c.contacts.length, 'contact', 'contacts')}${last ? ' · last meeting ' + e(fmtShort(last)) : ''}</span></div>
        <button class="b b-sm b-s" type="button" data-client-details="${e(c.client_id)}">Client details</button></header>
      <ul class="cl-ops">${os.map(o => `<li class="cl-op rowh" data-opp="${e(o.opportunity_id)}" data-row-opp="${e(o.opportunity_id)}">
        <span class="cl-on"><button class="rec" type="button" data-open-opp="${e(o.opportunity_id)}" title="open the CRM record">${e(o.name)}</button><span class="sub">${e(o.opportunity_id)}</span></span>
        <span>${CH.stage(stageOf(o))}</span>
        <span class="num"><b>${e(fmtUSD(o.amount_usd))}</b><span class="sub">${o.close_date ? 'closes ' + e(fmtShort(o.close_date)) : 'no close date'}</span></span>
        <span class="nw">${e(ownerName(o))}</span>
        <span>${dueChip(o)}</span>
        <span>${mdpStrip(o)}</span>
        <span class="cl-act"><button class="b b-sm b-t go" type="button" data-details="${e(o.opportunity_id)}" aria-label="open ${e(o.name)}" title="open the record">${ico('chevron-right')}</button></span></li>`).join('')}</ul>
    </article>`;
  }).join('') : '<div class="empty">No client matches.</div>';
  $$('#cl-list [data-details]').forEach(b => b.onclick = () => openOppDrawer(b.dataset.details));
  $$('#cl-list [data-client-details]').forEach(b => b.onclick = () => openClientDrawer(b.dataset.clientDetails));
}

// ------------------------------------------------------------------ view: settings
function renderSettings() {
  $$('#set-tabs [data-tab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === UI.setTab)));
  ({permissions: renderPerms, agent: renderAgentTab, sources: renderSources, team: renderTeam, activity: renderActivity, data: renderData})[UI.setTab]();
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
  download('orbita_crm_activity_log.json', JSON.stringify({exported_at: isoLocal(), schema: 'agent/run_log_schema.json', permissions: perms(), runs, decisions: S.events, feedback: visibleFeedback()}, null, 2), 'application/json');
}
/** The seller feedback panel of Quality checks: the explicit ratings, and the corrections sellers made in what they wrote. */
function fbPanel() {
  const all = visibleFeedback(), down = all.filter(f => f.rating === 'down');
  const share = s => { const xs = all.filter(f => f.surface === s); return xs.length ? `${Math.round(100 * xs.filter(f => f.rating === 'up').length / xs.length)}% rated right, of ${xs.length}` : 'no ratings yet'; };
  const rec = visibleRuns().flatMap(r => (r.record || []).filter(x => x.decided_by !== 'permission'));
  const cnt = ks => rec.filter(x => ks.includes(x.seller_decision)).length;
  const undone = visibleRuns().flatMap(r => r.autoRecord || []).filter(x => x.reverted_at).length;
  const rows = all.map(f => `<tr data-fb-row="${e(f.id)}" data-rating="${f.rating}"><td class="mid">${e(fmtDate(f.at))}<div class="sub">${e((userById(f.user) || {}).name || f.user)}</div></td>
      <td>${f.surface === 'update' ? 'CRM update' : 'Explore answer'}<div class="sub">${e(f.label)}</div></td>
      <td class="mid">${f.rating === 'up' ? '<span class="ch ch-ok">Right</span>' : '<span class="ch ch-bad">Not right</span>'}</td>
      <td>${f.rating === 'down' ? (f.sent ? e(reasonLabel(f)) : '<span class="nada">reason not sent yet</span>') + (f.note ? `<div class="sub">${e(f.note)}</div>` : '') : '<span class="nada">none needed</span>'}</td>
      <td class="mid">${e(fbModel(f))}</td>
      <td class="mid"><span class="acts">${f.rating === 'down' && (f.surface === 'explore' || S.runs[f.ref]) ? `<button class="b b-sm b-s" type="button" data-evtrace="${e(f.surface === 'update' ? 'PROD-' + f.ref : 'PRODX-' + String(f.ref).replace(':', '-'))}">Review trace</button>` : ''}${f.surface === 'update' && S.runs[f.ref] ? `<a class="b b-sm b-t" href="#/review/${e(f.ref)}">Open update</a>` : ''}</span></td></tr>`).join('');
  return `
    <div class="pn" id="fb-panel"><div class="pn-h"><h2>Seller feedback</h2><span class="pn-n">${all.length ? `${plural(all.length, 'rating', 'ratings')} · ${down.length} not right` : 'no ratings yet'}</span>
      <span class="acts"><button class="b b-sm b-t" type="button" id="fb-export"${all.length ? '' : ' disabled'}>${ico('download')}Download feedback (JSON)</button></span></div>
      <div class="pn-b purpose"><b>Who reads this.</b> The agent owner in sales operations reads every "not right" each Monday and reviews its trace. A confirmed failure becomes a note, then a failure mode, then a new test conversation in the eval set before the next change to the prompt, the examples or the model.</div>
      <div class="fb-sum"><span>CRM updates: <b>${share('update')}</b></span><span>Explore answers: <b>${share('explore')}</b></span><span>Corrections in written updates: <b>${cnt(['edit', 'replace'])} edited, ${cnt(['reject', 'clear'])} rejected, ${undone} undone</b> of ${plural(rec.length + undone, 'decided field', 'decided fields')}</span></div>
      <div class="tbw"><table class="tb" id="tb-fb"><thead><tr><th>When</th><th>Where</th><th>Rating</th><th>Reason</th><th>Model</th><th><span class="sr">Open</span></th></tr></thead><tbody>
      ${rows || '<tr><td colspan="6"><span class="nada">No ratings yet. Sellers rate each CRM update and each Explore answer with a thumbs up or down.</span></td></tr>'}
      </tbody></table></div>
      <div class="pn-f">${LIVE.ok ? "Each rating also goes to the server's feedback file." : 'Ratings stay in this browser until the server runs; download them for the weekly review.'}</div></div>`;
}
function exportFeedback() {
  download('orbita_crm_feedback.json', JSON.stringify({exported_at: isoLocal(), read_by: 'agent owner (sales operations), every Monday', feedback: visibleFeedback()}, null, 2), 'application/json');
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
  $('#ev-body').innerHTML = `
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
// ------------------------------------------------------------------ view: evals (collect -> review -> name -> fix and check)
// Error analysis as Hamel Husain and Shreya Shankar teach it: judge real traces Pass or Fail, write what went wrong
// in your own words, then group the notes into failure modes and fix the biggest. The labels, notes and modes are
// the same files as the standalone review app (eval/error_discovery/error_discovery_data), through the server.
const EVD = FOTO.evals || {traces: [], sample: [], batches: [], annotations: [], reviewed: {}, labels: {}, modes: []};
const EV_TABS = ['dashboard', 'feedback', 'traces', 'modes', 'evalset'];
const VERDICT = {pass: ['Pass', 'ch-ok'], fail: ['Fail', 'ch-bad'], defer: ['Deferred', 'ch-warn']};
const TSTATUS = {proposed: 'Proposed', unchanged: 'Same as CRM', contradictory: 'Contradicts CRM', no_evidence: 'No evidence', off: 'Off'};
function freshEvals() { return {ann: deep(EVD.annotations || []), reviewed: deep(EVD.reviewed || {}), labels: deep(EVD.labels || {}), modes: deep(EVD.modes || []), jl: deep(EVD.judge_labels || {})}; }
const evLabel = id => (S.evals.labels[id] || {}).verdict || null;
const evNote = id => S.evals.ann.find(a => a.record_id === id && a.block === 'trace') || null;
const modeKey = m => m.id || m.name;
const modeOfNote = aid => S.evals.modes.find(m => (m.annotation_ids || []).includes(aid)) || null;
const shortModel = id => id === 'platform' ? 'stopped before the model' : id === 'rules' ? 'CRM rules' : id === 'saved' ? 'saved result' : modelName(id).replace('Claude ', '');
const fmtV = v => (Array.isArray(v) ? v.join('; ') : typeof v === 'number' ? v.toLocaleString('en-US') : String(v));
const itemText = x => (typeof x === 'string' ? x : x && x.quote ? `“${x.quote}” · ${x.reason || ''}` : x ? [x.field, x.message || x.note || x.reason].filter(Boolean).join(': ') : '');

/** Production traces: every update or Explore answer a seller rated "not right", as long as it is in this browser. */
function prodTraces() {
  return visibleFeedback().filter(f => f.rating === 'down').map(f => {
    if (f.surface === 'update') {
      const r = S.runs[f.ref]; if (!r) return null;
      const m = meetingById(r.meetingId);
      return {id: 'PROD-' + r.id, kind: 'update', prod: true, fb: f, run: r, case_id: r.id, client: f.label || runTarget(r) || 'CRM update', case_name: m ? m.title : r.meetingId, model: r.mode === 'live' ? r.model : r.mode, meeting_id: r.meetingId};
    }
    const [chatId, i] = String(f.ref).split(':');
    const chat = S.chats.find(c => c.id === chatId), msg = chat && chat.messages[+i];
    if (!msg || !msg.answer) return null;
    return {id: 'PRODX-' + chatId + '-' + i, kind: 'explore', prod: true, fb: f, msg, question: f.question || (chat.messages[+i - 1] || {}).text || chat.title, case_id: 'Explore', client: 'Explore answer', case_name: f.question || chat.title, model: msg.via};
  }).filter(Boolean);
}
function evQueue() {
  const order = id => { const i = EVD.sample.indexOf(id); return i < 0 ? 999 : i; };
  const evals = EVD.traces.filter(t => UI.ev.all || !EVD.sample.length || EVD.sample.includes(t.id)).map(t => Object.assign({kind: 'eval'}, t)).sort((a, b) => order(a.id) - order(b.id));
  return prodTraces().concat(evals);
}
function evFiltered() { const f = UI.ev.filter; return evQueue().filter(t => f === 'all' || (f === 'todo' ? !evLabel(t.id) : evLabel(t.id) === f)); }

let evTimer = null;
function evSave() {
  save();
  UI.ev.saved = LIVE.ok ? 'saving' : 'local';
  evStatus();
  clearTimeout(evTimer); evTimer = setTimeout(evPush, 300);
}
async function evPush() {
  if (!LIVE.ok) return;
  try {
    const body = {annotations: S.evals.ann, reviewed: S.evals.reviewed, labels: S.evals.labels, modes: S.evals.modes, judge_labels: S.evals.jl || {}};
    const r = await fetch(API + '/api/evals', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
    UI.ev.saved = r.ok ? 'disk' : 'local';
  } catch (_) { UI.ev.saved = 'local'; }
  evStatus();
}
/** With the server on, the labels and notes on disk join the ones in this browser (the newest label wins). */
async function evPull() {
  if (!LIVE.ok) return;
  try {
    const r = await fetch(API + '/api/evals', {cache: 'no-store'});
    if (!r.ok) return;
    const d = await r.json();
    const have = new Set(S.evals.ann.map(a => a.id));
    (d.annotations || []).forEach(a => { if (!have.has(a.id)) S.evals.ann.push(a); });
    Object.entries(d.labels || {}).forEach(([k, v]) => { const cur = S.evals.labels[k]; if (v && v.verdict && (!cur || String(v.at || '') > String(cur.at || ''))) S.evals.labels[k] = v; });
    Object.entries(d.reviewed || {}).forEach(([k, v]) => { if (!S.evals.reviewed[k]) S.evals.reviewed[k] = v; });
    S.evals.jl = S.evals.jl || {};
    Object.entries(d.judge_labels || {}).forEach(([k, v]) => { if (!S.evals.jl[k] && v) S.evals.jl[k] = v; });
    (d.modes || []).forEach(m => {
      const mine = S.evals.modes.find(x => x.name.toLowerCase() === String(m.name || '').toLowerCase());
      if (!mine) S.evals.modes.push({id: m.id || null, name: m.name, description: m.description || '', fix: m.fix || null, annotation_ids: (m.annotation_ids || []).slice()});
      else (m.annotation_ids || []).forEach(x => { if (!mine.annotation_ids.includes(x) && !modeOfNote(x)) mine.annotation_ids.push(x); });
    });
    UI.ev.saved = 'disk'; save();
    if (view() === 'evals') renderEvals();
    renderNav();
  } catch (_) {}
}
function evStatus() {
  const s = $('#ev-saved'); if (!s) return;
  s.textContent = UI.ev.saved === 'disk' ? 'Saved to eval/error_discovery' : UI.ev.saved === 'saving' ? 'Saving…' : LIVE.ok ? 'Saved' : 'Saved in this browser';
}
function evSetLabel(id, verdict) {
  if (!id || !VERDICT[verdict]) return;
  UI.ev.undo.push({id, prev: S.evals.labels[id] ? Object.assign({}, S.evals.labels[id]) : null, rev: S.evals.reviewed[id] || null});
  S.evals.labels[id] = {verdict, at: isoLocal(), by: S.user};
  S.evals.reviewed[id] = S.evals.reviewed[id] || isoLocal();
  evSave(); renderEvals(); renderNav();
}
function evUndo() {
  const u = UI.ev.undo.pop(); if (!u) return;
  if (u.prev) S.evals.labels[u.id] = u.prev; else delete S.evals.labels[u.id];
  if (u.rev) S.evals.reviewed[u.id] = u.rev; else if (!evNote(u.id)) delete S.evals.reviewed[u.id];
  UI.ev.cur = u.id; evSave(); renderEvals(); renderNav();
  toast('Label taken back', 'neu');
}
function evSetNote(id, text) {
  if (!id) return;
  const t = String(text || '').trim().slice(0, 1000);
  let a = evNote(id);
  if (a && a.note === t) return;
  if (!a && !t) return;
  if (!a) { a = {id: 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), record_id: id, block: 'trace', start: null, end: null, text: '', note: t, created_at: isoLocal(), by: S.user}; S.evals.ann.push(a); }
  else if (!t) { S.evals.ann = S.evals.ann.filter(x => x !== a); S.evals.modes.forEach(m => { m.annotation_ids = (m.annotation_ids || []).filter(x => x !== a.id); }); }
  else a.note = t;
  S.evals.reviewed[id] = S.evals.reviewed[id] || isoLocal();
  evSave();
  const sel = $('#ev-mode'); if (sel) sel.disabled = !evNote(id);
}
function evFlushNote() { clearTimeout(UI.ev.nt); const t = $('#ev-note'); if (t && UI.ev.cur) evSetNote(UI.ev.cur, t.value); }
function evStep(d) {
  const list = evFiltered(); if (!list.length) return;
  const i = list.findIndex(t => t.id === UI.ev.cur);
  UI.ev.cur = list[(i < 0 ? 0 : i + d + list.length) % list.length].id;
  renderEvals();
  const tv = $('#tv'); if (tv) tv.scrollTop = 0;
}
function evAddMode(name, desc) {
  const n = String(name || '').trim().slice(0, 80);
  if (!n) { toast('Name the failure mode first', 'bad'); return false; }
  if (S.evals.modes.some(m => m.name.toLowerCase() === n.toLowerCase())) { toast('That failure mode already exists', 'neu'); return false; }
  S.evals.modes.push({id: 'M' + Date.now().toString(36), name: n, description: String(desc || '').trim().slice(0, 400), fix: null, annotation_ids: []});
  evSave(); renderEvals();
  return true;
}
function evAssign(annId, key) {
  S.evals.modes.forEach(m => { m.annotation_ids = (m.annotation_ids || []).filter(x => x !== annId); });
  const m = S.evals.modes.find(x => modeKey(x) === key);
  if (m) m.annotation_ids.push(annId);
  evSave(); renderEvals();
}

function renderEvals() {
  $$('#ev-tabs [data-evtab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.evtab === UI.ev.tab)));
  ({dashboard: evDashboard, feedback: evFeedback, traces: evTraces, modes: evModes, evalset: renderQuality})[UI.ev.tab]();
  evStatus();
}
// ------------------------------------------------------------------ evals: the dashboard (experiments, accuracy by field, the LLM judge)
// One row per configuration run over the eval set: eval/outputs/<model>[@<effort>[@<prompt>]] (coleta.py reads them).
const EXP = EVD.experiments || {rows: [], prompt: {}, judge: null};
const pct = (a, b) => (b ? Math.round(1000 * a / b) / 10 : null);
const fmtPct = v => (v == null ? '-' : (v % 1 ? v.toFixed(1) : String(v)) + '%');
const expName = r => `${shortModel(r.model)}${r.effort !== 'medium' ? ' · ' + r.effort + ' effort' : ''}`;
const promptTag = r => r.prompt || 'v1';
const expAcc = r => pct(r.field_ok, r.field_n);
const expSup = r => (r.judge && r.judge.judged ? pct(r.judge.passed, r.judge.judged) : null);
const expRow = label => EXP.rows.find(r => r.label === label) || null;
/** The configuration in production: the model chosen in Settings › Agent at medium effort. */
const prodRow = () => EXP.rows.find(r => r.model === S.settings.model && r.effort === 'medium' && !r.prompt) || EXP.rows.find(r => r.effort === 'medium') || EXP.rows[0] || null;
/** The judge's verdicts for one eval trace (records are named <case>-<label>). */
function judgeOf(t) {
  if (!t || t.prod || t.kind !== 'eval') return null;
  const r = expRow(t.model);
  return r && r.judge && r.judge.cases[t.case_id] ? Object.fromEntries(r.judge.cases[t.case_id].map(x => [x.field, x])) : null;
}
function judgeVerdict(key) {
  const i = key.lastIndexOf(':'), tid = key.slice(0, i), field = key.slice(i + 1);
  const t = EVD.traces.find(x => x.id === tid);
  const j = judgeOf(t && Object.assign({kind: 'eval'}, t));
  return j ? j[field] || null : null;
}
/** Alignment of the judge with the reviewer: on each verdict marked, the human's own call is the judge's when they agree. */
function judgeAgreement() {
  let tp = 0, fn = 0, tn = 0, fp = 0;
  Object.entries(S.evals.jl || {}).forEach(([k, v]) => {
    const j = judgeVerdict(k); if (!j) return;
    const jp = j.result === 'Pass', hp = v === 'agree' ? jp : !jp;
    if (hp && jp) tp++; else if (hp) fn++; else if (!jp) tn++; else fp++;
  });
  return {tp, fn, tn, fp, n: tp + fn + tn + fp, tpr: tp + fn ? tp / (tp + fn) : null, tnr: tn + fp ? tn / (tn + fp) : null};
}
function evDashboard() {
  const rows = EXP.rows, P = prodRow();
  if (!rows.length) {
    $('#ev-body').innerHTML = '<div class="empty">No experiment yet. Run <code>node agent/pipeline.mjs --all --model &lt;id&gt;</code>, then <code>node eval/run_eval.mjs</code> and <code>python mockups/dados/coleta.py</code>.</div>' + evLoopHtml();
    return;
  }
  const n = (v, cls) => `<span class="v${cls ? ' ' + cls : ''}">${v}</span>`;
  const ag = judgeAgreement();
  const failsJ = rows.flatMap(r => Object.entries((r.judge || {}).cases || {}).flatMap(([cid, xs]) => xs.filter(x => x.result === 'Fail').map(x => Object.assign({label: r.label, case_id: cid, name: expName(r)}, x))));
  const fieldsOf = g => SCHEMA.fields.filter(d => d.group === g.id);
  const hm = (r, k) => { const c = r.fields[k]; if (!c || !c[1]) return '<td class="hm hm-na">-</td>'; const miss = c[1] - c[0]; const lvl = miss === 0 ? 0 : miss === 1 ? 1 : miss === 2 ? 2 : 3;
    return `<td class="hm hm-${lvl}" title="${e(expName(r))} · ${e(DEF[k].label)}: right in ${c[0]} of ${c[1]} conversations${c[2] && c[2].length ? ' · missed in ' + e(c[2].join(', ')) : ''}">${c[0]}/${c[1]}</td>`; };
  const bar = v => (v == null ? '<span class="nada">not judged</span>' : `<span class="mtr"><span class="mtr-t"><i style="transform:scaleX(${(v / 100).toFixed(3)})"></i></span><b>${fmtPct(v)}</b></span>`);
  $('#ev-body').innerHTML = `
    <div class="ev-cfg">${ico('sliders-horizontal')}<span>In production: <b>${e(expName(P))}</b> · effort ${e(P.effort)} · prompt ${e(promptTag(P))}${EXP.prompt && EXP.prompt.commit ? ` (${e(EXP.prompt.commit.split(' ')[0])})` : ''}</span><span class="grow"></span><span class="mini">${plural(FOTO.expected.cases.length, 'test conversation', 'test conversations')} · ${P.cases} with fields to judge · ${P.field_n} field decisions</span></div>
    <div class="strip ev-kpi">
      <div class="st">${n(`${P.passed}/${P.total}`)}<span class="l">test conversations pass</span></div>
      <div class="st">${n(fmtPct(expAcc(P)))}<span class="l">field accuracy <span class="t">(${P.field_ok} of ${P.field_n} right)</span></span></div>
      <div class="st">${n(fmtPct(expSup(P)), expSup(P) == null ? 'na' : '')}<span class="l">values supported by the conversation <span class="t">(LLM judge)</span></span></div>
      <div class="st">${n(P.fixes, P.fixes ? 'hot' : 'zero')}<span class="l">quotes or values the checks had to fix</span></div>
      <div class="st">${n(P.cost_per_call != null ? 'USD ' + P.cost_per_call.toFixed(3) : '-')}<span class="l">per conversation</span></div>
      <div class="st">${n(P.latency_med != null ? Math.round(P.latency_med) + ' s' : '-')}<span class="l">median time to an update <span class="t">(max ${P.latency_max != null ? Math.round(P.latency_max) + ' s' : '-'})</span></span></div>
    </div>
    <div class="pn" id="ev-exp"><div class="pn-h"><span class="rvg-i hue-blue">${ico('gauge', 'ico-b')}</span><h2>Experiments</h2><span class="pn-d">the same ${plural(FOTO.expected.cases.length, 'conversation', 'conversations')}, one row per model, effort and prompt</span></div>
      <div class="tbw"><table class="tb" id="tb-exp"><thead><tr><th>Configuration</th><th>Prompt</th><th class="num">Tests</th><th>Field accuracy</th><th>Supported (judge)</th><th class="num">Fixed by checks</th><th class="num">Per conversation</th><th class="num">Median time</th></tr></thead><tbody>
      ${rows.map(r => `<tr data-exp="${e(r.label)}"${r === P ? ' class="is-prod"' : ''}><td><b>${e(expName(r))}</b>${r === P ? ' <span class="ch ch-ok">In production</span>' : ''}<div class="sub">${e(r.label)}</div></td><td class="mid">${e(promptTag(r))}</td>
        <td class="num mid"><b>${r.passed}/${r.total}</b></td><td class="mid">${bar(expAcc(r))}</td><td class="mid">${bar(expSup(r))}</td><td class="num mid">${r.fixes}</td>
        <td class="num mid">${r.cost_per_call != null ? 'USD ' + r.cost_per_call.toFixed(4) : '-'}</td><td class="num mid">${r.latency_med != null ? Math.round(r.latency_med) + ' s' : '-'}</td></tr>`).join('')}
      </tbody></table></div>
      <div class="pn-f">Field accuracy: the agent made the expected call on the field (propose, unchanged, contradictory or no evidence, per <code>eval/expected_results.json</code>) and the scorer found no missing or forbidden fact. Supported: the LLM judge found every fact of the proposed value in the conversation. To compare a new prompt, model or effort, run it into <code>eval/outputs/&lt;model&gt;@&lt;effort&gt;@&lt;prompt&gt;</code>; it becomes a row here.</div></div>
    <div class="ev-two">
      <div class="pn" id="ev-heat"><div class="pn-h"><span class="rvg-i hue-violet">${ico('list-checks', 'ico-b')}</span><h2>Accuracy by field</h2><span class="pn-d">conversations where the field was right · darker = more misses</span></div>
        <div class="tbw"><table class="tb hm-t"><thead><tr><th>Field</th>${rows.map(r => `<th class="num" title="${e(r.label)}">${e(expName(r))}</th>`).join('')}</tr></thead>
        ${SCHEMA.groups.map(g => `<tbody><tr class="hm-g"><th colspan="${rows.length + 1}">${e(g.label)}</th></tr>${fieldsOf(g).map(d => `<tr><td>${d.meddpicc ? `<span class="mdp-l">${e(d.meddpicc)}</span>` : ''}${e(d.label)}</td>${rows.map(r => hm(r, d.key)).join('')}</tr>`).join('')}</tbody>`).join('')}
        </table></div>
        <div class="pn-f hm-key"><span class="hm hm-0">9/9</span> no miss <span class="hm hm-1">8/9</span> one <span class="hm hm-2">7/9</span> two <span class="hm hm-3">6/9</span> three or more</div></div>
      <div class="pn" id="ev-judge"><div class="pn-h"><span class="rvg-i hue-amber">${ico('circle-help', 'ico-b')}</span><h2>LLM judge</h2>${EXP.judge ? `<span class="ch ${ag.n >= 40 && ag.tpr >= 0.9 && ag.tnr >= 0.9 ? 'ch-ok' : 'ch-warn'}">${ag.n >= 40 && ag.tpr >= 0.9 && ag.tnr >= 0.9 ? 'Validated' : 'Not validated yet'}</span>` : ''}</div>
        ${EXP.judge ? `<div class="pn-b jd">
          <p class="jd-q"><b>The question it answers, for every proposed value:</b> ${e(EXP.judge.criterion)}</p>
          <p class="mini">Judge ${e(modelName(EXP.judge.model))} · prompt ${e(EXP.judge.prompt_sha)} · Pass or Fail with a critique · <code>node eval/judge.mjs</code></p>
          <div class="jd-ag"><div><b>${ag.n}</b><span>verdicts you checked</span></div><div><b>${ag.tpr == null ? '-' : fmtPct(Math.round(ag.tpr * 1000) / 10)}</b><span>true positive rate (it passes what you pass)</span></div><div><b>${ag.tnr == null ? '-' : fmtPct(Math.round(ag.tnr * 1000) / 10)}</b><span>true negative rate (it fails what you fail)</span></div></div>
          <p class="mini">Trust the numbers above once you have checked about 20 Pass and 20 Fail verdicts in Trace review and both rates are 90% or more.</p></div>
          <h3 class="jd-h">Values the judge found unsupported <span class="mini">${failsJ.length} of ${rows.reduce((s, r) => s + (r.judge ? r.judge.judged : 0), 0)}</span></h3>
          ${(() => {
            // the production configuration first; the other experiments one click away
            const li = x => `<li><button class="rec" type="button" data-evtrace="${e(x.case_id + '-' + x.label)}">${e(x.case_id)} · ${e(x.name)} · ${e(DEF[x.field] ? DEF[x.field].label : x.field)}</button><q>${e(x.value)}</q><p>${e(x.critique)}</p></li>`;
            const mine = failsJ.filter(x => x.label === P.label), rest = failsJ.filter(x => x.label !== P.label);
            if (!failsJ.length) return '<p class="nada pad">None: every proposed value was supported.</p>';
            return `<ul class="jd-l">${mine.map(li).join('') || `<li class="nada">None for ${e(expName(P))}.</li>`}</ul>${rest.length ? `<details class="jd-more"><summary>${plural(rest.length, 'more in the other experiments', 'more in the other experiments')}</summary><ul class="jd-l">${rest.map(li).join('')}</ul></details>` : ''}`;
          })()}`
        : '<div class="pn-b"><p class="nada">The judge has not run yet: <code>node eval/judge.mjs</code>, then <code>python mockups/dados/coleta.py</code>.</p></div>'}</div>
    </div>
    ${evLoopHtml()}`;
}
/** The loop, step by step: what the owner does, and what happens after. */
function evLoopHtml() {
  const fb = visibleFeedback(), down = fb.filter(f => f.rating === 'down');
  const sample = EVD.traces.filter(t => EVD.sample.includes(t.id));
  const nl = v => sample.filter(t => evLabel(t.id) === v).length;
  const done = sample.filter(t => evLabel(t.id)).length;
  const prodOpen = prodTraces().filter(t => !evLabel(t.id)).length;
  const modes = S.evals.modes.slice().sort((a, b) => (b.annotation_ids || []).length - (a.annotation_ids || []).length);
  const notes = S.evals.ann.length, ag = judgeAgreement();
  const step = (k, title, what, status, btn) => `<li class="lp"><span class="lp-n">${k}</span><div class="lp-t"><h3>${title}</h3><p>${what}</p></div><div class="lp-s">${status}</div><div class="lp-a">${btn}</div></li>`;
  return `
    <div class="pn ev-ov"><div class="pn-h"><span class="rvg-i hue-green">${ico('rotate-ccw', 'ico-b')}</span><h2>How the agent gets better</h2><span class="pn-d">five steps, repeated every week by the agent owner in sales operations</span></div>
      <ol class="loop">
        ${step(1, 'Collect', 'Sellers rate every CRM update and every Explore answer. Each “not right” becomes a trace to review.',
          fb.length ? `<b>${plural(fb.length, 'rating', 'ratings')}</b><span>${down.length} not right${prodOpen ? ` · ${prodOpen} waiting for review` : ''}</span>` : '<b>No ratings yet</b><span>sellers rate from the review and from Explore</span>',
          `<button class="b b-sm b-s" type="button" data-evgo="feedback">Read the feedback</button>`)}
        ${step(2, 'Review', 'Read one trace at a time and judge it Pass or Fail. Write what went wrong in your own words, before naming any category (error analysis).',
          `<b>${done} of ${sample.length} sampled traces</b><span>${done ? `${nl('pass')} pass · ${nl('fail')} fail${nl('defer') ? ` · ${nl('defer')} deferred` : ''}` : `sample drawn from ${EVD.traces.length} eval traces`}</span>`,
          `<button class="b b-sm b-p" type="button" data-evgo="traces">${done ? 'Continue reviewing' : 'Start reviewing'}</button>`)}
        ${step(3, 'Name', 'Group the notes into failure modes and count them. The biggest mode is the next fix.',
          modes.length ? `<b>${plural(modes.length, 'failure mode', 'failure modes')}</b><span>largest: ${e(modes[0].name)} (${(modes[0].annotation_ids || []).length})</span>` : `<b>${notes ? plural(notes, 'note', 'notes') : 'No notes yet'}</b><span>${notes ? 'not grouped yet' : 'notes come from step 2'}</span>`,
          `<button class="b b-sm b-s" type="button" data-evgo="modes">Group the notes</button>`)}
        ${step(4, 'Automate the check', 'Each failure mode gets a check: code when a rule can decide it, an LLM judge when it takes reading. A judge counts only once it agrees with your labels.',
          `<b>${EXP.judge ? '1 LLM judge' : 'No LLM judge yet'} · code checks on every run</b><span>${EXP.judge ? `judge agreement measured on ${plural(ag.n, 'verdict', 'verdicts')}` : 'the scorer and the validator run on every output'}</span>`,
          `<button class="b b-sm b-s" type="button" data-evgo="traces">Check the judge</button>`)}
        ${step(5, 'Fix and re-run', 'Change the prompt, the examples, the model or the effort, add the failure as a test conversation, run the eval set and compare the new row in Experiments before it goes live.',
          `<b>${plural(EXP.rows.length, 'experiment', 'experiments')}</b><span>${EXP.rows.map(r => `${e(expName(r))} ${r.passed}/${r.total}`).join(' · ')}</span>`,
          `<button class="b b-sm b-s" type="button" data-evgo="evalset">Open the eval set</button>`)}
      </ol>
      <div class="pn-f">Judge real traces before writing any automated check, so the checks measure the failures that actually happen (error analysis, as Hamel Husain and Shreya Shankar teach it). Labels, notes and judge checks live in <code>eval/error_discovery/error_discovery_data</code>, the same files as the standalone review app${LIVE.ok ? '; the server keeps them in sync' : '; until the server runs they stay in this browser'}.</div>
    </div>`;
}
function evFeedback() {
  $('#ev-body').innerHTML = fbPanel();
  $('#fb-export').onclick = exportFeedback;
}
function traceHead(t) {
  const u = t.usage;
  const codeFails = !t.prod && t.scorer && (t.scorer.fails || []).length;
  const meta = t.prod
    ? [fmtDate(t.fb.at), (userById(t.fb.user) || {}).name, 'rated not right' + (t.fb.sent && t.fb.reason ? ': ' + reasonLabel(t.fb).toLowerCase() : ''), t.kind === 'update' ? (t.run.record ? 'submitted' : 'not submitted yet') : null]
    : [t.opportunity && 'Opportunity: ' + t.opportunity, t.stage_before && 'stage before: ' + t.stage_before, t.seller && 'run as ' + t.seller, u && u.output_tokens ? `${u.output_tokens.toLocaleString('en-US')} output tokens · USD ${(u.cost_usd || 0).toFixed(4)}` : null];
  return `<header class="tv-h"><div class="tv-t"><span class="tv-case">${e(t.prod ? 'From a seller' : t.case_id)}</span><h2>${e(t.client || '')}</h2></div>
    <p class="tv-sc">${e(t.case_name || '')}</p>
    <div class="tv-chips"><span class="ch ch-neu">${e(shortModel(t.model))}</span>${t.prod ? '' : t.model === 'platform' ? '' : codeFails ? `<span class="ch ch-bad">${plural(codeFails, 'code check failed', 'code checks failed')}</span>` : '<span class="ch ch-ok">Code checks pass</span>'}${(t.flags || []).map(f => `<span class="ch ch-nd">${e(f)}</span>`).join('')}</div>
    <p class="tv-m">${meta.filter(Boolean).map(e).join(' · ')}</p>
    ${t.prod && t.fb.note ? `<p class="tv-q">“${e(t.fb.note)}”</p>` : ''}${t.proves ? `<p class="tv-p"><b>Built to test</b> ${e(t.proves)}</p>` : ''}</header>`;
}
function traceField(f, decs, jv, tid) {
  const def = DEF[f.field] || {label: f.field};
  const d = decs && decs[f.field];
  const j = jv && jv[f.field], jk = tid + ':' + f.field, mine = (S.evals.jl || {})[jk];
  const has = v => v != null && v !== '' && !(Array.isArray(v) && !v.length);
  return `<div class="tvf st-${e(f.status)}"><div class="tvf-h"><b>${e(def.label)}</b><span class="ch ${f.status === 'proposed' ? 'ch-info' : f.status === 'contradictory' ? 'ch-warn' : 'ch-neu'}">${e(TSTATUS[f.status] || f.status)}</span>${d ? CH.decision(d.decision) : ''}</div>
    ${has(f.current_value) ? `<div class="tvf-c"><span class="k">CRM now</span>${e(fmtV(f.current_value))}</div>` : ''}${has(f.proposed_value) ? `<div class="tvf-v">${e(fmtV(f.proposed_value))}</div>` : ''}
    ${d && d.value != null && d.decision !== 'approve' ? `<div class="tvf-c"><span class="k">Seller wrote</span>${e(fmtV(d.value))}</div>` : ''}
    ${(f.evidence || []).length ? `<ul class="tvf-e">${f.evidence.map(x => `<li><span class="ln">L${String(x.line).padStart(3, '0')}</span><q>${e(x.quote)}</q><span class="sp">${e(spkName(x.speaker))}</span></li>`).join('')}</ul>` : ''}
    ${f.note ? `<div class="tvf-n">${e(f.note)}</div>` : ''}
    ${j ? `<div class="tvf-j"><div class="tvf-jh"><span class="ch ${j.result === 'Pass' ? 'ch-ok' : 'ch-bad'}">Judge: ${j.result === 'Pass' ? 'supported' : 'not supported'}</span><span class="tvf-jq">Do you agree?</span><span class="jag" role="group" aria-label="do you agree with the judge on ${e(def.label)}"><button class="jb" type="button" data-jl="${e(jk)}" data-v="agree" aria-pressed="${mine === 'agree'}">Agree</button><button class="jb" type="button" data-jl="${e(jk)}" data-v="disagree" aria-pressed="${mine === 'disagree'}">Disagree</button></span></div><p class="tvf-jc">${e(j.critique)}</p></div>` : ''}</div>`;
}
function traceTranscript(t) {
  const tx = t.prod ? transcriptOf(meetingById(t.meeting_id)) : FOTO.transcripts[t.meeting_id];
  const lines = CORE.transcriptLines(tx || '');
  if (!lines.length) return '';
  return `<details class="tv-tx"><summary>Transcript · ${plural(lines.length, 'line', 'lines')}</summary><ol class="tv-lines">${lines.map(l => `<li><span class="ln">L${String(l.n).padStart(3, '0')}</span><span class="sp${isSeller(l.speaker) ? ' us' : ''}">${e(spkName(l.speaker))}</span><span>${e(l.text)}</span></li>`).join('')}</ol></details>`;
}
function traceBody(t) {
  if (t.kind === 'explore') {
    const a = t.msg.answer;
    return `<section class="tv-s"><h3>The question</h3><p class="tv-big">${e(t.question)}</p></section>
      <section class="tv-s"><h3>The answer</h3><p class="tv-big">${e(a.verdict)}</p>${a.findings.length ? `<ol class="tv-fd">${a.findings.map(f => `<li>${e(f.text)}</li>`).join('')}</ol>` : ''}${a.open ? `<p><b>Not settled yet:</b> ${e(a.open)}</p>` : ''}
      ${(a.sources || []).length ? `<p class="mini">Sources: ${a.sources.map(e).join(' · ')}</p>` : ''}</section>`;
  }
  const out = t.kind === 'update' ? t.run.output : t;
  if (out.run_status === 'Blocked') return `<section class="tv-s"><h3>Stopped before the model</h3><p class="tv-big">${e(out.block_reason || '')}</p><p class="mini">${e(out.source_status || '')}</p></section>${traceTranscript(t)}`;
  const fields = out.fields || [], decs = t.kind === 'update' ? t.run.decisions : null, jv = judgeOf(t);
  const tg = out.target && out.target.kind === 'new' ? `<p class="tv-big">New ${out.target.client_id ? 'opportunity for' : 'client and opportunity:'} ${e(out.target.client_name || '')} · ${e(out.target.opportunity_name || '')}</p>` : '';
  const groups = SCHEMA.groups.map(g => {
    const fs = fields.filter(f => f.group === g.id); if (!fs.length) return '';
    const shown = fs.filter(f => f.status !== 'no_evidence' || f.note), bare = fs.filter(f => f.status === 'no_evidence' && !f.note);
    return `<div class="tv-g"><h4>${e(g.label)}</h4>${shown.map(f => traceField(f, decs, jv, t.id)).join('')}${bare.length ? `<p class="tv-none">No evidence: ${bare.map(f => e((DEF[f.field] || {label: f.field}).label)).join(', ')}</p>` : ''}</div>`;
  }).join('');
  const plat = [].concat((out.warnings || []).map(w => ['Warning', w]), (out.validation_notes || []).map(w => ['Fixed by the checks', w]), (out.ignored_out_of_scope || []).map(w => ['Left out as out of scope', w]));
  const fails = !t.prod && t.scorer && (t.scorer.fails || []).length ? `<section class="tv-s tv-fails"><h3>What the code checks flagged</h3><ul>${t.scorer.fails.map(x => `<li>${e(x)}</li>`).join('')}</ul></section>` : '';
  return `${fails}<section class="tv-s"><h3>What the agent proposed</h3>${tg}${groups}</section>
    ${plat.length ? `<section class="tv-s"><h3>Platform</h3><ul class="tv-plat">${plat.map(([k, w]) => `<li><span class="k">${k}</span>${e(itemText(w))}</li>`).join('')}</ul></section>` : ''}${traceTranscript(t)}`;
}
function evTraces() {
  const all = evQueue(), list = evFiltered();
  if (!list.some(t => t.id === UI.ev.cur)) UI.ev.cur = (list.find(t => !evLabel(t.id)) || list[0] || {}).id || null;
  const t = all.find(x => x.id === UI.ev.cur) || null;
  const i = list.findIndex(x => x.id === UI.ev.cur);
  const cnt = v => all.filter(x => v === 'all' ? true : v === 'todo' ? !evLabel(x.id) : evLabel(x.id) === v).length;
  const chips = [['all', 'All'], ['todo', 'To review'], ['pass', 'Pass'], ['fail', 'Fail'], ['defer', 'Deferred']].map(([k, l]) => `<button class="fchip" type="button" data-evf="${k}" aria-pressed="${UI.ev.filter === k}">${l} <span class="n">${cnt(k)}</span></button>`).join('');
  const item = x => { const v = evLabel(x.id), on = x.id === UI.ev.cur; return `<li><button class="tq-i${on ? ' on' : ''}" type="button" data-trace="${e(x.id)}"${on ? ' aria-current="true"' : ''}>
      <span class="tq-a"><b>${e(x.prod ? (x.kind === 'explore' ? 'Explore' : x.case_id) : x.case_id)}</b><span>${e(x.client || '')}</span></span>
      <span class="tq-b">${e(x.prod ? 'rated not right by a seller' : shortModel(x.model))}${!x.prod && x.scorer && (x.scorer.fails || []).length ? ' · code checks failed' : ''}</span>
      ${v ? `<span class="ch ${VERDICT[v][1]}">${VERDICT[v][0]}</span>` : '<span class="ch ch-nd">To review</span>'}</button></li>`; };
  const note = t && evNote(t.id), mode = note && modeOfNote(note.id), v = t && evLabel(t.id);
  const left = all.filter(x => !evLabel(x.id)).length;
  $('#ev-body').innerHTML = `
    <div class="tr-w">
      <aside class="pn tq" aria-label="traces to review">
        <div class="tq-h"><div class="fgroup" role="group" aria-label="filter traces">${chips}</div>
          <label class="tq-all"><input type="checkbox" id="ev-all"${UI.ev.all ? ' checked' : ''}>All ${EVD.traces.length} eval traces, not only the sample of ${EVD.sample.length}</label></div>
        <ul class="tq-l" id="tq-l">${list.map(item).join('') || '<li class="tq-e">No trace in this filter.</li>'}</ul>
      </aside>
      <section class="pn tv" id="tv" aria-label="trace">${t ? `
        <div class="tv-bar">
          <div class="tv-nav"><button class="b b-sm b-t" type="button" data-evstep="-1" aria-label="previous trace" title="Previous (←)"><span class="flip">${ico('chevron-right')}</span></button><span class="tv-pos"><b>${i + 1} of ${list.length}</b> · ${left} to review</span><button class="b b-sm b-t" type="button" data-evstep="1" aria-label="next trace" title="Next (→)">${ico('chevron-right')}</button></div>
          <div class="vseg" role="group" aria-label="your judgment of this trace">
            <button class="vs vs-pass" type="button" data-verdict="pass" aria-pressed="${v === 'pass'}">${ico('check')}Pass<kbd>1</kbd></button>
            <button class="vs vs-fail" type="button" data-verdict="fail" aria-pressed="${v === 'fail'}">${ico('x')}Fail<kbd>2</kbd></button>
            <button class="vs vs-defer" type="button" data-verdict="defer" aria-pressed="${v === 'defer'}">Defer<kbd>D</kbd></button></div>
          <span class="grow"></span><span class="mini" id="ev-saved"></span></div>
        <div class="tv-note"><label class="fld-l" for="ev-note">What went wrong? <i>in your own words: the first thing you would fix</i></label>
          <textarea class="inp" id="ev-note" rows="3" maxlength="1000" placeholder="e.g. the champion is the person who asked for the demo, not the one who pushed the project">${e(note ? note.note : '')}</textarea>
          <div class="tv-nr">${S.evals.modes.length ? `<label class="tv-mode"><span class="fld-l">Failure mode</span><select class="inp" id="ev-mode"${note ? '' : ' disabled title="write a note first"'}><option value="">Not grouped yet</option>${S.evals.modes.map(m => `<option value="${e(modeKey(m))}"${mode === m ? ' selected' : ''}>${e(m.name)}</option>`).join('')}</select></label>` : ''}
            <span class="tv-keys"><kbd>←</kbd><kbd>→</kbd> move · <kbd>1</kbd> pass · <kbd>2</kbd> fail · <kbd>D</kbd> defer · <kbd>U</kbd> undo · <kbd>Ctrl</kbd>+<kbd>Enter</kbd> save and next</span></div></div>
        <div class="tv-in">${traceHead(t)}${traceBody(t)}</div>` : '<div class="empty">No trace to show. Change the filter on the left.</div>'}</section>
    </div>`;
}
function evModes() {
  const notes = S.evals.ann.slice().sort((a, b) => String(a.record_id).localeCompare(String(b.record_id)));
  const modes = S.evals.modes.slice().sort((a, b) => (b.annotation_ids || []).length - (a.annotation_ids || []).length);
  const failed = Object.values(S.evals.labels).filter(l => l.verdict === 'fail').length;
  const known = evQueue().concat(EVD.traces);
  const trName = id => { const t = known.find(x => x.id === id); return t ? `${t.prod ? 'From a seller' : t.case_id} · ${t.client || ''}${t.model ? ' · ' + shortModel(t.model) : ''}` : id; };
  const max = Math.max(1, ...modes.map(m => (m.annotation_ids || []).length));
  $('#ev-body').innerHTML = `
    <div class="md-w">
      <div class="pn"><div class="pn-h"><h2>Notes from the review</h2><span class="pn-n">${notes.length ? `${plural(notes.length, 'note', 'notes')} · ${notes.filter(a => !modeOfNote(a.id)).length} not grouped` : 'none yet'}</span></div>
        ${notes.length ? `<ul class="nl">${notes.map(a => { const m = modeOfNote(a.id), v = evLabel(a.record_id); return `<li class="nl-i"><div class="nl-t"><button class="rec" type="button" data-evtrace="${e(a.record_id)}">${e(trName(a.record_id))}</button>${v ? `<span class="ch ${VERDICT[v][1]}">${VERDICT[v][0]}</span>` : ''}</div>
            ${a.text ? `<q class="nl-q">${e(a.text)}</q>` : ''}<p class="nl-n">${e(a.note)}</p>
            <label class="nl-m"><span class="sr">Failure mode for this note</span><select class="inp" data-assign="${e(a.id)}"><option value="">Not grouped yet</option>${S.evals.modes.map(x => `<option value="${e(modeKey(x))}"${m === x ? ' selected' : ''}>${e(x.name)}</option>`).join('')}</select></label></li>`; }).join('')}</ul>`
          : `<div class="empty">No notes yet. In <button class="rec" type="button" data-evgo="traces">Trace review</button>, write what went wrong on each failed trace. Name failure modes only after ten or so notes, so the names come from what you saw.</div>`}</div>
      <div class="pn"><div class="pn-h"><h2>Failure modes</h2><span class="pn-n">${modes.length ? `largest first · ${plural(failed, 'failed trace', 'failed traces')}` : 'none yet'}</span></div>
        <form class="md-new" id="md-new"><input class="inp" id="md-name" maxlength="80" placeholder="Name, e.g. Champion confused with the economic buyer" aria-label="name of the failure mode"><input class="inp" id="md-desc" maxlength="400" placeholder="What it looks like in a trace (optional)" aria-label="what the failure mode looks like"><button class="b b-sm b-p" type="submit">${ico('plus')}Add failure mode</button></form>
        ${modes.length ? `<ol class="ml">${modes.map(m => { const c = (m.annotation_ids || []).length; return `<li class="ml-i"><div class="ml-h"><b>${e(m.name)}</b><span class="ml-c">${plural(c, 'note', 'notes')}</span><button class="b b-xs b-t" type="button" data-mode-del="${e(modeKey(m))}" aria-label="delete the failure mode ${e(m.name)}" title="delete">${ico('x')}</button></div><span class="ml-bar" aria-hidden="true"><i style="width:${Math.round(100 * c / max)}%"></i></span>${m.description ? `<p>${e(m.description)}</p>` : ''}</li>`; }).join('')}</ol>`
          : '<p class="nada pad">Add a failure mode, then pick it on each note. The count says which failure to fix first.</p>'}
      </div></div>`;
}
function wireEvals() {
  const box = $('#ev-body');
  box.addEventListener('click', ev => {
    const b = ev.target.closest('[data-evgo],[data-evtrace],[data-trace],[data-verdict],[data-evstep],[data-evf],[data-mode-del],[data-jl]');
    if (!b) return;
    if (b.dataset.jl) {
      // a second click on the same answer takes it back
      const jl = S.evals.jl = S.evals.jl || {};
      if (jl[b.dataset.jl] === b.dataset.v) delete jl[b.dataset.jl]; else jl[b.dataset.jl] = b.dataset.v;
      evSave(); const y = (document.getElementById('tv') || {}).scrollTop; renderEvals(); const tv = $('#tv'); if (tv && y) tv.scrollTop = y;
      return;
    }
    if (b.dataset.evgo) { location.hash = '#/evals/' + b.dataset.evgo; return; }
    if (b.dataset.evtrace) { evOpenTrace(b.dataset.evtrace); return; }
    evFlushNote();
    if (b.dataset.trace) { UI.ev.cur = b.dataset.trace; renderEvals(); const tv = $('#tv'); if (tv) tv.scrollTop = 0; }
    else if (b.dataset.verdict) evSetLabel(UI.ev.cur, b.dataset.verdict);
    else if (b.dataset.evstep) evStep(+b.dataset.evstep);
    else if (b.dataset.evf) { UI.ev.filter = b.dataset.evf; renderEvals(); }
    else if (b.dataset.modeDel) { S.evals.modes = S.evals.modes.filter(m => modeKey(m) !== b.dataset.modeDel); evSave(); renderEvals(); }
  });
  box.addEventListener('change', ev => {
    const t = ev.target;
    if (t.id === 'ev-all') { UI.ev.all = t.checked; renderEvals(); }
    else if (t.id === 'ev-mode') { evFlushNote(); const a = evNote(UI.ev.cur); if (a) evAssign(a.id, t.value); }
    else if (t.dataset.assign) evAssign(t.dataset.assign, t.value);
  });
  box.addEventListener('input', ev => { if (ev.target.id === 'ev-note') { clearTimeout(UI.ev.nt); UI.ev.nt = setTimeout(evFlushNote, 500); } });
  box.addEventListener('focusout', ev => { if (ev.target.id === 'ev-note') evFlushNote(); });
  box.addEventListener('submit', ev => { if (ev.target.id === 'md-new') { ev.preventDefault(); if (evAddMode($('#md-name').value, $('#md-desc').value)) { const n = $('#md-name'); if (n) n.focus(); } } });
  document.addEventListener('keydown', ev => {
    if (view() !== 'evals' || UI.ev.tab !== 'traces' || document.querySelector('dialog[open]')) return;
    if ((ev.ctrlKey || ev.metaKey) && ev.key === 'Enter') { ev.preventDefault(); evFlushNote(); evStep(1); return; }
    if (ev.target.matches('input,textarea,select') || ev.altKey || ev.ctrlKey || ev.metaKey) return;
    const k = ev.key.toLowerCase();
    if (k === 'arrowright') { ev.preventDefault(); evStep(1); }
    else if (k === 'arrowleft') { ev.preventDefault(); evStep(-1); }
    else if (k === '1') evSetLabel(UI.ev.cur, 'pass');
    else if (k === '2') evSetLabel(UI.ev.cur, 'fail');
    else if (k === 'd') evSetLabel(UI.ev.cur, 'defer');
    else if (k === 'u') evUndo();
  });
}
/** Opens one trace in Trace review, whatever the filter (from a note, a rating or the overview). */
function evOpenTrace(id) {
  if (!evQueue().some(t => t.id === id)) UI.ev.all = true;
  UI.ev.cur = id; UI.ev.filter = 'all';
  if (view() === 'evals' && UI.ev.tab === 'traces') renderEvals(); else location.hash = '#/evals/traces';
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
  S.feedback = S.feedback || []; S.seq.fb = S.seq.fb || 0;
  S.evals = Object.assign(freshEvals(), S.evals || {});
  const um = $('#umenu'), ub = $('#umenubtn');
  ub.onclick = () => { const open = !um.classList.contains('open'); um.classList.toggle('open', open); ub.setAttribute('aria-expanded', String(open)); };
  document.addEventListener('click', ev => { if (!um.contains(ev.target)) { um.classList.remove('open'); ub.setAttribute('aria-expanded', 'false'); } });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && um.classList.contains('open')) { um.classList.remove('open'); ub.setAttribute('aria-expanded', 'false'); ub.focus(); } });
  $$('.pi[data-user]').forEach(b => b.onclick = () => { um.classList.remove('open'); switchUser(b.dataset.user); });
  $$('.pi[data-go]').forEach(b => b.onclick = () => { um.classList.remove('open'); location.hash = b.dataset.go; });
  $$('.nav-i[data-view]').forEach(b => b.onclick = () => {
    const v = b.dataset.view;
    if (v === 'explore') { newChat(); return; } // Explore always opens a new chat; the chats below reopen old ones
    location.hash = '#/' + v + (v === 'settings' ? '/' + UI.setTab : v === 'evals' ? '/' + UI.ev.tab : '');
  });
  // every name of a record opens it: the opportunity, the client, the meeting; so does a click anywhere on its row
  document.addEventListener('click', ev => {
    const t = ev.target.closest('[data-open-opp],[data-open-client],[data-open-mtg]');
    if (t) {
      ev.preventDefault();
      if (t.dataset.openOpp) openOppDrawer(t.dataset.openOpp);
      else if (t.dataset.openClient) openClientDrawer(t.dataset.openClient);
      else openMeeting(t.dataset.openMtg, {find: t.dataset.find || ''});
      return;
    }
    const row = ev.target.closest('[data-row-opp],[data-row-mtg]');
    if (!row || ev.target.closest('a,button,input,select,textarea,label,summary,details')) return;
    if (row.dataset.rowOpp) openOppDrawer(row.dataset.rowOpp); else openMeeting(row.dataset.rowMtg);
  });
  $('#nav-newchat').onclick = newChat; // New chat and Explore both open a new chat
  $('#mt-q').addEventListener('input', ev => { UI.mtQ = ev.target.value; renderMeetingRows(); });
  $$('#ev-tabs [data-evtab]').forEach(b => b.onclick = () => { location.hash = '#/evals/' + b.dataset.evtab; });
  wireEvals();
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
  $('#drw').addEventListener('close', () => { UI.mtg = null; });
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
  wireFeedback();
  window.addEventListener('hashchange', route);
  UI.navigated = false;
  route(); renderJob();
  probeServer();
}
document.addEventListener('DOMContentLoaded', boot);
window.CRM = {ingest, prepareDraft, startRun, decide, decideCreate, decideGroup, submitRun, undoAuto, confirmEnded, askExplore, newChat, resetAll, switchUser, rate, sendReason,
  runEvalInPage, openOppDrawer, openClientDrawer, openMeeting, openChat, evSetLabel, evSetNote, evAddMode, evAssign, evUndo, renderEvals, judgeAgreement,
  state: () => S, core: CORE, ui: () => UI, live: () => LIVE};
"""
