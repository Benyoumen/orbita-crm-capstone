---
name: Orbita CRM (capstone)
description: O CRM da Orbita com o agente dentro (v5) - qualquer conversa (transcrição ou chat) até o CRM, na pele do SalesOps v5 ("folha sobre a mesa"), com o Explore, a revisão agrupada com MEDDPICC, as permissões por campo, o funil por etapa, os clientes em cartões e as gavetas de registro.
colors:
  mesa: "#F5F5F5"
  folha: "#EFEFF0"
  surface: "#FFFFFF"
  surface-2: "#FAFAFA"
  ink: "#0A0A0A"
  text-primary: "rgba(10,10,10,.85)"
  text-secondary: "rgba(10,10,10,.75)"
  text-tertiary: "rgba(10,10,10,.60)"
  text-inactive: "rgba(10,10,10,.42)"
  line-card: "rgba(10,10,10,.09)"
  line: "rgba(10,10,10,.08)"
  line-soft: "rgba(10,10,10,.06)"
  line-control: "rgba(10,10,10,.14)"
  line-strong: "rgba(10,10,10,.22)"
  action: "#171717"
  action-hover: "#2E2E2E"
  on-action: "#FFFFFF"
  signal: "#FF0066"
  dk: "#0A0A0A"
  dk-hot: "#FF4D8D"
  dk-link: "#FF7DAA"
  success: "#2F6B3A"
  success-bg: "#E5F4EA"
  success-dot: "#22A35A"
  warning: "#7A5B14"
  warning-bg: "#F8EED6"
  warning-dot: "#C9951E"
  danger: "#A0302A"
  danger-bg: "#FBEAE8"
  danger-dot: "#D15A4A"
  info: "#1E4B99"
  info-bg: "#E8F0FE"
  neutral: "#52525B"
  neutral-bg: "#F3F3F3"
  teams: "#3B4A8C"
  teams-bg: "#ECEEF8"
  mono-1: "#4F46A5"
  mono-2: "#0F6E78"
  mono-3: "#7C4A1E"
  mono-4: "#5B3F8C"
  mono-5: "#2F5D8A"
  mono-6: "#5E5E1C"
typography:
  scale:
    xxs: "11px"
    xs: "12px"
    sm: "13px"
    base: "15px"
    lg: "17px"
    h2: "24px"
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: "31px"
    letterSpacing: "-0.0125em"
  conversation:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: "22px"
  section:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: "20px"
  reading:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 425
    lineHeight: "24px"
  ui:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 425
    lineHeight: "18px"
  meta:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 425
    lineHeight: "16px"
  chip:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: "14px"
  stamp:
    fontFamily: "DM Mono, ui-monospace, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "16px"
rounded:
  control: "6px"
  chip: "5px"
  field: "8px"
  card: "10px"
  sheet: "12px"
spacing:
  gap: "8px"
  bar: "52px"
  nav: "228px"
  page-x: "24px"
---

# Orbita CRM · registro de design (v5)

Esta peça herda o sistema de design do **SalesOps v5** (`../../quasar/premissas/agentes_de_vendas/agent_spec/R3/agent-spec/sales/ux-ui/mockup/v5/DESIGN.md`) palavra por palavra: mesa, folha e cartão; tinta em preto com alfa; um preto que age; magenta só como sinal (marca e contador da lateral); estado em chip pastel; banner escuro com brilho só na faixa de números e na identidade do registro; Inter 425/500 com a escala do app Lightfield e DM Mono só no carimbo de hora; nenhuma sombra em repouso. O que está abaixo é o que esta peça **acrescenta**, e por quê. As regras de densidade são as da skill design-operacional (rótulo antes do número, fato único, dois botões, coluna constante é ruído, nada acinzentado, três caminhos de fechar).

## A arquitetura de informação

Lateral: **Explore** no topo (como no SalesOps v5), o grupo **Sales** (Meetings · Opportunities · Clients), o grupo **Chat** (New chat e as quatro conversas mais recentes) e, no rodapé, **Settings**. Activity e Agent saíram da lateral e viraram abas de Settings: são ferramentas de quem configura, não telas do dia a dia. A Review abre a partir da reunião (Meetings fica aceso). O registro da oportunidade é uma **gaveta**, não um lugar.

A barra do topo tem só o estado do agente ("Agent · Claude Sonnet 5.5", ou "offline · sample transcripts only") e o avatar. O estado é um botão que abre Settings › Agent. Nenhum vocabulário de protótipo na tela (o portão procura "Call-to-CRM", "mock", "reference answers" e "demo notes").

## Explore

O padrão do Explore da v5, numa coluna de leitura de 760px: a saudação pelo primeiro nome (24/500), a caixa de pergunta (folha de 12px de canto, campo de três linhas, o chip da fonte "Your CRM" e o envio que vira preto quando há texto) e, embaixo, **From your pipeline**: até quatro perguntas calculadas do CRM (o follow-up mais vencido, o que espera revisão, a qualificação mais rasa, os follow-ups da semana), uma linha cada, com o monograma e o "quando" à direita.

A resposta segue o pacote da v5: o veredito numa frase, os achados numerados com a fonte em sobrescrito, **"Not settled yet"** específico da resposta (as letras do MEDDPICC que faltam e a próxima pergunta), as fontes numeradas sob um fio, no máximo dois botões que passam pelas portas que já existem (a gaveta da oportunidade, a revisão) e, em 11px terciária, quem respondeu ("answered from your CRM data", ou o modelo). Nada escreve a partir do balão. Empresa desconhecida: a frase honesta e as sugestões.

## Meetings: a faixa, e logo abaixo a entrada

A faixa escura com **duas** contas, rótulo embaixo do número: "meetings of yours" e "CRM updates waiting for your review" (em magenta-claro quando há). Logo abaixo, o cartão **Add a meeting**:

1. **Select your opportunity**: um select com "Detect it from the transcript" (padrão), as oportunidades abertas por cliente (optgroup) e "New opportunity…". A frase embaixo diz o efeito da escolha.
2. Dois segmentos, **Upload a file · Paste text**: a zona tracejada aceita .vtt, .srt, .txt e a exportação do WhatsApp; o colar é um textarea de nove linhas com o formato no placeholder.
3. O **rascunho**, numa superfície `--surface-2` com fio: a linha do arquivo (como foi lido, linhas, falantes, duração), o **cartão de atribuição** (ícone em verde para a oportunidade encontrada, azul para oportunidade nova, vermelho para acesso negado, âmbar para escolha pendente, sempre com o motivo em 12px), título e data, e os dois botões: **Prepare CRM update** (preto) e Discard.

Oportunidade nova: dois campos (Client, com as empresas do CRM como sugestão; Opportunity name) e a frase do que acontece conforme a permissão. A tabela "Your meetings" vem depois, com no máximo um botão por linha.

## A superfície central: a revisão agrupada

Uma linha por campo, cinco colunas (Field · Current value · Proposed value · Evidence · Decision), um bloco por grupo do esquema. O cabeçalho ganha a **faixa MEDDPICC**: oito letras de 20px (cheia em tinta quando o CRM já tem o elemento, azul de informação quando esta conversa o propõe, vazada quando falta), "6/8" e a frase "Still unknown after this conversation: … Ask next: …".

Campos em **Always allow** já chegam escritos: fundo `--surface-2`, chips "Always allow" e "Written", e o link **Undo** no lugar dos botões. Numa oportunidade nova que precisa de aprovação, eles dizem "written with the new opportunity". O cartão **New client and opportunity** vem antes da tabela: cliente, nome, dono e etapa, contatos que vieram da conversa, e os dois botões **Approve creation · Reject**; o Submit espera essa decisão.

As linhas quietas (no evidence, unchanged, off) recolhem numa frase por grupo; "Approve N in <grupo>" grava uma decisão por campo. A linha contradictory mantém o fio interno de 3px. Editor por tipo: textarea, número, mês, data, roster, etapas, chips de departamento; valor inválido não fecha o editor.

## Opportunities: o funil por etapa (o padrão do Forecast d4)

Chips com contagem por etapa, busca, dono (só para quem lê tudo) e ordenação (follow-up, valor, atualização recente, **qualificação mais rasa**). Uma seção por etapa empilhada na ordem do funil, com marcador, contagem e soma. A linha ganhou a **faixa MEDDPICC pequena** (oito letras de 14px e "3/8") na coluna de atualização. A faixa escura troca "awaiting review" por "with fewer than 4 of 8 MEDDPICC elements known".

## As gavetas de registro

640px à direita. A da oportunidade: a faixa escura de quatro fatos, o aviso de atualização pendente, **Qualification · MEDDPICC** primeiro (a faixa grande, até três perguntas "Ask next" por alavanca, os oito campos com a letra num quadrado cinza), os outros grupos, as reuniões e o History (com "undone" quando o Undo foi usado). A do cliente: perfil, contatos, oportunidades, reuniões. As duas fecham pelo ×, pelo clique fora e pelo Esc.

## Clients: um cartão por cliente

O padrão da Carteira do SalesOps: **cartões separados** (12px entre eles, fio e canto de cartão próprios), em vez de uma tabela contínua. Cabeçalho do cartão: monograma de 32px, o nome em 17/500, os fatos em etiquetas de fio (setor, sede, funcionários, solução atual), à direita "N open opportunities · USD" e contatos e última reunião, e **Client details**. Embaixo, uma linha por oportunidade em grid: nome e id · etapa · valor e fechamento · dono · follow-up · MEDDPICC · Details. A barra acima tem a busca e a ordenação (nome, pipeline aberto, última reunião). A sonda mede o vão entre cartões e o fio de cada um.

## Settings

Sete abas (Permissions · Agent · Sources · Team · Activity log · Quality checks · Data), o mesmo segmento da v5.

**Permissions** segue o padrão das permissões de ferramenta da Anthropic: uma legenda de três colunas (**Always allow** com ponto verde, **Needs approval** com ponto neutro, **Never** com ponto vazado, cada um com a frase do efeito) e, por campo, um controle segmentado de três opções (o ativo em superfície branca com fio; "Always allow" ativo em tinta verde). A linha de grupo tem "Set all". Depois, **New opportunities** com o mesmo controle e a frase do efeito, e **Always true, whatever you choose** com as regras que nenhuma permissão muda.

**Agent**: a conexão com o ponto de estado e, quando o servidor não está no ar, o comando exato; o modelo em três opções (com acerto e custo por reunião quando o eval ao vivo existe) e o esforço em três segmentos. **Sources**: uma linha por canal (ícone em quadrado cinza, nome, como usar, chip On / Not connected / Later). **Activity log**: o feed de antes. **Quality checks**: o propósito, as conversas de teste, as checagens de escrita, o placar por modelo.

## Chips desta peça

Além dos pares da v5: `proposed` em informação, `contradictory` em atenção, `unchanged` em neutro, `no evidence` e `off` tracejados; `Always allow` e `Written` em concluído, `Undone` e `Not written` em neutro; `Awaiting review` em atenção, `Blocked` em perigo, `Rejected` em neutro, `Approved`, `Edited and approved` e `Written automatically` em concluído; etapa em neutro; `On` em concluído, `Not connected` e `Later` tracejados.

## Exceções deliberadas (o portão as conhece)

1. **Inter embutida** em `data:` (InterVariable 4.1, de `fonte_v5.py`): o detector lê o `@font-face` como fonte repetida.
2. **Tamanhos em tokens**: toda fonte sai de `--fs-*`; o detector só enxerga os literais do monograma e das letras do MEDDPICC e acusa hierarquia rasa. A hierarquia real está na escala do frontmatter.
