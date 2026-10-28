# Stage rules

Stage list, in order:
`New Lead → Qualified Opportunity → Solution → Proposal → Negotiation → Contract`, then `Closed Won` / `Closed Lost`.

## Exit criteria (all must be evidenced in the conversation to propose the next stage)

| Current stage | Next stage | Exit criteria |
|---|---|---|
| New Lead | Qualified Opportunity | (1) The customer confirms a pain that Orbita's CRM addresses; (2) the customer agrees to a further conversation |
| Qualified Opportunity | Solution | (1) Pain confirmed; (2) economic buyer identified (who decides); (3) timeline stated |
| Solution | Proposal | (1) The customer agrees on a specific solution scope (users, modules, integrations); (2) the customer asks for a proposal |
| Proposal | Negotiation | (1) The economic buyer has received the proposal; (2) the customer raises specific commercial or contractual terms to negotiate |
| Negotiation | Contract | (1) The economic buyer agrees to the terms in the conversation (spoken or written); (2) the contract is requested or sent for signature |

## Rules
- Propose at most **one step forward**. Never propose a backward move.
- Never propose `Closed Won` or `Closed Lost`. Only the seller sets them, manually.
- Enthusiasm or a verbal "yes" is not a criterion. Check each criterion literally, including **who** said it (for example, whether that person is the economic buyer). An unattributed speaker cannot satisfy a criterion that depends on who said it.
- When the criteria are not met, return `stage` as `no_evidence` and use `note` to name the missing criteria. Example: "Qualified Opportunity exit criteria not met: no timeline stated."
- When the criteria are met, the evidence must include a quote for each criterion (up to 3 quotes; pick the strongest).
