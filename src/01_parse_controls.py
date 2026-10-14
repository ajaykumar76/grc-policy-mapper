"""
Parse the NIST SP 800-53 Rev 5 OSCAL catalog into a flat list of base controls
(id, family, title, statement text, guidance). Public-domain US government text.

Download first (PowerShell, ~10 MB):
  Invoke-WebRequest -Uri "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json" -OutFile data\\raw\\catalog.json

Usage:  python src\\01_parse_controls.py
"""
import json
import re
from pathlib import Path

SRC = Path("data/raw/catalog.json")
OUT = Path("data/processed/controls.json")

INSERT_RE = re.compile(r"\{\{\s*insert:\s*param,\s*([\w.\-]+)\s*\}\}")


def param_text(params):
    """Map param id -> readable placeholder text."""
    out = {}
    for p in params or []:
        if p.get("label"):
            out[p["id"]] = f"[{p['label']}]"
        elif "select" in p:
            out[p["id"]] = "[" + " | ".join(p["select"].get("choice", [])) + "]"
        else:
            out[p["id"]] = "[organization-defined value]"
    return out


def collect_prose(parts, names):
    chunks = []
    for part in parts or []:
        if part.get("name") in names and part.get("prose"):
            chunks.append(part["prose"])
        chunks.extend(collect_prose(part.get("parts"), names))
        # nested statement items (a., b., ...) carry prose without the name filter
        if part.get("name") == "item" and part.get("prose") and "item" in names:
            chunks.append(part["prose"])
    return chunks


def statement_text(control, pmap):
    chunks = []

    def walk(parts):
        for part in parts or []:
            if part.get("prose"):
                chunks.append(part["prose"])
            walk(part.get("parts"))

    for part in control.get("parts", []):
        if part.get("name") == "statement":
            walk([part])
    text = " ".join(chunks)
    return INSERT_RE.sub(lambda m: pmap.get(m.group(1), "[value]"), text)


def guidance_text(control, pmap):
    chunks = []
    for part in control.get("parts", []):
        if part.get("name") == "guidance" and part.get("prose"):
            chunks.append(part["prose"])
    text = " ".join(chunks)
    return INSERT_RE.sub(lambda m: pmap.get(m.group(1), "[value]"), text)


def is_withdrawn(control):
    return any(p.get("name") == "status" and p.get("value") == "withdrawn"
               for p in control.get("props", []))


def main():
    with open(SRC, encoding="utf-8") as f:
        catalog = json.load(f)["catalog"]

    controls = []
    for group in catalog["groups"]:
        for c in group.get("controls", []):          # base controls only, no enhancements
            if is_withdrawn(c):
                continue
            pmap = param_text(c.get("params"))
            stmt = statement_text(c, pmap)
            if not stmt:
                continue
            controls.append({
                "id": c["id"].upper(),
                "family": group["title"],
                "title": c["title"],
                "statement": stmt,
                "guidance": guidance_text(c, pmap),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(controls, f, indent=2)

    families = sorted({c["family"] for c in controls})
    print(f"Parsed {len(controls)} base controls across {len(families)} families")
    ex = next(c for c in controls if c["id"] == "AC-2")
    print(f"\nExample {ex['id']} - {ex['title']} ({ex['family']}):")
    print(ex["statement"][:400], "...")
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()
