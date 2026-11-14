# Prompt candidate (not promoted)

Optimizer: claude-sonnet-5-5 · cost USD 0.1802 · 6 failing runs as input

Length 29156 -> 30485 chars (+1329); 2 original lines changed or removed; {{run_input}} untouched in the user message.

## Reasoning

- Failures are Haiku-only and vary between runs; I made minimal clarifying edits to the system prompt and left the rest unchanged.
- decision_criteria (T9, twice): Haiku listed only some requirements and skipped the day-one must-do capabilities. Added a rule to include every requirement the customer states as a must or day-one need (capabilities, integrations, compliance), within the word limit.
- integrations (T1): Haiku proposed a partial list, missing Orion ERP. Added a rule to list every named system the customer says the CRM connects to or that data must flow to, including systems named elsewhere in the conversation, not just the first one.
- objection (T10): Haiku picked minor concerns and missed the main blocker (no signal, so the tool must work offline). Added a rule to cover all customer concerns, putting the main blocker first, and to prefer the one the customer calls the problem or main worry.
- decision_process (T5): Haiku turned a casual remark (sharing material with a director) into a decision process. Added a clarification that forwarding material is not a decision process, which needs evaluation or approval steps described by the customer.
- paper_process (T11): Haiku omitted the signature routing (procurement then signing). Added a clarification that a stated routing of the contract through procurement and who signs counts as paper process even in a chat. The T10 and T1 oracles look reasonable; T10 relies on an unattributed speaker for facts, which is allowed.
- Output contract, JSON examples, field names, statuses and {{run_input}} are unchanged.
