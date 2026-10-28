# Repository guidance

## Purpose and navigation

This repository maintains the English-only `olcli-workflow` Codex skill. The skill supports local LaTeX editing with task-scoped delivery and compilation on Overleaf; it does not implement olcli itself.

- [SKILL.md](skills/olcli-workflow/SKILL.md) owns the installable behavior and routing description.
- [UI metadata](skills/olcli-workflow/agents/openai.yaml) owns display strings and implicit invocation.
- [README.md](README.md) owns setup, installation, and compatibility guidance.
- [Behavioral scenarios](tests/scenarios.md) define manual acceptance expectations.
- [Validator](scripts/validate.py), its [tests](tests/test_validate.py), and [CI](.github/workflows/validate.yml) own offline repository checks.

## Editing boundaries

Keep all tracked prose, comments, prompts, and metadata in English. Keep repository maintenance files outside the installable skill. Preserve implicit invocation unless the user specifically requests a different policy.

Preserve the existing scope: confirm the project ID, protect local work, upload only task changes, keep tool confirmations, and check the same cloud build's log. Local-only requests and read-only work must remain local. Do not silently extend authorization to deletions, Git operations, or sharing.

Do not commit authentication material, personal Codex configuration, `.olcli.json`, real project sources, downloaded artifacts, or machine-specific absolute paths. Use placeholders and portable paths in documentation. This repository contains no local TeX dependency.

## Verification

With Python 3.12 and the pinned dependency installed, run:

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
git diff --check
```

The validator must remain offline and read-only. Test it with temporary fixtures. Preserve useful diagnostics for malformed metadata, disabled invocation, language remnants, and broken links. Do not replace behavioral checks with assertions that merely match the skill's wording.

For changes to synchronization, upload, conflict handling, or compilation, update the relevant manual scenarios and perform them in an explicitly authorized disposable project copy. Confirm the copy's ID before every cloud write, preserve the original, and clean the copy and local artifacts afterward. Never use a live original project for test writes.

Documentation-only changes can use offline verification. Report automated results separately from manual cloud evidence. Do not describe a planned or previously observed check as a new successful run. When upgrading olcli, recheck the installed CLI/MCP interfaces and the version-specific cautions before claiming compatibility.

Keep this guidance short. Add plans, logs, dependencies, and additional tooling only when a concrete maintenance task needs them.
