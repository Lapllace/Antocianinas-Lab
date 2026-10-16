---
name: literature-traceability
description: Use this skill when adding, normalizing, or reviewing literature evidence so every claim keeps source metadata, citation details, and provenance intact.
---

# Literature traceability

This project depends on rigorous source tracking for each bibliographic entry. Use this skill for literature tables, metadata reviews, or claims derived from published work.

## Mandatory provenance fields
- Study identifier and study title
- Authors and year
- DOI and/or URL
- Full bibliographic citation
- Table, figure, section, or page used for the value
- Original value and its unit
- Experimental conditions and matrix context
- Whether the value was directly reported or calculated
- Formula and units used in any derived calculation
- Any uncertainty or limitation documented by the source

## Guardrails
- Do not convert a literature value into an experimental value.
- Do not assume a DOI or mean value if the source cannot support it.
- Do not edit raw literature tables to hide uncertainty or normalize away useful distinctions.
- If a published claim is missing source detail, capture the gap rather than filling it in.

## Review checklist
- The source is stored in `data/literature/` and not mixed with raw measurements.
- The metadata can be traced back to a real publication or an explicit source record.
- Derived values are labeled clearly and remain reproducible.
- The original evidence remains available alongside the normalized or aggregated version.
