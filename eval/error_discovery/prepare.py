"""Error discovery, step 2: features per record, a 2D map (PCA), clusters (k-means), outlier flags for the
record header, and the initial sample (cluster representatives + random picks). Creates the empty
annotation, pattern and suggestion files the first time; never overwrites the reviewer's work.

    python eval/error_discovery/prepare.py                  keep the current sample if there is one
    python eval/error_discovery/prepare.py --reset-sample   draw the initial sample again
"""
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "error_discovery_data")
SEED = 7
MODEL_ORDER = {"claude-sonnet-5-5": 0, "claude-opus-5-5": 1, "claude-haiku-5-5": 2, "platform": 3}
STATUSES = ["proposed", "unchanged", "contradictory", "no_evidence"]


def path(name):
    return os.path.join(DATA, name)


def load(name, default=None):
    if not os.path.exists(path(name)):
        return default
    with open(path(name), encoding="utf-8") as f:
        return json.load(f)


def save(name, obj):
    tmp = path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path(name))


def features(r):
    fs = r["fields"]
    count = {s: sum(1 for f in fs if f["status"] == s) for s in STATUSES}
    quotes = [e for f in fs for e in (f.get("evidence") or [])]
    u = r.get("usage") or {}
    return {
        "proposed": count["proposed"],
        "unchanged": count["unchanged"],
        "contradictory": count["contradictory"],
        "no_evidence": count["no_evidence"],
        "quotes": len(quotes),
        "words_per_quote": (sum(len(str(e.get("quote", "")).split()) for e in quotes) / len(quotes)) if quotes else 0.0,
        "validator_fixes": len(r.get("validation_notes") or []),
        "ignored": len(r.get("ignored_out_of_scope") or []),
        "output_tokens": u.get("output_tokens", 0),
        "lines": len(r["lines"]),
        "code_check_failures": len(r["scorer"]["fails"]),
        "blocked": 1 if r["run_status"] == "Blocked" else 0,
        "new_opportunity": 1 if (r.get("target") or {}).get("kind") == "new" else 0,
        "chat": 1 if r.get("chat") else 0,
    }


def kmeans(X, k, rng, iters=60, restarts=12):
    best = None
    for _ in range(restarts):
        centers = [X[rng.integers(len(X))]]
        for _ in range(1, k):  # k-means++
            d = np.min([((X - c) ** 2).sum(1) for c in centers], axis=0)
            p = d / d.sum() if d.sum() > 0 else np.full(len(X), 1 / len(X))
            centers.append(X[rng.choice(len(X), p=p)])
        C = np.array(centers)
        for _ in range(iters):
            lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(2), axis=1)
            newC = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            if np.allclose(newC, C):
                break
            C = newC
        inertia = sum(((X[lab == j] - C[j]) ** 2).sum() for j in range(k))
        if best is None or inertia < best[0]:
            best = (inertia, lab, C)
    return best[1], best[2]


FLAG_FEATURES = [  # (feature, how the header says it)
    ("output_tokens", "{:,} output tokens"),
    ("validator_fixes", "{} validator fix{}"),
    ("no_evidence", "{} fields without evidence"),
    ("proposed", "{} fields proposed"),
    ("quotes", "{} quotes"),
    ("words_per_quote", "{:.0f} words per quote"),
]


def flags_for(r, live):
    out = []
    v = r["features"]
    others = [o["features"] for o in live if o["id"] != r["id"]]
    if not others or r["run_status"] == "Blocked":
        return out
    for key, fmt in FLAG_FEATURES:
        x = v[key]
        below = sum(1 for o in others if o[key] < x) / len(others)
        above = sum(1 for o in others if o[key] > x) / len(others)
        text = fmt.format(x, "" if x == 1 else "es") if "{}" in fmt and fmt.count("{}") == 2 else fmt.format(x)
        if below >= 0.9:
            out.append((below, f"{text} (highest of all)" if below == 1 else f"{text} (more than {below:.0%})"))
        elif above >= 0.9:
            out.append((above, f"{text} (lowest of all)" if above == 1 else f"{text} (fewer than {above:.0%})"))
    return [t for _, t in sorted(out, reverse=True)[:2]]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    records = load("records.json")
    if not records:
        sys.exit("No records: run node eval/error_discovery/build_records.mjs first.")
    for r in records:
        r["features"] = features(r)
    live = [r for r in records if r["run_status"] != "Blocked"]
    for r in records:
        r["flags"] = flags_for(r, live)
    save("records.json", records)

    names = list(records[0]["features"].keys())
    X = np.array([[r["features"][n] for n in names] for r in records], dtype=float)
    sd = X.std(0)
    Z = (X - X.mean(0)) / np.where(sd > 0, sd, 1)
    U, S, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
    P = Z @ Vt[:2].T
    rng = np.random.default_rng(SEED)
    k = max(2, min(7, len(records) // 4))
    lab, C = kmeans(Z, k, rng)

    points = []
    for r, (x, y), c in zip(records, P, lab):
        points.append({"id": r["id"], "x": float(x), "y": float(y), "cluster": int(c), "model": r["model"], "model_short": r["model_short"],
                       "case_id": r["case_id"], "case_name": r["case_name"], "verdict": r["scorer"]["verdict"], "code_check_failures": len(r["scorer"]["fails"])})
    save("graph.json", {"points": points, "k": k, "features": names,
                        "explained": [float(s) for s in (S[:2] ** 2 / (S ** 2).sum())]})

    sample = load("samples.json")
    if sample is None or "--reset-sample" in sys.argv:
        # cluster representatives (about two thirds): the records closest to each centroid, preferring new cases
        reps, seen_cases = [], set()
        for j in range(k):
            members = [i for i in range(len(records)) if lab[i] == j]
            members.sort(key=lambda i: float(((Z[i] - C[j]) ** 2).sum()))
            take = 2 if len(members) >= 5 else 1
            for i in members:
                if take == 0:
                    break
                if records[i]["case_id"] in seen_cases and any(records[m]["case_id"] not in seen_cases for m in members):
                    continue
                reps.append(records[i]["id"])
                seen_cases.add(records[i]["case_id"])
                take -= 1
        # random picks (about a third) from everything else: the clusters do not see every dimension
        pool = [r["id"] for r in records if r["id"] not in reps]
        random.Random(SEED).shuffle(pool)
        n_random = max(3, round(len(reps) * 0.5))
        rand = pool[:n_random]
        order = {r["id"]: (int(r["case_id"][1:]), MODEL_ORDER.get(r["model"], 9)) for r in records}
        ids = sorted(set(reps + rand), key=lambda i: order[i])
        sample = {"ids": ids, "batches": [{"at": None, "reason": f"Initial sample: {len(reps)} cluster representatives and {len(rand)} random picks", "ids": ids}]}
        save("samples.json", sample)

    if load("annotations.json") is None:
        save("annotations.json", {"annotations": [], "reviewed": {}})
    if load("patterns.json") is None:
        save("patterns.json", {"modes": [], "updated_at": None})
    if load("suggestions.json") is None:
        save("suggestions.json", {"suggestions": []})

    print(f"{len(records)} records · {k} clusters · sample of {len(sample['ids'])}: {', '.join(sample['ids'])}")


if __name__ == "__main__":
    main()
