# Workspace agent skills

VS Code documents `.agents/skills/<skill-name>/SKILL.md` as a supported project-skill location. Skills placed here remain scoped to this checkout; they do not install a global agent or prove that a new Copilot Chat session has loaded them.

## Project-specific skills

- `scientific-data-integrity`
- `literature-traceability`
- `experimental-planning`

These local instructions remain unchanged and are aligned with `AGENTS.md`, `.github/copilot-instructions.md`, `README.md`, and `protocol.md`.

## Imported Scientific Agent Skills

Source: [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
Revision: `a1043ef544e3a100c28e70a736b6cf32554d0677`
License: MIT; a copy of the upstream `LICENSE.md` is included in each imported skill directory.

Imported original folders and their original `SKILL.md` files:

- `citation-management` — metadata lookup and citation checking; `requests` is required, `scholarly` is optional for Google Scholar.
- `literature-review` — reproducible search and review workflow; Python 3.10+ and `requests` for cited scripts. Parallel CLI, PDF tooling, and AI-generated schematics are optional and have additional dependencies/credentials.
- `experimental-design` — randomization, blocking, and DOE guidance/scripts; its script environment specifies Python 3.12+, NumPy, pandas, and `pydoe==1.5.0`.
- `statistical-analysis` — test selection, assumptions, effect sizes, and reporting; it specifies a separate environment with Python 3.12+, Pingouin, SciPy, statsmodels, pandas, matplotlib, and seaborn. PyMC and ArviZ are optional.

These tools and optional dependencies have not been installed or run. Do not install their scientific stacks into the project `.venv` without a separate compatibility review. Verify original publications and evidence independently; skills and automated metadata checks are not scientific validation.

## Selected Superpowers skills

Source: [obra/superpowers](https://github.com/obra/superpowers)
Revision: `bb92a77741419a4ab5f06e711a283343f1ada0c3`
License: MIT; a copy of the upstream `LICENSE` is included in each imported skill directory.

Imported original skill folders:

- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`

These are workspace Agent Skills, not an installed or activated Superpowers plugin. The official Superpowers installation documentation lists a GitHub Copilot CLI plugin command, not a native VS Code Copilot Chat plugin. The VS Code Marketplace search also returned `dwaintr.superpowers-vscode` (1.0.0), but its publisher is not the upstream Superpowers project; its linked source repository describes itself as Copilot CLI packaging. It was not installed as an official Superpowers integration. No user-level copy, junction, or alternate installer was added. The `systematic-debugging` folder includes upstream shell-oriented helper material; do not run POSIX scripts from PowerShell without checking compatibility. The separate `writing-plans` skill was not imported because its mandatory plan-file/commit workflow conflicts with this repository's instruction not to create planning documents unless requested.

## Updating imported skills

Before updating, review the upstream skill contents, dependencies, license, and destination for collisions. Import only a selected upstream skill folder and its referenced resources, record its commit and checksums, preserve its upstream `SKILL.md` unchanged, and retain the applicable license. Re-test skill discovery in a fresh VS Code Copilot Chat session; folder presence alone is not evidence of activation.
