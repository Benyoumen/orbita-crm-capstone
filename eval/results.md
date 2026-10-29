# Eval results

Run: 2026-10-28T22:27:39.515Z  
Cases: 11 (eval/expected_results.json); outputs: eval/outputs/<label>/

## Score by model

| Label | Passed | Model calls | Input tokens | Cache read | Cache write | Output tokens | Cost (USD) | Cost per call |
|---|---|---|---|---|---|---|---|---|
| mock | 11/11 | 0 | 0 | 0 | 0 | 0 | - | - |
| claude-haiku-5-5 | 10/11 | 9 | 16,492 | 106,326 | 0 | 48,745 | 0.0271 | 0.0030 |
| claude-opus-5-5 | 11/11 | 9 | 16,492 | 94,512 | 11,814 | 24,492 | 0.6338 | 0.0704 |
| claude-sonnet-5-5 | 11/11 | 9 | 16,492 | 94,512 | 11,814 | 20,591 | 0.2873 | 0.0319 |

Blocked cases (T4, T8) stop in code before any model call, so a full live run makes 9 calls. `mock` replays the reference answers through the same validator: it proves the platform, not the model.

## Cases: mock

| Case | PRD case | Scenario | Result | Issues |
|---|---|---|---|---|
| T1 | 1 | Happy path - complete discovery call | PASS | - |
| T2 | 2 | No evidence - no follow-up date or further meeting agreed | PASS | - |
| T3 | 3 | Contradiction with seller-approved values (short call) | PASS | - |
| T4 | 4 | Unusable source - recording cut off mid-sentence | PASS | - |
| T5 | 4 | New client - a meeting with a company that is not in the CRM | PASS | - |
| T6 | 5 | Stage boundary - 'let's sign' before the decision-maker has the proposal, spoken deal amount, stated budget | PASS | - |
| T7 | 6 | Seller edits a proposal | PASS | - |
| T8 | 7 | Access boundary - seller does not own the opportunity | PASS | - |
| T9 | 8 | Solution fit - scope session with every typed field; scope agreed and proposal requested | PASS | - |
| T10 | 9 | Granola speaker attribution - customer voices without a name | PASS | - |
| T11 | 10 | WhatsApp chat - terms agreed in an exported chat | PASS | - |

## Cases: claude-haiku-5-5

| Case | PRD case | Scenario | Result | Issues |
|---|---|---|---|---|
| T1 | 1 | Happy path - complete discovery call | PASS | - |
| T2 | 2 | No evidence - no follow-up date or further meeting agreed | PASS | - |
| T3 | 3 | Contradiction with seller-approved values (short call) | PASS | - |
| T4 | 4 | Unusable source - recording cut off mid-sentence | PASS | - |
| T5 | 4 | New client - a meeting with a company that is not in the CRM | PASS | - |
| T6 | 5 | Stage boundary - 'let's sign' before the decision-maker has the proposal, spoken deal amount, stated budget | PASS | - |
| T7 | 6 | Seller edits a proposal | PASS | - |
| T8 | 7 | Access boundary - seller does not own the opportunity | PASS | - |
| T9 | 8 | Solution fit - scope session with every typed field; scope agreed and proposal requested | FAIL | decision_criteria: missing key facts [["lead","campaign"],["funnel","enrol"],["WhatsApp"]] |
| T10 | 9 | Granola speaker attribution - customer voices without a name | PASS | - |
| T11 | 10 | WhatsApp chat - terms agreed in an exported chat | PASS | - |

## Cases: claude-opus-5-5

| Case | PRD case | Scenario | Result | Issues |
|---|---|---|---|---|
| T1 | 1 | Happy path - complete discovery call | PASS | - |
| T2 | 2 | No evidence - no follow-up date or further meeting agreed | PASS | - |
| T3 | 3 | Contradiction with seller-approved values (short call) | PASS | - |
| T4 | 4 | Unusable source - recording cut off mid-sentence | PASS | - |
| T5 | 4 | New client - a meeting with a company that is not in the CRM | PASS | - |
| T6 | 5 | Stage boundary - 'let's sign' before the decision-maker has the proposal, spoken deal amount, stated budget | PASS | - |
| T7 | 6 | Seller edits a proposal | PASS | - |
| T8 | 7 | Access boundary - seller does not own the opportunity | PASS | - |
| T9 | 8 | Solution fit - scope session with every typed field; scope agreed and proposal requested | PASS | - |
| T10 | 9 | Granola speaker attribution - customer voices without a name | PASS | - |
| T11 | 10 | WhatsApp chat - terms agreed in an exported chat | PASS | - |

## Cases: claude-sonnet-5-5

| Case | PRD case | Scenario | Result | Issues |
|---|---|---|---|---|
| T1 | 1 | Happy path - complete discovery call | PASS | - |
| T2 | 2 | No evidence - no follow-up date or further meeting agreed | PASS | - |
| T3 | 3 | Contradiction with seller-approved values (short call) | PASS | - |
| T4 | 4 | Unusable source - recording cut off mid-sentence | PASS | - |
| T5 | 4 | New client - a meeting with a company that is not in the CRM | PASS | - |
| T6 | 5 | Stage boundary - 'let's sign' before the decision-maker has the proposal, spoken deal amount, stated budget | PASS | - |
| T7 | 6 | Seller edits a proposal | PASS | - |
| T8 | 7 | Access boundary - seller does not own the opportunity | PASS | - |
| T9 | 8 | Solution fit - scope session with every typed field; scope agreed and proposal requested | PASS | - |
| T10 | 9 | Granola speaker attribution - customer voices without a name | PASS | - |
| T11 | 10 | WhatsApp chat - terms agreed in an exported chat | PASS | - |

## Platform checks (run in the mockup: Agent > Quality checks, and by the mockup gate)

**T7: Seller edits a proposal**
- The CRM receives the seller's edited customer need, not the agent's version
- The activity record keeps both the agent proposal and the seller's final value
- The activity record stores the reviewer (U01) and the decision time
- Each written field records its write result (Succeeded)

**T8: Access boundary - seller does not own the opportunity**
- No opportunity or client data is shown to U01
- The access-denied attempt is written to the activity log
