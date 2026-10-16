---
name: scientific-data-integrity
description: Use this skill when validating scientific provenance, data separation, and safe handling of raw, literature, and simulation files in the anthocyanin stability project.
---

# Scientific data integrity

Use this skill whenever a change could affect data provenance, source integrity, or the boundary between experimental evidence and simulation.

## Required checks
- Confirm whether the file belongs to `data/raw/`, `data/literature/`, `data/simulation/`, or `data/processed/`.
- Preserve original values and source metadata.
- Do not mix simulated outputs with experimental measurements.
- Keep literature evidence separate from laboratory measurements.
- If a value is derived from a source, mark it as calculated and record the formula or transformation.

## Decision rules
- If a record is from the lab, treat it as experimental evidence and keep it in raw or processed experimental folders.
- If a record is from a published source, keep it in `data/literature/` and preserve DOI, citation, figure/table, unit, and conditions.
- If a record is from a scenario model or demo run, keep it in `data/simulation/` and label it `SIMULATION_ONLY`.
- If a row may be ambiguous, do not silently reinterpret it; add a note or stop for confirmation.

## Validation before completion
- Check that no scientific file has been overwritten without justification.
- Confirm that any new output is stored in the correct separation bucket.
- Verify that the change preserves existing tests and does not modify protected input data without traceability.
