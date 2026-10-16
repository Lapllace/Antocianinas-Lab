# Project-local scientific skill integration

This workspace keeps a minimal, project-specific set of skills under `.agents/skills/` so GitHub Copilot in VS Code can apply the repository's scientific constraints without depending on a global installation.

## Evaluated upstream sources

### Scientific Agent Skills (K-Dense-AI)
Source: https://github.com/K-Dense-AI/scientific-agent-skills
License: MIT
Status: evaluated for scientific literature research, data provenance, and analysis workflows.
Reason not imported directly: the project-local VS Code agent environment does not provide the external plugin installation path, and a direct workspace-only import would require a curated subset of the upstream repository. For this repository, the essential rules were captured in local skills that match the project requirements.

### Superpowers (obra)
Source: https://github.com/obra/superpowers
License: MIT
Status: evaluated for software engineering workflows such as TDD, debugging, and review.
Reason not imported directly: the documented `agy` installation flow is not available in the current environment, and the project already has a working validation workflow with tests. The project-local instruction files therefore prioritize scientific rigor and a small, maintainable workflow.

## Local workspace adaptation
The repository now includes these workspace-compatible skills:
- `scientific-data-integrity`
- `literature-traceability`
- `experimental-planning`

These are intentionally aligned with `AGENTS.md` and `.github/copilot-instructions.md` so they remain explicit and auditable in the project itself.

## Update procedure
When a new upstream skill set is needed, review the licensing and compatibility constraints before copying or adapting any file. Prefer a staged import into `.agents/skills/<skill-name>/SKILL.md` and keep the project instructions synchronized with the local adaptation.
