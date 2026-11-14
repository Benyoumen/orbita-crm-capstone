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

Os traces do eval (eval/error_discovery/error_discovery_data/: os 29 registros, a amostra de 15, as notas e
os modos de falha) entram enxutos em `evals`, para a aba Evals da pagina: sem as linhas da transcricao (a
pagina usa as de `transcripts`, pela reuniao do caso) e sem as medidas internas do mapa.

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


def _evals(expected):
    """Os traces da revisao de erros, enxutos: o que a aba Evals mostra e anota. Sem a pasta, uma lista vazia."""
    base = os.path.join(KIT, "eval", "error_discovery", "error_discovery_data")
    if not os.path.isfile(os.path.join(base, "records.json")):
        return {"traces": [], "sample": [], "batches": [], "annotations": [], "reviewed": {}, "labels": {}, "judge_labels": {}, "modes": []}
    def rd(nome, padrao):
        p = os.path.join(base, nome)
        if not os.path.isfile(p):
            return padrao
        with open(p, encoding="utf-8") as fp:
            return json.load(fp)
    mtg = {c["case_id"]: c.get("meeting_id") for c in expected.get("cases", [])}
    keep = ("id", "case_id", "case_name", "proves", "model", "model_short", "client", "opportunity", "stage_before", "seller", "source",
            "chat", "run_status", "source_status", "block_reason", "warnings", "target", "validation_notes", "ignored_out_of_scope", "scorer", "flags")
    traces = []
    for r in rd("records.json", []):
        t = {k: r.get(k) for k in keep}
        t["meeting_id"] = mtg.get(r.get("case_id"))
        u = r.get("usage") or {}
        t["usage"] = {k: u.get(k) for k in ("input_tokens", "output_tokens", "cost_usd")} if u else None
        t["fields"] = [{k: f.get(k) for k in ("field", "group", "record", "status", "current_value", "current_approved", "proposed_value", "evidence", "note")}
                       for f in r.get("fields") or []]
        traces.append(t)
    smp = rd("samples.json", {"ids": [], "batches": []})
    ann = rd("annotations.json", {})
    return {"traces": traces, "sample": smp.get("ids", []), "batches": [{"reason": b.get("reason"), "n": len(b.get("ids", []))} for b in smp.get("batches", [])],
            "annotations": ann.get("annotations", []), "reviewed": ann.get("reviewed", {}), "labels": ann.get("labels", {}), "judge_labels": ann.get("judge_labels", {}),
            "modes": rd("patterns.json", {}).get("modes", [])}


def _prompt_versao():
    """A versao do prompt que as rodadas usaram: o hash do system_prompt.md e das politicas, e o ultimo commit que os tocou."""
    import hashlib
    h = hashlib.sha256()
    for rel in ["agent/system_prompt.md"] + ["policies/" + f for f in sorted(os.listdir(os.path.join(KIT, "policies")))]:
        with open(os.path.join(KIT, rel), "rb") as fp:
            h.update(fp.read())
    try:
        commit = subprocess.run(["git", "log", "-1", "--format=%h %cs", "--", "agent/system_prompt.md", "policies"], cwd=KIT,
                                capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        commit = ""
    return {"sha": h.hexdigest()[:8], "commit": commit}


def _experimentos(expected, results):
    """Uma linha por configuracao rodada sobre o conjunto de testes (modelo, esforco, prompt): testes que passam,
    acerto por campo contra eval/expected_results.json, citacoes que o validador teve de corrigir, custo, latencia e,
    quando eval/judge_results.json existe, o veredito do juiz (valor sustentado pela conversa ou nao)."""
    from datetime import datetime
    from statistics import median
    raiz = os.path.join(KIT, "eval", "outputs")
    if not os.path.isdir(raiz):
        return {"prompt": _prompt_versao(), "rows": [], "judge": None}
    juiz = _rj("eval/judge_results.json") if os.path.isfile(os.path.join(KIT, "eval", "judge_results.json")) else None
    campos = [d["key"] for d in _rj("agent/field_schema.json")["fields"]]
    linhas = []
    for label in sorted(os.listdir(raiz)):
        if label == "mock" or not os.path.isdir(os.path.join(raiz, label)):
            continue
        partes = label.split("@")
        model, esforco, prompt = partes[0], (partes[1] if len(partes) > 1 else ""), (partes[2] if len(partes) > 2 else None)
        res = ((results or {}).get("labels") or {}).get(label) or {}
        falhas = {r["case_id"]: r.get("fails") or [] for r in res.get("rows") or []}
        por_campo = {k: [0, 0, []] for k in campos}  # acertos, conversas, casos errados
        correcoes = citacoes = 0
        segs = []
        casos = 0
        for c in expected["cases"]:
            f = os.path.join(raiz, label, c["case_id"] + ".json")
            if not os.path.isfile(f):
                continue
            with open(f, encoding="utf-8") as fp:
                out = json.load(fp)
            lf = f[:-5] + ".log.json"
            if os.path.isfile(lf):
                with open(lf, encoding="utf-8") as fp:
                    ev = json.load(fp)
                t = {e["action"]: datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) for e in ev if e.get("action") in ("agent_called", "agent_answered")}
                if len(t) == 2:
                    segs.append((t["agent_answered"] - t["agent_called"]).total_seconds())
            if c.get("expected_run_status") == "Blocked" or out.get("run_status") == "Blocked":
                continue  # o bloqueio conta nos testes; campo nao ha
            casos += 1
            got = {x["field"]: x["status"] for x in out.get("fields") or []}
            ruins = {s.split(":", 1)[0].strip() for s in falhas.get(c["case_id"], [])}
            for k in campos:
                ex = (c.get("fields") or {}).get(k) or {"status": "no_evidence"}
                ok = got.get(k, "no_evidence") in (ex.get("status_any") or [ex.get("status")]) and k not in ruins
                por_campo[k][0] += 1 if ok else 0
                por_campo[k][1] += 1
                if not ok:
                    por_campo[k][2].append(c["case_id"])
            correcoes += len(out.get("validation_notes") or [])
            citacoes += sum(len(x.get("evidence") or []) for x in out.get("fields") or [])
        acertos, total = sum(v[0] for v in por_campo.values()), sum(v[1] for v in por_campo.values())
        jl = ((juiz or {}).get("labels") or {}).get(label)
        linhas.append({
            "label": label, "model": model, "effort": esforco or "medium", "prompt": prompt,
            "passed": res.get("passed"), "total": res.get("total"), "cost_per_call": res.get("cost_per_call_usd"),
            "cost_total": (res.get("usage") or {}).get("cost_usd"),
            "latency_med": round(median(segs), 1) if segs else None, "latency_max": round(max(segs), 1) if segs else None,
            "cases": casos, "field_ok": acertos, "field_n": total, "fields": por_campo,
            "fixes": correcoes, "quotes": citacoes,
            "judge": None if not jl else {
                "judged": jl.get("judged", 0), "passed": jl.get("passed", 0),
                "cases": {cid: [{"field": x["field"], "result": x["result"], "critique": x["critique"], "value": x["value"]} for x in v.get("fields", [])]
                          for cid, v in (jl.get("cases") or {}).items()},
            },
        })
    return {"prompt": _prompt_versao(), "rows": linhas, "judge": (juiz or {}).get("judge")}


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
    foto["evals"] = _evals(foto["expected"])
    foto["evals"]["experiments"] = _experimentos(foto["expected"], foto["eval_results"])
    with open(SAIDA, "w", encoding="utf-8") as fp:
        json.dump(foto, fp, ensure_ascii=False, indent=1)
    print("foto: %s (%.0f KB) · %d clientes · %d oportunidades · %d reunioes · %d transcricoes · %d referencias · data da foto %s"
          % (SAIDA, os.path.getsize(SAIDA) / 1024.0, len(foto["clients"]), len(foto["opportunities"]), len(meetings),
             len(transcripts), len(refs), data_da_foto))
    ev = foto["evals"]
    print("  evals: %d traces, amostra de %d, %d notas, %d modos de falha" % (len(ev["traces"]), len(ev["sample"]), len(ev["annotations"]), len(ev["modes"])))
    res = foto["eval_results"]
    if res:
        print("  scorer do kit: " + ", ".join("%s %d/%d" % (k, v["passed"], v["total"]) for k, v in res["labels"].items()))


if __name__ == "__main__":
    main()
