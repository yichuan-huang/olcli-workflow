# olcli Workflow

A Codex skill for editing LaTeX locally and delivering changes to Overleaf through [olcli](https://github.com/aloth/olcli). In a project already linked by `.olcli.json`, an editing request includes safely refreshing the sources, editing, reviewing differences, uploading task changes, and checking a cloud build and its log. Before an MCP write, the workflow automatically disables olcli's extra write-confirmation layer so approvals follow Codex's active settings.

No local TeX distribution is required. This is an instruction skill for Codex, not a file watcher: a manual save or OneDrive update does not automatically upload anything to Overleaf.

## Requirements

- Codex with local skill support and access to the project directory.
- An authenticated installation of `@aloth/olcli`. This workflow was developed against **0.15.2**; its version-specific cautions are documented in the [skill](skills/olcli-workflow/SKILL.md). Recheck those cautions when upgrading olcli.
- A project root containing a valid `.olcli.json` association with the intended Overleaf project ID. Confirm the ID before editing.
- Access to olcli's CLI and, when using the MCP tools, an existing `olcli-mcp` connection. The workflow handles its confirmation setting automatically within Codex's permissions.

For a new setup, install the tested package and authenticate with your Overleaf email. The command prompts for the password:

```sh
npm install -g @aloth/olcli@0.15.2
olcli auth --email "you@example.com"
olcli whoami
olcli list
```

To establish a local association, pull the selected project into a new or empty folder:

```sh
olcli pull "PROJECT_ID" "./my-paper"
```

Use the actual ID from your own account. Keep authentication secrets out of prompts, command arguments, repository files, and logs. This repository contains neither an Overleaf account nor an MCP server implementation.

## Install the skill

Ask Codex to use its skill installer with this source:

```text
Use $skill-installer to install the skill from
https://github.com/yichuan-huang/olcli-workflow/tree/main/skills/olcli-workflow
```

Alternatively, clone this repository and copy only `skills/olcli-workflow/` into `${CODEX_HOME:-$HOME/.codex}/skills/olcli-workflow/`. If the destination already exists, review the differences and back it up before replacing it. Do not copy the repository-level maintenance instructions into the installed skill.

Reload Codex after installation so it discovers the skill. [UI metadata](skills/olcli-workflow/agents/openai.yaml) keeps implicit invocation enabled; explicit invocation is also available as `$olcli-workflow`.

## Use

Open the associated local project in Codex and make a normal editing request, for example:

```text
Revise the introduction for clarity, preserving the technical claims.
```

The skill treats task-scoped upload and cloud compilation as part of the editing request. Adopting this workflow also authorizes its automatic olcli confirmation setup, subject to Codex permissions. Installing it does not override Codex permissions or managed policy. A narrower request such as "edit locally only" takes precedence.

Existing local work is preserved. Unclear conflicts require a decision. Questions, read-only reviews, and unlinked files do not initiate uploads. Deletions, Git operations, and sharing changes require a separate request. Only a verified association determines the cloud destination.

Local projects can live in an available OneDrive folder. OneDrive replication, olcli transfers, and Git version control remain separate operations.

## Permissions and confirmation

The skill follows Codex's active permissions and approval settings. It does not define an independent permission profile, change global approval or sandbox settings, or add its own confirmation for already authorized uploads and builds. Required client and tool approvals still apply. The skill's `allow_implicit_invocation` metadata controls discovery, not execution privileges.

olcli 0.15.2 separately asks for confirmation before MCP writes by default. Before an authorized MCP write, this skill checks the effective configuration for the existing olcli server. If the extra confirmation is still enabled, Codex sets `OLCLI_MCP_UNCONFIRMED_WRITES` to `1` in that server's environment. If the opt-out is already enabled, the configuration is left untouched. There is no recurring manual opt-out step or separate skill-level approval question; any configuration access or approval required by Codex still applies.

The resulting setting looks like this for a server named `overleaf`; the actual server name and configuration location are discovered rather than assumed:

```toml
[mcp_servers.overleaf.env]
OLCLI_MCP_UNCONFIRMED_WRITES = "1"
```

Codex reconnects the affected MCP server when supported and verifies the policy on a fresh connection. If the client cannot reconnect, the setting is saved and a one-time Codex reload is reported as necessary for the running connection. A reload is distinct from manually disabling confirmation. The preflight preserves other environment variables, server options, global Codex permissions, and managed restrictions. An explicit user request to retain olcli confirmation takes precedence over this default.

The switch applies to all writes exposed by that olcli MCP server, including deletion and renaming tools; those operations remain outside this skill's default task authorization. Questions, read-only reviews, local-only work, and unlinked files do not trigger configuration changes. CLI-only work does not create an MCP connection. A remaining Codex permission prompt must be handled under Codex's active policy.

See the [olcli write-confirmation documentation](https://github.com/aloth/olcli/blob/v0.15.2/docs/MCP.md#write-confirmation) and [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). No account credentials belong in the example above or in this repository.

## Maintain and validate

The installable skill is under `skills/olcli-workflow/`. Repository-only guidance is in [AGENTS.md](AGENTS.md), and realistic behavioral checks are in [tests/scenarios.md](tests/scenarios.md).

Use Python **3.12** for the maintenance tools. The only additional validation dependency is pinned in [requirements-dev.txt](requirements-dev.txt):

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

[GitHub Actions](.github/workflows/validate.yml) runs the same offline validator and tests on pushes, pull requests, and manual dispatch. It uses read-only repository permissions and no Overleaf credentials. The validator checks skill metadata, UI configuration, implicit invocation, Han character remnants, and relative Markdown file links. English prose still requires human review; external URLs and link fragments are not fetched or validated.

Passing CI proves these repository checks passed. It does not prove that Codex selected the skill, preserved a real conflict, uploaded a file, or compiled on Overleaf. Changes to synchronization or compilation behavior require the relevant manual scenarios in a disposable project copy. Documentation-only changes do not require a live cloud run. Confirmation-policy checks can use an isolated MCP server with a fake Overleaf client, without a cloud write.

## Compatibility and verification

The workflow's operational guidance targets olcli **0.15.2**. Its initial development included checks of bidirectional transfer, local source editing, and Overleaf compilation in a disposable project. Language, maintenance tooling, and confirmation-policy updates do not constitute a new run of those cloud checks. Future maintainers must record the version, scenario, observed evidence, and cleanup outcome when performing live acceptance.

This repository is published without an additional license file.
