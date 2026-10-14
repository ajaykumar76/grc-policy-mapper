"""
Where do the mapping errors come from? For every policy statement that has gold
controls, show for each gold control whether it was:
  - not retrieved in the top 10      (retrieval problem)
  - retrieved but outside the top 5  (never shown to the LLM)
  - shown to the LLM but rejected    (LLM judgment problem)
  - accepted
Also compares the gap report with the gaps we EXPECT by design.

Usage:  python src\\05_error_analysis.py [reports\\map_results_<tag>.json]
"""
import json
from collections import Counter

doc = json.load(open("data/sample_policy.json", encoding="utf-8"))
policy = doc["statements"]
scope = doc["scope"]["controls"]
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "reports/map_results.json"
saved = json.load(open(path))
res = saved["results"]
TOP_K = saved["summary"].get("config", {}).get("top_k", 5)
print(f"Analysing {path} (top_k={TOP_K}, config={saved['summary'].get('config')})\n")

counts = Counter()
print("=== Per gold control ===")
for p in policy:
    if not p["gold"]:
        continue
    r = res[p["id"]]
    ranks = {c: i + 1 for i, (c, _) in enumerate(r["cands"])}
    judged = {j["control"]: j for j in r["judged"]}
    for g in p["gold"]:
        if g not in ranks:
            status = "NOT_IN_TOP10"
        elif ranks[g] > TOP_K:
            status = f"RANK_{ranks[g]}_NOT_SHOWN_TO_LLM"
        else:
            v = judged[g]["verdict"]
            status = "ACCEPTED_" + v.upper() if v != "no" else "LLM_REJECTED"
            if judged[g]["flag"]:
                status += "(quote_flag)"
        key = status.split("_NOT_SHOWN")[0] if status.startswith("RANK") else status.replace("(quote_flag)", "")
        counts["RANK_6_10" if status.startswith("RANK") else key] += 1
        print(f"{p['id']} {g:6s} rank={ranks.get(g, '>10'):<4} {status}")

print("\n=== Summary of gold controls ===")
total = sum(counts.values())
for k, v in counts.most_common():
    print(f"  {k:22s} {v}/{total} ({v/total:.0%})")

# Gap report check
covered_by_design = {g for p in policy for g in p["gold"]}
expected_gaps = [c for c in scope if c not in covered_by_design]
supported = set()
for r in res.values():
    for j in r["judged"]:
        if j["verdict"] in ("yes", "partial"):
            supported.add(j["control"])
reported_gaps = [c for c in scope if c not in supported]
false_gaps = [c for c in reported_gaps if c in covered_by_design]
missed_gaps = [c for c in expected_gaps if c in supported]
print(f"\nExpected gaps by design ({len(expected_gaps)}): {expected_gaps}")
print(f"Reported gaps ({len(reported_gaps)}): {reported_gaps}")
print(f"FALSE gaps (policy covers them, tool says no): {len(false_gaps)} {false_gaps}")
print(f"MISSED gaps (tool says supported, policy has no statement): {missed_gaps}")

print("\n=== Sample LLM rejections of gold controls (check the reason) ===")
shown = 0
for p in policy:
    for g in p["gold"]:
        j = {x["control"]: x for x in res[p["id"]]["judged"]}.get(g)
        if j and j["verdict"] == "no" and shown < 6:
            print(f"{p['id']} vs {g}: {j['reason']}")
            shown += 1
