# -*- coding: utf-8 -*-
"""Coleta do mockup Orbita CRM (capstone Product Faculty): congela o kit em UM JSON.

    python coleta.py            # grava foto.json a partir do kit (a pasta capstone/, mae de mockups/)
    python coleta.py --sem-node # nao roda o pipeline/eval do kit (so copia os dados)

A foto e o KIT inteiro que a tela precisa: o esquema dos campos, o time e o acesso,
os clientes e as oportunidades (a semente do CRM), as conversas do eval (as notas
sinteticas do Granola normalizadas em data/meetings.json e as exportacoes de chat em
data/channel_meetings.json), o texto de cada transcricao, as respostas de
referencia (o resultado salvo das transcricoes de exemplo, quando o agente esta
offline) e os resultados esperados (o oraculo das verificacoes de qualidade). Nada
e inventado: o que a fonte nao tem aparece como `null`.

NUNCA entra na foto o cache das notas reais do Granola (capstone/.granola-cache/):
a pagina gerada e uma demonstracao com dado sintetico; a pasta real so aparece pelo
servidor, ao vivo.

`data_da_foto` e a data da reuniao mais recente do kit, e nao a data de hoje: os
vencimentos da tela ("overdue") sao medidos contra ela, e a trilha usa o relogio de
verdade do navegador (registra o que a pessoa fez agora).

Com Node no PATH, a coleta tambem roda `pipeline.mjs --all --mock` e `run_eval.mjs`
do kit e congela `eval/results.json`, com o placar de cada rotulo que houver em
eval/outputs/ (mock e, quando rodado, cada modelo ao vivo).
"""
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MOCKUP = os.path.dirname(HERE)
CAPSTONE = os.path.dirname(MOCKUP)
# o kit (dados, politicas, pipeline, eval) mora solto na pasta capstone/, mae de mockups/
KIT = CAPSTONE
SAIDA = os.path.join(HERE, "foto.json")


def _rj(rel):
    with open(os.path.join(KIT, rel), encoding="utf-8") as fp:
        return json.load(fp)


def _rt(rel):
    with open(os.path.join(KIT, rel), encoding="utf-8") as fp:
        return fp.read()


def _eval_node():
    """Roda o pipeline do kit em modo mock e o scorer; devolve o results.json (todos os rotulos)."""
    try:
        for cmd in (["node", "agent/pipeline.mjs", "--all", "--mock"], ["node", "eval/run_eval.mjs"]):
            subprocess.run(cmd, cwd=KIT, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except (OSError, subprocess.CalledProcessError) as exc:
        print("  eval do kit nao rodou (%s); a aba Quality checks mostra so o replay da pagina" % exc)
        return None
    return _rj("eval/results.json")


def main():
    sem_node = "--sem-node" in sys.argv
    if not os.path.isfile(os.path.join(KIT, "agent", "field_schema.json")):
        raise SystemExit("kit nao encontrado em %s (falta agent/field_schema.json)" % KIT)
    # as reunioes do eval: as notas do Granola normalizadas e as conversas exportadas (WhatsApp)
    meetings = _rj("data/meetings.json") + _rj("data/channel_meetings.json")
    transcripts = {m["meeting_id"]: _rt(m["transcript_file"]) for m in meetings if m.get("transcript_file")}
    refs = {}
    for nome in sorted(os.listdir(os.path.join(KIT, "eval", "reference_outputs"))):
        if nome.endswith(".json"):
            o = _rj("eval/reference_outputs/" + nome)
            if o.get("run_status") != "Blocked":
                refs[o["meeting_id"]] = o
    data_da_foto = max(m["start"][:10] for m in meetings)
    foto = {
        "data_da_foto": data_da_foto,
        "kit": os.path.relpath(KIT, MOCKUP).replace("\\", "/"),
        "schema": _rj("agent/field_schema.json"),
        "team": _rj("data/team.json"),
        "clients": _rj("data/clients.json"),
        "opportunities": _rj("data/opportunities.json"),
        "meetings": meetings,
        "transcripts": transcripts,
        "refs": refs,
        "expected": _rj("eval/expected_results.json"),
        "eval_results": None if sem_node else _eval_node(),
    }
    with open(SAIDA, "w", encoding="utf-8") as fp:
        json.dump(foto, fp, ensure_ascii=False, indent=1)
    print("foto: %s (%.0f KB) · %d clientes · %d oportunidades · %d reunioes · %d transcricoes · %d referencias · data da foto %s"
          % (SAIDA, os.path.getsize(SAIDA) / 1024.0, len(foto["clients"]), len(foto["opportunities"]), len(meetings),
             len(transcripts), len(refs), data_da_foto))
    res = foto["eval_results"]
    if res:
        print("  scorer do kit: " + ", ".join("%s %d/%d" % (k, v["passed"], v["total"]) for k, v in res["labels"].items()))


if __name__ == "__main__":
    main()
