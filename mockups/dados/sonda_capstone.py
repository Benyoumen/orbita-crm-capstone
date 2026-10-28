# -*- coding: utf-8 -*-
"""Sonda de comportamento do mockup Orbita CRM (v5): exercita a tela no Edge headless
pelo caminho que a vendedora usa (soltar um arquivo, colar o texto, escolher a
oportunidade, aprovar, perguntar no Explore) e confere os criterios de aceite mais
o contrato da pele. Stdlib pura.

    python sonda_capstone.py                       # roda tudo; sai 0 so com tudo OK
    python sonda_capstone.py --foto review-t1      # tira um print de uma cena (ver CENAS)
    python sonda_capstone.py --foto clients --largura 1280

Como funciona: copia o HTML gerado para um caminho ASCII (acento quebra o Edge),
isola a pagina de qualquer servidor local (CAPSTONE_API aponta para uma porta
fechada: o agente fica offline e so as transcricoes de exemplo tem resultado
salvo), injeta os arquivos de capstone/samples/ e o roteiro, abre no Edge com
--dump-dom e le as linhas OK/FAIL/EXC que o roteiro escreveu em <pre id="sonda-out">.
O oraculo e o proprio kit (eval/expected_results.json, a semente e o esquema,
embutidos em FOTO), nunca um numero copiado para ca.

As verificacoes:
  A0  Explore: saudacao, sugestoes respondidas pelo CRM, status de uma oportunidade
      com fonte e "Not settled yet", follow-ups vencidos = o CRM, empresa
      desconhecida respondida com honestidade, nada sobre oportunidade sem acesso,
      chat na lateral, New chat; o Explore nunca escreve.
  A1  Meetings + T1 (WebVTT): faixa "meetings of yours / CRM updates waiting for
      your review", cartao logo abaixo, "Select your opportunity" acima da entrada;
      leitura do formato, atribuicao com o motivo, titulo do arquivo; revisao com
      todos os campos; Always allow escrito na hora, o resto so no Submit; MEDDPICC.
  A2  T2 (txt): sem evidencia sem controle; "No budget allocated".
  A3  T3 (Otter): contradicao com Keep/Replace/Clear; budget unchanged; Keep nao escreve.
  A4  T4 (cortada): Incomplete; "the meeting ended there" registrado.
  A5  T5 (empresa nova): proposta de cliente e oportunidade; nada criado antes da
      decisao; criacao com o contato; o cliente aparece em Clients.
  A6  T6 (SRT): etapa parada, "one million" ignorado, budget, champion.
  A7  T7 (texto colado): edicao da vendedora; o activity log em Settings.
  A8  T8: acesso negado ja no rascunho, sem o nome; Lucas ve a sua.
  A9  T9: editores por tipo; valor invalido recusado; Solution -> Proposal.
  A10 T10: vozes genericas nao atribuidas; nunca economic buyer nem champion.
  A11 T11 (WhatsApp): chat lido, atribuido pelo contato, Negotiation -> Contract.
  A12 a escolha da vendedora vence a deteccao; New opportunity pede o nome;
      offline, conversa nova nao tem resposta e a pagina diz como ligar o agente.
  P1  Permissoes: tres niveis, um controle por campo, padroes do esquema, Never,
      Always allow com Undo, grupo inteiro, restaurar, criacao Never e Always allow.
  S1  Settings: as abas; Agent (conexao, modelos, esforco); Sources; o Activity log
      saiu da lateral; as rotas antigas redirecionam.
  S2  Quality checks: as conversas de teste passam e nao tocam no CRM.
  F1-F3 funil (com MEDDPICC), gavetas, Clients em cartoes separados.
  C0-C6 titulo abaixo da barra, nada de jargao de prototipo na tela, reset, os
      formatos de capstone/samples, a gaveta da transcricao, o contrato e o contraste.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import saida  # noqa: E402

HTML = saida.HTML
SAMPLES = os.path.join(os.path.dirname(os.path.dirname(HERE)), "samples")
EDGE = os.environ.get("EDGE") or r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ROTEIRO = r"""
<script>
(function () {
  const SAMPLES = __SAMPLES__;
  const out = [];
  const pre = document.createElement('pre'); pre.id = 'sonda-out'; pre.hidden = true; document.body.appendChild(pre);
  const flush = () => { pre.textContent = out.join('\n'); };
  const ok = n => { out.push('OK ' + n); flush(); };
  const fail = (n, d) => { out.push('FAIL ' + n + ' :: ' + (d || '')); flush(); };
  const check = (n, c, d) => c ? ok(n) : fail(n, d);
  const errs = [];
  window.addEventListener('error', ev => errs.push(String(ev.message)));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  async function until(fn, label, ms) { let n = 0; while (!fn()) { await wait(20); if (++n > (ms || 6000) / 20) throw new Error('timeout: ' + label); } }
  const q = (s, r) => (r || document).querySelector(s);
  const qq = (s, r) => Array.from((r || document).querySelectorAll(s));
  const txt = el => (el ? el.textContent : '').replace(/\s+/g, ' ').trim();
  const shown = el => !!el && getComputedStyle(el).display !== 'none' && !el.closest('[hidden]');
  const row = f => q('#tb-rev tr[data-field="' + f + '"]');
  const fv = (rec, k) => CRM.core.fieldOf(rec, k);
  const seed = () => JSON.stringify({clients: FOTO.clients, opportunities: FOTO.opportunities});
  const crm = () => JSON.stringify(CRM.state().crm);
  const expected = id => FOTO.expected.cases.find(c => c.case_id === id);
  const runs = () => CRM.state().runOrder.map(id => CRM.state().runs[id]);
  const runOf = id => CRM.state().runs[id];
  const oppOf = id => CRM.state().crm.opportunities.find(o => o.opportunity_id === id);
  const cliOf = id => CRM.state().crm.clients.find(c => c.client_id === id);
  const seedOpp = id => FOTO.opportunities.find(o => o.opportunity_id === id);
  const view = v => q('.view[data-view="' + v + '"]');
  const T = {T1: 'acme-logistics_discovery-call.vtt', T2: 'verde-retail_intro-call.txt', T3: 'nimbus-health_demo-planning.txt', T4: 'verde-retail_pos-data-questions.vtt',
    T5: 'delta-pharma_intro-call.vtt', T6: 'atlas-manufacturing_proposal-check-in.srt', T7: 'cedro-construtora_discovery-call.txt', T8: 'horizonte-foods_solution-walkthrough.vtt',
    T9: 'lumen-education_scope-session.vtt', T10: 'pampa-agro_discovery-call.txt', T11: 'WhatsApp Chat with Henrique Prado.txt'};
  async function goto(hash, sel) { location.hash = hash; await until(() => q(sel), hash); await wait(10); }
  async function reset() { CRM.resetAll(); CRM.switchUser('U01'); location.hash = '#/meetings'; await until(() => !view('meetings').hidden && q('#mt-opp'), 'meetings'); await wait(10); }
  async function drop(name, choice) {
    location.hash = '#/meetings'; await until(() => !view('meetings').hidden, 'meetings view');
    if (choice != null) { const s = q('#mt-opp'); s.value = choice; s.dispatchEvent(new Event('change')); await wait(10); }
    const inp = q('#drop-file'); const dt = new DataTransfer(); dt.items.add(new File([SAMPLES[name]], name, {type: 'text/plain'}));
    inp.files = dt.files; inp.dispatchEvent(new Event('change'));
    await until(() => q('#dr-go') && q('#mt-draft').textContent.includes(name), 'draft ' + name);
  }
  async function prepare(label) {
    const before = CRM.state().runOrder.length;
    q('#rev-body').innerHTML = ''; q('#rev-body').dataset.run = '';
    q('#dr-go').click();
    await until(() => CRM.state().runOrder.length === before + 1 && q('#rev-body').dataset.run === CRM.state().lastRun && q('#rev-body').children.length, 'review ' + (label || ''));
    return CRM.state().lastRun;
  }
  async function addRun(name, choice) { await drop(name, choice); return prepare(name); }
  function statuses() { const o = {}; qq('#tb-rev tr[data-field]').forEach(tr => { o[tr.dataset.field] = tr.dataset.status; }); return o; }
  function expectStatuses(caseId, label) {
    const c = expected(caseId), got = statuses();
    const bad = FIELDS.filter(f => { const ex = c.fields[f] || {status: 'no_evidence'}; return !(ex.status_any || [ex.status]).includes(got[f]); });
    check(label + ' field statuses match expected_results', !bad.length, bad.map(f => f + '=' + got[f]).join(', '));
  }
  async function approveAll() {
    for (let i = 0; i < 80; i++) { const b = q('#tb-rev [data-approve-group]') || q('#tb-rev [data-dec="approve"]'); if (!b) break; b.click(); await wait(5); }
  }
  async function keepAll() { for (let i = 0; i < 20; i++) { const b = q('#tb-rev [data-dec="keep"]'); if (!b) break; b.click(); await wait(5); } }
  async function submit(label) {
    const sb = q('#rev-submit');
    check(label + ' submit enabled once every waiting row is decided', sb && !sb.disabled, sb ? 'disabled' : 'no button');
    sb.click();
    await until(() => !q('#rev-submit'), 'submitted ' + label);
  }
  async function ask(question) {
    location.hash = '#/explore'; await until(() => !view('explore').hidden, 'explore');
    const n = qq('#ex-thread .msg.nex').length;
    q('#ex-in').value = question; q('#ex-cmp').dispatchEvent(new Event('submit', {cancelable: true}));
    await until(() => qq('#ex-thread .msg.nex').length === n + 1 && !q('#ex-thread .msg.wait'), 'answer to ' + question);
    const chat = CRM.state().chats.find(c => c.id === CRM.state().chatCurrent);
    return {el: qq('#ex-thread .msg.nex').pop(), a: chat.messages[chat.messages.length - 1].answer};
  }
  const JARGON = /Call-to-CRM|\bmock\b|reference answers?|demo notes|Granola demo/i;

  async function A0() {
    await reset();
    await goto('#/explore', '#ex-cmp');
    check('A0 Explore greets the seller by name', /Ana/.test(txt(q('#ex-t'))) && /^Good (morning|afternoon|evening)/.test(txt(q('#ex-t'))), txt(q('#ex-t')));
    check('A0 Explore is the first item of the navigation', q('.nav .nav-i').dataset.view === 'explore');
    const sugs = qq('#ex-sg .sg');
    check('A0 Explore suggests questions from the pipeline', sugs.length >= 3, sugs.length);
    const s0 = txt(q('.sg-t', sugs[0]));
    sugs[0].click(); await until(() => q('#ex-thread .msg.nex') && !q('#ex-thread .msg.wait'), 'suggestion answer');
    const chat0 = CRM.state().chats[0];
    check('A0 a suggestion is answered from the CRM', chat0 && chat0.messages[1].answer.kind !== 'none' && txt(q('#ex-thread .msg.eu')) === s0, chat0 && chat0.messages[1].answer.kind);
    CRM.newChat(); await wait(20);
    const r1 = await ask("What's the status of Acme Logistics?");
    const st = fv(seedOpp('OPP-0142'), 'stage').value;
    check('A0 the status answer names the opportunity and its stage', r1.a.kind === 'status' && /Acme Logistics/.test(r1.a.verdict) && r1.a.verdict.includes(st), r1.a.verdict);
    check('A0 the answer shows its source and what is not settled', !!q('.msg-f', r1.el) && /OPP-0142/.test(txt(q('.msg-f', r1.el))) && !!q('.msg-ab', r1.el));
    q('[data-ex-opp]', r1.el).click(); await until(() => q('#opp-drw').open, 'drawer from Explore');
    check('A0 Open opportunity opens the record drawer', /Acme Logistics/.test(txt(q('#opp-drw-t'))));
    q('#opp-drw-x').click(); await wait(20);
    const late = FOTO.opportunities.filter(o => o.owner_id === 'U01' && fv(o, 'follow_up_due_date').value && fv(o, 'follow_up_due_date').value < FOTO.data_da_foto).length;
    const r2 = await ask('Which follow-ups are overdue?');
    check('A0 overdue follow-ups match the CRM', r2.a.kind === 'followups' && new RegExp('^' + late + ' follow-up').test(r2.a.verdict), r2.a.verdict);
    const r3 = await ask('How is Zeta Mining doing?');
    check('A0 an unknown company is answered honestly, with suggestions', r3.a.kind === 'none' && /couldn't find/.test(r3.a.verdict) && qq('.msg-sg .sg', r3.el).length > 0);
    check('A0 the chat is listed in the sidebar', qq('#nav-chats [data-chat]').length >= 1);
    CRM.switchUser('U02');
    const r4 = await ask("What's the status of Acme Logistics?");
    check('A0 Explore never answers about an opportunity the user cannot read', r4.a.kind === 'none' && !txt(r4.el).includes('OPP-0142') && !txt(r4.el).includes('Sales CRM rollout'));
    CRM.switchUser('U01');
    q('#nav-newchat').click(); await until(() => !q('.ex').classList.contains('ex-on'), 'new chat');
    check('A0 New chat goes back to the greeting and the suggestions', /Ana/.test(txt(q('#ex-t'))) && shown(q('#ex-sg-box')));
    check('A0 Explore never writes to the CRM', crm() === seed());
  }
  async function A1() {
    await reset();
    const strip = q('#mt-strip');
    check('A1 the banner says meetings of yours and CRM updates waiting for your review', qq('.st', strip).length === 2 && /0\s*meetings of yours/.test(txt(strip)) && /0\s*CRM updates waiting for your review/.test(txt(strip)), txt(strip));
    check('A1 the add card comes right after the banner', strip.nextElementSibling && strip.nextElementSibling.id === 'mt-add');
    check('A1 Select your opportunity sits above the transcript input', /Select your opportunity/.test(txt(q('.add-opp'))) && q('.add-opp').compareDocumentPosition(q('#drop')) & Node.DOCUMENT_POSITION_FOLLOWING);
    const mine = FOTO.opportunities.filter(o => o.owner_id === 'U01' && !FOTO.schema.closed_stages.includes(o.fields.stage.value));
    check('A1 the select offers detect, your open opportunities and a new one', q('#mt-opp').options[0].value === '' && qq('#mt-opp option').filter(o => /^OPP-/.test(o.value)).length === mine.length && !!q('#mt-opp option[value="__new__"]'));
    check('A1 a file or pasted text', !!q('#tab-file') && !!q('#tab-paste'));
    await drop(T.T1);
    check('A1 the draft says the format and the speakers', /read as WebVTT/.test(txt(q('#mt-draft'))) && /3 speakers/.test(txt(q('#mt-draft'))), txt(q('#mt-draft')).slice(0, 120));
    check('A1 the conversation is attributed to its opportunity, with the reason', /Acme Logistics · Sales CRM rollout/.test(txt(q('.dr-att'))) && /Marina Lopes is a contact at Acme Logistics/.test(txt(q('.dr-att'))));
    check('A1 a title read from the file name', q('#dr-title').value === 'Acme Logistics - Discovery call', q('#dr-title').value);
    const id = await prepare('T1');
    const r = runOf(id);
    check('A1 the review lists every field of the schema, grouped', qq('#tb-rev tr[data-field]').length === FIELDS.length && qq('#tb-rev tbody.rg').length === FOTO.schema.groups.length);
    expectStatuses('T1', 'A1');
    const auto = FIELDS.filter(k => DEF[k].permission === 'auto');
    check('A1 Always allow fields are written as soon as the update is prepared', auto.every(k => fv(oppOf('OPP-0142'), k).value) && auto.every(k => row(k).dataset.auto === '1' && /Always allow/.test(txt(q('.dec', row(k))))), auto.filter(k => !fv(oppOf('OPP-0142'), k).value).join(','));
    check('A1 fields that need approval are not written before Submit', !fv(oppOf('OPP-0142'), 'budget').value && !fv(cliOf('CLI-001'), 'employee_count').value);
    check('A1 the header shows MEDDPICC after this conversation', /8\/8/.test(txt(q('.rev-mdp'))) && qq('.rev-mdp .mdp-c').length === 8);
    await goto('#/meetings', '#tb-meetings tr[data-mtg]');
    check('A1 the banner counts the meeting and the update waiting', /1\s*meeting of yours/.test(txt(q('#mt-strip'))) && /1\s*CRM update waiting/.test(txt(q('#mt-strip'))) && txt(q('#nav-meetings-n')) === '1', txt(q('#mt-strip')));
    location.hash = '#/review/' + id; await until(() => q('#rev-body').dataset.run === id && q('#tb-rev'), 'back to review');
    const g = q('#tb-rev [data-approve-group="qualification"]');
    check('A1 the MEDDPICC section can be approved at once', !!g);
    if (g) { g.click(); await wait(10); }
    check('A1 the section approval decided each of its fields', r.output.fields.filter(f => f.group === 'qualification' && f.status === 'proposed').every(f => runOf(id).decisions[f.field]));
    await approveAll(); await submit('A1');
    const opp = oppOf('OPP-0142'), cli = cliOf('CLI-001');
    check('A1 after Submit the stage is Solution, approved', fv(opp, 'stage').value === 'Solution' && fv(opp, 'stage').approved);
    check('A1 client fields went to the client record', fv(cli, 'employee_count').value === '850' && !(opp.fields || {}).employee_count);
    check('A1 the champion and the paper process are in the CRM', /Felipe/.test(fv(opp, 'champion').value || '') && /quote/.test(fv(opp, 'paper_process').value || ''));
    await goto('#/opportunities', '#opps-groups .fg');
    check('A1 the opportunity moved to Solution in the funnel', !!q('.fg[data-stage="Solution"] [data-opp="OPP-0142"]'));
  }
  async function A2() {
    await reset();
    await addRun(T.T2);
    expectStatuses('T2', 'A2');
    for (const f of ['follow_up_due_date', 'stage']) check('A2 ' + f + ' says No evidence and has no control', /No evidence/.test(txt(q('.dec', row(f)))) && !q('.dec button', row(f)));
    check('A2 budget proposed as No budget allocated', txt(q('.prop .val', row('budget'))) === 'No budget allocated');
    check('A2 the stage note names the missing New Lead criterion', /New Lead exit criteria/.test(txt(q('.notes'))));
  }
  async function A3() {
    await reset();
    await drop(T.T3);
    check('A3 an Otter export is read', /read as Otter/.test(txt(q('#mt-draft'))));
    const id = await prepare('T3');
    expectStatuses('T3', 'A3');
    for (const f of ['next_step', 'follow_up_due_date']) {
      const tr = row(f);
      check('A3 ' + f + ' is contradictory with Keep, Replace and Clear', tr.dataset.status === 'contradictory' && q('[data-dec="keep"]', tr) && q('[data-open="replace"]', tr) && q('[data-dec="clear"]', tr));
    }
    check('A3 the unchanged budget asks for no decision', row('budget').dataset.status === 'unchanged' && !q('.dec button', row('budget')));
    await keepAll(); await approveAll(); await submit('A3');
    const opp = oppOf('OPP-0143'), so = seedOpp('OPP-0143');
    check('A3 Keep leaves next step and due date as they were', fv(opp, 'next_step').value === fv(so, 'next_step').value && fv(opp, 'follow_up_due_date').value === fv(so, 'follow_up_due_date').value);
    check('A3 kept fields are Not written', runOf(id).record.filter(x => x.seller_decision === 'keep').every(x => x.write_result === 'Not written'));
  }
  async function A4() {
    await reset();
    await drop(T.T4);
    check('A4 the draft warns that the transcript stops mid-sentence', /stops mid-sentence/.test(txt(q('#mt-draft'))));
    const id = await prepare('T4');
    const r = runOf(id);
    check('A4 a cut recording is blocked as Incomplete, with no table', r.status === 'Blocked' && r.output.source_status === 'Incomplete' && !q('#tb-rev') && !q('#rev-submit'), r.output.source_status);
    const n = runs().length;
    q('#rev-confirm').click(); await wait(80);
    check('A4 "the meeting ended there" is recorded and the pre-check passes; offline the agent says so', !!CRM.state().confirmed[r.meetingId] && runs().length === n && /agent is offline/.test(txt(q('#toast-tx'))), txt(q('#toast-tx')));
    await goto('#/settings/activity', '#act-list');
    check('A4 the activity log records the blocked update and the decision', !!q('#act-list .fi[data-kind="blocked"]') && /ended there/.test(txt(q('#act-list'))));
  }
  async function A5() {
    await reset();
    await drop(T.T5);
    check('A5 a company the CRM does not know becomes a new opportunity', /New opportunity/.test(txt(q('.dr-att'))) && /no client in your CRM matches/.test(txt(q('.dr-att'))));
    check('A5 the client name comes from the file and the contact from the speakers', q('#dr-client').value === 'Delta Pharma' && /Livia Prado/.test(txt(q('#mt-draft'))), q('#dr-client').value);
    const id = await prepare('T5');
    const r = runOf(id);
    check('A5 the review starts with the new client and opportunity', !!q('#rev-new') && !!q('#rev-new [data-create="approve"]') && !!q('#rev-new [data-create="reject"]'));
    check('A5 nothing is created before the decision', JSON.stringify(CRM.state().crm.clients) === JSON.stringify(FOTO.clients) && crm() === seed());
    check('A5 Always allow fields wait for the new opportunity', r.autoPending.length > 0 && r.autoPending.every(k => /written with the new opportunity/.test(txt(q('.dec', row(k))))));
    await approveAll();
    check('A5 Submit waits for the creation decision', q('#rev-submit').disabled);
    q('#rev-new [data-create="approve"]').click(); await wait(20);
    await submit('A5');
    const cli = CRM.state().crm.clients.find(c => c.name === 'Delta Pharma');
    const opp = cli && CRM.state().crm.opportunities.find(o => o.client_id === cli.client_id);
    check('A5 the client is created with its contact', !!cli && cli.contacts.some(p => p.name === 'Livia Prado'));
    check('A5 the opportunity is created at New Lead, owned by the seller, with the fields', !!opp && opp.owner_id === 'U01' && fv(opp, 'stage').value === 'New Lead' && !!fv(opp, 'call_summary').value && !!fv(opp, 'customer_need').value);
    await goto('#/clients', '#cl-list .cl-card');
    check('A5 the new client has its card in Clients', !!q('#cl-list .cl-card[data-client="' + (cli && cli.client_id) + '"]'));
  }
  async function A6() {
    await reset();
    await drop(T.T6);
    check('A6 an SRT file is read', /read as subtitles/.test(txt(q('#mt-draft'))));
    await prepare('T6');
    expectStatuses('T6', 'A6');
    check('A6 the stage does not move and the note names the CFO', row('stage').dataset.status === 'no_evidence' && /CFO|Helena/.test(txt(q('.notes .pn:first-child'))));
    check('A6 the one-million request is ignored, the stated budget proposed', /one million/.test(txt(q('.notes .pn:nth-child(2)'))) && /120,000/.test(txt(q('.prop .val', row('budget')))));
    check('A6 the champion is not the economic buyer', /Tiago/.test(txt(q('.prop .val', row('champion')))));
    check('A6 no Closed stage proposed', !/Closed Won|Closed Lost/.test(qq('#tb-rev .prop .val').map(txt).join(' ')));
  }
  async function A7() {
    await reset();
    q('#tab-paste').click(); await until(() => shown(q('#paste')), 'paste box');
    check('A7 Paste text shows a text box instead of the drop zone', shown(q('#paste-in')) && !shown(q('#drop')));
    q('#paste-in').value = SAMPLES[T.T7]; q('#paste-in').dispatchEvent(new Event('input'));
    q('#paste-go').click(); await until(() => q('#dr-go'), 'pasted draft');
    check('A7 pasted speaker lines are read and attributed', /read as speaker lines/.test(txt(q('#mt-draft'))) && /Cedro Construtora/.test(txt(q('.dr-att'))));
    const id = await prepare('T7');
    expectStatuses('T7', 'A7');
    const edited = expected('T7').review_script.edit.customer_need;
    q('[data-open="edit"]', row('customer_need')).click(); await until(() => q('#dec-text'), 'editor');
    q('#dec-text').value = edited; q('[data-save="edit"]', row('customer_need')).click();
    await until(() => /Edited/.test(txt(q('.dec', row('customer_need')))), 'edited');
    await approveAll(); await submit('A7');
    const opp = oppOf('OPP-0146');
    const rec = runOf(id).record.find(x => x.field === 'customer_need');
    check('A7 the CRM shows the edited text and the record keeps both versions', fv(opp, 'customer_need').value === edited && rec.agent_proposal !== edited && rec.final_value === edited);
    await goto('#/settings/activity', '#act-list .fi');
    const item = q('#act-list .fi[data-run="' + id + '"]');
    check('A7 the activity log says who wrote what in one sentence', /Ana Ribeiro wrote \d+ fields to Cedro Construtora/.test(txt(item)) && /1 edited/.test(txt(item)) && /always allowed/.test(txt(item)), txt(item).slice(0, 140));
    q('[data-expand]', item).click(); await wait(20);
    check('A7 the changes show before, after and the agent proposal', txt(q('#act-list .fi[data-run="' + id + '"] .fi-x')).includes('Agent proposed: ' + rec.agent_proposal));
  }
  async function A8() {
    await reset();
    await drop(T.T8);
    const o = seedOpp('OPP-0145');
    check('A8 another seller\'s conversation is denied in the draft, without its name', /do not have access/.test(txt(q('.dr-att'))) && !txt(q('#mt-draft')).includes(o.name) && !txt(q('#mt-draft')).includes('OPP-0145'));
    const id = await prepare('T8');
    const r = runOf(id);
    check('A8 blocked AccessDenied', r.status === 'Blocked' && r.output.source_status === 'AccessDenied');
    const page = txt(view('review'));
    const leaks = ['OPP-0145', o.name, fv(o, 'customer_need').value, fv(o, 'next_step').value, String(o.amount_usd)].filter(s => s && page.includes(s));
    check('A8 no opportunity data on the review page', !leaks.length, leaks.join(' | '));
    check('A8 the attempt is logged as access_checked blocked', r.log.some(ev => ev.action === 'access_checked' && ev.outcome === 'blocked'));
    await goto('#/meetings', '#tb-meetings tr[data-mtg]');
    check('A8 the meetings row says no access', /no access/.test(txt(q('#tb-meetings tbody'))) && !txt(q('#tb-meetings tbody')).includes(o.name));
    CRM.switchUser('U02');
    await drop(T.T8);
    check('A8 as Lucas, the owner, the same file goes to his opportunity', new RegExp(o.name).test(txt(q('.dr-att'))), txt(q('.dr-att')));
  }
  async function A9() {
    await reset();
    const id = await addRun(T.T9);
    expectStatuses('T9', 'A9');
    q('[data-open="edit"]', row('seats')).click(); await until(() => q('#dec-text'), 'seats editor');
    check('A9 seats edit with a number field', q('#dec-text').type === 'number');
    q('#dec-text').value = ''; q('[data-save="edit"]', row('seats')).click(); await wait(20);
    check('A9 an empty seller value is refused', !runOf(id).decisions.seats && !!q('#dec-text') && /without a value/.test(txt(q('#toast-tx'))));
    q('[data-cancel]', row('seats')).click(); await wait(10);
    q('[data-open="edit"]', row('departments')).click(); await until(() => q('#dec-multi'), 'departments editor');
    qq('#dec-multi input').forEach(i => { i.checked = ['IT', 'Sales'].includes(i.value); });
    q('[data-save="edit"]', row('departments')).click(); await wait(20);
    check('A9 departments edit with chips, stored in list order', runOf(id).decisions.departments && runOf(id).decisions.departments.value === 'Sales; IT');
    q('[data-open="edit"]', row('stage')).click(); await until(() => q('#dec-text'), 'stage editor');
    check('A9 stage edit is the list of stages', q('#dec-text').tagName === 'SELECT' && q('#dec-text').options.length === FOTO.schema.stages.length);
    q('[data-cancel]', row('stage')).click(); await wait(10);
    await approveAll(); await submit('A9');
    check('A9 Solution -> Proposal written', fv(oppOf('OPP-0147'), 'stage').value === 'Proposal');
  }
  async function A10() {
    await reset();
    const id = await addRun(T.T10);
    expectStatuses('T10', 'A10');
    const lines = CRM.core.transcriptLines(CRM.state().transcripts[runOf(id).meetingId]);
    check('A10 generic voices are marked unattributed', lines.some(l => /Speaker 2 \(unattributed\)/.test(l.speaker)));
    check('A10 an unattributed voice is never economic buyer or champion', row('decision_maker').dataset.status === 'no_evidence' && row('champion').dataset.status === 'no_evidence' && row('stage').dataset.status === 'no_evidence');
  }
  async function A11() {
    await reset();
    await drop(T.T11);
    check('A11 a WhatsApp export is read as a chat', /read as WhatsApp chat export/.test(txt(q('#mt-draft'))) && /8 messages/.test(txt(q('#mt-draft'))), txt(q('#mt-draft')).slice(0, 120));
    check('A11 the chat is attributed by the contact name', /Solaris Energy/.test(txt(q('.dr-att'))) && /Henrique Prado is a contact/.test(txt(q('.dr-att'))));
    const id = await prepare('T11');
    expectStatuses('T11', 'A11');
    check('A11 the written yes moves Negotiation to Contract', txt(q('.prop .val', row('stage'))) === 'Contract');
    check('A11 tomorrow is resolved from the message date', txt(q('.prop .val', row('follow_up_due_date'))) === '2026-11-06');
    check('A11 the evidence shows the message day and time', /Thu 5 Nov 18:4\d/.test(txt(q('.evm time', row('stage')))), txt(q('.evm time', row('stage'))));
    await approveAll(); await submit('A11');
    check('A11 the stage is Contract in the CRM', fv(oppOf('OPP-0149'), 'stage').value === 'Contract');
  }
  async function A12() {
    await reset();
    await drop(T.T1, 'OPP-0141');
    check('A12 the chosen opportunity overrides the detection', /Verde Retail · Franchise sales CRM/.test(txt(q('.dr-att'))) && /chosen by you/.test(txt(q('.dr-att'))));
    const id = await prepare('chosen');
    check('A12 the update goes to the chosen opportunity', runOf(id).output.opportunity_id === 'OPP-0141');
    await reset();
    const inp = q('#mt-opp'); inp.value = '__new__'; inp.dispatchEvent(new Event('change')); await wait(10);
    q('#tab-paste').click(); await wait(10);
    q('#paste-in').value = 'Ana Ribeiro: Thanks for the time, Bruno.\nBruno Lemos: Sure. We sell solar panels and track every lead in a spreadsheet.\nAna Ribeiro: Let us book a demo next week.';
    q('#paste-go').click(); await until(() => q('#dr-go'), 'new draft');
    check('A12 New opportunity asks for the client name', /New opportunity/.test(txt(q('.dr-att'))) && q('#dr-go').disabled && q('#dr-client').value === '');
    q('#dr-client').value = 'Brisa Solar'; q('#dr-client').dispatchEvent(new Event('input')); await wait(10);
    check('A12 with a client name the update can be prepared', !q('#dr-go').disabled && q('#dr-oname').value === 'Brisa Solar - CRM');
    q('#dr-go').click(); await wait(80);
    check('A12 offline, a new conversation is not answered: the page says how to connect the agent', /agent is offline/.test(txt(q('#toast-tx'))) && /Settings/.test(txt(q('#toast-act'))), txt(q('#toast-tx')));
  }
  async function P1() {
    await reset();
    await goto('#/settings/permissions', '#tb-perm');
    check('P1 Permissions explain the three levels', qq('.perm-legend .pl').length === 3 && /Always allow/.test(txt(q('.perm-legend'))) && /Needs approval/.test(txt(q('.perm-legend'))) && /Never/.test(txt(q('.perm-legend'))));
    check('P1 every field has its own control', qq('#tb-perm tr[data-perm-field]').length === FIELDS.length && qq('#tb-perm tr[data-perm-field]').every(tr => qq('[data-pf]', tr).length === 3));
    check('P1 the defaults come from the field schema', FIELDS.every(k => q('#tb-perm tr[data-perm-field="' + k + '"] [aria-checked="true"]').dataset.pf === (DEF[k].permission || 'ask')));
    q('#tb-perm tr[data-perm-field="budget"] [data-pf="off"]').click(); await wait(10);
    q('#tb-perm tr[data-perm-field="next_step"] [data-pf="auto"]').click(); await wait(10);
    check('P1 a click changes the permission and it is saved', CRM.state().settings.permissions.fields.budget === 'off' && CRM.state().settings.permissions.fields.next_step === 'auto');
    const id = await addRun(T.T1);
    check('P1 a field set to Never is left alone', row('budget').dataset.status === 'off' && !q('.dec button', row('budget')) && !fv(oppOf('OPP-0142'), 'budget').value);
    check('P1 a field set to Always allow is written without a click', !!fv(oppOf('OPP-0142'), 'next_step').value && row('next_step').dataset.auto === '1');
    q('[data-undo-auto]', row('next_step')).click(); await wait(20);
    check('P1 Undo puts the previous value back', !fv(oppOf('OPP-0142'), 'next_step').value && /Undone/.test(txt(q('.dec', row('next_step')))) && runOf(id).log.some(ev => ev.action === 'crm_write_reverted'));
    await goto('#/settings/permissions', '#tb-perm');
    q('#tb-perm [data-pg-qualification="auto"]').click(); await wait(10);
    check('P1 a whole group can be set at once', FIELDS.filter(k => DEF[k].group === 'qualification').every(k => CRM.state().settings.permissions.fields[k] === 'auto'));
    q('#perm-reset').click(); await wait(10);
    check('P1 Restore defaults', FIELDS.every(k => CRM.state().settings.permissions.fields[k] === (DEF[k].permission || 'ask')));
    q('[data-pc="off"]').click(); await wait(10);
    const id2 = await addRun(T.T5);
    check('P1 with new opportunities set to Never, an unknown company is blocked', runOf(id2).status === 'Blocked' && /turned off/.test(runOf(id2).output.block_reason));
    await goto('#/settings/permissions', '#tb-perm');
    q('[data-pc="auto"]').click(); await wait(10);
    const id3 = await addRun(T.T5);
    const r3 = runOf(id3);
    check('P1 with Always allow, the opportunity is created as soon as the update is prepared', !!(r3.output.target && r3.output.target.created && r3.output.target.created.auto) && !!oppOf(r3.output.opportunity_id) && !q('#rev-new [data-create]'));
    await goto('#/settings/permissions', '#tb-perm');
    q('[data-pc="ask"]').click(); await wait(10);
    check('P1 new opportunities back to Needs approval', CRM.state().settings.permissions.create_opportunity === 'ask');
    check('P1 the rules that no permission changes are listed', qq('#set-body .rules li').length >= 3 && /Closed Won/.test(txt(q('#set-body .rules'))) && /contradicts/.test(txt(q('#set-body .rules'))));
  }
  async function S1() {
    await reset();
    const tabs = qq('#set-tabs [data-tab]').map(b => b.dataset.tab);
    check('S1 Settings has its tabs', tabs.join('|') === 'permissions|agent|sources|team|activity|quality|data', tabs.join('|'));
    for (const t of tabs) {
      await goto('#/settings/' + t, '#set-body .pn');
      check('S1 the ' + t + ' tab renders', q('#set-tabs [data-tab="' + t + '"]').getAttribute('aria-selected') === 'true' && txt(q('#set-body')).length > 40);
    }
    await goto('#/settings/agent', '#ag-check');
    check('S1 Agent shows the connection and how to start the server', /not running/.test(txt(q('#set-body'))) && /node mockups\/server\.mjs/.test(txt(q('#set-body'))) && /ANTHROPIC_API_KEY/.test(txt(q('#set-body'))));
    check('S1 Agent offers the three Claude models and the effort', qq('#set-body [data-model]').length === 3 && qq('#set-body [data-effort]').length === 3);
    q('#set-body [data-model="claude-haiku-5-5"]').click(); await wait(10);
    check('S1 the model choice is saved', CRM.state().settings.model === 'claude-haiku-5-5');
    await goto('#/settings/sources', '.src-l');
    check('S1 Sources lists transcripts, WhatsApp and Granola', /Meeting transcripts/.test(txt(q('.src-l'))) && /WhatsApp/.test(txt(q('.src-l'))) && /Granola/.test(txt(q('.src-l'))) && /Not connected/.test(txt(q('.src-l'))));
    check('S1 Activity is in Settings, not in the navigation', !q('.nav-i[data-view="activity"]') && !q('.nav-i[data-view="agent"]'));
    location.hash = '#/activity'; await until(() => /#\/settings\/activity/.test(location.hash), 'old route redirects');
    ok('S1 the old activity route lands on Settings > Activity log');
  }
  async function S2() {
    await reset();
    await goto('#/settings/quality', '#eval-run');
    q('#eval-run').click();
    await until(() => q('#tb-eval .ev-res'), 'eval replayed');
    const rows = CRM.state().evalRows;
    check('S2 every test conversation passes in this page', rows.length === FOTO.expected.cases.length && rows.every(r => r.pass), rows.filter(r => !r.pass).map(r => r.case_id + ': ' + r.fails.join('; ')).join(' | '));
    const plat = rows.flatMap(r => r.platform);
    check('S2 the write checks pass', plat.length >= 6 && plat.every(p => p[1]), plat.filter(p => !p[1]).map(p => p[0]).join(' | '));
    check('S2 the replay does not touch the CRM', crm() === seed());
  }
  async function F1() {
    await reset();
    CRM.switchUser('U04');
    await goto('#/opportunities', '#opps-groups .fg');
    const groups = qq('#opps-groups .fg');
    const open = FOTO.schema.stages.filter(s => !FOTO.schema.closed_stages.includes(s));
    check('F1 one section per open stage, in funnel order', groups.map(g => g.dataset.stage).join('|') === open.join('|'));
    check('F1 the manager sees every open opportunity', qq('#opps-groups .fr').length === FOTO.opportunities.length, qq('#opps-groups .fr').length);
    check('F1 each section count equals its rows', groups.every(g => txt(q('[data-n]', g)) === String(qq('.fr', g).length)));
    check('F1 every row shows its MEDDPICC coverage', qq('#opps-groups .fr').every(r => qq('.mdp-c', r).length === 8));
    q('#opps-chips [data-stage="Proposal"]').click(); await wait(20);
    const vis = qq('#opps-groups .fg').filter(shown).map(g => g.dataset.stage);
    check('F1 a stage chip shows only its section', vis.length === 1 && vis[0] === 'Proposal', vis.join(','));
    q('#opps-chips [data-stage="all"]').click(); await wait(20);
    q('#opps-sort').value = 'qual'; q('#opps-sort').dispatchEvent(new Event('change')); await wait(20);
    const sec = qq('#opps-groups .fg').find(g => qq('.fr', g).length >= 2);
    const known = r => CRM.core.meddpiccOf(FOTO.schema, FOTO.opportunities.find(o => o.opportunity_id === r.dataset.opp)).known;
    check('F1 sort by thinnest qualification', !sec || known(qq('.fr', sec)[0]) <= known(qq('.fr', sec)[1]));
    CRM.switchUser('U01'); await goto('#/opportunities', '#opps-groups .fg');
    check('F1 Ana sees only her opportunities', qq('#opps-groups .fr').length === FOTO.opportunities.filter(o => o.owner_id === 'U01').length && !shown(q('#opps-owner-w')));
  }
  async function F2() {
    await reset();
    await goto('#/opportunities', '#opps-groups .fr');
    q('#opps-groups [data-details="OPP-0144"]').click(); await until(() => q('#opp-drw').open, 'drawer');
    check('F2 the drawer shows MEDDPICC and what to ask next', !!q('#opp-drw .dsec-mdp .mdp') && qq('#opp-drw .ask li').length >= 1 && /MEDDPICC/.test(txt(q('#opp-drw .dsec-mdp'))));
    check('F2 the drawer is modal (Esc closes it)', q('#opp-drw').matches(':modal'));
    q('#opp-drw-x').click(); await until(() => !q('#opp-drw').open, 'closed by x');
    location.hash = '#/opportunities/OPP-0142'; await until(() => q('#opp-drw').open, 'drawer by route');
    check('F2 the route opens the drawer', /Acme Logistics/.test(txt(q('#opp-drw-t'))));
    q('#opp-drw').dispatchEvent(new MouseEvent('click', {bubbles: true}));
    await until(() => !q('#opp-drw').open && location.hash === '#/opportunities', 'closed by backdrop');
    ok('F2 a click outside closes it and the route goes back to the list');
    CRM.switchUser('U02');
    location.hash = '#/opportunities/OPP-0142'; await until(() => q('#opp-drw').open, 'drawer as Lucas');
    check('F2 no access: the drawer shows no data', /do not have access/.test(txt(q('#opp-drw-b'))) && !/Acme|Sales CRM rollout/.test(txt(q('#opp-drw'))));
    q('#opp-drw-x').click(); await wait(20);
  }
  async function F3() {
    await reset();
    CRM.switchUser('U04');
    await goto('#/clients', '#cl-list .cl-card');
    const cards = qq('#cl-list .cl-card');
    check('F3 one card per client', cards.length === FOTO.clients.length, cards.length);
    const gaps = cards.slice(1).map((c, i) => c.getBoundingClientRect().top - cards[i].getBoundingClientRect().bottom);
    check('F3 the clients are separated: a gap between cards', gaps.every(g => g >= 8), gaps.slice(0, 4).map(Math.round).join(','));
    check('F3 each card has its own border', cards.every(c => parseFloat(getComputedStyle(c).borderTopWidth) >= 1));
    check('F3 every card lists its own opportunities', cards.every(c => qq('.cl-op', c).length === FOTO.opportunities.filter(o => o.client_id === c.dataset.client).length));
    const many = FOTO.clients.find(c => FOTO.opportunities.filter(o => o.client_id === c.client_id).length > 1);
    q('#cl-list [data-client-details="' + many.client_id + '"]').click(); await until(() => q('#cli-drw').open, 'client drawer');
    check('F3 the client drawer shows contacts and opportunities', qq('#cli-drw-b [data-details]').length > 1 && /Contacts/.test(txt(q('#cli-drw-b'))));
    q('#cli-drw-b [data-details]').click(); await until(() => q('#opp-drw').open, 'opp from client');
    check('F3 from a client to one of its opportunities', !q('#cli-drw').open && txt(q('#opp-drw-t')).indexOf(many.name) === 0);
    q('#opp-drw-x').click(); await wait(20);
    CRM.switchUser('U01'); await goto('#/clients', '#cl-list .cl-card');
    const anaClients = FOTO.clients.filter(c => FOTO.opportunities.some(o => o.client_id === c.client_id && o.owner_id === 'U01'));
    check('F3 Ana sees only the clients where she owns an opportunity', qq('#cl-list .cl-card').length === anaClients.length);
  }
  async function C0() {
    const bar = () => q('.hd').getBoundingClientRect().bottom;
    const titleOk = (v, how) => {
      const h1 = q('.view[data-view="' + v + '"] h1').getBoundingClientRect();
      check('C0 ' + how + ' lands on ' + v + ' with its title below the sticky bar', h1.top >= bar() - 1 && h1.bottom <= window.innerHeight, 'h1 top ' + Math.round(h1.top) + ', bar ' + Math.round(bar()) + ', scrollY ' + window.scrollY);
    };
    await reset();
    await addRun(T.T1); window.scrollTo(0, 2000); await wait(20);
    for (const v of ['opportunities', 'clients', 'settings', 'meetings', 'explore']) {
      q('.nav-i[data-view="' + v + '"]').click(); await until(() => !view(v).hidden, v); await wait(20);
      titleOk(v, 'a nav click');
    }
    await goto('#/meetings', '#mt-add');
    CRM.switchUser('U04'); await wait(30); titleOk('meetings', 'a user switch');
    CRM.switchUser('U01');
  }
  async function C1() {
    await reset();
    const views = ['explore', 'meetings', 'opportunities', 'clients', 'settings'];
    const hits = [];
    for (const v of views) { await goto('#/' + v, '.view[data-view="' + v + '"]:not([hidden])'); const t = txt(view(v)) + ' ' + txt(q('.hd')) + ' ' + txt(q('.side')); const m = t.match(JARGON); if (m) hits.push(v + ': ' + m[0]); }
    await addRun(T.T1); const m2 = (txt(view('review')) + txt(q('.hd'))).match(JARGON); if (m2) hits.push('review: ' + m2[0]);
    check('C1 no prototype jargon on screen (Call-to-CRM, mock, reference answers, demo notes)', !hits.length, hits.join(' | '));
    check('C1 the agent pill says how it runs and opens Settings > Agent', /offline/.test(txt(q('#job'))));
    q('#job').click(); await until(() => /#\/settings\/agent/.test(location.hash), 'pill to settings');
    ok('C1 the pill opens Settings > Agent');
    CRM.switchUser('U04'); await goto('#/meetings', '#tb-meetings');
    check('C1 the manager has no meetings of her own and the page says why', !qq('#tb-meetings tr[data-mtg]').length && /manager/.test(txt(q('#tb-meetings'))));
    CRM.switchUser('U01');
  }
  async function C2() {
    await reset();
    await goto('#/settings/agent', '[data-model]');
    q('#set-body [data-model="claude-opus-5-5"]').click(); await wait(10);
    await addRun(T.T1); await approveAll(); await submit('C2');
    check('C2 CRM changed by the update', crm() !== seed());
    CRM.resetAll(); location.hash = '#/meetings'; await until(() => !view('meetings').hidden, 'meetings');
    check('C2 reset restores the seed and empties the meetings, but keeps the settings', crm() === seed() && CRM.state().runOrder.length === 0 && CRM.state().meetings.length === 0 && CRM.state().settings.model === 'claude-opus-5-5');
    CRM.state().settings.model = 'claude-sonnet-5-5';
  }
  async function C3() {
    const kinds = {vtt: [T.T1, T.T4, T.T5, T.T8, T.T9], srt: [T.T6], otter: [T.T3], plain: [T.T7], kit: [T.T2, T.T10], whatsapp: [T.T11]};
    const keys = new Set(Object.values(FOTO.transcripts).map(t => CRM.core.conversationKey(CRM.core.transcriptLines(t))));
    for (const [k, files] of Object.entries(kinds)) for (const f of files) {
      const p = CRM.core.parseConversation(SAMPLES[f], {now: FOTO.data_da_foto});
      check('C3 ' + f + ' reads as ' + k + ' and back to the same spoken text', p.kind === k && keys.has(CRM.core.conversationKey(p.lines)), p.kind + ' ' + p.lines.length);
    }
  }
  async function C4() {
    await reset();
    const id = await addRun(T.T1);
    const evb = q('#tb-rev .evb'); const line = +evb.dataset.ev.split('|')[1];
    evb.click(); await until(() => q('#drw').open, 'drawer');
    const L = CRM.core.transcriptLines(CRM.state().transcripts[runOf(id).meetingId])[line - 1];
    check('C4 evidence opens the transcript with its line highlighted', !!q('#tl-hl') && txt(q('#tl-hl time')) === L.timestamp && !!q('#tl-hl .tl-mark'));
    q('#drw-x').click(); await until(() => !q('#drw').open, 'drawer closed');
    ok('C4 the x closes the transcript');
  }
  async function contrato(label) {
    const noName = qq('button').filter(b => !txt(b) && !b.getAttribute('aria-label') && !b.title);
    check(label + ' every button has an accessible name', !noName.length, noName.map(b => b.outerHTML.slice(0, 60)).join(' | '));
    check(label + ' no button or link nested in a button', !q('button button, button a, a button, a a'));
    const rest = ['.pn', '.strip', '.tb', '.ch', '.b', '.nav-i', '.job', '.hd-in', '.mn', '.evb', '.fid', '.fr', '.fi', '.dsec', '.cl-card', '.cmp', '.msg'];
    const shadow = rest.filter(sel => qq(sel).some(el => getComputedStyle(el).boxShadow !== 'none'));
    check(label + ' no shadow at rest', !shadow.length, shadow.join(' '));
    const magenta = qq('body *').filter(el => { const cs = getComputedStyle(el); return cs.backgroundColor === 'rgb(255, 0, 102)' || cs.color === 'rgb(255, 0, 102)'; });
    check(label + ' magenta only as signal (mark and counter)', magenta.length <= 2 && magenta.every(el => el.matches('.ws-mk i, .nav-n.hot, .unseen')), magenta.map(el => el.className).join(' '));
    const heavy = qq('body *').filter(el => { const w = parseInt(getComputedStyle(el).fontWeight, 10); return w > 500 && txt(el); });
    check(label + ' no weight above 500', !heavy.length, heavy.slice(0, 3).map(el => el.tagName + '.' + el.className).join(' '));
    check(label + ' the visible view has one h1', qq('.view').filter(v => !v.hidden).every(v => qq('h1', v).length === 1));
    check(label + ' no horizontal scroll at this width', document.documentElement.scrollWidth <= window.innerWidth + 1, document.documentElement.scrollWidth + ' > ' + window.innerWidth);
  }
  async function C5() {
    await reset();
    await addRun(T.T3);
    await contrato('C5 review');
    check('C5 body font is Inter', /Inter/.test(getComputedStyle(document.body).fontFamily));
    check('C5 contradictory row carries the warning rule', getComputedStyle(row('next_step').querySelector('td')).boxShadow !== 'none');
    await drop(T.T5); await contrato('C5 meetings with a draft');
    await goto('#/explore', '#ex-cmp'); await contrato('C5 explore');
    await ask("What's missing to qualify Atlas Manufacturing?"); await contrato('C5 explore answer');
    CRM.switchUser('U04');
    for (const [h, sel] of [['#/opportunities', '#opps-groups .fr'], ['#/clients', '#cl-list .cl-card'], ['#/settings/permissions', '#tb-perm'], ['#/settings/activity', '#act-list'], ['#/settings/quality', '#tb-eval'], ['#/settings/agent', '[data-model]'], ['#/settings/sources', '.src-l']]) {
      await goto(h, sel); await contrato('C5 ' + h.slice(2));
    }
    CRM.switchUser('U01');
  }

  // C6: real contrast of every visible text (ink over the effective background, alpha composed)
  function parseRgba(s) { const m = /rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/.exec(s || ''); return m ? [+m[1], +m[2], +m[3], m[4] == null ? 1 : +m[4]] : null; }
  function over(fg, bg) { const a = fg[3]; return [fg[0] * a + bg[0] * (1 - a), fg[1] * a + bg[1] * (1 - a), fg[2] * a + bg[2] * (1 - a), 1]; }
  function lum(c) { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); }
  function ratio(a, b) { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); }
  function bgOf(el) {
    let node = el, stack = [];
    while (node && node !== document.documentElement) { const c = parseRgba(getComputedStyle(node).backgroundColor); if (c && c[3] > 0) { stack.push(c); if (c[3] >= 1) break; } node = node.parentElement; }
    let bg = [245, 245, 245, 1];
    for (let i = stack.length - 1; i >= 0; i--) bg = over(stack[i], bg);
    return bg;
  }
  function contraste(label, root) {
    const bad = [], seen = new Set();
    for (const el of qq('*', root || document.body)) {
      if (el.closest('[hidden], dialog:not([open]), #sonda-out, script, style')) continue;
      const hasText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
      if (!hasText) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || !el.getClientRects().length) continue;
      const fg = parseRgba(cs.color); if (!fg) continue;
      const bg = bgOf(el);
      const r = ratio(over(fg, bg), bg);
      const big = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
      if (r < (big ? 3 : 4.5)) { const key = el.tagName + '.' + el.className; if (!seen.has(key)) { seen.add(key); bad.push(key + ' ' + r.toFixed(2) + ':1 "' + txt(el).slice(0, 30) + '"'); } }
    }
    check(label + ' every visible text meets 4.5:1 (3:1 above 24px) on its real background', !bad.length, bad.slice(0, 8).join(' | '));
  }
  async function C6() {
    await reset();
    await goto('#/explore', '#ex-cmp'); contraste('C6 explore');
    await ask("What's the status of Solaris Energy?"); contraste('C6 explore answer');
    await drop(T.T5); contraste('C6 meetings with a draft');
    await prepare('T5'); contraste('C6 review new client');
    await reset(); await addRun(T.T1); contraste('C6 review');
    CRM.switchUser('U04');
    await goto('#/opportunities', '#opps-groups .fr'); contraste('C6 opportunities');
    CRM.openOppDrawer('OPP-0149'); await until(() => q('#opp-drw').open, 'drawer'); contraste('C6 opportunity drawer', q('#opp-drw')); q('#opp-drw').close();
    await goto('#/clients', '#cl-list .cl-card'); contraste('C6 clients');
    await goto('#/settings/permissions', '#tb-perm'); contraste('C6 permissions');
    await goto('#/settings/sources', '.src-l'); contraste('C6 sources');
    await goto('#/settings/activity', '#act-list'); contraste('C6 activity log');
    CRM.switchUser('U01');
  }
  async function main() {
    const steps = [A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, P1, S1, S2, F1, F2, F3, C0, C1, C2, C3, C4, C5, C6];
    for (const s of steps) { try { await s(); } catch (err) { out.push('EXC ' + s.name + ' :: ' + err.message); flush(); } }
    out.push('ERRS ' + errs.length + (errs.length ? ' :: ' + errs.join(' | ') : ''));
    out.push('DONE'); flush();
  }
  document.addEventListener('DOMContentLoaded', () => { setTimeout(main, 30); });
})();
</script>

"""

STEPS_LINE = "const steps = [A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, P1, S1, S2, F1, F2, F3, C0, C1, C2, C3, C4, C5, C6];"

CENAS = {
    "explore": "await goto('#/explore', '#ex-cmp');",
    "explore-answer": "await ask(\"What's the status of Atlas Manufacturing?\");",
    "meetings-draft": "await drop(T.T1); window.scrollTo(0, 0);",
    "meetings-new": "await drop(T.T5); window.scrollTo(0, 300);",
    "review-t1": "await addRun(T.T1); window.scrollTo(0, 0);",
    "review-t5": "await addRun(T.T5); window.scrollTo(0, 0);",
    "review-t11": "await addRun(T.T11); window.scrollTo(0, 0);",
    "opportunities": "CRM.switchUser('U04'); await goto('#/opportunities', '#opps-groups .fr');",
    "opp-drawer": "await goto('#/opportunities/OPP-0144', '#opp-drw[open]');",
    "clients": "await goto('#/clients', '#cl-list .cl-card');",
    "permissions": "await goto('#/settings/permissions', '#tb-perm');",
    "agent": "await goto('#/settings/agent', '[data-model]');",
    "sources": "await goto('#/settings/sources', '.src-l');",
    "activity": "await addRun(T.T7); await approveAll(); q('#rev-submit').click(); await wait(40); await goto('#/settings/activity', '#act-list .fi');",
    "quality": "await goto('#/settings/quality', '#eval-run'); q('#eval-run').click(); await wait(60);",
}


def _cena(nome):
    return ROTEIRO.replace(STEPS_LINE, "const steps = [async function cena() { await reset(); %s }];" % CENAS[nome])


def com_amostras(roteiro):
    """Os arquivos de capstone/samples/ entram no roteiro como texto: a sonda solta cada um no campo de arquivo."""
    amostras = {f: open(os.path.join(SAMPLES, f), encoding="utf-8").read() for f in sorted(os.listdir(SAMPLES)) if not f.endswith(".md")}
    return roteiro.replace("__SAMPLES__", json.dumps(amostras, ensure_ascii=False).replace("</", "<\\/"))


def _copia_ascii(roteiro):
    base = tempfile.mkdtemp(prefix="sonda_cap_")
    with open(HTML, encoding="utf-8") as fp:
        doc = fp.read()
    roteiro = com_amostras(roteiro)
    # a porta fechada deixa o agente offline: a sonda nunca depende de um servidor rodando na maquina
    doc = doc.replace("<head>", "<head><script>window.CAPSTONE_API='http://127.0.0.1:9';</script>", 1)
    doc = doc.replace("</body>", roteiro + "\n</body>")
    alvo = os.path.join(base, "cap.html")
    with open(alvo, "w", encoding="utf-8") as fp:
        fp.write(doc)
    return base, alvo


def _edge(alvo, base, largura, altura, rota, foto=None, budget=90000):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
           "--window-size=%d,%d" % (largura, altura), "--user-data-dir=" + os.path.join(base, "ud"),
           "--virtual-time-budget=%d" % budget]
    if foto:
        cmd.append("--screenshot=" + foto)
    else:
        cmd.append("--dump-dom")
    cmd.append("file:///" + alvo.replace("\\", "/") + rota)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout or ""


def sondar(largura=1440, altura=900):
    base, alvo = _copia_ascii(ROTEIRO)
    try:
        dom = _edge(alvo, base, largura, altura, "#/meetings")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    m = re.search(r'<pre id="sonda-out"[^>]*>(.*?)</pre>', dom, re.S)
    if not m:
        return ["EXC sonda :: a pagina nao escreveu o laudo (dump sem #sonda-out)"]
    import html as _h
    return [_h.unescape(l) for l in m.group(1).split("\n") if l.strip()]


def main():
    if "--foto" in sys.argv:
        nome = sys.argv[sys.argv.index("--foto") + 1]
        largura = int(sys.argv[sys.argv.index("--largura") + 1]) if "--largura" in sys.argv else 1440
        saida_png = sys.argv[sys.argv.index("--saida") + 1] if "--saida" in sys.argv else os.path.join(tempfile.gettempdir(), "cap_%s_%d.png" % (nome, largura))
        base, alvo = _copia_ascii(_cena(nome))
        try:
            _edge(alvo, base, largura, 900, "#/meetings", foto=saida_png, budget=12000)
        finally:
            shutil.rmtree(base, ignore_errors=True)
        print("foto: %s" % saida_png)
        return 0
    total_ok, ruins = 0, []
    for w in (1440, 1280):
        linhas = sondar(w)
        oks = [l for l in linhas if l.startswith("OK")]
        maus = [l for l in linhas if l.startswith("FAIL") or l.startswith("EXC") or (l.startswith("ERRS") and not l.startswith("ERRS 0"))]
        if "DONE" not in linhas:
            maus.append("EXC %d :: o roteiro nao chegou ao fim" % w)
        total_ok += len(oks)
        print("[%d] %d ok, %d problemas" % (w, len(oks), len(maus)))
        for l in maus:
            print("   " + l)
            ruins.append("%d: %s" % (w, l))
    print("SONDA: %d verificacoes ok, %d problemas" % (total_ok, len(ruins)))
    return 1 if ruins else 0


if __name__ == "__main__":
    raise SystemExit(main())
