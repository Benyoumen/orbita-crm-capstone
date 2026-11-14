# -*- coding: utf-8 -*-
"""Folha de estilo do mockup Orbita CRM: a pele do SalesOps v5 ("folha sobre a
mesa") escrita do zero para as superficies desta peca. Stdlib pura. A camada v6
(31/10, no fim) clareia a folha, enche a tinta do texto lido e traz a revisao em
cartoes por grupo, o leitor da reuniao, o Explore como chat e a aba Evals.

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
  --mesa:#EDEDEE; --folha:#FAFAFA; --surface:#FFFFFF; --surface-2:#F7F7F8;
  --glass:rgba(250,250,250,.88);
  --ink:#0A0A0A;
  --t1:rgba(10,10,10,.90); --t2:rgba(10,10,10,.72); --t3:rgba(10,10,10,.60); --t4:rgba(10,10,10,.42);
  --line:rgba(10,10,10,.08); --line2:rgba(10,10,10,.06); --line3:rgba(10,10,10,.14); --line4:rgba(10,10,10,.22);
  --line-card:rgba(10,10,10,.10);
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
/* a tabela de revisao: campo · o que muda · evidencia · decisao (v6)     */
/* ===================================================================== */
#tb-rev td{color:var(--t2);word-wrap:break-word;overflow-wrap:anywhere}
#tb-rev td .fname,.tb.perm td .fname{color:var(--t1);font-weight:var(--w-m)}
#tb-rev td .fkind,.tb.perm td .fkind{display:block;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3);margin-top:2px}
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
/* a avaliacao da vendedora (polegar para cima ou para baixo): dois botoes de icone, sem cor de estado;
   o motivo so abre no polegar para baixo, e pode ser pulado */
.fb{display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-top:6px;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t3)}
.fb-q{margin-right:4px}
.fb-b{width:28px;height:28px;display:inline-grid;place-items:center;padding:0;border:0;border-radius:var(--r);background:transparent;color:var(--t3)}
.fb-b:hover{background:var(--fill-1);color:var(--t1)}
.fb-b[aria-pressed="true"]{background:var(--fill-2);color:var(--t1)}
.fb-b .ico-s{width:16px;height:16px;color:inherit}
.fb-s{margin-left:6px;color:var(--t2)}
.fb-f{flex-basis:100%;display:flex;flex-direction:column;align-items:flex-start;gap:10px;margin-top:6px;padding:12px 14px;border:1px solid var(--line2);border-radius:var(--r-card);background:var(--surface)}
.fb-l{font-size:var(--fs-sm);line-height:var(--lh-sm);font-weight:var(--w-m);color:var(--t1)}
.fb-rs{display:flex;flex-wrap:wrap;gap:6px 16px}
.fb-r{display:inline-flex;align-items:center;gap:6px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t1);cursor:pointer}
.fb-f .inp{width:100%;max-width:520px}
.rev-fb{padding:6px 16px 10px;border-top:1px solid var(--line2)}
.rev-fb .fb{margin-top:0}
.fb-sum{display:flex;flex-wrap:wrap;gap:6px 24px;padding:10px 16px;border-top:1px solid var(--line2);color:var(--t2)}
.fb-sum b{color:var(--t1)}
#tb-fb td:nth-child(2),#tb-fb td:nth-child(4){max-width:340px}
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

/* ===================================================================== */
/* v6 (31/10): leitura confortavel. Registros que abrem pelo nome, a       */
/* revisao em cartoes por grupo com a barra de decisao a vista, o leitor   */
/* da reuniao com busca, o Explore como um app de chat e a aba Evals.      */
/* Nada sublinhado: o nome de um registro e um botao com fundo no hover.   */
/* ===================================================================== */
.rec{border:0;background:transparent;padding:0;margin:0;font:inherit;color:var(--t1);font-weight:var(--w-m);text-align:left;cursor:pointer;border-radius:3px}
.rec:hover{background:var(--fill-2);box-shadow:0 0 0 3px var(--fill-2)}
.rec-b{font-size:var(--fs-base);line-height:var(--lh-base)}
.rec-h,.rec-h2{font-size:inherit;line-height:inherit;font-weight:inherit;letter-spacing:inherit}
.rowh{cursor:pointer}
.b.go{width:28px;padding:0;color:var(--t3)}
.rowh:hover .b.go,.b.go:hover{background:var(--fill-2);color:var(--t1)}
.flip{display:inline-flex;transform:scaleX(-1)}
.lk{border-bottom:0;font-weight:var(--w-m);color:var(--t1);border-radius:3px}
.lk:hover{background:var(--fill-2);box-shadow:0 0 0 3px var(--fill-2)}
.lnk{border:0;background:transparent;padding:2px 6px;margin:-2px -6px;border-radius:var(--r);color:var(--t1);font:inherit;font-size:var(--fs-sm);font-weight:var(--w-m);text-decoration:none;cursor:pointer}
.lnk:hover{background:var(--fill-1);color:var(--t1)}
mark{background:var(--warn-bg);color:var(--ink);border-radius:2px;padding:0 1px}

/* menos cinza: o texto que se le fica em tinta cheia; o cinza so no rotulo */
.tb td{color:var(--t1)}
.tb td .sub,.fr-c .sub,.cl-op .sub,.cl-r .sub,.mlist .sub,.kv dt .sub,.kv dd .sub,.ttl .sub,.drw-id .ttl .sub{color:var(--t2)}
.tb th{color:var(--t2)}
.kv dt{color:var(--t2)}
.fr,.cl-op{color:var(--t1)}
.ph .ph-c{color:var(--t2)}
.pn-h .pn-n,.pn-h .pn-d,.pn-f,.note,.mini{color:var(--t2)}
.nav-g{color:var(--t2)}

/* lateral: os chats recentes alinhados ao texto dos itens, sem icone repetido */
.nav-c{padding-left:34px}
.nav-c .lb{color:var(--t2)}
.nav-c.on .lb,.nav-c:hover .lb{color:var(--t1)}

/* ---- Review ---- */
.ph-rev{margin-bottom:16px}
.crumbs{display:flex;align-items:center;gap:6px;margin-bottom:10px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.crumbs a{color:var(--t2);text-decoration:none;border-radius:3px}
.crumbs a:hover{color:var(--t1);background:var(--fill-2);box-shadow:0 0 0 3px var(--fill-2)}
.crumbs svg{width:14px;height:14px;color:var(--t3)}
.crumbs .rec{font-weight:var(--w-r);color:var(--t2)}
.crumbs .rec:hover{color:var(--t1)}
.h1-s{font-weight:var(--w-r);color:var(--t2)}
.hdr-facts{gap:8px 20px;margin-top:10px;color:var(--t2)}
.hdr-facts .k{color:var(--t2)}
.rev-mdp{margin-top:14px;padding:10px 14px;border:1px solid var(--line-card);border-radius:var(--r-card);background:var(--surface);gap:8px 16px}
.rev-mdp-t{flex:1;min-width:260px;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.rev-mdp-t b{color:var(--t1);font-weight:var(--w-m)}
/* a barra de decisao fica a vista enquanto a pagina rola */
.rv-bar{position:sticky;top:var(--hd-h);z-index:30;display:flex;align-items:center;gap:16px;margin:0 calc(-1 * var(--mn-x)) 16px;
  padding:10px var(--mn-x);background:var(--glass);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.rv-p{display:flex;align-items:center;flex-wrap:wrap;gap:6px 14px;min-width:0}
.rv-c{font-size:var(--fs-base);line-height:var(--lh-base);color:var(--t1)}
.rv-c b{font-weight:var(--w-m)}
.rv-m{display:block;width:160px;height:4px;border-radius:var(--r-pill);background:var(--fill-3);overflow:hidden}
.rv-m i{display:block;height:100%;background:var(--act);transform-origin:left center;transition:transform .2s var(--ease)}
.rv-l{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.rv-bar .b-p{height:36px;padding:0 16px}
.rv-st{display:inline-flex;align-items:center;gap:8px;color:var(--t1)}
.rv-st b{font-weight:var(--w-m)}
.rv-st .ico-b{color:var(--ok-dot)}
.view[data-view="review"] .newopp{margin:0 0 16px}
/* um cartao por grupo do esquema: as categorias nunca se misturam */
.rv{display:flex;flex-direction:column;gap:16px}
.rvt{table-layout:fixed}
.rvt col.k-f{width:200px}
.rvt col.k-e{width:31%}
.rvt col.k-d{width:236px}
.rv-cols{margin-bottom:-10px}
.rv-cols th{height:auto;padding:0 12px 2px;background:transparent;border:0;color:var(--t2)}
.rv-cols th:first-child{padding-left:17px}
.rvt thead.vh th{height:0;padding:0;border:0;font-size:0;line-height:0;overflow:hidden}
.rvg{background:var(--surface);border:1px solid var(--line-card);border-radius:var(--r-card);overflow:hidden}
.rvg-h{display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line)}
.rvg-i{display:inline-grid;place-items:center;width:32px;height:32px;flex:none;border-radius:var(--r-field);background:var(--fill-1);color:var(--t1)}
.pn-h .rvg-i{width:28px;height:28px}
.rvg-t{flex:1;min-width:0}
.rvg-t h2{font-size:var(--fs-lg);line-height:var(--lh-lg);font-weight:var(--w-m);color:var(--t1)}
.rvg-t p{margin-top:2px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2);max-width:76ch}
.rvg-n{display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex:none;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2);text-align:right}
.rvg-n b{color:var(--t1);font-weight:var(--w-m);white-space:nowrap}
.rvg-n span{font-size:var(--fs-xs);line-height:var(--lh-xs)}
.rvg.has-left .rvg-n b::before{content:'';display:inline-block;width:7px;height:7px;margin-right:7px;border-radius:var(--r-pill);background:var(--warn-dot);vertical-align:1px}
#tb-rev td{height:auto;padding:16px 12px;border-top:1px solid var(--line2);color:var(--t1);vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}
#tb-rev tbody tr:first-child td{border-top:0}
#tb-rev tbody tr:hover td{background:transparent}
#tb-rev td.c-f{padding-left:16px}
#tb-rev td.c-d{padding-right:16px}
#tb-rev tr[data-status="contradictory"] td:first-child{box-shadow:none}
#tb-rev tr[data-status="contradictory"] td{background:rgba(248,238,214,.45)}
#tb-rev tr[data-d] td,#tb-rev tr[data-auto="1"] td{background:var(--surface-2)}
#tb-rev td .fname{display:flex;align-items:flex-start;gap:8px;font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m);color:var(--t1)}
#tb-rev td .fname .mdp-l{margin:1px 0 0}
#tb-rev td .fkind{display:block;margin-top:4px;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.prop{gap:8px}
.prop .val{color:var(--t1);font-size:var(--fs-base);line-height:22px}
.dl{display:grid;grid-template-columns:36px minmax(0,1fr);gap:0 10px;align-items:baseline}
.prop:not(.two) .dl{grid-template-columns:minmax(0,1fr)}
.dk{font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t2)}
.dl.dn .dk{color:var(--info)}
.dv{display:flex;flex-direction:column;gap:4px;min-width:0}
.dl .cv{color:var(--t2);font-size:var(--fs-sm);line-height:20px}
.prop .ed{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.prop .ed s{color:var(--t2)}
.prop .lab{font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.prop .lab b{color:var(--t1)}
.prop .appr{align-self:flex-start}
/* a evidencia: a citacao com um fio de 1px, sem caixa; a segunda citacao em diante abre com um clique */
.ev{gap:10px}
.ev .evb{border:0;border-left:1px solid var(--line4);border-radius:0;background:transparent;padding:2px 0 2px 12px;color:var(--t2)}
.ev .evb:hover{border-left-color:var(--t1);background:var(--fill-0);color:var(--t2)}
.ev .evb q{margin-bottom:4px;color:var(--t1);font-size:var(--fs-sm);line-height:20px}
.ev .evb .evm{flex-wrap:wrap;gap:2px 8px}
.ev .evb .evm time{color:var(--t2)}
.ev .evb .evm .evw{color:var(--t2);white-space:normal;overflow:visible}
.ev .evb .evw b{color:var(--t1);font-weight:var(--w-m)}
.evx summary{display:inline-flex;align-items:center;gap:4px;margin-left:6px;padding:2px 6px;border-radius:var(--r);list-style:none;cursor:pointer;
  font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t2)}
.evx summary::-webkit-details-marker{display:none}
.evx summary::before{content:'+'}
.evx[open] summary::before{content:'\2212'}
.evx summary:hover{background:var(--fill-1);color:var(--t1)}
.evx[open]{display:flex;flex-direction:column;gap:10px}
/* a decisao: um controle segmentado; o aprovar leva o visto verde */
.c-d .dec{gap:8px}
.dseg{display:inline-flex;align-items:stretch;border:1px solid var(--line3);border-radius:var(--r-field);overflow:hidden;background:var(--surface)}
.ds{display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 10px;border:0;border-left:1px solid var(--line3);background:transparent;
  color:var(--t1);font-size:var(--fs-sm);font-weight:var(--w-m);white-space:nowrap}
.ds:first-child{border-left:0}
.ds:hover{background:var(--fill-1)}
.ds .ico-s{width:14px;height:14px}
.ds-ok .ico-s{color:var(--ok-dot)}
.ds-ok:hover{background:var(--ok-bg);color:var(--ok)}
.dec .chg{display:inline-flex;align-items:center;gap:4px;height:26px;padding:0 8px;margin-left:-8px;font-size:var(--fs-xs);color:var(--t2)}
.dec .chg .ico-s,.newopp .chg .ico-s{width:12px;height:12px}
.dec .note{color:var(--t2)}
.newopp .no-dec{justify-content:flex-start}
#tb-rev tr.qsum td{padding:8px 16px 10px;border-top:1px solid var(--line2);background:transparent}
.qbtn{display:flex;align-items:baseline;gap:8px;width:calc(100% + 16px);margin:0 -8px;padding:6px 8px;border:0;border-radius:var(--r);background:transparent;
  text-align:left;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.qbtn:hover{background:var(--fill-1)}
.qbtn svg{width:14px;height:14px;flex:none;align-self:center;color:var(--t2)}
.qb-t{font-weight:var(--w-m);color:var(--t1);white-space:nowrap}
.qn{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--t2)}
.rev-fb{margin-top:16px;padding:12px 16px;border:1px solid var(--line-card);border-top:1px solid var(--line-card);border-radius:var(--r-card);background:var(--surface)}
.notes li{color:var(--t1)}
.notes li .why{color:var(--t2)}
@media(max-width:1400px){.rvt col.k-f{width:164px}.rvt col.k-d{width:224px}.ds{padding:0 8px}}

/* ---- Meetings ---- */
.mt-add .add-b{display:grid;grid-template-columns:minmax(240px,320px) minmax(0,1fr);gap:16px 24px;align-items:start}
.mt-add .draft{grid-column:1/-1}
.add-src{display:flex;flex-direction:column;gap:10px;min-width:0}
.add-opp select.inp{width:100%}
.mt-add .drop{padding:14px 16px}
.srch-w input{width:250px}
.mt-list .pn-h{flex-wrap:wrap}
.tb-mt td{vertical-align:middle;padding-top:12px;padding-bottom:12px}
.mt-t{display:flex;align-items:flex-start;gap:12px;min-width:0}
.mt-ic{display:inline-grid;place-items:center;width:32px;height:32px;flex:none;border-radius:var(--r-field);background:var(--fill-1);color:var(--t1)}
.mt-tx{display:flex;flex-direction:column;gap:2px;min-width:0}
.snip{display:block;max-width:640px;margin-top:6px;padding:6px 10px;border:0;border-radius:var(--r);background:var(--surface-2);
  text-align:left;font-size:var(--fs-sm);line-height:20px;color:var(--t1);outline:1px solid var(--line2);outline-offset:-1px}
.snip:hover{background:var(--fill-1)}
.snip b{font-weight:var(--w-m)}
.mlist li{justify-content:flex-start}
.mlist .mt-ic{display:inline-grid;width:26px;height:26px}
.mlist .ml-x{flex:1;min-width:0}
.mlist li .ch{flex:none}
/* o leitor da reuniao: o que veio dela, quem falou, e a transcricao com busca */
.drw-mtg{width:700px}
.drw-mtg .drw-b{padding:0 0 24px}
.mtg-sum{margin:16px 24px 0;border:1px solid var(--line-card);border-radius:var(--r-card)}
.ms-r{display:grid;grid-template-columns:104px minmax(0,1fr) auto;gap:12px;align-items:center;padding:10px 14px;border-top:1px solid var(--line2)}
.ms-r:first-child{border-top:0}
.ms-k{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.ms-v{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;min-width:0;color:var(--t1)}
.ms-x{font-size:var(--fs-sm);color:var(--t2)}
.pp{display:inline-flex;align-items:baseline;gap:6px;padding:3px 9px;border-radius:var(--r-pill);background:var(--fill-1);font-size:var(--fs-sm);line-height:var(--lh-sm)}
.pp b{font-weight:var(--w-m);color:var(--t1)}
.pp span{font-size:var(--fs-xs);color:var(--t2)}
.pp.us{background:var(--info-bg)}
.tl-bar{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:12px;margin-top:14px;padding:12px 24px;background:var(--surface);border-bottom:1px solid var(--line2)}
.tl-find{flex:1}
.tl-find input{width:100%}
.tl-n{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2);white-space:nowrap}
.tl-list{padding:8px 16px 0}
.tl{color:var(--t1)}
.tl.cont{padding-top:0}
.tl time{color:var(--t2)}
.tl .who{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 8px;margin-bottom:2px}
.tl .who b{font-weight:var(--w-m);color:var(--t1)}
.tl .who .org{font-weight:var(--w-r);color:var(--t2)}
.tl.us .who b{color:var(--info)}
.tl-x{margin:0}
.tl.hit{background:var(--surface-2)}
.tl.hit.cur{outline:1px solid var(--line4);outline-offset:-1px}
.tl.hl{background:var(--info-bg)}

/* ---- Opportunities e Clients: cabecalho de colunas, a linha inteira abre o registro ---- */
.fr{grid-template-columns:minmax(0,2.3fr) 124px 132px minmax(0,1.9fr) 176px 150px}
#opps-groups.own .fr{grid-template-columns:minmax(0,2.5fr) 132px minmax(0,2fr) 176px 150px}
#opps-groups.own .fr>:nth-child(2){display:none}
.fr-h{min-height:0;padding-top:10px;padding-bottom:8px;border-top:0;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t2)}
.fr-h:hover{background:transparent}
#opps-groups .fr-h+.fg .fg-h{border-top:1px solid var(--line2)}
.fr .ttl .rec{font-size:var(--fs-sm)}
.mdp-c{width:16px;height:18px;font-size:11px}
.mdp-lg .mdp-c{width:22px;height:24px;font-size:12px}
.mdp-l{width:18px;height:18px;font-size:11px}
.cl-id h2 .rec{font-size:var(--fs-lg);line-height:var(--lh-lg)}
@media(max-width:1400px){
  .fr{grid-template-columns:minmax(0,2.2fr) 112px 120px minmax(0,1.7fr) 168px 140px;gap:0 10px}
  #opps-groups.own .fr{grid-template-columns:minmax(0,2.4fr) 120px minmax(0,1.8fr) 168px 140px}
}

/* ---- Explore como um app de chat: a pergunta a direita, a resposta em prosa, a caixa presa embaixo ---- */
.ex.ex-on{padding-top:24px;padding-bottom:16px}
.ex.ex-on .cmp{position:sticky;bottom:16px;z-index:20}
.ex.ex-on .cmp::before{content:'';position:absolute;left:-2px;right:-2px;bottom:100%;height:40px;background:linear-gradient(to bottom,rgba(250,250,250,0),var(--folha));pointer-events:none}
.ex.ex-on .cmp::after{content:'';position:absolute;left:-2px;right:-2px;top:100%;height:18px;background:var(--folha);pointer-events:none}
.cv-l{gap:28px;margin-bottom:28px}
.msg.eu{max-width:75%;padding:10px 16px;border:0;border-radius:18px;background:var(--fill-2)}
.msg-who{font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.msg-a>li::marker{color:var(--t2)}
.msg-a .ref{color:var(--t2)}
.msg-ab{color:var(--t1)}
.msg-f{color:var(--t2)}
.msg-m{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.fb{color:var(--t2)}
.sg-k{color:var(--t2)}
.ex-sg h2{color:var(--t2)}

/* ---- Evals ---- */
.ev-ov .loop{list-style:none;margin:0;padding:0}
.lp{display:grid;grid-template-columns:36px minmax(0,1.6fr) minmax(0,1fr) auto;gap:16px;align-items:center;padding:16px;border-top:1px solid var(--line2)}
.lp:first-child{border-top:0}
.lp-n{display:inline-grid;place-items:center;width:28px;height:28px;border:1px solid var(--line4);border-radius:var(--r-pill);font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t1)}
.lp-t h3{font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m);color:var(--t1)}
.lp-t p{margin-top:2px;max-width:64ch;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.lp-s{display:flex;flex-direction:column;gap:2px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.lp-s b{font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m);color:var(--t1)}
.lp-a{justify-self:end}
.tr-w{display:grid;grid-template-columns:320px minmax(0,1fr);gap:16px;align-items:start}
.tr-w>.pn,.md-w>.pn{margin-top:0}
.tq{position:sticky;top:calc(var(--hd-h) + 12px);display:flex;flex-direction:column;max-height:calc(100vh - var(--hd-h) - 24px);overflow:hidden}
.tq-h{display:flex;flex-direction:column;gap:8px;padding:10px 12px;border-bottom:1px solid var(--line2)}
.tq-h .fgroup{flex-wrap:wrap}
.tq-h .fchip{height:26px;padding:0 8px;font-size:var(--fs-xs)}
.tq-all{display:flex;align-items:center;gap:6px;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.tq-all input{margin:0;accent-color:var(--act)}
.tq-l{flex:1;list-style:none;margin:0;padding:6px;overflow-y:auto}
.tq-i{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 8px;width:100%;padding:8px 10px;border:0;border-radius:var(--r-field);background:transparent;text-align:left;color:var(--t1)}
.tq-i:hover{background:var(--fill-1)}
.tq-i.on{background:var(--fill-2)}
.tq-a{display:flex;gap:6px;min-width:0;font-size:var(--fs-sm);line-height:var(--lh-sm)}
.tq-a b{flex:none;font-weight:var(--w-m)}
.tq-a span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tq-b{grid-column:1;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.tq-i .ch{grid-column:2;grid-row:1/3;align-self:center}
.tq-e{padding:12px;color:var(--t2)}
.tv{min-width:0}
.tv-bar{position:sticky;top:var(--hd-h);z-index:5;display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:10px 16px;background:var(--surface);border-bottom:1px solid var(--line2);border-radius:var(--r-card-in) var(--r-card-in) 0 0}
.tv-nav{display:flex;align-items:center;gap:2px}
.tv-nav .b{width:28px;padding:0}
.tv-pos{padding:0 6px;font-size:var(--fs-sm);color:var(--t2)}
.tv-pos b{font-weight:var(--w-m);color:var(--t1)}
.vseg{display:inline-flex;border:1px solid var(--line3);border-radius:var(--r-field);overflow:hidden}
.vs{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 12px;border:0;border-left:1px solid var(--line3);background:var(--surface);
  font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t1)}
.vs:first-child{border-left:0}
.vs:hover{background:var(--fill-1)}
.vs .ico-s{width:14px;height:14px}
.vs-pass[aria-pressed="true"]{background:var(--ok-bg);color:var(--ok)}
.vs-fail[aria-pressed="true"]{background:var(--bad-bg);color:var(--bad)}
.vs-defer[aria-pressed="true"]{background:var(--warn-bg);color:var(--warn)}
.tv-note{display:flex;flex-direction:column;gap:6px;padding:12px 16px;border-bottom:1px solid var(--line2);background:var(--surface-2)}
.tv-note textarea.inp{min-height:64px;background:var(--surface);font-size:var(--fs-sm);line-height:20px}
.tv-nr{display:flex;align-items:flex-end;flex-wrap:wrap;gap:8px 16px}
.tv-mode{display:flex;flex-direction:column;gap:4px;min-width:260px}
.tv-mode select.inp{height:32px}
.tv-keys{margin-left:auto;font-size:var(--fs-xs);line-height:20px;color:var(--t2)}
.tv-keys kbd{margin:0 1px}
.tv-in{padding:16px 20px 24px}
.tv-h{padding-bottom:14px;border-bottom:1px solid var(--line2)}
.tv-t{display:flex;align-items:baseline;gap:10px;min-width:0}
.tv-case{flex:none;padding:1px 6px;border-radius:var(--r-chip);background:var(--fill-1);font-family:var(--mono);font-size:var(--fs-xs);color:var(--t2)}
.tv-t h2{font-size:var(--fs-lg);line-height:var(--lh-lg);font-weight:var(--w-m)}
.tv-sc{margin-top:2px;font-size:var(--fs-base);line-height:var(--lh-base);color:var(--t1)}
.tv-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.tv-m{margin-top:8px;font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t2)}
.tv-q{margin-top:8px;color:var(--t1)}
.tv-p{max-width:80ch;margin-top:8px;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.tv-p b{margin-right:4px;font-weight:var(--w-m);color:var(--t1)}
.tv-s{margin-top:18px}
.tv-s h3{margin-bottom:8px;font-size:var(--fs-base);line-height:var(--lh-base);font-weight:var(--w-m)}
.tv-big{font-size:var(--fs-base);line-height:22px;color:var(--t1)}
.tv-fails{padding:12px 14px;border-radius:var(--r-card);background:var(--bad-bg)}
.tv-fails h3{color:var(--bad)}
.tv-fails ul{margin:0;padding-left:18px;color:var(--t1)}
.tv-g{margin-top:14px}
.tv-g h4{margin-bottom:6px;font-size:var(--fs-xs);line-height:var(--lh-xs);font-weight:var(--w-m);color:var(--t2)}
.tvf{margin-top:6px;padding:10px 12px;border:1px solid var(--line2);border-radius:var(--r-field)}
.tvf-h{display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.tvf-h b{font-weight:var(--w-m)}
.tvf-c{margin-top:6px;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.tvf-c .k{margin-right:6px;font-weight:var(--w-m)}
.tvf-v{margin-top:6px;font-size:var(--fs-base);line-height:22px;color:var(--t1)}
.tvf-e{display:flex;flex-direction:column;gap:6px;margin:8px 0 0;padding:0;list-style:none}
.tvf-e li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:0 8px;font-size:var(--fs-sm);line-height:20px}
.tvf-e .ln,.tv-lines .ln{font-family:var(--mono);font-size:var(--fs-xs);color:var(--t2)}
.tvf-e q{color:var(--t1)}
.tvf-e .sp{grid-column:2;font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--t2)}
.tvf-n,.tv-none{margin-top:6px;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
.tv-plat{display:flex;flex-direction:column;gap:6px;margin:0;padding:0;list-style:none}
.tv-plat li{font-size:var(--fs-sm);line-height:20px;color:var(--t1)}
.tv-plat .k{margin-right:8px;font-weight:var(--w-m);color:var(--t2)}
.tv-fd{display:flex;flex-direction:column;gap:4px;margin:8px 0 0;padding-left:20px}
.tv-tx{margin-top:18px;border:1px solid var(--line2);border-radius:var(--r-field)}
.tv-tx summary{padding:10px 12px;font-weight:var(--w-m);cursor:pointer}
.tv-lines{display:flex;flex-direction:column;gap:6px;margin:0;padding:4px 12px 12px;list-style:none}
.tv-lines li{display:grid;grid-template-columns:44px 140px minmax(0,1fr);gap:8px;font-size:var(--fs-sm);line-height:20px}
.tv-lines .sp{font-weight:var(--w-m);color:var(--t1)}
.tv-lines .sp.us{color:var(--info)}
.md-w{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:16px;align-items:start}
.nl{margin:0;padding:0;list-style:none}
.nl-i{display:flex;flex-direction:column;gap:6px;padding:12px 16px;border-top:1px solid var(--line2)}
.nl-i:first-child{border-top:0}
.nl-t{display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.nl-q{font-size:var(--fs-sm);color:var(--t2)}
.nl-n{font-size:var(--fs-base);line-height:22px;color:var(--t1)}
.nl-m select.inp{height:32px;max-width:340px}
.md-new{display:grid;gap:8px;padding:14px 16px;border-bottom:1px solid var(--line2)}
.md-new .b{justify-self:start}
.ml{margin:0;padding:0;list-style:none}
.ml-i{padding:12px 16px;border-top:1px solid var(--line2)}
.ml-i:first-child{border-top:0}
.ml-h{display:flex;align-items:center;gap:8px}
.ml-h b{flex:1;min-width:0;font-weight:var(--w-m)}
.ml-c{font-size:var(--fs-sm);color:var(--t2)}
.ml-bar{display:block;height:6px;margin-top:8px;border-radius:var(--r-pill);background:var(--fill-2);overflow:hidden}
.ml-bar i{display:block;height:100%;border-radius:inherit;background:var(--act)}
.ml-i p{margin-top:6px;font-size:var(--fs-sm);color:var(--t2)}
#tb-fb .acts{display:inline-flex;gap:6px;flex-wrap:nowrap}
@media(max-width:1280px){.tr-w{grid-template-columns:280px minmax(0,1fr)}}
@media(max-width:1180px){
  .mt-add .add-b,.md-w,.tr-w{grid-template-columns:1fr}
  .tq{position:static;max-height:none}
  .lp{grid-template-columns:36px minmax(0,1fr) auto}.lp-s{grid-column:2}
}

/* ===================================================================== */
/* v6.1 (31/10): cor que ajuda a ler. Cada tipo de coisa tem um matiz e o  */
/* guarda em toda tela: a etapa do funil, o grupo de campos, a fonte da   */
/* conversa, o lado de quem fala, o MEDDPICC, a secao da lateral. Pares   */
/* pastel + tinta escura do mesmo matiz (contraste >= 4.5:1); o magenta   */
/* continua so na marca e no contador.                                    */
/* ===================================================================== */
:root{
  --hue-blue:#2B5FB3; --hue-blue-bg:#E8F0FC;
  --hue-indigo:#4848B8; --hue-indigo-bg:#ECECFB;
  --hue-violet:#6E42B0; --hue-violet-bg:#F1EBFB;
  --hue-teal:#0B6B6B; --hue-teal-bg:#E0F3F1;
  --hue-amber:#8A5300; --hue-amber-bg:#FBEFD9;
  --hue-green:#2A6E39; --hue-green-bg:#E3F3E6;
  --hue-slate:#475467; --hue-slate-bg:#EDF0F4;
  --hue-sand:#7A4A1F; --hue-sand-bg:#F8EEE3;
  --seq-0:#F3F7FD; --seq-1:#B7D3F6; --seq-2:#5598E7; --seq-3:#1C5CAB;
}
.hue-blue{background:var(--hue-blue-bg);color:var(--hue-blue)}
.hue-indigo{background:var(--hue-indigo-bg);color:var(--hue-indigo)}
.hue-violet{background:var(--hue-violet-bg);color:var(--hue-violet)}
.hue-teal{background:var(--hue-teal-bg);color:var(--hue-teal)}
.hue-amber{background:var(--hue-amber-bg);color:var(--hue-amber)}
.hue-green{background:var(--hue-green-bg);color:var(--hue-green)}
.hue-slate{background:var(--hue-slate-bg);color:var(--hue-slate)}
.hue-sand{background:var(--hue-sand-bg);color:var(--hue-sand)}
.rvg-i[class*="hue-"] .ico-b,.mt-ic[class*="hue-"] .ico-b,.mt-ic[class*="hue-"] .ico-s{color:inherit}
/* a lateral: cada secao com o seu matiz no icone */
.nav-i[data-view="explore"] .ni{color:var(--hue-blue)}
.nav-i[data-view="meetings"] .ni{color:var(--hue-indigo)}
.nav-i[data-view="opportunities"] .ni{color:var(--hue-violet)}
.nav-i[data-view="clients"] .ni{color:var(--hue-teal)}
.nav-i[data-view="evals"] .ni{color:var(--hue-amber)}
.nav-novo .ni{color:var(--hue-blue)}
/* a etapa do funil: o mesmo matiz no chip e no marcador da secao */
.ch.st-0{background:var(--hue-slate-bg);color:var(--hue-slate)}
.ch.st-1{background:var(--hue-blue-bg);color:var(--hue-blue)}
.ch.st-2{background:var(--hue-teal-bg);color:var(--hue-teal)}
.ch.st-3{background:var(--hue-indigo-bg);color:var(--hue-indigo)}
.ch.st-4{background:var(--hue-amber-bg);color:var(--hue-amber)}
.ch.st-5{background:var(--hue-green-bg);color:var(--hue-green)}
.ch.st-6{background:var(--ok-bg);color:var(--ok)}
.ch.st-7{background:var(--neutral-bg);color:var(--neutral)}
.fg-h .mk{width:9px;height:9px;border:0;border-radius:var(--r-mark)}
.fg-h .mk-0{background:var(--hue-slate)}
.fg-h .mk-1{background:var(--hue-blue)}
.fg-h .mk-2{background:var(--hue-teal)}
.fg-h .mk-3{background:var(--hue-indigo)}
.fg-h .mk-4{background:var(--hue-amber)}
.fg-h .mk-5{background:var(--hue-green)}
/* MEDDPICC: violeta, o matiz do grupo Qualification */
.mdp-c{border-color:rgba(110,66,176,.30);color:var(--t2)}
.mdp-c.on{background:var(--hue-violet);border-color:var(--hue-violet);color:#fff}
.mdp-c.add{background:var(--hue-violet-bg);border-color:var(--hue-violet);color:var(--hue-violet)}
.mdp-l{background:var(--hue-violet-bg);color:var(--hue-violet)}
/* quem fala: a Orbita em azul, o cliente em areia */
.pp{background:var(--hue-sand-bg)}
.pp span{color:var(--hue-sand)}
.pp.us{background:var(--hue-blue-bg)}
.pp.us span{color:var(--hue-blue)}
.tl .who b{color:var(--hue-sand)}
.tl.us .who b{color:var(--hue-blue)}
.tv-lines .sp{color:var(--hue-sand)}
.tv-lines .sp.us{color:var(--hue-blue)}
.ev .evb .evw b{color:var(--t1)}
/* os nomes de cliente na lista com o monograma de 20px */
.fr .ttl,.tb-mt .ttl{gap:10px}

/* ---- Evals: o painel ---- */
.ev-cfg{display:flex;align-items:center;gap:10px;margin-bottom:12px;padding:10px 14px;border:1px solid var(--line-card);border-radius:var(--r-card);background:var(--surface);font-size:var(--fs-sm);color:var(--t2)}
.ev-cfg b{color:var(--t1);font-weight:var(--w-m)}
.ev-cfg svg{width:16px;height:16px;color:var(--hue-blue)}
.ev-kpi{grid-auto-columns:minmax(0,1fr)}
.ev-kpi+.pn{margin-top:16px}
#tb-exp tr.is-prod td{background:var(--hue-blue-bg)}
#tb-exp tr.is-prod td:first-child{box-shadow:none}
.mtr{display:inline-flex;align-items:center;gap:8px}
.mtr-t{display:block;width:96px;height:6px;border-radius:var(--r-pill);background:var(--fill-2);overflow:hidden}
.mtr-t i{display:block;height:100%;background:var(--hue-blue);transform-origin:left center}
.mtr b{font-weight:var(--w-m);font-variant-numeric:tabular-nums;min-width:44px}
.ev-two{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:16px;align-items:start;margin-top:16px}
.ev-two>.pn{margin-top:0}
.hm-t td,.hm-t th{height:auto;padding:5px 10px}
.hm-t th.num{white-space:normal;line-height:var(--lh-xs);vertical-align:bottom}
.hm-t tr.hm-g th{padding:10px 10px 4px;background:transparent;border-bottom:0;font-size:var(--fs-xs);color:var(--t2)}
.hm-t td:first-child{white-space:nowrap}
.hm-t td .mdp-l{margin-right:6px}
td.hm,.hm-key .hm{text-align:center;font-size:var(--fs-xs);font-variant-numeric:tabular-nums;border:2px solid var(--surface);border-radius:4px}
.hm-0{background:var(--seq-0);color:var(--t2)}
.hm-1{background:var(--seq-1);color:var(--ink)}
.hm-2{background:var(--seq-2);color:var(--ink)}
.hm-3{background:var(--seq-3);color:#fff}
.hm-na{color:var(--t3)}
.hm-key{display:flex;align-items:center;flex-wrap:wrap;gap:6px 10px}
.hm-key .hm{display:inline-block;min-width:36px;padding:1px 4px}
.jd{display:flex;flex-direction:column;gap:10px}
.jd-q{font-size:var(--fs-sm);line-height:20px;color:var(--t1)}
.jd-q b{font-weight:var(--w-m)}
.jd-ag{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.jd-ag>div{display:flex;flex-direction:column;gap:2px;padding:10px 12px;border-radius:var(--r-field);background:var(--hue-amber-bg)}
.jd-ag b{font-size:var(--fs-lg);line-height:var(--lh-lg);font-weight:var(--w-m);color:var(--t1)}
.jd-ag span{font-size:var(--fs-xs);line-height:var(--lh-xs);color:var(--hue-amber)}
.jd-h{display:flex;align-items:baseline;gap:8px;padding:10px 16px;border-top:1px solid var(--line2);font-size:var(--fs-sm);font-weight:var(--w-m)}
.jd-l{list-style:none;margin:0;padding:0 16px 12px;display:flex;flex-direction:column;gap:12px}
.jd-l li{display:flex;flex-direction:column;gap:4px;font-size:var(--fs-sm);line-height:20px}
.jd-l q{color:var(--t1)}
.jd-l p{color:var(--t2)}
.jd-more summary{margin:0 16px 12px;padding:4px 8px;border-radius:var(--r);cursor:pointer;font-size:var(--fs-sm);font-weight:var(--w-m);color:var(--t1);list-style:none;display:inline-block}
.jd-more summary::-webkit-details-marker{display:none}
.jd-more summary::before{content:'+ '}
.jd-more[open] summary::before{content:'2 '}
.jd-more summary:hover{background:var(--fill-1)}
/* o juiz no trace: o veredito, a critica e a sua concordancia */
.tvf-j{margin-top:8px;padding:8px 10px;border-radius:var(--r);background:var(--surface-2)}
.tvf-jh{display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.tvf-jq{margin-left:auto;font-size:var(--fs-xs);color:var(--t2)}
.jag{display:inline-flex;border:1px solid var(--line3);border-radius:var(--r);overflow:hidden}
.jb{height:24px;padding:0 8px;border:0;border-left:1px solid var(--line3);background:var(--surface);font-size:var(--fs-xs);font-weight:var(--w-m);color:var(--t1)}
.jb:first-child{border-left:0}
.jb:hover{background:var(--fill-1)}
.jb[aria-pressed="true"]{background:var(--hue-amber-bg);color:var(--hue-amber)}
.tvf-jc{margin-top:6px;font-size:var(--fs-sm);line-height:20px;color:var(--t2)}
@media(max-width:1280px){.ev-two{grid-template-columns:1fr}}

/* v6.2 (31/10): os campos de lista (schema v4) leem como chips; o texto continua o valor gravado */
.opts{display:inline-flex;flex-wrap:wrap;gap:4px;vertical-align:middle}
.opt{display:inline-flex;align-items:center;min-height:22px;padding:1px 8px;border-radius:var(--r-pill);background:var(--fill-2);font-size:var(--fs-sm);line-height:var(--lh-sm);color:var(--t1)}
.opt.oth{background:transparent;box-shadow:inset 0 0 0 1px var(--line4)}
.sep{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap}
.prop .val.opts{font-size:var(--fs-sm)}
.dl .cv.opts .opt{background:transparent;box-shadow:inset 0 0 0 1px var(--line3);color:var(--t2)}
.chkset{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
#dec-other{margin-top:6px}
"""
