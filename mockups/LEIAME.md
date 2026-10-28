# Orbita CRM v5: o mockup do capstone (Product Faculty)

**Arquivo:** `mockup-call-to-crm_2026-10-28.html` (≈900 KB, abre do disco, sem rede). A v3 (`mockup-call-to-crm_2026-10-27.html`, Teams e 8 campos) fica ao lado, intacta.
**Gerado por:** `dados/render_capstone.py` (depois de `dados/coleta.py`); o nome da saída mora em `dados/saida.py`.
**Portão:** `python dados/qa_capstone.py` (sai 0 só com os cinco passos verdes).
**Agente ao vivo:** `node server.mjs`, com `ANTHROPIC_API_KEY` em `capstone/.env`.
**Transcrições para soltar:** `capstone/samples/` (onze conversas em sete formatos; o `README.md` de lá diz o que cada uma mostra).
**Kit:** a pasta-mãe, `capstone/` (esquema, dados, políticas, núcleo, Explore, pipeline, eval). **Foto do kit:** reunião mais recente em 06/11/2026.
**Design:** `DESIGN.md`, ao lado (herda o SalesOps v5).

Nunca editar o `.html` à mão. Ele é 100% gerado.

---

## O que esta peça é

O CRM da **Orbita CRM** (empresa fictícia que vende CRM) com o agente dentro. A ideia é a de um CRM que deixa de ser formulário: ele **absorve conversas de qualquer canal** (transcrição de reunião de qualquer notetaker, exportação do WhatsApp; e-mail, Telegram e Messenger depois), **atribui cada uma à oportunidade certa** (ou propõe uma nova) e atualiza os campos com a citação de cada valor. A vendedora decide o que é escrito, campo a campo ou por permissão.

O **núcleo do kit** (`agent/core.mjs`, `eval/score.mjs` e `agent/explore.mjs`) entra na página **tal como está**: o render tira só `import` e `export`. Leitura dos formatos, atribuição, pré-checagens, validador, escrita, scorer e respostas do Explore são o mesmo código da linha de comando e do servidor.

**Fora de escopo, e não construído:** briefing pré-reunião, recomendação de solução, propostas e preços, edição de contatos, painel do gestor.

---

## O que mudou da v4 para a v5 (e por quê)

| Pedido | O que a peça faz agora |
|---|---|
| Um **Explore** como no outro mockup, para perguntar sobre as oportunidades | Explore é o primeiro item da lateral: saudação, caixa de pergunta, perguntas sugeridas do pipeline, e a resposta no pacote da v5 (veredito, achados com fonte, "Not settled yet", no máximo dois botões). Sem servidor, responde por regras sobre o CRM; com o servidor e a chave, o Claude responde (`/api/explore`), com o mesmo controle de acesso. O grupo **Chat** da lateral guarda as conversas. |
| Meetings: tirar informação, a faixa no topo, e adicionar a transcrição logo abaixo de "Select your opportunity" | A faixa tem só "meetings of yours" e "CRM updates waiting for your review". Logo abaixo, **Add a meeting**: Select your opportunity (detectar, uma das suas, ou nova), Upload a file ou Paste text, e o rascunho com o formato lido e a atribuição com o motivo. |
| Procurar nas oportunidades do CRM e **criar a oportunidade** quando não houver | A atribuição usa os contatos que falam, o nome do cliente no título ou no arquivo, o domínio e as menções. Sem oportunidade aberta, o rascunho propõe um cliente e uma oportunidade novos (com os contatos da conversa), criados conforme a permissão: pedindo aprovação (padrão), na hora, ou nunca. |
| Não precisa da pasta do Granola | O Granola saiu de Meetings e virou um conector opcional em Settings › Sources (plano Business, chave no servidor). O caminho principal é soltar ou colar a transcrição. |
| Clients: separar melhor um cliente do outro | Um **cartão por cliente**, separados como na Carteira do SalesOps, com as oportunidades dentro. |
| Tirar Activity da lateral; Settings com autorização em três níveis, como na Anthropic, e prática para teste ao vivo | Settings tem sete abas. **Permissions**: por campo, **Always allow / Needs approval / Never**, mais a regra para oportunidades novas e as regras fixas. **Agent**: conexão, modelo (Sonnet, Haiku, Opus 5.5) e esforço. **Sources**, **Team**, **Activity log** (a antiga Activity), **Quality checks**, **Data**. |
| Nada de "Call-to-CRM agent", "mock references", "Granola demo notes" | Removidos da tela (o portão procura essas palavras). O estado do agente é uma pílula: o modelo, ou "offline · sample transcripts only". |
| Qualificação otimizada | **MEDDPICC** (Metrics, Economic buyer, Decision criteria, Decision process, Paper process, Pain, Champion, Competition): oito campos, a faixa de letras na revisão, no funil, nos clientes e na gaveta, e "Ask next" com a pergunta da lacuna de maior alavanca. |
| Transcrições compatíveis para soltar | `capstone/samples/`: Teams e Zoom (.vtt), SRT, Otter, linhas com hora, texto simples e WhatsApp. |

---

## Como abrir e como demonstrar (o roteiro de 90 s)

1. Abra `mockup-call-to-crm_2026-10-28.html` no Edge ou no Chrome. Entra no **Explore** como **Ana Ribeiro**. Pergunte "What's the status of Atlas Manufacturing?" ou clique numa sugestão.
2. **Meetings**: a faixa diz 0 e 0. Deixe "Detect it from the transcript" e solte `samples/acme-logistics_discovery-call.vtt`. O rascunho diz "read as WebVTT · 48 lines" e "Acme Logistics · Sales CRM rollout · Marina Lopes is a contact at Acme Logistics". **Prepare CRM update**.
3. **Review**: 22 campos em seis grupos; os da conversa já escritos (Always allow, com Undo); a faixa MEDDPICC 8/8. Clique numa citação: a transcrição abre na linha. **Approve 8 in Qualification**, **Edit** em Pain, **Reject** em um campo, **Submit to CRM**. Abra o registro: Acme está em Solution.
4. Solte `samples/delta-pharma_intro-call.vtt`: **New opportunity · Delta Pharma**, com a Livia Prado como contato. Na revisão, **Approve creation** e Submit: a Delta Pharma aparece em Clients e em Opportunities (New Lead).
5. Solte `samples/WhatsApp Chat with Henrique Prado.txt`: um chat, atribuído pelo contato, que leva a Solaris de Negotiation a **Contract**.
6. Extras: Nimbus (contradição: Keep), Verde POS (gravação cortada: bloqueada), Atlas (a etapa não muda; "one million" ignorado), Pampa (vozes sem nome: nenhum economic buyer), Horizonte como Ana (sem acesso, nada mostrado). Em **Settings › Permissions**, ponha Budget em Never e Next step em Always allow e solte a Acme de novo.

### Ao vivo (o Claude lendo qualquer transcrição)

```powershell
# uma vez: a chave fica fora do código, num arquivo que nunca entra na entrega
Set-Content ..\.env "ANTHROPIC_API_KEY=sk-ant-..."
cd ..; npm install; cd mockups
node server.mjs                       # agente ao vivo (ORBITA_MODEL, padrão claude-sonnet-5-5)
node server.mjs --mock                # servidor sem chamar o modelo (só as transcrições de exemplo); o portão usa este
node server.mjs --granola-live        # + o conector opcional do Granola (GRANOLA_API_KEY e GRANOLA_FOLDER)
```

Abra `http://localhost:8787/`. A pílula do topo passa a mostrar o modelo; **Settings › Agent** escolhe o modelo e o esforço. Qualquer transcrição ou chat que você soltar ou colar é lido pelo Claude, e o Explore passa a responder com ele.

O eval **ao vivo** e a comparação de modelos são do kit, na linha de comando:

```powershell
cd ..
node agent/pipeline.mjs --all --model claude-sonnet-5-5
node agent/pipeline.mjs --all --model claude-haiku-5-5
node agent/pipeline.mjs --all --model claude-opus-5-5
node eval/run_eval.mjs                # eval/results.md + eval/results.json (placar por modelo)
cd mockups; python dados/coleta.py; python dados/render_capstone.py   # leva o placar para Quality checks
```

---

## As telas

| Lateral | O que mostra |
|---|---|
| **Explore** | Saudação, pergunta, sugestões do pipeline; a conversa com veredito, achados, fontes e "Not settled yet". |
| **Meetings** | A faixa (reuniões suas, atualizações esperando revisão), **Add a meeting** (Select your opportunity, arquivo ou texto, rascunho com a atribuição) e a tabela das suas reuniões. |
| **Review** | Aberta a partir da reunião: cabeçalho com MEDDPICC, o cartão da oportunidade nova quando houver, a tabela por grupo (Always allow já escrito, com Undo), as notas e o Submit. Bloqueada: o motivo e a saída. |
| **Opportunities** | Funil por etapa com a faixa MEDDPICC em cada linha; gaveta do registro. |
| **Clients** | Um cartão por cliente com as suas oportunidades; gaveta do cliente. |
| **Chat** | New chat e as conversas recentes do Explore. |
| **Settings** | Permissions, Agent, Sources, Team, Activity log, Quality checks, Data. |

---

## Decisões registradas

- **Interface em inglês.** O kit, a PRD, as reuniões e a banca são em inglês; o registro desta pasta é em português.
- **Um núcleo, três hospedeiros.** `agent/core.mjs`, `eval/score.mjs` e `agent/explore.mjs` são puros: a CLI, o servidor e a página rodam os mesmos arquivos.
- **Nada escreve no CRM fora de `applyApprovedFields`**, e só o que a vendedora aprovou ou deixou em Always allow. Contradição com valor aprovado espera sempre a decisão dela. A criação de cliente e oportunidade passa pela mesma função.
- **Always allow tem Undo**: o valor anterior volta, e o log guarda `crm_write_reverted`.
- **Offline, só as transcrições de exemplo têm resultado salvo** (reconhecidas pelo texto falado, qualquer que seja o formato). Conversa nova pede o servidor com a chave; a página diz isso no aviso, não em rótulo permanente.
- **Completude**: com horário marcado (Granola), bloqueia quando a gravação cobre menos de 60% e termina no meio da frase; arquivo sem horário, quando termina no meio da frase. Chat nunca é "cortado". A vendedora pode liberar ("the meeting ended there").
- **Acesso negado** esconde o nome e o id da oportunidade já no rascunho, e em todo o resto.
- **A data de referência é a da foto** (06/11/2026); a trilha usa o relógio do navegador.
- **Ao trocar de vista, a página volta ao topo** e o título nunca fica embaixo da barra fixa.
- **As gavetas fecham pelo ×, pelo clique fora e pelo Esc**, e cada caminho devolve a rota da lista.

---

## O que o portão confere (`python dados/qa_capstone.py`)

1. **Coleta e regeração**: `coleta.py` congela o kit em `dados/foto.json` e roda `pipeline.mjs --all --mock` + `run_eval.mjs`; `render_capstone.py` monta o HTML com o núcleo embutido.
2. **Sonda** (`sonda_capstone.py`, Edge headless, 1440 e 1280): os aceites pelo caminho da vendedora (cada arquivo de `capstone/samples/` solto no campo de arquivo ou colado), com `eval/expected_results.json`, a semente e o esquema como oráculo, mais o contrato da pele e o contraste real de todo texto visível.
3. **Servidor**: sobe `server.mjs --mock` numa porta livre e faz o laço pela porta HTTP (atualização pelo pipeline do kit, oportunidade nova, acesso negado decidido na página, `/api/explore` com o controle de acesso no servidor, conversa nova recusada sem chave).
4. **Detector** de antipadrões do impeccable, com dois achados conhecidos (motivo no `DESIGN.md`).
5. **Documentação**: este LEIAME cita o arquivo gerado e os comandos.

| Aceite | O que a sonda prova |
|---|---|
| A0 | Explore: saudação, sugestões respondidas, status com fonte e "Not settled yet", follow-ups vencidos = CRM, empresa desconhecida, nada sem acesso, chat na lateral, nunca escreve |
| A1 | Meetings + Acme (.vtt): a faixa, o cartão logo abaixo, Select your opportunity acima da entrada, formato e atribuição com motivo, 22 campos, Always allow escrito na hora e o resto só no Submit, MEDDPICC, aprovação por seção, cliente e oportunidade gravados, funil |
| A2–A4 | Verde (.txt), Nimbus (Otter: contradição e Keep), Verde POS (cortada: bloqueada e "ended there") |
| A5 | Delta Pharma: cliente e oportunidade novos só depois da decisão, com o contato, e o cartão em Clients |
| A6–A11 | Atlas (.srt), Cedro colado (edição e activity log), Horizonte (acesso), Lumen (editores), Pampa (vozes sem nome), WhatsApp (Negotiation → Contract) |
| A12 | a escolha da vendedora vence a detecção; New opportunity pede o nome; offline, conversa nova vira aviso |
| P1 | Permissões: três níveis, um controle por campo, padrões do esquema, Never, Always allow com Undo, grupo inteiro, restaurar, criação Never e Always allow |
| S1–S2 | Settings e as rotas antigas; Quality checks |
| F1–F3 | Funil com MEDDPICC, gavetas, Clients em cartões separados (o vão entre cartões é medido) |
| C0–C6 | título abaixo da barra, nenhum jargão de protótipo, reset que mantém os ajustes, os formatos de samples/, a transcrição, a pele, o contraste |

Para tirar um print de uma cena: `python dados/sonda_capstone.py --foto clients` (cenas em `CENAS`, dentro do script; `--largura 1280`, `--saida <png>`).

---

## Arquivos

```
mockups/
  mockup-call-to-crm_2026-10-28.html   gerado (v5)
  mockup-call-to-crm_2026-10-27.html   v3, mantido como estava
  server.mjs                           agente ao vivo (runs e Explore); usa o pipeline e o núcleo do kit
  LEIAME.md · DESIGN.md
  dados/
    coleta.py           congela o kit em foto.json (+ eval/results.json do scorer)
    foto.json           a foto (gerada)
    saida.py            o nome do HTML gerado, num lugar só
    capstone_css.py     a folha de estilo, tokens da v5 no topo
    capstone_js.py      store, entrada de conversas, rodada, Explore, vistas, gavetas, Settings
    vistas_capstone.py  casca e esqueleto das vistas
    render_capstone.py  monta o HTML (fontes e ícones da v5; núcleo do kit embutido)
    sonda_capstone.py   a sonda (aceites + contrato) e as cenas de print
    qa_capstone.py      o portão
```
