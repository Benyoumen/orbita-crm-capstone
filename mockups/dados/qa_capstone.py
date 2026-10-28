# -*- coding: utf-8 -*-
"""Portao de qualidade do mockup Orbita CRM: um comando, um codigo de saida.

    python qa_capstone.py            # roda tudo
    python qa_capstone.py --rapido   # pula a coleta e a regeracao (usa o HTML como esta)

  1. COLETA + REGERA   congela o kit (foto.json, com o scorer do kit em modo mock)
                       e monta o HTML a partir dos geradores
  2. SONDA             os criterios de aceite do HANDOFF (Explore, as onze conversas
                       de capstone/samples soltas ou coladas, atribuicao, oportunidade
                       nova, permissoes e Undo, Settings, funil, clientes) e o contrato
                       da pele, exercitados no Edge headless pelo caminho da vendedora,
                       em 1440 e em 1280
  3. SERVIDOR          sobe server.mjs --mock numa porta de teste e faz o laco pela
                       porta HTTP: a atualizacao vem do pipeline.mjs do KIT (resultados
                       salvos, sem chave), o Explore responde pela rota /api/explore com
                       o mesmo controle de acesso, e conversa nova sem chave e recusada
  4. DETECTOR          antipadroes visuais (impeccable detect.mjs), com a allowlist
                       do que ja foi decidido na v5 (a Inter embutida)
  5. DOCUMENTACAO      o LEIAME cita o arquivo gerado e os comandos deste portao

Sai 0 so com os cinco passos verdes. Achado novo fecha o portao.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MOCKUP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import saida  # noqa: E402
HTML = saida.HTML
LEIAME = os.path.join(MOCKUP, "LEIAME.md")
sys.path.insert(0, HERE)
import sonda_capstone as SO  # noqa: E402


def raiz_repo(inicio):
    d = inicio
    while True:
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        pai = os.path.dirname(d)
        if pai == d:
            return None
        d = pai


RAIZ = raiz_repo(HERE)
DETECT = os.path.join(RAIZ, ".claude", "skills", "impeccable", "scripts", "detect.mjs") if RAIZ else None
# Desvios registrados no DESIGN.md desta pasta: a InterVariable embutida em data: (decisao do PM de
# 13/09, v5), que o detector le como fonte repetida; e os tamanhos em tokens --fs-*, que deixam o
# detector ver so os tres literais do monograma e acusar hierarquia rasa
CONHECIDOS = {("overused-font", 'font-family:"Inter'), ("flat-type-hierarchy", "Sizes:")}


def passo(n, titulo):
    print("\n[%d/5] %s" % (n, titulo))
    print("      " + "-" * (len(titulo) + 2))


def roda(cmd, cwd=None, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


SERVIDOR_ROTEIRO = r"""
    await reset();
    await until(() => CRM.live().checked, 'probe');
    check('S server probed from the page, without a Claude key', CRM.live().ok === true && CRM.live().mode === 'saved', JSON.stringify(CRM.live()));
    check('S the agent pill says the server has no Claude key', /server without a Claude key/.test(txt(q('#job'))), txt(q('#job')));
    const id = await addRun(T.T1);
    const r = runOf(id);
    check('S the update came from the kit pipeline on the server', r.mode === 'saved' && r.log.some(ev => ev.action === 'agent_called' && /MOCK/.test(ev.detail)) && r.log.some(ev => ev.action === 'output_validated'));
    check('S every field of the schema', qq('#tb-rev tr[data-field]').length === FIELDS.length);
    check('S Always allow wrote on the page after the server answered', FIELDS.filter(k => DEF[k].permission === 'auto').every(k => fv(oppOf('OPP-0142'), k).value));
    await approveAll(); await submit('S');
    check('S Submit wrote the opportunity and the client record', fv(oppOf('OPP-0142'), 'stage').value === 'Solution' && fv(cliOf('CLI-001'), 'employee_count').value === '850');
    const id5 = await addRun(T.T5);
    check('S a new client through the server: the request comes back with the answer', !!runOf(id5).output.target && runOf(id5).output.target.client_name === 'Delta Pharma' && !!q('#rev-new [data-create]'));
    const id8 = await addRun(T.T8);
    check('S access denied is decided in the page, before any call', runOf(id8).output.source_status === 'AccessDenied' && runOf(id8).mode === 'checks');
    const post = (u, b) => fetch(window.CAPSTONE_API + u, {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(b)}).then(x => x.json());
    const crm0 = {clients: FOTO.clients, opportunities: FOTO.opportunities};
    const a1 = await post('/api/explore', {question: "What's the status of Atlas Manufacturing?", userId: 'U01', crm: crm0, now: FOTO.data_da_foto});
    check('S /api/explore answers from the CRM', a1.answer && a1.answer.kind === 'status' && /Atlas Manufacturing/.test(a1.answer.verdict), JSON.stringify(a1).slice(0, 120));
    const a2 = await post('/api/explore', {question: "What's the status of Atlas Manufacturing?", userId: 'U02', crm: crm0, now: FOTO.data_da_foto});
    check('S /api/explore filters by access on the server', a2.answer && a2.answer.kind === 'none' && !JSON.stringify(a2).includes('OPP-0144'));
    await reset();
    q('#tab-paste').click(); await wait(10);
    q('#paste-in').value = 'Ana Ribeiro: Thanks for the time, Bruno.\nBruno Lemos: We sell solar panels and track every lead in a spreadsheet.\nAna Ribeiro: Let us book a demo next week.';
    q('#paste-go').click(); await until(() => q('#dr-client'), 'new draft');
    q('#dr-client').value = 'Brisa Solar'; q('#dr-client').dispatchEvent(new Event('input')); await wait(10);
    q('#dr-go').click(); await until(() => /No saved result/.test(txt(q('#toast-tx'))), 'server refusal');
    ok('S a new conversation without a Claude key is refused by the server, with the reason');
"""

STEPS_LINE = SO.STEPS_LINE


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def servidor():
    """Sobe server.mjs --mock, exercita pela porta HTTP e derruba. Devolve as linhas da sonda."""
    porta = porta_livre()
    proc = subprocess.Popen(["node", "server.mjs", "--mock", "--port", str(porta)], cwd=MOCKUP,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/api/health" % porta, timeout=1) as r:
                    saude = json.loads(r.read().decode("utf-8"))
                    break
            except Exception:
                time.sleep(0.2)
        else:
            return ["FAIL servidor :: nao respondeu em /api/health"]
        if saude.get("mode") != "saved":
            return ["FAIL servidor :: modo inesperado %s" % saude]
        assert STEPS_LINE in SO.ROTEIRO, "a linha de passos da sonda mudou"
        roteiro = SO.com_amostras(SO.ROTEIRO.replace(STEPS_LINE, "const steps = [async function servidor() { %s }];" % SERVIDOR_ROTEIRO))
        # a copia com o roteiro abre do disco e aponta a API para a porta de teste: e o
        # mesmo caminho de quem abre o HTML do disco com o servidor no ar
        base = tempfile.mkdtemp(prefix="qa_cap_srv_")
        try:
            with open(HTML, encoding="utf-8") as fp:
                doc = fp.read()
            # a pagina le window.CAPSTONE_API antes de decidir a URL do servidor: injeta no <head>
            assert "window.CAPSTONE_API" in doc, "a pagina nao le window.CAPSTONE_API"
            doc = doc.replace("<head>", "<head>\n<script>window.CAPSTONE_API = 'http://127.0.0.1:%d';</script>" % porta, 1)
            doc = doc.replace("</body>", roteiro + "\n</body>")
            alvo = os.path.join(base, "cap.html")
            with open(alvo, "w", encoding="utf-8") as fp:
                fp.write(doc)
            dom = SO._edge(alvo, base, 1440, 900, "#/meetings", budget=60000)
        finally:
            shutil.rmtree(base, ignore_errors=True)
        m = re.search(r'<pre id="sonda-out"[^>]*>(.*?)</pre>', dom, re.S)
        if not m:
            return ["EXC servidor :: a pagina nao escreveu o laudo"]
        import html as _h
        return [_h.unescape(l) for l in m.group(1).split("\n") if l.strip()]
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


def main():
    rapido = "--rapido" in sys.argv
    falhas = []

    passo(1, "Coleta do kit e regeracao do mockup")
    if rapido:
        print("      pulado (--rapido)")
    else:
        for cmd in (["coleta.py"], ["render_capstone.py"]):
            cod, texto = roda([sys.executable] + cmd, cwd=HERE)
            ultima = [l for l in texto.strip().splitlines() if l.strip()]
            print("      " + (ultima[-1].strip() if ultima else "(sem saida)")[:150])
            if cod != 0:
                print(texto[-800:])
                falhas.append(cmd[0])

    passo(2, "Sonda de comportamento (aceites + contrato da pele, 1440 e 1280)")
    total_ok = 0
    for w in (1440, 1280):
        linhas = SO.sondar(w)
        oks = [l for l in linhas if l.startswith("OK")]
        maus = [l for l in linhas if l.startswith("FAIL") or l.startswith("EXC") or (l.startswith("ERRS") and not l.startswith("ERRS 0"))]
        if "DONE" not in linhas:
            maus.append("EXC :: o roteiro nao chegou ao fim")
        total_ok += len(oks)
        print("      %d: %d ok, %d problemas" % (w, len(oks), len(maus)))
        for l in maus:
            print("      " + l)
        if maus:
            falhas.append("sonda %d" % w)
    print("      %d verificacoes ok" % total_ok)

    passo(3, "Servidor local sem chave: o laco inteiro pela porta HTTP")
    try:
        linhas = servidor()
    except Exception as exc:
        linhas = ["EXC servidor :: %s" % exc]
    oks = [l for l in linhas if l.startswith("OK")]
    maus = [l for l in linhas if not l.startswith("OK") and l != "DONE" and not l.startswith("ERRS 0")]
    print("      %d ok" % len(oks))
    for l in maus:
        print("      " + l)
    if maus or "DONE" not in linhas:
        falhas.append("servidor")

    passo(4, "Detector de antipadroes (impeccable)")
    if DETECT and os.path.isfile(DETECT):
        cod, texto = roda(["node", DETECT, "--json", HTML], cwd=RAIZ)
        itens = None
        try:
            itens = json.loads(texto[texto.index("["):texto.rindex("]") + 1])
        except (ValueError, IndexError):
            print("      nao consegui ler a saida do detector")
        if itens is None:
            falhas.append("detector")
        else:
            graves = [x for x in itens if x.get("severity") in ("warning", "error")]
            conhecido = lambda x: any(x.get("antipattern") == a and (x.get("snippet") or "").startswith(b) for a, b in CONHECIDOS)
            novos = [x for x in graves if not conhecido(x)]
            print("      %d achados, %d graves, %d conhecidos, %d novos" % (len(itens), len(graves), len(graves) - len(novos), len(novos)))
            for x in novos:
                print("      NOVO %s | linha %s | %s" % (x.get("antipattern"), x.get("line"), (x.get("snippet") or "")[:70]))
            if novos:
                falhas.append("detector")
    else:
        print("      detector ausente (sem .claude/skills/impeccable): passo pulado")

    passo(5, "Documentacao: o LEIAME cita o arquivo gerado e os comandos do portao")
    try:
        with open(LEIAME, encoding="utf-8") as fp:
            leiame = fp.read()
        faltas = [t for t in (os.path.basename(HTML), "qa_capstone.py", "render_capstone.py", "coleta.py", "server.mjs", "sonda_capstone.py") if t not in leiame]
        print("      " + ("ok" if not faltas else "faltam: " + ", ".join(faltas)))
        if faltas:
            falhas.append("documentacao")
    except OSError:
        print("      LEIAME.md ausente")
        falhas.append("documentacao")

    print("\n" + "=" * 64)
    if falhas:
        print("PORTAO FECHADO: %s" % ", ".join(falhas))
        return 1
    print("PORTAO ABERTO: aceites, contrato da pele, servidor, detector e documentacao em dia")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
