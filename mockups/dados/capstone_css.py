# -*- coding: utf-8 -*-
"""Folha de estilo do mockup Call-to-CRM: a pele do SalesOps v5 ("folha sobre a
mesa") escrita do zero para as superficies desta peca. Stdlib pura.

    import capstone_css as CS; CS.CSS

O que vem da v5 sem mudar: os tokens do :root (mesa, folha, cartao, tinta em
preto com alfa, acao preta, magenta so como sinal, estados em par pastel e
tinta, banner escuro com brilho), a escala tipografica do app Lightfield
(11/14 · 12/16 · 13/18 · 15/20 · 15/24 · 17/22 · 24/31), a casca (lateral sobre
a mesa, folha com fio e canto de 12px, barra do agente), botao, chip, cartao,
tabela, gaveta, dialogo e recibo. O que e desta peca: a tabela de revisao
agrupada pelas secoes do esquema de campos, a evidencia como botao que abre a
transcricao, os controles de decisao na linha (com editor por tipo), o estado
"bloqueado", o cartao do Granola, o funil de oportunidades por etapa (chips em
cima, secoes empilhadas na ordem do funil, linha em grid, gaveta do registro), a
lista de clientes com as suas oportunidades, o feed da atividade e as
verificacoes de qualidade do agente.

Regras herdadas que a sonda confere: nenhuma sombra em repouso (so a camada
que flutua), magenta cheio em tres lugares (marca, contador da lateral, ponto
de nao visto), nenhum peso acima de 500, cor de estado so em chip e ponto.
"""

CSS = r"""
:root{
  color-scheme:only light;
  --mesa:#F5F5F5; --folha:#EFEFF0; --surface:#FFFFFF; --surface-2:#FAFAFA;
  --glass:rgba(239,239,240,.92);
  --ink:#0A0A0A;
  --t1:rgba(10,10,10,.85); --t2:rgba(10,10,10,.75); --t3:rgba(10,10,10,.60); --t4:rgba(10,10,10,.42);
  --line:rgba(10,10,10,.08); --line2:rgba(10,10,10,.06); --line3:rgba(10,10,10,.14); --line4:rgba(10,10,10,.22);
  --line-card:rgba(10,10,10,.09);
  --fill-0:rgba(10,10,10,.03); --fill-1:rgba(10,10,10,.04); --fill-2:rgba(10,10,10,.06); --fill-3:rgba(10,10,10,.10);
  --scrim:rgba(10,10,10,.20); --scrim-2:rgba(10,10,10,.32); --focus-line:rgba(10,10,10,.50);
  --act:#171717; --act-h:#2E2E2E; --on-act:#FFFFFF;
  --signal:#FF0066;
  --ok:#2F6B3A; --ok-bg:#E5F4EA; --ok-dot:#22A35A;
  --warn:#7A5B14; --warn-bg:#F8EED6; --warn-dot:#C9951E;
  --bad:#A0302A; --bad-bg:#FBEAE8; --bad-dot:#D15A4A; --bad-h:#8A2823;
  --info:#1E4B99; --info-bg:#E8F0FE;
  --neutral:#52525B; --neutral-bg:#F3F3F3;
  --teams:#3B4A8C; --teams-bg:#ECEEF8;
  --dk:#0A0A0A; --dk-t1:#FFFFFF; --dk-t2:rgba(255,255,255,.76); --dk-t3:rgba(255,255,255,.60);
  --dk-line:rgba(255,255,255,.14); --dk-fill:rgba(255,255,255,.06); --dk-hover:rgba(255,255,255,.08);
  --dk-hot:#FF4D8D; --dk-link:#FF7DAA;
  --glow:radial-gradient(60% 150% at 92% 0%, rgba(255,0,102,.38), transparent 60%),
         radial-gradient(55% 150% at 0% 100%, rgba(150,18,98,.28), transparent 60%),
         radial-gradient(40% 120% at 100% 100%, rgba(29,224,208,.08), transparent 60%);
  --r:6px; --r-chip:5px; --r-field:8px; --r-card:10px; --r-card-in:9px; --r-sheet:12px; --r-pill:999px; --r-mark:2px;
  --font:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --mono:'DM Mono',ui-monospace,'Cascadia Mono',Consolas,monospace;
  --fs-xxs:11px; --lh-xxs:14px; --fs-xs:12px; --lh-xs:16px; --fs-sm:13px; --lh-sm:18px;
  --fs-base:15px; --lh-base:20px; --fs-lg:17px; --lh-lg:22px; --fs-h2:24px; --lh-h2:31px; --fs-p:15px; --lh-p:24px;
  --w-r:425; --w-m:500;
  --gap:8px; --bar-h:52px; --hd-h:calc(var(--gap) + var(--bar-h)); --nav-w:228px; --mn-x:24px;
  --float:0 0 0 1px rgba(10,10,10,.05),0 12px 32px -8px rgba(10,10,10,.16);
  --ease:cubic-bezier(.2,.7,.2,1);
}
@media(max-width:1400px){:root{--nav-w:216px;--mn-x:16px}}

*,*::before,*::after{box-sizing:border-box}
html{background:var(--mesa);scroll-padding-top:calc(var(--hd-h) + var(--gap))}
body{margin:0;background:var(--mesa);color:var(--t1);font-family:var(--font);font-size:var(--fs-sm);line-height:1.385;
  font-weight:var(--w-r);font-feature-settings:normal;letter-spacing:0;-webkit-font-smoothing:antialiased}
::selection{background:var(--fill-3)}
:focus-visible{outline:2px solid var(--act);outline-offset:2px}
h1,h2,h3,h4{margin:0;font-weight:var(--w-m);letter-spacing:0}
h1{font-size:var(--fs-h2);line-height:var(--lh-h2);letter-spacing:-.0125em}
h2{font-size:var(--fs-base);line-height:var(--lh-base)}
p{margin:0}
b,strong{font-weight:var(--w-m)}
a{color:inherit}
button{font:inherit;color:inherit;cursor:pointer}
input,textarea,select{font:inherit;color:var(--t1)}
kbd{font:500 var(--fs-xxs)/1 var(--mono);color:var(--t3);background:var(--surface);border:1px solid var(--line3);
  border-radius:var(--r-chip);padding:2px 5px}
.mini{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.t3{color:var(--t3)}
.mono{font-family:var(--mono);font-size:var(--fs-xs);font-weight:400}
.grow{flex:1}
.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
[hidden]{display:none!important}
*{scrollbar-width:thin;scrollbar-color:var(--line4) transparent}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--line3);border-radius:var(--r-pill);border:3px solid transparent;background-clip:content-box}
::-webkit-scrollbar-track{background:transparent}

/* ===================================================================== */
/* casca: a lateral sobre a mesa, a folha com fio e canto de 12px          */
/* ===================================================================== */
.app{display:grid;grid-template-columns:var(--nav-w) minmax(0,1fr);align-items:start;min-height:100vh}
.side{position:sticky;top:0;z-index:65;height:100vh;display:flex;flex-direction:column;min-width:0;padding:var(--gap) 0 0 var(--gap)}
.side-top{display:flex;flex-direction:column;gap:10px;padding:8px 8px 12px 6px;flex:none}
.ws{display:flex;align-items:center;gap:10px;padding:4px 4px 2px}
.ws-mk{width:26px;height:26px;border-radius:var(--r);background:var(--act);display:grid;place-items:center;flex:none}
.ws-mk i{width:9px;height:9px;border-radius:var(--r-mark);background:var(--signal);transform:rotate(45deg);display:block}
.ws-t{display:flex;flex-direction:column;min-width:0;line-height:1.25}
.ws-t b{font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t1)}
.ws-t span{font-size:var(--fs-xs);color:var(--t3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav{flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;gap:1px;padding:0 8px 8px 0}
.nav-g{padding:18px 8px 6px;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t3)}
.nav-g:first-child{padding-top:6px}
.nav-i{display:flex;align-items:center;gap:10px;height:30px;padding:0 8px;border:0;border-radius:var(--r);background:transparent;
  font-size:var(--fs-sm);font-weight:var(--w-r);color:var(--t2);text-align:left;width:100%;flex:none}
.nav-i:hover{background:var(--fill-1);color:var(--t1)}
.nav-i.on{background:var(--fill-2);color:var(--t1);font-weight:var(--w-m)}
.nav-i .lb{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-i .nav-n{font-size:var(--fs-xs);color:var(--t3);font-weight:var(--w-r)}
.nav-i .nav-n.hot{min-width:20px;height:18px;padding:0 6px;border-radius:var(--r-pill);background:var(--signal);color:var(--ink);
  font-size:var(--fs-xxs);line-height:18px;font-weight:var(--w-m);text-align:center}
.nav-i.two{display:grid;grid-template-columns:16px minmax(0,1fr);column-gap:10px;row-gap:0;align-items:center;height:auto;min-height:30px;padding:4px 8px}
.nav-i.two .ni{grid-row:1/3;grid-column:1}
.nav-i.two .lb{grid-column:2}
.nav-i.two .sub{grid-column:2;font-size:var(--fs-xs);line-height:1.3;color:var(--t3);font-weight:var(--w-r);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-i.on .sub{color:var(--t2)}
.nav-foot{border-top:1px solid var(--line);display:flex;flex-direction:column;gap:1px;padding-top:8px;margin-top:auto}
.ni{width:16px;height:16px;flex:none;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round;color:var(--t3)}
.nav-i:hover .ni,.nav-i.on .ni{color:var(--t1)}
.ico-b{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round;flex:none}
.ico-s{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round;flex:none}

.folha{min-width:0;margin:0 var(--gap) var(--gap) 0}
.hd{position:sticky;top:0;z-index:50;height:var(--hd-h);padding:var(--gap) 0 0;background:var(--mesa)}
.hd-in{height:var(--bar-h);display:flex;align-items:center;gap:10px;padding:0 12px 0 16px;background:var(--folha);
  border:1px solid var(--line);border-bottom-color:var(--line2);border-radius:var(--r-sheet) var(--r-sheet) 0 0}
.mn{min-width:0;padding:0 var(--mn-x) 40px;background:var(--folha);border:1px solid var(--line);border-top:0;
  border-radius:0 0 var(--r-sheet) var(--r-sheet);min-height:calc(100vh - var(--hd-h) - var(--gap))}
.view{padding-top:28px}
.view:focus{outline:0}
.ph{display:flex;align-items:flex-start;gap:16px;margin-bottom:20px}
.ph .ph-t{min-width:0;flex:1}
.ph .ph-c{font-size:var(--fs-sm);color:var(--t3);margin-top:4px;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
.ph .ph-c b{color:var(--t2)}
.ph .acts{display:flex;gap:8px;align-items:center;flex:none;padding-top:2px}

/* ---- a barra do agente (job bar) ---- */
.job{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px 0 10px;min-width:0;max-width:62%;
  border:1px solid var(--line);border-radius:var(--r-pill);background:var(--surface);font-size:var(--fs-sm);white-space:nowrap}
.job-ic{width:16px;height:16px;flex:none;display:grid;place-items:center;color:var(--t3)}
.job-ic svg{width:16px;height:16px}
.job-t{font-weight:var(--w-m);color:var(--t1);flex:none}
.job-s{color:var(--t3);overflow:hidden;text-overflow:ellipsis;min-width:0}
.job-s b{color:var(--t2);font-weight:var(--w-m)}
.job .spin{display:none;width:12px;height:12px;border-radius:50%;border:1.5px solid var(--line4);border-top-color:var(--act);animation:giraJob .6s linear infinite}
.job[data-estado="rodando"] .spin{display:block}
.job[data-estado="rodando"] .job-ic svg{display:none}
@keyframes giraJob{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.job .spin{animation-duration:2.4s}}
.hd .b{height:32px}
.hbtn{height:32px;width:32px;padding:0;border:0;border-radius:var(--r);color:var(--t2);display:inline-grid;place-items:center;background:transparent}
.hbtn:hover{background:var(--fill-1);color:var(--t1)}
.hbtn.uav{width:28px;height:28px;border-radius:var(--r-pill);background:var(--fill-3);color:var(--t1)}
.hbtn.uav:hover,.umenu.open .hbtn.uav{background:var(--line4)}
.uav-i{font-size:var(--fs-xxs);line-height:var(--lh-xxs);font-weight:var(--w-m);letter-spacing:0;color:inherit}
.umenu{position:relative}
.umenu .pop{display:none;position:absolute;right:0;top:calc(100% + 6px);z-index:70;background:var(--surface);border:0;border-radius:var(--r-card);
  box-shadow:var(--float);padding:6px;width:300px}
.umenu.open .pop{display:block}
.pop-id{display:flex;align-items:center;gap:10px;margin:-6px -6px 6px;padding:12px 16px;border-bottom:1px solid var(--line2)}
.pop-id .uav-i{width:28px;height:28px;flex:none;display:inline-grid;place-items:center;border-radius:var(--r-pill);background:var(--fill-3);color:var(--t1)}
.pop-idt{display:flex;flex-direction:column;min-width:0}
.pop-nm{font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pop-org{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.pop-l{display:flex;flex-direction:column;gap:1px}
.pop-lab{padding:8px 10px 2px;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t3)}
.pi{display:flex;flex-direction:column;align-items:flex-start;gap:0;width:100%;border:0;background:transparent;text-align:left;
  color:var(--t1);font-size:var(--fs-sm);font-weight:var(--w-m);border-radius:var(--r);padding:8px 10px}
.pi:hover{background:var(--fill-1)}
.pi .sub{color:var(--t3);font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-r)}
.pi[aria-checked="true"]{background:var(--fill-2)}
.pi[aria-checked="true"]::after{content:'';display:none}
.pi .chk{display:inline-flex;align-items:center;gap:8px}
.pi .chk .ico-s{color:var(--t1)}

/* ===================================================================== */
/* botoes                                                                 */
/* ===================================================================== */
.b{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:32px;padding:0 12px;border-radius:var(--r);
  font-size:var(--fs-sm);font-weight:var(--w-m);border:1px solid transparent;background:transparent;color:var(--t1);
  white-space:nowrap;transition:background .12s,border-color .12s,color .12s;text-decoration:none}
.b-sm{height:28px;padding:0 10px}
.b-xs{height:24px;padding:0 8px;font-size:var(--fs-xs)}
.b-p{background:var(--act);color:var(--on-act);border-color:var(--act)}
.b-p:hover{background:var(--act-h);border-color:var(--act-h)}
.b-s{background:var(--fill-1);color:var(--t1)}
.b-s:hover{background:var(--fill-2)}
.b-t{background:transparent;color:var(--t2)}
.b-t:hover{background:var(--fill-1);color:var(--t1)}
.b-d{background:var(--bad);color:var(--on-act);border-color:var(--bad)}
.b-d:hover{background:var(--bad-h);border-color:var(--bad-h)}
.b[disabled]{opacity:.45;cursor:not-allowed}
.b .ico-b,.b .ico-s{color:inherit}
/* verbo de linha: cinza 6% em repouso, preto na linha em hover ou com foco */
.b-row{background:var(--fill-2);color:var(--t1)}
tr:hover .b-row,tr:focus-within .b-row,.rowh:hover .b-row,.rowh:focus-within .b-row,.b-row:hover{background:var(--act);color:var(--on-act);border-color:var(--act)}
.acts{display:inline-flex;gap:6px;align-items:center;flex-wrap:wrap}

/* ===================================================================== */
/* chips: fundo pastel, tinta do mesmo matiz, 11/14/500, canto de 5px      */
/* ===================================================================== */
.ch{display:inline-flex;align-items:center;gap:4px;height:20px;padding:0 6px;border-radius:var(--r-chip);
  font-size:var(--fs-xxs);line-height:var(--lh-xxs);font-weight:var(--w-m);border:1px solid transparent;white-space:nowrap;vertical-align:middle}
.ch-ok{background:var(--ok-bg);color:var(--ok)}
.ch-warn{background:var(--warn-bg);color:var(--warn)}
.ch-bad{background:var(--bad-bg);color:var(--bad)}
.ch-info{background:var(--info-bg);color:var(--info)}
.ch-neu{background:var(--neutral-bg);color:var(--neutral)}
.ch-teams{background:var(--teams-bg);color:var(--teams)}
.ch-nd{background:transparent;color:var(--t3);border:1px dashed var(--line4)}
.ch-sim{background:var(--surface);color:var(--info);border:1px dashed var(--info)}
.ch .ico-s{width:12px;height:12px}
.dot{display:inline-block;width:7px;height:7px;border-radius:var(--r-pill);vertical-align:middle;margin-right:6px}
.dot.ok{background:var(--ok-dot)}.dot.warn{background:var(--warn-dot)}.dot.bad{background:var(--bad-dot)}
.unseen{display:inline-block;width:6px;height:6px;border-radius:var(--r-pill);background:var(--signal);margin-left:6px;vertical-align:middle}

/* ===================================================================== */
/* cartao, banner, tabela, vazio                                          */
/* ===================================================================== */
.pn{background:var(--surface);border:1px solid var(--line-card);border-radius:var(--r-card);margin-top:16px}
.view .ph+.pn,.pn:first-child{margin-top:0}
.strip+.pn{margin-top:20px}
.pn-h{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line2);border-radius:var(--r-card-in) var(--r-card-in) 0 0}
.pn-h h2{font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m);letter-spacing:-.009em}
.pn-h .pn-n{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.pn-h .pn-d{font-size:var(--fs-sm);color:var(--t3)}
.pn-h .pn-d b{color:var(--t2)}
.pn-h .acts{margin-left:auto}
.pn-b{padding:14px 16px}
.pn-f{display:block;padding:10px 16px;border-top:1px solid var(--line2);font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.pn-f.row{display:flex;align-items:center;gap:10px}
.pn-f code{font-family:var(--mono);color:var(--t2)}
.pn-f .grow{flex:1}
.pn>.empty{margin:14px 16px}
.gr2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px}
@media(max-width:1180px){.gr2{grid-template-columns:1fr}}
.gr2>.pn{margin-top:0}

.strip{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;background-color:var(--dk);background-image:var(--glow);
  border:1px solid var(--dk-line);border-radius:var(--r-card);color:var(--dk-t1);overflow:hidden}
.strip .st{display:flex;flex-direction:column;gap:4px;padding:14px 16px 13px;border-left:1px solid var(--dk-line);min-width:0;
  text-align:left;background:transparent;border-top:0;border-right:0;border-bottom:0;color:var(--dk-t1)}
.strip .st:first-child{border-left:0}
.strip .st .v{font-size:var(--fs-h2);line-height:var(--lh-h2);font-weight:var(--w-m);letter-spacing:-.0125em;color:var(--dk-t1)}
.strip .st .v.hot{color:var(--dk-hot)}
.strip .st .v.zero{color:var(--dk-t3)}
.strip .st .v.na{font-size:var(--fs-base);line-height:var(--lh-h2);color:var(--dk-t3);font-weight:var(--w-r)}
.strip .st .l{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--dk-t2)}
.strip .st .l b{color:var(--dk-t1)}
.strip .st .go{font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--dk-link)}
.strip .st .go::after{content:'\2192';margin-left:5px}
.strip button.st{cursor:pointer}
.strip button.st:hover{background:var(--dk-hover)}
.strip button.st:hover .go{color:var(--dk-t1)}
.strip button.st:focus-visible{outline:2px solid var(--dk-t1);outline-offset:-4px}

.tbw{overflow-x:auto}
.tb{width:100%;border-collapse:collapse;font-size:var(--fs-sm);line-height:var(--lh-sm)}
.tb th{background:var(--surface);color:var(--t3);font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);letter-spacing:.005em;
  padding:0 12px;height:36px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
.tb th.num,.tb td.num{text-align:right}
.tb td{padding:10px 12px;height:44px;border-top:1px solid var(--line2);color:var(--t2);vertical-align:top}
.tb td.mid{vertical-align:middle}
.tb td.nw{white-space:nowrap}
.tb tbody tr:first-child td{border-top:0}
.tb tbody tr:hover td{background:var(--fill-0)}
.tb td b{color:var(--t1);font-weight:var(--w-m)}
.tb td .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);margin-top:1px}
.tb th:first-child,.tb td:first-child{padding-left:16px}
.tb th:last-child,.tb td:last-child{padding-right:16px}
.tb .nada{color:var(--t3)}
.lk{color:inherit;text-decoration:none;border-bottom:1px solid var(--line3)}
.lk:hover{border-bottom-color:var(--t1)}
.ttl{display:inline-flex;align-items:center;gap:8px;min-width:0}
.ttl>span:last-child{display:flex;flex-direction:column;min-width:0}
.ttl .sub{display:block}
.lg{display:inline-grid;place-items:center;flex:none;border-radius:4px;color:#fff;font-size:11px;line-height:1;font-weight:var(--w-m);width:16px;height:16px}
.lg.lg-20{width:20px;height:20px;border-radius:5px;font-size:12px}
.lg.lg-32{width:32px;height:32px;border-radius:7px;font-size:16px}

.empty{background:transparent;border:1px dashed var(--line3);border-radius:var(--r-card);color:var(--t2);font-size:var(--fs-sm);padding:14px 16px}
.empty b{color:var(--t1)}
.empty.soft{background:var(--surface-2);border:1px solid var(--line2)}
.empty.block{display:flex;gap:12px;align-items:flex-start;padding:16px}
.empty.block .ico-b{margin-top:1px;color:var(--bad)}
.empty.block p{margin-top:4px;color:var(--t2)}
.note{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}

/* filtro: o mesmo item da lateral (ativo = cinza 6%) */
.fgroup{display:inline-flex;gap:2px;align-items:center}
.fchip{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;border:0;border-radius:var(--r);background:transparent;
  font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t3)}
.fchip .n{font-size:var(--fs-xs);font-weight:var(--w-r);color:var(--t3)}
.fchip:hover{background:var(--fill-1);color:var(--t1)}
.fchip[aria-pressed="true"]{background:var(--fill-2);color:var(--t1)}
.fchip[aria-pressed="true"] .n{color:var(--t2)}
.seg{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;border:0;border-radius:var(--r);background:transparent;
  font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t3)}
.seg:hover{background:var(--fill-1);color:var(--t1)}
.seg[aria-checked="true"],.seg.on{background:var(--fill-2);color:var(--t1)}

/* ===================================================================== */
/* campos                                                                 */
/* ===================================================================== */
.fld{display:flex;flex-direction:column;gap:4px;min-width:0}
.fld-l{font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t2)}
.fld-l i{font-style:normal;color:var(--t3);font-weight:var(--w-r)}
.fld input,.fld select,.fld textarea,.inp{height:36px;border:1px solid var(--line3);border-radius:var(--r-field);padding:0 10px;
  font-size:var(--fs-sm);background:var(--surface);color:var(--t1);width:100%;margin:0}
.fld textarea,textarea.inp{height:auto;min-height:72px;padding:8px 10px;line-height:var(--lh-sm);resize:vertical}
.fld input:focus,.fld select:focus,.fld textarea:focus,.inp:focus{border-color:var(--focus-line);box-shadow:0 0 0 3px var(--fill-2);outline:0}
.fld input[readonly]{background:var(--fill-1);color:var(--t2)}
.frow{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px 16px;align-items:end}

/* ===================================================================== */
/* a tabela de revisao: campo · atual · proposta · evidencia · decisao      */
/* ===================================================================== */
#tb-rev{table-layout:fixed}
#tb-rev th:nth-child(1){width:150px}
#tb-rev th:nth-child(2){width:21%}
#tb-rev th:nth-child(3){width:25%}
#tb-rev th:nth-child(5){width:236px}
@media(max-width:1400px){#tb-rev th:nth-child(1){width:132px}#tb-rev th:nth-child(5){width:216px}}
#tb-rev td{color:var(--t2);word-wrap:break-word;overflow-wrap:anywhere}
#tb-rev td .fname,.tb.perm td .fname{color:var(--t1);font-weight:var(--w-m)}
#tb-rev td .fkind,.tb.perm td .fkind{display:block;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);margin-top:2px}
#tb-rev tr[data-status="contradictory"] td:first-child{box-shadow:inset 3px 0 0 var(--warn-dot)}
.cur{display:flex;flex-direction:column;gap:4px}
.cur .val{color:var(--t2)}
.cur .val.kept{color:var(--t1)}
.appr{display:inline-flex;align-items:center;gap:4px;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--ok)}
.appr .ico-s{width:12px;height:12px}
.appr.no{color:var(--t3)}
.prop{display:flex;flex-direction:column;gap:6px}
.prop .val{color:var(--t1)}
.prop .val.strike{color:var(--t3);text-decoration:line-through}
.prop .lab{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.prop .lab b{color:var(--t2);font-weight:var(--w-m)}
.prop .ch{align-self:flex-start}
.ev{display:flex;flex-direction:column;gap:6px}
.ev .evb{display:block;width:100%;text-align:left;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface-2);
  padding:6px 8px;color:var(--t2);font-size:var(--fs-xs);line-height:var(--lh-xs)}
.ev .evb:hover{border-color:var(--line4);background:var(--surface);color:var(--t1)}
.ev .evb q{quotes:'\201C' '\201D';color:var(--t1);font-size:var(--fs-sm);line-height:var(--lh-sm);display:block;margin-bottom:2px}
.ev .evb .evm{display:flex;gap:8px;align-items:baseline;flex-wrap:nowrap}
.ev .evb .evm time{font-family:var(--mono);font-size:var(--fs-xs);color:var(--t2);white-space:nowrap;flex:none}
.ev .evb .evm span{color:var(--t3);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ev .note{margin-top:2px}
.dec{display:flex;flex-direction:column;gap:6px;align-items:flex-start}
.dec .acts{gap:4px}
.dec .b-sm{padding:0 9px}
.dec .dres{display:flex;flex-direction:column;gap:4px;align-items:flex-start;width:100%}
.dec .dres .mini{color:var(--t2)}
.dec .edit{display:flex;flex-direction:column;gap:6px;width:100%}
.dec .edit textarea,.dec .edit input{width:100%}
.dec .b-xs{height:24px}
.dec .chg{height:24px;padding:0 6px;font-size:var(--fs-xs);color:var(--t3)}
.dec .chg:hover{color:var(--t1)}
.rev-foot{display:flex;align-items:center;gap:12px;padding:12px 16px;border-top:1px solid var(--line2)}
.rev-foot .cnt{color:var(--t3);font-size:var(--fs-sm)}
.rev-foot .cnt b{color:var(--t1)}
.rev-foot .b-p{height:34px}
.notes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
@media(max-width:1180px){.notes{grid-template-columns:1fr}}
.notes>.pn{margin-top:0}
.notes ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px}
.notes li{color:var(--t2)}
.notes li .q{display:block;color:var(--t1)}
.notes li .q::before{content:'\201C'}
.notes li .q::after{content:'\201D'}
.notes li .why{display:block;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.notes .nada{color:var(--t3)}
.hdr-facts{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;margin-top:6px;font-size:var(--fs-sm);color:var(--t3)}
.hdr-facts b{color:var(--t1);font-weight:var(--w-m)}
.hdr-facts .kf{display:inline-flex;align-items:center;gap:6px}

/* a identidade da oportunidade (o banner da ficha) */
.fid{background-color:var(--dk);background-image:var(--glow);border:1px solid var(--dk-line);border-radius:var(--r-card);color:var(--dk-t1);
  padding:18px 20px 16px;margin-bottom:16px}
.fid-top{display:flex;align-items:center;gap:12px}
.fid h1{color:var(--dk-t1)}
.fid .fid-sub{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--dk-t3);margin-top:2px}
.fid .chips{display:flex;gap:6px;margin-top:10px}
.fid .chips .ch{background:var(--dk-fill);color:var(--dk-t1);border-color:transparent}
.fid .facts{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;margin-top:18px;padding:14px 0 13px;border:1px solid var(--dk-line);border-radius:var(--r-card)}
.fid .facts .f{padding:0 16px;border-left:1px solid var(--dk-line);min-width:0}
.fid .facts .f:first-child{border-left:0}
.fid .facts .l{font-size:var(--fs-xxs);line-height:var(--lh-xxs);font-weight:var(--w-m);color:var(--dk-t3);margin-bottom:6px;letter-spacing:.0025em}
.fid .facts .v{font-size:var(--fs-h2);line-height:var(--lh-h2);font-weight:var(--w-m);letter-spacing:-.0125em;color:var(--dk-t1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fid .facts .v.na{font-size:var(--fs-base);color:var(--dk-t3);font-weight:var(--w-r)}
.fid .facts .m{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--dk-t3);margin-top:4px}
.kv{display:grid;grid-template-columns:150px minmax(0,1fr);gap:0;margin:0}
.kv>div{display:contents}
.kv dt,.kv dd{padding:9px 16px;border-top:1px solid var(--line2);margin:0}
.kv>div:first-child dt,.kv>div:first-child dd{border-top:0}
.kv dt{color:var(--t3);font-size:var(--fs-sm)}
.kv dd{color:var(--t1)}
.kv dt .sub,.kv dd .sub{display:block;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);margin-top:2px}

/* ---- transcricao (gaveta) ---- */
.drw{margin:var(--gap) var(--gap) var(--gap) auto;width:560px;max-width:calc(100vw - 2*var(--gap));height:calc(100% - 2*var(--gap));max-height:calc(100% - 2*var(--gap));
  background:var(--surface);border:1px solid var(--line);border-radius:var(--r-sheet);box-shadow:var(--float);padding:0;color:var(--t1)}
.drw::backdrop{background:var(--scrim)}
.drw-in{display:flex;flex-direction:column;height:100%;border-radius:var(--r-sheet);overflow:hidden}
.drw-h{display:flex;align-items:flex-start;gap:10px;padding:16px 24px 14px;border-bottom:1px solid var(--line2)}
.drw-h h2{font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m)}
.drw-h .mini{margin-top:2px}
.drw-b{flex:1;min-height:0;overflow-y:auto;padding:12px 24px 24px}
.dlg-x{width:28px;height:28px;border:0;border-radius:var(--r);color:var(--t3);background:transparent;display:inline-grid;place-items:center;flex:none;margin-left:auto}
.dlg-x:hover{background:var(--fill-1);color:var(--t1)}
.tl{display:grid;grid-template-columns:64px minmax(0,1fr);gap:0 12px;padding:8px 8px;border-radius:var(--r);font-size:var(--fs-p);line-height:var(--lh-p);color:var(--t2)}
.tl time{font-family:var(--mono);font-size:var(--fs-xs);line-height:var(--lh-p);color:var(--t3)}
.tl .who{display:block;font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1)}
.tl.hl{background:var(--info-bg);color:var(--t1)}
.tl.hl time{color:var(--info)}
.tl.sys{color:var(--t3);font-size:var(--fs-sm);font-style:normal}
.tl-mark{display:inline-block;margin-left:8px;font-size:var(--fs-xxs);line-height:14px;padding:0 5px;border-radius:var(--r-chip);background:var(--info);color:#fff;font-weight:var(--w-m);vertical-align:2px}

/* ---- dialogo e recibo ---- */
.dlg{border:0;border-radius:var(--r-sheet);box-shadow:var(--float);background:var(--surface);padding:0;width:440px;max-width:calc(100vw - 32px);color:var(--t1)}
.dlg::backdrop{background:var(--scrim-2)}
.dlg-h{display:flex;align-items:center;gap:8px;padding:16px 20px 12px;border-bottom:1px solid var(--line2)}
.dlg-h h2{font-size:var(--fs-base);line-height:var(--lh-base)}
.dlg-b{padding:14px 20px 18px;color:var(--t2)}
.dlg-b p+p{margin-top:8px}
.dlg-f{display:flex;gap:8px;justify-content:flex-end;padding:0 20px 18px}
.toast{position:fixed;left:calc(var(--nav-w) + (100vw - var(--nav-w) - var(--gap)) / 2);bottom:24px;transform:translateX(-50%);z-index:80;
  display:flex;align-items:center;gap:10px;min-height:40px;max-width:min(680px,80vw);padding:6px 6px 6px 10px;
  background:var(--surface);color:var(--t1);border:0;border-radius:var(--r-pill);box-shadow:var(--float)}
.toast .tk{width:20px;height:20px;border-radius:var(--r-pill);background:var(--ok-bg);color:var(--ok);display:grid;place-items:center;flex:none}
.toast .tk.bad{background:var(--bad-bg);color:var(--bad)}
.toast .tk.neu{background:var(--neutral-bg);color:var(--neutral)}
.toast .tk .ico-s{width:12px;height:12px}
.toast .tx{font-size:var(--fs-sm);font-weight:var(--w-m);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toast .tu{border:0;background:transparent;color:var(--t1);font-weight:var(--w-m);font-size:var(--fs-sm);text-decoration:underline;text-underline-offset:2px;text-decoration-color:var(--line4);padding:0 4px}
.toast .tu:hover{text-decoration-color:var(--t1)}
.toast .tx-x{width:28px;height:28px;border:0;border-radius:var(--r-pill);background:transparent;color:var(--t3);display:grid;place-items:center}
.toast .tx-x:hover{background:var(--fill-1);color:var(--t1)}

/* ---- zona de soltar transcricao ---- */
.drop{margin:14px 16px;border:1px dashed var(--line4);border-radius:var(--r-card);padding:18px 16px;display:flex;align-items:center;gap:14px;color:var(--t2);background:transparent}
.drop.over{background:var(--fill-1);border-color:var(--t1)}
.drop .ico-b{width:20px;height:20px;color:var(--t3);flex:none}
.drop .drop-t{flex:1;min-width:0}
.drop .drop-t b{color:var(--t1)}
.drop .drop-t .mini{margin-top:2px}
.drop input[type=file]{display:none}
.dropform{margin:0 16px 16px;padding:14px 16px;border:1px solid var(--line2);border-radius:var(--r-card);background:var(--surface-2);display:flex;flex-direction:column;gap:12px}
.dropform .frow .fld:first-child{grid-column:span 2}
.dropform .acts{justify-content:flex-end}
.dropform .warn{display:flex;gap:8px;align-items:flex-start;color:var(--warn);font-size:var(--fs-xs);line-height:var(--lh-xs)}

/* ---- eval ---- */
.ev-res{font-weight:var(--w-m)}
.ev-res.pass{color:var(--ok)}.ev-res.fail{color:var(--bad)}
.tb td ul.issues{margin:0;padding-left:16px;color:var(--t2);font-size:var(--fs-xs);line-height:var(--lh-xs)}
.checks{display:flex;flex-direction:column;gap:8px;padding:14px 16px}
.checks label{display:flex;gap:10px;align-items:flex-start;color:var(--t2);cursor:pointer}
.checks input{margin:2px 0 0;width:14px;height:14px;accent-color:var(--act)}
.checks .case{font-weight:var(--w-m);color:var(--t1);margin-top:6px}
.checks .case:first-child{margin-top:0}

/* ---- audit ---- */
.tb td code,.ev-code{font-family:var(--mono);font-size:var(--fs-xs);color:var(--t2);white-space:nowrap}
#tb-audit td:nth-child(1),#audit-detail td{white-space:normal}
#audit-detail table td:nth-child(2) code{white-space:nowrap}
.tb tr.blocked td:first-child{box-shadow:inset 3px 0 0 var(--bad-dot)}
.outc-ok{color:var(--ok)}.outc-blocked{color:var(--bad)}.outc-failed{color:var(--bad)}

/* ---- documento (politicas em Markdown) ---- */
.doc{padding:18px 20px 22px;max-width:760px;color:var(--t2);font-size:var(--fs-p);line-height:var(--lh-p)}
.doc h1{font-size:var(--fs-lg);line-height:var(--lh-lg);color:var(--t1);margin:0 0 12px}
.doc h2{font-size:var(--fs-base);line-height:var(--lh-base);color:var(--t1);margin:22px 0 8px}
.doc h3{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t1);margin:16px 0 6px}
.doc p{margin:0 0 10px}
.doc ul,.doc ol{margin:0 0 10px;padding-left:22px}
.doc li{margin:2px 0}
.doc code{font-family:var(--mono);font-size:var(--fs-sm);color:var(--t1);background:var(--fill-1);padding:1px 4px;border-radius:3px}
.doc table{border-collapse:collapse;width:100%;font-size:var(--fs-sm);line-height:var(--lh-sm);margin:8px 0 14px}
.doc th{text-align:left;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t3);padding:6px 8px;border-bottom:1px solid var(--line)}
.doc td{padding:8px 8px;border-top:1px solid var(--line2);vertical-align:top}
.doc strong{color:var(--t1)}
.src-list{list-style:none;margin:0;padding:0}
.src-list li{display:grid;grid-template-columns:170px minmax(0,1fr);gap:12px;padding:10px 16px;border-top:1px solid var(--line2);color:var(--t2)}
.src-list li:first-child{border-top:0}
.src-list li b{color:var(--t1)}
.src-list li .mini{margin-top:2px}

/* ---- settings ---- */
.set-row{display:grid;grid-template-columns:170px minmax(0,1fr);gap:12px;padding:12px 16px;border-top:1px solid var(--line2);align-items:start}
.set-row:first-child{border-top:0}
.set-row .sl{color:var(--t3);padding-top:4px}
.set-row .sv{display:flex;flex-direction:column;gap:6px;color:var(--t2)}
.set-row .sv .mini{color:var(--t3)}
.radio{display:flex;flex-direction:column;gap:2px}
.radio .seg{justify-content:flex-start;height:auto;min-height:30px;padding:5px 10px;flex-direction:column;align-items:flex-start;gap:0;text-align:left}
.radio .seg .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-r);color:var(--t3)}
.radio .seg[aria-checked="true"] .sub{color:var(--t2)}

/* ===================================================================== */
/* v4: Granola, revisao agrupada, funil por etapa, gavetas, clientes,      */
/* atividade, agente                                                       */
/* ===================================================================== */
.view .ph+.pn#gr-card{margin-top:0}
#gr-card+.strip{margin-top:16px}
.gr-b{display:flex;flex-direction:column;gap:6px}
.gr-row{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--t3)}
.gr-row b{color:var(--t1);font-weight:var(--w-m)}
#gr-state{display:inline-flex;align-items:center;gap:8px}
.warnline{display:flex;gap:6px;align-items:center;margin-top:8px;color:var(--warn);font-size:var(--fs-xs);line-height:var(--lh-xs)}
.warnline .ico-s{width:13px;height:13px}
.lnk{border:0;background:transparent;padding:0;color:var(--t2);font-size:var(--fs-xs);line-height:var(--lh-xs);text-decoration:underline;text-decoration-color:var(--line4);text-underline-offset:2px;text-align:left}
.lnk:hover{color:var(--t1);text-decoration-color:var(--t1)}

/* revisao: um bloco por grupo do esquema */
#tb-rev tbody.rg tr.grp th{padding:0;height:auto;background:var(--surface-2);border-top:1px solid var(--line);border-bottom:1px solid var(--line2);white-space:normal}
#tb-rev tbody.rg:first-of-type tr.grp th{border-top:0}
.grp-in{display:flex;align-items:center;gap:10px;padding:8px 16px}
.grp-t{font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1)}
.grp-n{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);font-weight:var(--w-r)}
#tb-rev tr.qsum td{height:auto;padding:6px 16px 8px;border-top:1px solid var(--line2)}
#tb-rev tbody.rg tr.grp+tr td{border-top:0}
.chkset{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 8px;padding:4px 0}
.chkset label{display:flex;gap:6px;align-items:center;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.chkset input{margin:0;width:14px;height:14px;accent-color:var(--act)}
.dec .edit .fld-l i{font-style:normal;color:var(--t3);font-weight:var(--w-r)}
.dec .edit select.inp{height:32px}

/* oportunidades: barra de chips + secoes empilhadas por etapa (o padrao do Forecast) */
.fc .fc-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px;border-bottom:1px solid var(--line2)}
.srch{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 8px;border:1px solid var(--line3);border-radius:var(--r);background:var(--surface);color:var(--t3)}
.srch input{border:0;outline:0;background:transparent;font-size:var(--fs-sm);width:180px;color:var(--t1);padding:0}
#tb-meetings td.act-c{width:1%;white-space:nowrap}
#tb-meetings td.act-c .acts{flex-wrap:nowrap}
.srch:focus-within{border-color:var(--focus-line)}
.fsel select{height:28px;border:1px solid var(--line3);border-radius:var(--r);background:var(--surface);padding:0 8px;font-size:var(--fs-sm);color:var(--t1)}
.fg[data-fora="1"]{display:none}
.fg-h{display:flex;align-items:center;gap:8px;padding:11px 16px;background:var(--surface-2);border-top:1px solid var(--line2);font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1)}
#opps-groups .fg:first-child .fg-h{border-top:0}
.fg-h .mk{width:8px;height:8px;border-radius:var(--r-mark);flex:none;background:var(--t1)}
.fg-h .mk-0{background:transparent;border:1.5px solid var(--line4)}
.fg-h .mk-1{background:var(--line4)}
.fg-h .mk-2{background:var(--t3)}
.fg-h .mk-3{background:var(--t2)}
.fg-h .mk-4{background:var(--t1)}
.fg-h .mk-5{background:var(--ink)}
.fg-h .fg-sum{margin-left:auto;font-weight:var(--w-r);color:var(--t2)}
.fg-l{list-style:none;margin:0;padding:0}
.fr{display:grid;grid-template-columns:minmax(0,2.3fr) 124px 132px minmax(0,1.9fr) 150px 186px;gap:0 14px;align-items:center;min-height:56px;padding:8px 16px;border-top:1px solid var(--line2);color:var(--t2)}
.fr:hover{background:var(--fill-0)}
.fr-c{min-width:0;display:flex;flex-direction:column;gap:2px}
.fr-c .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.fr-c b{color:var(--t1);font-weight:var(--w-m)}
.fr-num b{font-size:var(--fs-sm)}
.fr-ns{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fr-c .ch{align-self:flex-start}
.fr-act{flex-direction:row;justify-content:flex-end;align-items:center;gap:6px}
.fg-empty{margin:0;padding:12px 16px;color:var(--t3);font-size:var(--fs-sm);border-top:1px solid var(--line2)}
@media(max-width:1400px){.fr{grid-template-columns:minmax(0,2.2fr) 112px 120px minmax(0,1.7fr) 132px 178px;gap:0 10px}}

/* gavetas de registro (oportunidade e cliente) */
.drw-rec{width:640px}
.drw-id{min-width:0}
.drw-id .ttl{align-items:center}
.drw-id .ttl h2{font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m)}
.drw-id .ttl .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.drw-rec .drw-b{padding:16px 24px 28px}
.drw-rec .fid{padding:0;margin-bottom:14px}
.drw-rec .fid .facts{margin-top:0;border:0}
.dsec{margin-top:16px;border:1px solid var(--line-card);border-radius:var(--r-card);background:var(--surface)}
.dsec h3{display:flex;align-items:baseline;gap:8px;padding:10px 16px;border-bottom:1px solid var(--line2);font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1)}
.dsec h3 .mini{font-weight:var(--w-r)}
.dsec .kv{grid-template-columns:170px minmax(0,1fr)}
.dsec .tb td,.dsec .tb th{height:auto}
.mlist{list-style:none;margin:0;padding:0}
.mlist li{display:flex;align-items:center;gap:10px;justify-content:space-between;padding:9px 16px;border-top:1px solid var(--line2)}
.mlist li:first-child{border-top:0}
.mlist li>span{display:flex;flex-direction:column;min-width:0}
.mlist li b{color:var(--t1);font-weight:var(--w-m)}
.mlist .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.pad{padding:10px 16px;margin:0;color:var(--t3)}
.pend{display:flex;align-items:center;gap:10px;margin-top:0;padding:10px 14px;border:1px solid var(--line3);border-radius:var(--r-card);background:var(--surface-2);color:var(--t2)}
.pend b{color:var(--t1)}
.pend .b{margin-left:auto}

/* clientes: um bloco por cliente, com as suas oportunidades embaixo */
#tb-clients tbody.cg tr.cg-h td{background:var(--surface-2);border-top:1px solid var(--line);padding:8px 16px;height:auto}
#tb-clients tbody.cg:first-of-type tr.cg-h td{border-top:0}
.cg-in{display:flex;align-items:center;gap:10px;min-width:0}
.cg-in b{color:var(--t1);font-weight:var(--w-m);white-space:nowrap}
.cg-in .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#tb-clients tbody.cg tr.cg-h+tr td{border-top:0}

/* atividade: uma linha por atualizacao, em frase */
.feed{list-style:none;margin:0;padding:0}
.fi{display:grid;grid-template-columns:170px minmax(0,1fr) auto auto;gap:4px 14px;align-items:center;padding:10px 16px;border-top:1px solid var(--line2)}
.fi:first-child{border-top:0}
.fi-t{font-family:var(--mono);font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);white-space:nowrap}
.fi-m{min-width:0;color:var(--t2)}
.fi-m b{color:var(--t1);font-weight:var(--w-m)}
.fi-m .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);margin-top:1px}
.fi-a{justify-content:flex-end}
.fi-x{grid-column:1/-1;margin-top:8px;border:1px solid var(--line2);border-radius:var(--r-card);overflow:hidden}
.fi-x .tb td,.fi-x .tb th{height:auto}
.fi-none{padding:14px 16px}

/* agente */
.subnav{display:flex;gap:2px;margin:-4px 0 16px}
.subnav .seg[aria-selected="true"]{background:var(--fill-2);color:var(--t1)}
.purpose{color:var(--t2);font-size:var(--fs-p);line-height:var(--lh-p);max-width:900px}
.purpose b{color:var(--t1)}
.checks .chk{display:flex;gap:10px;align-items:flex-start;color:var(--t2)}
#tb-eval td:nth-child(2){max-width:520px}

/* ===================================================================== */
/* v5 (28/10): Explore, Meetings que aceita qualquer conversa, Clients em */
/* cartoes, Settings com permissoes por campo, MEDDPICC                   */
/* ===================================================================== */
/* lateral: o grupo Chat (Novo chat + as conversas recentes) */
.nav-cs{display:flex;flex-direction:column;gap:1px;flex:none}
.nav-c .lb,.nav-novo .lb{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.nav>.nav-i:first-child{margin-top:4px}

/* a barra: o estado do agente e um botao que abre Settings > Agent */
button.job{cursor:pointer;font:inherit;text-align:left}
button.job:hover{border-color:var(--line4)}
.job[data-on="1"] .job-ic{color:var(--ok-dot)}

/* Explore: a conversa numa coluna de leitura (o padrao do SalesOps v5) */
.view[data-view="explore"]{padding-top:0}
.ex{max-width:760px;margin:0 auto;padding:12vh 0 48px}
.ex.ex-on{padding-top:28px}
.ex-t{margin:0 0 20px;color:var(--t1)}
.ex.ex-on .ex-t{font-size:var(--fs-lg);line-height:var(--lh-lg)}
.cmp{display:block;margin:0;background:var(--surface);border:1px solid var(--line3);border-radius:var(--r-sheet);padding:16px 18px}
.cmp:focus-within{border-color:var(--line4)}
.cmp textarea{display:block;width:100%;margin:0;padding:0;border:0;outline:0;resize:none;background:transparent;
  font-family:var(--font);font-size:var(--fs-p);line-height:var(--lh-p);font-weight:var(--w-r);color:var(--t1)}
.cmp textarea::placeholder{color:var(--t3)}
.cmp-b{display:flex;align-items:center;gap:4px;margin-top:12px;min-width:0}
.cmp-b .grow{flex:1}
.cmp-ctx{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 8px;border-radius:var(--r-chip);background:var(--fill-1);
  color:var(--t2);font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m)}
.cmp-ctx .ico-s{width:14px;height:14px}
.cmp-env{width:28px;height:28px;flex:none;display:inline-grid;place-items:center;padding:0;border:0;border-radius:var(--r);
  background:var(--fill-2);color:var(--t3);cursor:pointer}
.cmp-env .ico-b{width:16px;height:16px;color:inherit}
.cmp:has(textarea:not(:placeholder-shown)) .cmp-env{background:var(--act);color:var(--on-act)}
.ex-sg{margin-top:32px}
.ex-sg h2{margin:0 0 6px;padding:0 19px;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);letter-spacing:.005em;color:var(--t3)}
.sg-l{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.sg{display:flex;align-items:center;gap:10px;width:100%;margin:0;padding:8px 19px;border:0;border-radius:var(--r-field);background:transparent;
  color:var(--t1);text-align:left;cursor:pointer;font-family:var(--font)}
.sg:hover{background:var(--fill-1)}
.sg-i{display:inline-grid;place-items:center;width:16px;height:16px;flex:none;color:var(--t3)}
.sg-t{flex:1 1 auto;min-width:0;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t1)}
.sg-k{flex:none;margin-left:auto;padding-left:12px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t3);white-space:nowrap}
.cv-l{list-style:none;margin:0 0 24px;padding:0;display:flex;flex-direction:column;gap:24px}
.msg{margin:0;font-size:var(--fs-p);line-height:var(--lh-p);color:var(--t1)}
.msg p{margin:0}
.msg.eu{align-self:flex-end;max-width:80%;padding:10px 14px;background:var(--surface);border:1px solid var(--line-card);border-radius:var(--r-card)}
.msg.nex{max-width:680px}
.msg.wait .msg-v{color:var(--t3)}
.msg-who{margin-bottom:6px;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t3)}
.msg-a{margin:10px 0 0;padding-left:22px;display:flex;flex-direction:column;gap:6px}
.msg-a>li::marker{color:var(--t3);font-size:var(--fs-sm)}
.msg-a .ref{margin-left:3px;font-size:var(--fs-xxs);color:var(--t3)}
.msg-ab{margin-top:12px!important;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.msg-ab b{font-weight:var(--w-m);color:var(--t1)}
.msg-f{margin:12px 0 0;padding:8px 0 0 18px;border-top:1px solid var(--line2);font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.msg-acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.msg-m{margin-top:8px;font-size:var(--fs-xxs);line-height:var(--lh-xxs);color:var(--t3)}
optgroup{font-weight:var(--w-m)}
.msg-sgh{margin-top:12px!important;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t3)}
.msg-sg{margin-top:4px}
.msg-sg .sg{padding:8px 10px;margin-left:-10px;width:calc(100% + 10px)}

/* Meetings: a faixa (duas contas), e o cartao de entrada logo abaixo */
#mt-strip{grid-auto-columns:1fr}
.mt-add .add-b{padding:16px;display:flex;flex-direction:column;gap:14px}
.add-opp{display:flex;flex-direction:column;gap:6px;max-width:560px}
.add-opp select.inp{max-width:560px}
.src-tabs{display:flex;gap:2px}
.src-tabs .seg[aria-selected="true"]{background:var(--fill-2);color:var(--t1)}
.src-tabs .seg .ico-s{width:14px;height:14px}
.mt-add .drop{margin:0}
.paste{display:flex;flex-direction:column;gap:8px}
.paste textarea.inp{min-height:180px;font-family:var(--font)}
.paste .acts{display:flex;align-items:center;gap:8px}
.paste .grow{flex:1}
.draft{border:1px solid var(--line3);border-radius:var(--r-card);background:var(--surface-2);padding:14px 16px;display:flex;flex-direction:column;gap:12px}
.dr-file{display:flex;gap:10px;align-items:flex-start;color:var(--t2)}
.dr-file b{color:var(--t1);font-weight:var(--w-m)}
.dr-file .mini{display:block;margin-top:2px}
.dr-att{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border-radius:var(--r-field);background:var(--surface);border:1px solid var(--line2)}
.dr-att>.ico-s{margin-top:2px;flex:none}
.dr-att>span{flex:1;min-width:0;color:var(--t2)}
.dr-att b{color:var(--t1);font-weight:var(--w-m)}
.dr-att .mini{display:block;margin-top:2px}
.dr-att.ok>.ico-s{color:var(--ok-dot)}
.dr-att.new>.ico-s{color:var(--info)}
.dr-att.bad>.ico-s{color:var(--bad-dot)}
.dr-att.warn>.ico-s{color:var(--warn-dot)}
.draft .frow{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}
.draft .fld-w{min-width:0}
.fld-v{display:flex;align-items:center;gap:8px;min-height:36px;color:var(--t1)}
.draft .acts{display:flex;gap:8px}
.lnk{border:0;background:transparent;padding:0;color:var(--t2);font:inherit;font-size:var(--fs-sm);cursor:pointer;border-bottom:1px solid var(--line3)}
.lnk:hover{color:var(--t1);border-bottom-color:var(--t1)}

/* Review: o MEDDPICC depois desta conversa, e o cartao da oportunidade nova */
.rev-mdp{display:flex;align-items:center;flex-wrap:wrap;gap:6px 12px;margin-top:10px}
.newopp .no-b{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px 16px;padding:14px 16px;align-items:end}
.newopp .no-dec{display:flex;align-items:center;justify-content:flex-end;min-height:36px}
#tb-rev tr[data-auto="1"] td{background:var(--surface-2)}

/* MEDDPICC: oito letras, cheias quando o CRM tem o elemento */
.mdp{display:inline-flex;align-items:center;gap:2px;vertical-align:middle}
.mdp-c{display:inline-grid;place-items:center;width:14px;height:16px;border-radius:3px;border:1px solid var(--line3);
  font-size:10px;line-height:1;font-weight:var(--w-m);color:var(--t3);background:var(--surface)}
.mdp-c.on{background:var(--act);border-color:var(--act);color:var(--on-act)}
.mdp-c.add{background:var(--info-bg);border-color:var(--info);color:var(--info)}
.mdp-n{margin-left:6px;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);font-variant-numeric:tabular-nums}
.mdp-lg .mdp-c{width:20px;height:22px;font-size:12px;border-radius:4px}
.mdp-l{display:inline-grid;place-items:center;width:16px;height:16px;margin-right:6px;border-radius:3px;background:var(--fill-2);
  font-size:10px;line-height:1;font-weight:var(--w-m);color:var(--t2);vertical-align:1px}
.dsec-mdp .mdp-row{padding:4px 16px 8px}
.dsec-mdp .ask{margin:0 16px 10px;padding-left:18px;color:var(--t2);font-size:var(--fs-sm);line-height:var(--lh-sm)}
.dsec-mdp .ask b{color:var(--t1);font-weight:var(--w-m)}
.pad{padding:0 16px 12px}

/* Clients: um cartao por cliente, separados (o padrao da Carteira do SalesOps) */
.cl-bar{display:flex;align-items:center;gap:10px;margin:0 0 12px}
.cl-bar .grow{flex:1}
.cl-bar .srch{width:360px;max-width:100%}
.cl-list{display:flex;flex-direction:column;gap:12px}
.cl-card{background:var(--surface);border:1px solid var(--line-card);border-radius:var(--r-card)}
.cl-h{display:flex;align-items:center;gap:12px;padding:14px 16px}
.cl-id{flex:1;min-width:0}
.cl-id h2{font-size:var(--fs-lg);line-height:var(--lh-lg);font-weight:var(--w-m);color:var(--t1)}
.cl-f{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.tag{display:inline-flex;align-items:center;height:20px;padding:0 6px;border-radius:var(--r-chip);border:1px solid var(--line3);
  font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2);background:var(--surface);max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cl-r{display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex:none;text-align:right}
.cl-sum{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.cl-sum b{color:var(--t1);font-weight:var(--w-m)}
.cl-r .sub{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.cl-ops{list-style:none;margin:0;padding:0;border-top:1px solid var(--line2)}
.cl-op{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1.3fr) minmax(0,1fr) minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.3fr) auto;
  gap:12px;align-items:center;padding:10px 16px;border-top:1px solid var(--line2);font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.cl-op:first-child{border-top:0}
.cl-op:hover{background:var(--fill-0)}
.cl-op b{color:var(--t1);font-weight:var(--w-m)}
.cl-op .sub{display:block;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.cl-op .num{text-align:right}
.cl-op .nw{white-space:nowrap}

/* Settings: abas; permissoes por campo no padrao Always allow / Needs approval / Never */
.subnav{flex-wrap:wrap}
.perm-legend{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-bottom:1px solid var(--line2)}
.perm-legend .pl{display:flex;flex-direction:column;gap:2px;padding:12px 16px;border-left:1px solid var(--line2);color:var(--t2);font-size:var(--fs-sm);line-height:var(--lh-sm)}
.perm-legend .pl:first-child{border-left:0}
.perm-legend .pl b{color:var(--t1);font-weight:var(--w-m)}
.perm-legend .pl-auto b::before,.perm-legend .pl-ask b::before,.perm-legend .pl-off b::before{content:"";display:inline-block;width:7px;height:7px;border-radius:var(--r-pill);margin-right:7px;vertical-align:1px}
.perm-legend .pl-auto b::before{background:var(--ok-dot)}
.perm-legend .pl-ask b::before{background:var(--neutral)}
.perm-legend .pl-off b::before{background:transparent;border:1px solid var(--line4)}
.tb.perm td.perm-d{color:var(--t3);font-size:var(--fs-xs);line-height:var(--lh-xs);max-width:460px}
.tb.perm td:last-child{width:1%;white-space:nowrap}
.grp-set{display:inline-flex;align-items:center;gap:8px;font-size:var(--fs-xs);color:var(--t3);font-weight:var(--w-r)}
.pseg{display:inline-flex;gap:0;padding:2px;border-radius:var(--r-field);background:var(--fill-1)}
.ps{height:26px;padding:0 10px;border:0;border-radius:var(--r);background:transparent;color:var(--t2);font:inherit;font-size:var(--fs-xs);
  line-height:var(--lh-xs);font-weight:var(--w-m);cursor:pointer;white-space:nowrap}
.ps:hover{color:var(--t1)}
.ps[aria-checked="true"]{background:var(--surface);color:var(--t1);box-shadow:0 0 0 1px var(--line3)}
.ps-auto[aria-checked="true"]{color:var(--ok)}
.ps-off[aria-checked="true"]{color:var(--t2)}
.rules{list-style:none;margin:0;padding:6px 0}
.rules li{display:flex;gap:10px;align-items:flex-start;padding:8px 16px;color:var(--t2)}
.rules li .ico-s{margin-top:3px;color:var(--ok-dot);flex:none}
.radio-row{flex-direction:row;gap:2px}
.radio-row .seg{min-height:28px}
.src-l{display:flex;flex-direction:column}
.src-i{display:grid;grid-template-columns:28px minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px 16px;border-top:1px solid var(--line2);color:var(--t2)}
.src-i:first-child{border-top:0}
.src-i b{color:var(--t1);font-weight:var(--w-m)}
.src-i .mini{display:block;margin-top:2px}
.src-i.soft b{color:var(--t2)}
.src-k{display:grid;place-items:center;width:28px;height:28px;border-radius:var(--r);background:var(--fill-1);color:var(--t2)}
.src-k .ico-b{width:16px;height:16px}
.set-row .sv code{font-family:var(--mono);color:var(--t2);font-size:var(--fs-xs)}

@media(max-width:1400px){
  .cl-op{grid-template-columns:minmax(0,2fr) minmax(0,1.3fr) minmax(0,1fr) minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.2fr) auto;gap:10px}
  .perm-legend .pl{padding:10px 12px}
}
"""
