---
name: experimental-planning
description: Use this skill when designing experimental protocols, working with batch structure, or planning storage and pH conditions while preserving independence between lots.
---

# Experimental planning

Use this skill before adding a new plan or modifying the experiment design for anthocyanin stability work.

## Core constraints
- Use independent batches as the unit of experimental replication.
- Keep `BASELINE` and stored-time observations clearly separated.
- Keep pH, temperature, light, oxygen, and packaging conditions explicitly documented.
- Treat the day-0 shared baseline as a valid reference but do not treat all observations from the same vial as independent replicates.
- Do not claim a condition is optimal without experimental evidence.

## Recommended design pattern
- Use multiple independent extractions as the main source of variation.
- Compare relevant formulations with the same extraction lot and consistent acidification method.
- Separate the baseline sample from storage-time samples with explicit `storage_condition` values.
- Use stored conditions such as `C4_DARK` and `C25_DARK` consistently and document the actual temperature.

## Output expectations
- Keep the plan consistent with `README.md` and `protocol.md`.
- Record whether a number is a hypothesis, an observed measurement, or a derived calculation.
- Preserve any data origin markers used by the analysis pipeline.
- Recommend the smallest credible design that can test the scientific question rather than over-claiming certainty.
