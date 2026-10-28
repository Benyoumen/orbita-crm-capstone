# -*- coding: utf-8 -*-
"""Gera o mockup Call-to-CRM (capstone Product Faculty) na pele do SalesOps v5.

    python coleta.py              # 1. congela o kit em foto.json
    python render_capstone.py     # 2. monta ../mockup-call-to-crm_<data>.html (nome em saida.py)

Uma peca so, que abre do disco: fontes embutidas (InterVariable 4.1 e DM Mono, as
mesmas do SalesOps v5, importadas de `fonte_v5.py`), a familia de icones
(`icones_v5.py`), a foto do kit e o JavaScript. Nada de rede.

O que a peca e (v4, 28/10/2026): o CRM da Orbita (empresa ficticia que vende CRM)
com o Call-to-CRM Agent dentro. As reunioes chegam do Granola (notas sinteticas no
formato da API, ou a pasta real pelo servidor); cada uma vira uma proposta de
atualizacao de 19 campos em seis grupos, com a citacao de cada um; a vendedora
aprova, edita ou rejeita; so o aprovado e escrito, na oportunidade ou no cliente.
O nucleo do kit (agent/core.mjs + eval/score.mjs) entra na pagina TAL COMO ESTA:
pre-checagens, validador, escrita e scorer sao o mesmo codigo da linha de comando.

Decisoes desta peca, registradas no LEIAME.md ao lado:
  - o CRM e o proprio mockup (localStorage), semeado do kit; exportacao em CSV;
  - Granola por fixtures (offline, padrao) ou ao vivo pelo server.mjs (chave Business);
  - modo mock (resposta de referencia pelo MESMO validador) e modo live
    (servidor local com o pipeline.mjs do kit e a chave);
  - interface em ingles, como o kit e a PRD; o registro desta pasta em portugues.

Nunca editar o HTML gerado: mude o gerador e rode de novo.
"""
import hashlib
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
MOCKUP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import saida  # noqa: E402
SAIDA = os.environ.get("CAPSTONE_SAIDA") or saida.HTML
FOTO = os.path.join(HERE, "foto.json")

# os modulos da v5 que esta peca reaproveita (fontes e icones), sem copiar. A peca saiu de
# quasar/premissas/agentes_de_vendas/apresentacoes/capstone/mockup para capstone/mockups, entao o
# caminho parte de capstone/ e sobe para o quasar irmao; V5_DADOS no ambiente sobrescreve
CAPSTONE = os.path.dirname(MOCKUP)
V5_DADOS = os.environ.get("V5_DADOS") or os.path.normpath(os.path.join(
    CAPSTONE, "..", "quasar", "premissas", "agentes_de_vendas", "agent_spec", "R3", "agent-spec", "sales", "ux-ui", "mockup", "dados"))
if os.path.isdir(V5_DADOS) and V5_DADOS not in sys.path:
    sys.path.insert(0, V5_DADOS)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import capstone_css as CS      # noqa: E402
import capstone_js as JSM      # noqa: E402
import vistas_capstone as VC   # noqa: E402

# sem os modulos da v5 a peca sairia sem a Inter e com circulos no lugar dos icones: e erro, nao aviso
try:
    import fonte_v5 as FT
    import icones_v5 as IC
except Exception as exc:
    raise SystemExit("modulos da v5 (fonte_v5, icones_v5) nao encontrados em %s (%s). "
                     "Defina V5_DADOS com a pasta dados/ do mockup v5." % (V5_DADOS, exc))

_RAIZ = ('<svg class="%s" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><g fill="none">%s</g></svg>')
# dois desenhos que a familia da v5 nao tem (Lucide 1.46.0, mesma grade): upload e rotate-ccw
_EXTRA = {
    "upload": '<path d="M12 3v12"/><path d="m17 8-5-5-5 5"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
}


def ic(nome, cls="ni"):
    if nome in _EXTRA:
        return _RAIZ % (cls, _EXTRA[nome])
    if IC is None:
        return _RAIZ % (cls, '<circle cx="12" cy="12" r="8"/>')
    return IC.svg(nome, cls)


# icones que o JavaScript desenha em tempo de execucao (chips, botoes, recibo)
ICONES_JS = ["check", "x", "circle-x", "circle-minus", "circle-dashed", "circle-help", "circle-check", "history", "download",
             "id-card", "gauge", "file-text", "external-link", "chevron-right", "chevron-down", "square-pen", "rotate-ccw",
             "search", "list-checks", "building-2", "audio-lines", "users", "calendar-clock", "plus", "compass",
             "message-circle", "arrow-up", "upload", "database", "mail", "briefcase", "sliders-horizontal"]

PALETA = ("#4F46A5", "#0F6E78", "#7C4A1E", "#5B3F8C", "#2F5D8A", "#5E5E1C")
PARADAS = {"GRUPO", "BANCO", "HOSPITAL", "CARTAO", "S/A", "SA", "LTDA", "LTDA.", "BRASIL"}


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")


def monograma(nome):
    """(letra, cor) de uma conta: a MESMA regra de logos_v5.monograma, sem o cache."""
    base = _sem_acento(nome).upper().strip()
    toks = [t for t in re.split(r"[\s\-/]+", base) if t and t not in PARADAS] or [base]
    letra = next((ch for ch in toks[0] if ch.isalnum()), "")
    cor = PALETA[int(hashlib.sha1(base.encode("utf-8")).hexdigest(), 16) % len(PALETA)]
    return {"letter": letra, "color": cor}


DOC = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="only light">
<title>Orbita CRM</title>
<style>%(fontes)s%(css)s</style>
</head>
<body>
<div class="app">
%(lado)s
<div class="folha">
%(barra)s
<main class="mn">
%(vistas)s
</main>
</div>
</div>
%(gavetas)s
<script>%(js)s</script>
</body>
</html>"""


def nucleo_js():
    """agent/core.mjs + eval/score.mjs + agent/explore.mjs TAL COMO ESTAO, para a pagina rodar as mesmas
    regras da linha de comando e do servidor: saem so as linhas de import e a palavra export; o corpo
    devolve os nomes exportados (o JS os le como CORE.prepareRun, CORE.scoreCase, CORE.answerQuestion...)."""
    partes, nomes = [], []
    for rel in (("agent", "core.mjs"), ("eval", "score.mjs"), ("agent", "explore.mjs")):
        with open(os.path.join(CAPSTONE, *rel), encoding="utf-8") as fp:
            src = fp.read()
        src = re.sub(r"^import .*?;[ \t]*$", "", src, flags=re.M)
        nomes += re.findall(r"^export (?:async )?(?:function|const|let) (\w+)", src, re.M)
        src = re.sub(r"^export (?=(?:async )?(?:function|const|let) )", "", src, flags=re.M)
        assert not re.search(r"^\s*export\b", src, re.M), "%s: export que o render nao sabe tirar" % "/".join(rel)
        partes.append("// ---- %s, embedded verbatim by render_capstone.py\n%s" % ("/".join(rel), src))
    return "\n".join(partes) + "\nreturn {%s};" % ", ".join(nomes), nomes


def montar():
    with open(FOTO, encoding="utf-8") as fp:
        foto = json.load(fp)
    foto["monos"] = {c["name"]: monograma(c["name"]) for c in foto["clients"]}
    core, nomes = nucleo_js()
    js = (JSM.JS.replace("__CORE__", core)
          .replace("__FOTO__", json.dumps(foto, ensure_ascii=False).replace("</", "<\\/"))
          .replace("__ICO__", json.dumps({n: ic(n) for n in ICONES_JS}, ensure_ascii=False).replace("</", "<\\/")))
    return DOC % {
        "fontes": FT.CSS if FT else "",
        "css": CS.CSS,
        "lado": VC.lateral(ic),
        "barra": VC.barra(ic),
        "vistas": VC.vistas(foto, ic),
        "gavetas": VC.gavetas(ic),
        "js": js,
    }, foto, nomes


def main():
    doc, foto, nomes = montar()
    assert "__FOTO__" not in doc and "__ICO__" not in doc and "__CORE__" not in doc
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as fp:
        fp.write(doc)
    res = foto.get("eval_results") or {}
    placar = ", ".join("%s %s/%s" % (k, v["passed"], v["total"]) for k, v in (res.get("labels") or {}).items()) or "sem arquivo"
    print("gerado: %s (%.0f KB) · %d clientes · %d oportunidades · %d reunioes · nucleo do kit embutido (%d funcoes) · eval %s"
          % (SAIDA, len(doc.encode("utf-8")) / 1024.0, len(foto["clients"]), len(foto["opportunities"]), len(foto["meetings"]), len(nomes), placar))


if __name__ == "__main__":
    main()
