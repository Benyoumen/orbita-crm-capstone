// Explore: questions about the seller's own pipeline, answered from the CRM only (pure; the mockup page
// embeds this file after agent/core.mjs). The live server answers the same questions with Claude and returns
// the same package, so the page draws one shape:
//   { kind, verdict, findings: [{ text, src: [n] }], open, sources: [text], actions: [{ label, opp?, run? }], opportunity_ids }
// Nothing here writes. Only opportunities the user can read are ever looked at.
import { norm, canRead, fieldOf, isClosed, meddpiccOf, clientKeyWord } from "./core.mjs";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DAY_MS = 86400000;
const day = (iso) => { const d = new Date(String(iso).slice(0, 10) + "T12:00:00Z"); return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; };
const daysFrom = (iso, now) => Math.round((Date.parse(String(iso).slice(0, 10)) - Date.parse(String(now).slice(0, 10))) / DAY_MS);
const money = (n) => (n == null ? "no amount yet" : n >= 1e6 ? `USD ${(n / 1e6).toFixed(1)}M` : `USD ${Math.round(n / 1000)}k`);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
const has = (q, re) => re.test(q);
const inText = (q, w) => !!w && new RegExp(`(^|[^a-z0-9])${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^a-z0-9]|$)`).test(q);

/** What Explore may look at for this user: open opportunities they can read, their clients, runs and writes. */
export function exploreContext({ crm, team, user, schema, runs = [], now }) {
  const opps = crm.opportunities.filter((o) => canRead(user, o) && !isClosed(schema, fieldOf(o, "stage").value));
  const ids = new Set(opps.map((o) => o.opportunity_id));
  const clients = crm.clients.filter((c) => opps.some((o) => o.client_id === c.client_id));
  return { schema, team, user, now: String(now).slice(0, 10), opps, clients, runs: runs.filter((r) => !r.opportunity_id || ids.has(r.opportunity_id)) };
}

function view(ctx, o) {
  const c = ctx.clients.find((x) => x.client_id === o.client_id) || { name: o.client_id };
  const v = (k) => fieldOf(o, k).value;
  const due = v("follow_up_due_date");
  return { o, c, label: `${c.name} · ${o.name}`, stage: v("stage"), next: v("next_step"), owner: v("follow_up_owner"), due,
    dueIn: due ? daysFrom(due, ctx.now) : null, m: meddpiccOf(ctx.schema, o) };
}
const dueText = (x) => (x.due == null ? "no due date" : x.dueIn < 0 ? `overdue since ${day(x.due)}` : x.dueIn === 0 ? "due today" : `due ${day(x.due)}`);
const source = (o) => `Orbita CRM · ${o.opportunity_id} · updated ${o.last_updated ? day(o.last_updated) : "never"}`;

function entities(q, ctx) {
  const opps = [];
  for (const o of ctx.opps) if (q.includes(norm(o.opportunity_id)) || (norm(o.name).length > 6 && q.includes(norm(o.name)))) opps.push(o);
  if (opps.length) return opps;
  const hit = ctx.clients.filter((c) => q.includes(norm(c.name)) || inText(q, clientKeyWord(c.name))
    || (c.contacts || []).some((p) => q.includes(norm(p.name))));
  return ctx.opps.filter((o) => hit.some((c) => c.client_id === o.client_id));
}

function pack(kind, verdict, findings, open, sources, actions, opps) {
  return { kind, verdict, findings: findings.filter(Boolean), open: open || null, sources, actions: actions.filter(Boolean).slice(0, 2),
    opportunity_ids: [...new Set((opps || []).map((o) => o.opportunity_id))] };
}

function statusOf(ctx, list) {
  if (list.length > 1) {
    const vs = list.map((o) => view(ctx, o));
    const total = list.reduce((s, o) => s + (o.amount_usd || 0), 0);
    return pack("status", `${vs[0].c.name} has ${plural(list.length, "open opportunity", "open opportunities")}, ${money(total)} in total.`,
      vs.map((x) => ({ text: `${x.o.name}: ${x.stage}, ${money(x.o.amount_usd)}, next step ${dueText(x)}.`, src: [1] })),
      null, [`Orbita CRM · ${list.length} opportunities of ${vs[0].c.name}`], vs.slice(0, 2).map((x) => ({ label: `Open ${x.o.name}`, opp: x.o.opportunity_id })), list);
  }
  const x = view(ctx, list[0]);
  const runs = ctx.runs.filter((r) => r.opportunity_id === x.o.opportunity_id);
  const lastWrite = runs.filter((r) => r.written).sort((a, b) => String(b.at).localeCompare(String(a.at)))[0];
  const pending = runs.find((r) => r.pending > 0);
  const known = x.m.items.filter((i) => i.known).map((i) => i.label);
  const sources = [source(x.o)];
  const ref = (title) => { if (!sources.includes(title)) sources.push(title); return sources.indexOf(title) + 1; };
  const findings = [
    { text: x.next ? `Next step: ${x.next} (${x.owner ? `${x.owner}, ` : ""}${dueText(x)}).` : "No next step is recorded.", src: [1] },
    { text: `Qualification: MEDDPICC ${x.m.known} of ${x.m.total} known${known.length ? ` (${known.join(", ")})` : ""}.`, src: [1] },
    fieldOf(x.o, "budget").value ? { text: `Budget: ${fieldOf(x.o, "budget").value}.`, src: [1] } : null,
    fieldOf(x.o, "competitors").value ? { text: `Competition: ${fieldOf(x.o, "competitors").value}.`, src: [1] } : null,
    lastWrite ? { text: `Last update: ${plural(lastWrite.written, "field", "fields")} written on ${day(lastWrite.at)} from "${lastWrite.title}".`, src: [ref(`Meeting · ${lastWrite.title} · ${day(lastWrite.date || lastWrite.at)}`)] } : null,
    pending ? { text: `An update from "${pending.title}" is waiting for your review (${plural(pending.pending, "field", "fields")}).`, src: [ref(`Meeting · ${pending.title} · ${day(pending.date || pending.at)}`)] } : null,
  ];
  const open = x.m.gaps.length ? `${x.m.gaps.map((g) => g.label).join(", ")} ${x.m.gaps.length === 1 ? "is" : "are"} still unknown. Ask next: "${x.m.gaps[0].ask}"` : null;
  const amount = x.o.amount_usd != null ? `, ${money(x.o.amount_usd)}` : "";
  const close = x.o.close_date ? `, closing ${day(x.o.close_date)}` : "";
  return pack("status", `${x.label} is in ${x.stage}${amount}${close}.`, findings, open, sources,
    [{ label: "Open opportunity", opp: x.o.opportunity_id }, pending ? { label: "Review update", run: pending.run_id } : null], [x.o]);
}

function qualificationOf(ctx, list) {
  if (list.length === 1) {
    const x = view(ctx, list[0]);
    return pack("qualification", `${x.label}: MEDDPICC ${x.m.known} of ${x.m.total} known.`,
      x.m.items.map((i) => ({ text: `${i.letter} · ${i.label}: ${i.known ? i.value : "unknown"}`, src: [1] })),
      x.m.gaps.length ? `Ask next, by leverage: ${x.m.gaps.slice(0, 2).map((g) => `"${g.ask}"`).join(" Then ")}` : "Every element holds a value; coverage does not grade how strong each one is.",
      [source(x.o)], [{ label: "Open opportunity", opp: x.o.opportunity_id }], [x.o]);
  }
  const vs = (list.length ? list : ctx.opps).map((o) => view(ctx, o)).sort((a, b) => a.m.known - b.m.known || (b.o.amount_usd || 0) - (a.o.amount_usd || 0));
  if (!vs.length) return empty(ctx);
  const miss = {};
  for (const x of vs) for (const g of x.m.gaps) miss[g.label] = (miss[g.label] || 0) + 1;
  const top = Object.entries(miss).sort((a, b) => b[1] - a[1])[0];
  return pack("qualification", `${vs[0].label} has the thinnest qualification: MEDDPICC ${vs[0].m.known} of ${vs[0].m.total}.`, [
    ...vs.slice(0, 4).map((x) => ({ text: `${x.label}: ${x.m.known} of ${x.m.total}${x.m.gaps.length ? `, missing ${x.m.gaps.slice(0, 3).map((g) => g.label).join(", ")}` : ""}.`, src: [1] })),
    top ? { text: `Most often missing across your pipeline: ${top[0]} (${top[1]} of ${vs.length} opportunities).`, src: [1] } : null,
  ], "Coverage counts the elements that hold a value in the CRM; it does not grade how strong each one is.",
  [`Orbita CRM · ${plural(vs.length, "open opportunity", "open opportunities")}`], [{ label: `Open ${vs[0].o.name}`, opp: vs[0].o.opportunity_id }], vs.map((x) => x.o));
}

function competitionOf(ctx, list) {
  const vs = (list.length ? list : ctx.opps).map((o) => view(ctx, o));
  const by = {};
  for (const x of vs) for (const n of String(fieldOf(x.o, "competitors").value || "").split(";").map((s) => s.trim()).filter(Boolean)) (by[n] = by[n] || []).push(x);
  const names = Object.keys(by).sort((a, b) => by[b].length - by[a].length);
  if (!names.length) return pack("competition", list.length ? `No competitor is recorded for ${vs[0].label}.` : "No competitor is recorded in your open opportunities.", [], 'Ask: "Who else are you looking at, including keeping today\'s tools?"', [`Orbita CRM · ${plural(vs.length, "open opportunity", "open opportunities")}`], [], vs.map((x) => x.o));
  return pack("competition", `${plural(names.length, "named alternative", "named alternatives")} across ${plural(new Set(names.flatMap((n) => by[n])).size, "opportunity", "opportunities")}: ${names.slice(0, 3).join(", ")}${names.length > 3 ? "…" : ""}.`,
    names.slice(0, 5).map((n) => ({ text: `${n}: ${by[n].map((x) => x.label).join("; ")}.`, src: [1] })),
    `${vs.filter((x) => !fieldOf(x.o, "competitors").value).length} of ${vs.length} opportunities have no competition recorded.`,
    [`Orbita CRM · ${plural(vs.length, "open opportunity", "open opportunities")}`], [], vs.map((x) => x.o));
}

function followUps(ctx, list) {
  const vs = (list.length ? list : ctx.opps).map((o) => view(ctx, o)).filter((x) => x.due != null).sort((a, b) => a.dueIn - b.dueIn);
  const late = vs.filter((x) => x.dueIn < 0), soon = vs.filter((x) => x.dueIn >= 0 && x.dueIn <= 7);
  const none = (list.length ? list : ctx.opps).length - vs.length;
  if (!late.length && !soon.length) return pack("followups", "Nothing is overdue or due in the next 7 days.", [], none ? `${plural(none, "opportunity has", "opportunities have")} no follow-up date.` : null, [`Orbita CRM · follow-up dates on ${day(ctx.now)}`], [], vs.map((x) => x.o));
  return pack("followups", `${plural(late.length, "follow-up is", "follow-ups are")} overdue and ${plural(soon.length, "is", "are")} due in the next 7 days.`,
    [...late, ...soon].slice(0, 6).map((x) => ({ text: `${x.label}: ${x.next || "next step not recorded"} (${dueText(x)}).`, src: [1] })),
    none ? `${plural(none, "opportunity has", "opportunities have")} no follow-up date.` : null,
    [`Orbita CRM · follow-up dates on ${day(ctx.now)}`], [late[0] || soon[0]].map((x) => ({ label: `Open ${x.o.name}`, opp: x.o.opportunity_id })), [...late, ...soon].map((x) => x.o));
}

function byStage(ctx, stage) {
  const sum = (l) => l.reduce((s, o) => s + (o.amount_usd || 0), 0);
  if (stage) {
    const l = ctx.opps.filter((o) => fieldOf(o, "stage").value === stage).map((o) => view(ctx, o));
    return pack("stages", l.length ? `${plural(l.length, "opportunity is", "opportunities are")} in ${stage}, ${money(sum(l.map((x) => x.o)))}.` : `No open opportunity of yours is in ${stage}.`,
      l.map((x) => ({ text: `${x.label}: ${money(x.o.amount_usd)}, next step ${dueText(x)}.`, src: [1] })), null,
      [`Orbita CRM · ${stage}`], l.slice(0, 2).map((x) => ({ label: `Open ${x.o.name}`, opp: x.o.opportunity_id })), l.map((x) => x.o));
  }
  const stages = ctx.schema.stages.filter((s) => !isClosed(ctx.schema, s));
  return pack("stages", `Your open pipeline: ${plural(ctx.opps.length, "opportunity", "opportunities")}, ${money(sum(ctx.opps))}.`,
    stages.map((s) => { const l = ctx.opps.filter((o) => fieldOf(o, "stage").value === s); return l.length ? { text: `${s}: ${l.length} · ${money(sum(l))}.`, src: [1] } : null; }),
    null, [`Orbita CRM · open pipeline on ${day(ctx.now)}`], [], ctx.opps);
}

function biggest(ctx) {
  const l = ctx.opps.filter((o) => o.amount_usd != null).sort((a, b) => b.amount_usd - a.amount_usd).map((o) => view(ctx, o));
  if (!l.length) return empty(ctx);
  return pack("value", `Your biggest open opportunity is ${l[0].label}, ${money(l[0].o.amount_usd)}.`,
    [...l.slice(0, 3).map((x) => ({ text: `${x.label}: ${money(x.o.amount_usd)}, ${x.stage}.`, src: [1] })),
      { text: `Open pipeline in total: ${money(ctx.opps.reduce((s, o) => s + (o.amount_usd || 0), 0))}.`, src: [1] }],
    "Amounts are the seller's own; the agent never writes them.", [`Orbita CRM · open pipeline on ${day(ctx.now)}`],
    [{ label: `Open ${l[0].o.name}`, opp: l[0].o.opportunity_id }], l.map((x) => x.o));
}

function pendingReviews(ctx) {
  const l = ctx.runs.filter((r) => r.pending > 0).sort((a, b) => String(b.at).localeCompare(String(a.at)));
  if (!l.length) return pack("pending", "Nothing is waiting for your review.", [], null, ["Orbita CRM · Meetings"], [], []);
  return pack("pending", `${plural(l.length, "CRM update is", "CRM updates are")} waiting for your review.`,
    l.slice(0, 6).map((r) => ({ text: `${r.label}: ${plural(r.pending, "field", "fields")} from "${r.title}".`, src: [1] })), null,
    ["Orbita CRM · Meetings"], [{ label: "Review update", run: l[0].run_id }], []);
}

function recent(ctx) {
  const l = ctx.runs.filter((r) => r.written || r.created).sort((a, b) => String(b.at).localeCompare(String(a.at)));
  if (!l.length) return pack("recent", "No CRM updates yet. Add a meeting transcript in Meetings and the agent prepares one.", [], null, ["Orbita CRM · Meetings"], [], []);
  return pack("recent", `${plural(l.length, "update has", "updates have")} been written to your CRM.`,
    l.slice(0, 6).map((r) => ({ text: `${day(r.at)} · ${r.label}: ${r.created ? "opportunity created, " : ""}${plural(r.written, "field", "fields")} from "${r.title}".`, src: [1] })),
    null, ["Orbita CRM · Activity"], l[0].opportunity_id ? [{ label: "Open opportunity", opp: l[0].opportunity_id }] : [], []);
}

function empty(ctx) {
  return pack("empty", "You have no open opportunities yet.", [], null, ["Orbita CRM"], [], []);
}

/** The deterministic answer used when no model is connected (and by the eval of the page). */
export function answerQuestion(question, ctx) {
  const q = norm(question);
  if (!q) return pack("none", "Ask about a client, an opportunity or your pipeline.", [], null, [], [], []);
  if (!ctx.opps.length) return empty(ctx);
  const list = entities(q, ctx);
  const stage = ctx.schema.stages.find((s) => !isClosed(ctx.schema, s) && (q.includes(norm(s)) || (s === "Qualified Opportunity" && /\bqualified\b/.test(q))));
  const qual = has(q, /\b(meddpicc|qualif\w*|missing|gaps?|champion|economic buyer|paper process|decision criteria|metrics?|pain|unknown)\b/);
  const comp = has(q, /\b(compet\w*|against|versus|vs|rivals?|alternatives?)\b/);
  const follow = has(q, /\b(overdue|late|behind|follow[- ]?ups?|due|this week|next week|today|tomorrow)\b/);
  if (list.length) {
    if (qual) return qualificationOf(ctx, list);
    if (comp) return competitionOf(ctx, list);
    return statusOf(ctx, list);
  }
  if (has(q, /\b(review|reviews|waiting|pending|awaiting|approve|approval)\b/)) return pendingReviews(ctx);
  if (qual) return qualificationOf(ctx, []);
  if (comp) return competitionOf(ctx, []);
  if (follow) return followUps(ctx, []);
  if (stage) return byStage(ctx, stage);
  if (has(q, /\b(pipeline|funnel|stages?|by stage)\b/)) return byStage(ctx, null);
  if (has(q, /\b(biggest|largest|top|highest|value|amount|worth|total|size)\b/)) return biggest(ctx);
  if (has(q, /\b(changed|changes|updated|recent|lately|created|latest)\b/)) return recent(ctx);
  return pack("none", "I couldn't find a client or an opportunity with that name in your CRM.", [], null,
    [`Orbita CRM · ${plural(ctx.opps.length, "open opportunity", "open opportunities")} of yours`], [], []);
}

/** Up to four questions worth asking now, each answerable from the CRM (the Explore start page). */
export function exploreSuggestions(ctx) {
  const out = [];
  const vs = ctx.opps.map((o) => view(ctx, o));
  const late = vs.filter((x) => x.dueIn != null && x.dueIn < 0).sort((a, b) => a.dueIn - b.dueIn)[0];
  if (late) out.push({ q: `What's the status of ${late.c.name}?`, client: late.c.name, when: "overdue" });
  if (ctx.runs.some((r) => r.pending > 0)) out.push({ q: "What's waiting for my review?", client: null, when: "now" });
  const thin = vs.filter((x) => x !== late).sort((a, b) => a.m.known - b.m.known || (b.o.amount_usd || 0) - (a.o.amount_usd || 0))[0];
  if (thin) out.push({ q: `What's missing to qualify ${thin.c.name}?`, client: thin.c.name, when: `MEDDPICC ${thin.m.known}/${thin.m.total}` });
  const soon = vs.filter((x) => x.dueIn != null && x.dueIn >= 0 && x.dueIn <= 7).length;
  out.push({ q: "Which follow-ups are due this week?", client: null, when: soon ? plural(soon, "due", "due") : "this week" });
  if (out.length < 4) out.push({ q: "Show my pipeline by stage", client: null, when: plural(ctx.opps.length, "deal", "deals") });
  return out.slice(0, 4);
}
