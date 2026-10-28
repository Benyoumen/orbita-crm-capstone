# -*- coding: utf-8 -*-
"""As superficies ESTATICAS do mockup Orbita CRM: a casca (lateral com Explore, as
vistas de vendas, o grupo Chat e Settings; a barra com o estado do agente e o menu
da conta), o esqueleto de cada vista (o JavaScript preenche as caixas), as gavetas
(transcricao, oportunidade, cliente) e os dialogos. Stdlib pura.

    import vistas_capstone as VC
    VC.lateral(ic) · VC.barra(ic) · VC.vistas(foto, ic) · VC.gavetas(ic)

`ic(nome, cls)` e a funcao que desenha um icone da familia (icones_v5.svg, ou o
substituto desta pasta). Todo texto que vem do kit passa por `e()` uma vez.
"""
import html

e = html.escape


# ---------------------------------------------------------------------------
# a casca
# ---------------------------------------------------------------------------
def lateral(ic):
    return f"""
<aside class="side" aria-label="Orbita CRM">
  <div class="side-top">
    <div class="ws"><span class="ws-mk" aria-hidden="true"><i></i></span><span class="ws-t"><b>Orbita CRM</b><span id="who">Ana Ribeiro</span></span></div>
  </div>
  <nav class="nav" aria-label="sections">
    <button class="nav-i" type="button" data-view="explore" title="ask anything about your clients and opportunities">{ic("compass")}<span class="lb">Explore</span></button>
    <div class="nav-g">Sales</div>
    <button class="nav-i" type="button" data-view="meetings" title="add a meeting transcript or a chat; the agent prepares the CRM update">{ic("audio-lines")}<span class="lb">Meetings</span><span class="nav-n" id="nav-meetings-n"></span></button>
    <button class="nav-i" type="button" data-view="opportunities" title="the opportunities you can read, by stage of the funnel">{ic("briefcase")}<span class="lb">Opportunities</span><span class="nav-n" id="nav-opps-n"></span></button>
    <button class="nav-i" type="button" data-view="clients" title="every client you work with, with its opportunities">{ic("building-2")}<span class="lb">Clients</span><span class="nav-n" id="nav-clients-n"></span></button>
    <div class="nav-g">Chat</div>
    <button class="nav-i nav-novo" type="button" id="nav-newchat" title="start a new conversation in Explore">{ic("plus")}<span class="lb">New chat</span></button>
    <div class="nav-cs" id="nav-chats"></div>
    <div class="nav-foot">
      <button class="nav-i" type="button" data-view="settings" title="permissions, agent, sources, team, activity log, quality checks and data">{ic("sliders-horizontal")}<span class="lb">Settings</span></button>
    </div>
  </nav>
</aside>"""


def barra(ic):
    return f"""
<header class="hd"><div class="hd-in">
  <button class="job" id="job" type="button" data-estado="pronto" aria-live="polite" title="the agent that reads your conversations · open Settings > Agent">
    <span class="job-ic" aria-hidden="true">{ic("circle-check", "ico-b")}<span class="spin"></span></span>
    <span class="job-t" id="job-t">Agent</span>
    <span class="job-s" id="job-s"></span>
  </button>
  <span class="grow"></span>
  <div class="umenu" id="umenu">
    <button class="hbtn uav" id="umenubtn" type="button" aria-expanded="false" aria-controls="umenu-l" aria-label="Account" title="your account"><span class="uav-i" id="uav-i" aria-hidden="true">AR</span></button>
    <div class="pop"><div class="pop-id"><span class="uav-i" aria-hidden="true"></span><span class="pop-idt"><span class="pop-nm" id="umenu-nm"></span><span class="pop-org" id="umenu-role"></span></span></div>
      <div class="pop-l" id="umenu-l">
        <div class="pop-lab">Switch user</div>
        <button class="pi" type="button" role="radio" aria-checked="true" data-user="U01">Ana Ribeiro<span class="sub">Account executive · own opportunities</span></button>
        <button class="pi" type="button" role="radio" aria-checked="false" data-user="U02">Lucas Moreira<span class="sub">Account executive · own opportunities</span></button>
        <button class="pi" type="button" role="radio" aria-checked="false" data-user="U04">Juliana Costa<span class="sub">Sales manager · reads all opportunities</span></button>
        <div class="pop-lab">Orbita CRM</div>
        <button class="pi" type="button" data-go="#/settings/permissions">Settings<span class="sub">permissions, agent, sources, activity log</span></button>
      </div></div>
  </div>
</div></header>"""


# ---------------------------------------------------------------------------
# as vistas
# ---------------------------------------------------------------------------
def _vista(nome, titulo, corpo):
    return f'<section class="view" data-view="{nome}" data-title="{e(titulo)}" tabindex="-1" aria-label="{e(titulo)}" hidden>\n{corpo}\n</section>'


def vistas(foto, ic):
    explore = f"""
<div class="ex">
  <h1 class="ex-t" id="ex-t">Explore</h1>
  <ol class="cv-l" id="ex-thread" aria-live="polite" aria-label="conversation"></ol>
  <form class="cmp" id="ex-cmp" autocomplete="off">
    <label class="sr" for="ex-in">Question for Explore</label>
    <textarea id="ex-in" rows="3" maxlength="600" placeholder="Ask about a client, an opportunity or your pipeline"></textarea>
    <div class="cmp-b"><span class="cmp-ctx" id="ex-src">{ic("database", "ico-s")}<span id="ex-src-t">Your CRM</span></span><span class="grow"></span>
      <button class="cmp-env" type="submit" aria-label="Ask" title="Ask (Enter)">{ic("arrow-up", "ico-b")}</button></div>
  </form>
  <section class="ex-sg" id="ex-sg-box" aria-labelledby="ex-sg-t"><h2 id="ex-sg-t">From your pipeline</h2><ul class="sg-l" id="ex-sg"></ul></section>
</div>"""
    meetings = f"""
<div class="ph"><div class="ph-t"><h1>Meetings</h1></div></div>
<div class="strip" id="mt-strip"></div>
<div class="pn mt-add" id="mt-add">
  <div class="pn-h"><h2>Add a meeting</h2><span class="pn-d">a meeting transcript or a chat export · the agent prepares the CRM update · nothing is written without your permission</span></div>
  <div class="add-b">
    <div class="add-opp">
      <label class="fld-l" for="mt-opp">Select your opportunity</label>
      <select id="mt-opp" class="inp"></select>
      <span class="mini" id="mt-opp-h">Leave it on detect: the agent finds the opportunity from the speakers and the company named in the conversation.</span>
    </div>
    <div class="src-tabs" role="tablist" aria-label="how to add the transcript">
      <button class="seg" type="button" role="tab" id="tab-file" data-src="file" aria-selected="true" aria-controls="drop">{ic("upload", "ico-s")}Upload a file</button>
      <button class="seg" type="button" role="tab" id="tab-paste" data-src="paste" aria-selected="false" aria-controls="paste">{ic("file-text", "ico-s")}Paste text</button>
    </div>
    <div class="drop" id="drop" role="button" tabindex="0" aria-label="drop a transcript or a chat export, or click to choose a file">{ic("file-audio", "ico-b")}<div class="drop-t"><b>Drop a transcript or a chat export here</b>, or click to choose a file<div class="mini">Teams, Zoom or Google Meet (.vtt), subtitles (.srt), Granola, Otter or Fathom (.txt), a WhatsApp chat export (.txt) · the file stays in this browser</div></div>
      <label class="b b-sm b-s" for="drop-file">Choose file<input id="drop-file" type="file" accept=".txt,.vtt,.srt,.md,.text,text/plain,text/vtt"></label></div>
    <div class="paste" id="paste" hidden>
      <label class="sr" for="paste-in">Transcript text</label>
      <textarea id="paste-in" class="inp" rows="9" placeholder="Paste the conversation, one speaker per line:&#10;Ana Ribeiro: Good morning, Sofia. Thanks for the time.&#10;Sofia Martins: Good morning, Ana.&#10;(times like [00:01:02] or a WhatsApp export also work)"></textarea>
      <div class="acts"><span class="mini" id="paste-n"></span><span class="grow"></span><button class="b b-sm b-p" type="button" id="paste-go">Read the text</button></div>
    </div>
    <div class="draft" id="mt-draft" hidden></div>
  </div>
</div>
<div class="pn"><div class="pn-h"><h2>Your meetings</h2><span class="pn-n" id="mt-n"></span><span class="pn-d">most recent first</span></div>
  <div class="tbw"><table class="tb" id="tb-meetings"><thead><tr><th>Meeting</th><th>Client · opportunity</th><th>CRM update</th><th></th></tr></thead><tbody></tbody></table></div>
</div>"""
    review = """
<div class="ph"><div class="ph-t" id="rev-head"><h1>Review</h1></div></div>
<div id="rev-body"></div>"""
    opps = f"""
<div class="ph"><div class="ph-t"><h1>Opportunities</h1><div class="ph-c" id="opps-ctx"></div></div><div class="acts"><button class="b b-s" type="button" id="opps-export" title="download the CRM as a CSV, ready to import into a spreadsheet">{ic("download", "ico-b")}Export CRM (CSV)</button></div></div>
<div class="strip" id="opps-strip"></div>
<div class="pn fc" id="opps-card">
  <div class="fc-bar"><span class="fgroup" id="opps-chips" role="group" aria-label="stage of the funnel"></span><span class="grow"></span>
    <label class="srch">{ic("search", "ico-s")}<input id="opps-q" type="search" placeholder="Search client or opportunity" aria-label="search client or opportunity"></label>
    <label class="fsel" id="opps-owner-w"><span class="sr">Owner</span><select id="opps-owner" aria-label="owner"></select></label>
    <label class="fsel"><span class="sr">Sort by</span><select id="opps-sort" aria-label="sort by"><option value="due">Next follow-up</option><option value="amount">Highest amount</option><option value="updated">Recently updated</option><option value="qual">Thinnest qualification</option></select></label></div>
  <div id="opps-groups"></div>
  <div class="pn-f">Amount, close date and owner are set by the seller only: the agent never proposes them. Everything else changes through a CRM update, under the permissions in Settings.</div>
</div>"""
    clients = f"""
<div class="ph"><div class="ph-t"><h1>Clients</h1><div class="ph-c" id="cl-ctx"></div></div></div>
<div class="cl-bar"><label class="srch">{ic("search", "ico-s")}<input id="cl-q" type="search" placeholder="Search client, contact or industry" aria-label="search client, contact or industry"></label>
  <span class="grow"></span><label class="fsel"><span class="sr">Sort by</span><select id="cl-sort" aria-label="sort clients by"><option value="name">Name</option><option value="pipeline">Open pipeline</option><option value="recent">Last meeting</option></select></label></div>
<div class="cl-list" id="cl-list"></div>"""
    settings = """
<div class="ph"><div class="ph-t"><h1>Settings</h1><div class="ph-c" id="set-ctx">how the agent may change your CRM, where conversations come from, and who is using it</div></div></div>
<div class="subnav" role="tablist" aria-label="settings" id="set-tabs">
  <button class="seg" type="button" role="tab" data-tab="permissions" aria-selected="true">Permissions</button>
  <button class="seg" type="button" role="tab" data-tab="agent" aria-selected="false">Agent</button>
  <button class="seg" type="button" role="tab" data-tab="sources" aria-selected="false">Sources</button>
  <button class="seg" type="button" role="tab" data-tab="team" aria-selected="false">Team</button>
  <button class="seg" type="button" role="tab" data-tab="activity" aria-selected="false">Activity log</button>
  <button class="seg" type="button" role="tab" data-tab="quality" aria-selected="false">Quality checks</button>
  <button class="seg" type="button" role="tab" data-tab="data" aria-selected="false">Data</button>
</div>
<div id="set-body"></div>"""
    return "\n".join([
        _vista("explore", "Explore", explore),
        _vista("meetings", "Meetings", meetings),
        _vista("review", "Review", review),
        _vista("opportunities", "Opportunities", opps),
        _vista("clients", "Clients", clients),
        _vista("settings", "Settings", settings),
    ])


def gavetas(ic):
    return f"""
<dialog class="drw" id="drw" aria-labelledby="drw-t">
  <div class="drw-in">
    <div class="drw-h"><div><h2 id="drw-t">Transcript</h2><div class="mini" id="drw-m"></div></div><button class="dlg-x" id="drw-x" type="button" aria-label="close">{ic("x", "ico-b")}</button></div>
    <div class="drw-b" id="drw-b"></div>
  </div>
</dialog>
<dialog class="drw drw-rec" id="opp-drw" aria-labelledby="opp-drw-t">
  <div class="drw-in">
    <div class="drw-h"><div class="drw-id" id="opp-drw-id"><h2 id="opp-drw-t">Opportunity</h2></div><button class="dlg-x" id="opp-drw-x" type="button" aria-label="close">{ic("x", "ico-b")}</button></div>
    <div class="drw-b" id="opp-drw-b"></div>
  </div>
</dialog>
<dialog class="drw drw-rec" id="cli-drw" aria-labelledby="cli-drw-t">
  <div class="drw-in">
    <div class="drw-h"><div class="drw-id" id="cli-drw-id"><h2 id="cli-drw-t">Client</h2></div><button class="dlg-x" id="cli-drw-x" type="button" aria-label="close">{ic("x", "ico-b")}</button></div>
    <div class="drw-b" id="cli-drw-b"></div>
  </div>
</dialog>
<dialog class="dlg" id="dlg-reset" aria-labelledby="dlg-reset-t">
  <div class="dlg-h"><h2 id="dlg-reset-t">Reset the CRM to the seed?</h2><button class="dlg-x" id="dlg-reset-x" type="button" aria-label="close">{ic("x", "ico-b")}</button></div>
  <div class="dlg-b"><p>The clients and opportunities go back to the seed. Every meeting, CRM update, decision, chat and activity item in this browser is deleted. Your permissions and agent settings stay.</p></div>
  <div class="dlg-f"><button class="b b-t" type="button" id="dlg-reset-cancel" autofocus>Keep everything</button><button class="b b-d" type="button" id="dlg-reset-ok">Reset to the seed</button></div>
</dialog>
<div class="toast" id="toast" role="status" aria-live="polite" hidden>
  <span class="tk" id="toast-k" aria-hidden="true"></span>
  <span class="tx" id="toast-tx"></span>
  <button class="tu" id="toast-act" type="button" hidden></button>
  <button class="tx-x" id="toast-x" type="button" aria-label="close the notice">{ic("x", "ico-s")}</button>
</div>"""
