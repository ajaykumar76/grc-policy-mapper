# GRC Policy Mapper: Policy-to-Control Mapping with NIST SP 800-53

A research and portfolio prototype that maps fictional organisational policy statements to candidate controls from **NIST SP 800-53 Rev. 5**. It combines semantic retrieval with an optional local LLM review step and produces draft mappings and a policy-gap report for human validation.

> **Important:** This is an educational prototype using a fictional organisation and author-written sample policy statements. It is not an audit tool, a compliance certification, legal advice, or evidence that any real organisation meets NIST requirements. All mappings and gap classifications require review by a qualified person.

## Problem addressed

Security and GRC teams often need to compare policy wording with a control framework. Manually searching a large control catalogue can be time-consuming. This project explores whether semantic retrieval can shortlist relevant controls and whether a local LLM can help assess the strength of a possible mapping.

## How it works

1. **Parse the catalogue:** Read the NIST SP 800-53 Rev. 5 OSCAL JSON catalogue, extract active base controls, statements and guidance, and replace parameter insertions with readable placeholders.
2. **Build embeddings:** Use `all-MiniLM-L6-v2` to embed control titles/statements and sample policy statements.
3. **Retrieve candidates:** Rank controls by cosine similarity and return the top candidates for each policy statement.
4. **LLM-assisted review (optional):** Send the top five candidate controls and one policy statement to `llama3.2` through Ollama. The model returns `yes`, `partial` or `no`, with a supporting quote and short reason.
5. **Apply an evidence guardrail:** If the quoted evidence is not present in the policy statement, downgrade the result to `partial` and flag it for review.
6. **Generate outputs:** Produce a mapping CSV, JSON results, and a draft gap report for a human reviewer.

The LLM is restricted to retrieved control IDs. Its accepted mappings are drafts, not audit conclusions.

## Repository contents

```
data/
  sample_policy.json       Fictional Acme Analytics policy statements,
                           author-defined gold mappings and illustrative scope
src/
  01_parse_controls.py     Parse NIST OSCAL catalogue into base controls
  02_build_index.py        Create sentence-transformer embeddings
  03_map.py                Retrieve and assess candidate mappings
  04_gap_report.py         Generate draft policy-gap report
  05_error_analysis.py     Analyse retrieval and mapping errors
reports/
  mapping.csv              Draft policy-to-control mappings
  map_results.json         Retrieval and mapping results
  gap_report.md            Draft gap report
  map_results_*.json       Earlier experiment outputs
```

Generated catalogue and embedding files are excluded by `.gitignore`. The NIST catalogue must be downloaded and the processing steps run locally before mapping.

## Setup

Requirements: Python, the packages in `requirements.txt`, `numpy`, `sentence-transformers`, and (for LLM review) Ollama with `llama3.2`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt numpy sentence-transformers
ollama pull llama3.2
```

Download the NIST SP 800-53 Rev. 5 OSCAL catalogue (the source URL is also documented in `src/01_parse_controls.py`):

```powershell
New-Item -ItemType Directory -Force data\raw
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json" -OutFile data\raw\catalog.json
```

Run the pipeline from the repository root:

```powershell
python src\01_parse_controls.py
python src\02_build_index.py
python src\03_map.py --retrieval-only
```

To run the LLM-assisted mapping, make sure Ollama is running and execute:

```powershell
python src\03_map.py
python src\04_gap_report.py
python src\05_error_analysis.py
```

The sample policy is fictional and the illustrative control scope is author-selected; it is not an official NIST baseline.

## Current retrieval experiment

The committed retrieval result contains 28 policy statements with author-defined gold control mappings and 3 statements without gold mappings.

| Retrieval measure | Result |
|---|---:|
| Gold control present in top 1 | 16/28 (57%) |
| Gold control present in top 3 | 25/28 (89%) |
| Gold control present in top 5 | 25/28 (89%) |
| Gold control present in top 10 | 26/28 (93%) |

These are retrieval hit rates against the project's own non-exhaustive labels. They do **not** measure compliance, audit effectiveness, or generalisation to real policies. The labels are author-written and the gold mappings are not exhaustive.

The committed illustrative gap report covers 42 selected controls and classifies 19 as supported, 9 as partial/needs review, and 14 as having no policy support found. These are automated draft classifications from the sample policy, not confirmed control gaps.

## Limitations and next steps

- The organisation and policy statements are fictional and manually authored.
- Gold mappings are not exhaustive; reported precision can therefore be understated.
- Semantic similarity is only a candidate-finding method; similar wording does not prove a control is implemented or operating effectively.
- LLM judgments can be wrong, incomplete or inconsistent. The quote check only verifies that quoted words occur in the policy; it does not prove that the quote adequately satisfies a control.
- The sample control scope is illustrative, not a complete or official baseline.
- The current experiment is small and should not be generalised to enterprise policy sets without independent evaluation.
- Next steps include a held-out policy set, reviewer-labelled mappings, clearer precision/recall evaluation, and stronger provenance for each proposed mapping.

## References

- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST OSCAL content repository](https://github.com/usnistgov/oscal-content)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama](https://ollama.com/)
