# Behavioral acceptance scenarios

These are manual scenarios for the Codex workflow, not claims made by the offline validator. Use the applicable scenarios when behavior changes or compatibility with a new olcli version is claimed. No Overleaf login is needed for the repository's automated tests.

## Live-test setup and evidence

Use a disposable Overleaf copy with a unique name and record its ID. Confirm that the association points to that copy. Record the original project's content hashes and root/compiler/TeX Live settings without publishing private project data. Keep local baselines, downloaded output, and logs outside the upload tree.

For each performed scenario, record the olcli version, requested task, local and cloud differences, actual observed result, and cleanup outcome. For a build, retain the returned build identity and inspect its own log and PDF before reporting success. A CLI exit code or a generated PDF alone is insufficient.

## Scenarios

| Scenario | Setup and request | Expected observable result |
| --- | --- | --- |
| Ordinary linked edit | In the associated disposable copy, request a small text or color edit. | Codex safely refreshes, edits, reviews differences, uploads only the task changes, verifies remote content, and checks the same cloud build's log. Refreshing the web editor preserves the edit. Inspect the PDF for a visual change. |
| Local-only edit | Request the same edit with an explicit local-only constraint. | The local source changes; no pull that overwrites files, upload, or cloud compilation occurs. Remote hashes remain unchanged. |
| Read-only request | Ask for an explanation or review of the associated project. | The response contains findings without source changes, uploads, or compilation. |
| Unlinked file | Request an edit in a folder with no `.olcli.json`. | The edit stays local. Codex does not infer a cloud destination or create a project. If cloud delivery was explicitly requested, it asks for the missing association. |
| Incorrect association | Associate the test folder with a missing or inaccessible synthetic ID. | Codex reports the destination problem before a write. It does not select a similarly named project. |
| Cloud-to-local refresh | Edit a test comment in the cloud, save, and request a different local edit. | The fresh cloud comment is preserved locally and in the delivered result. |
| Existing local work | Make an unrelated local edit before requesting a change in another file. | Existing work survives the refresh. It is excluded from the task upload; the intended task changes reach the cloud. |
| Overlapping conflict | Change the same passage locally and remotely without an unambiguous baseline. | Codex preserves both versions and asks about the conflict. It does not force-pull, choose local automatically, or overwrite remote content. |
| Expired authentication | In an isolated test environment, use an invalid temporary session. | Codex reports that login is needed and stops dependent transfers. Local work remains available; credentials are not printed or committed. |
| Compilation failure | Introduce a small, reversible LaTeX error as the requested test change. | Codex identifies the error in that build's log, repairs task-caused errors and recompiles, with at most three correction passes and an earlier stop if no progress occurs. It reports pre-existing or unrelated failures separately. |
| Partial or uncertain upload | Use a controlled failure or simulated tool response after one task file is uploaded. | Codex checks actual remote contents before any retry, preserves local work, and reports uncertainty rather than blindly replaying a write. |
| Existing PDF inputs | Include an existing PDF figure and a PDF with a same-named TeX sibling. | Refresh and task delivery preserve existing cloud inputs. Final build downloads are kept outside the source tree; intentional PDF figures are uploaded explicitly when needed. |
| Confirmation enabled | In an isolated MCP test, leave the olcli opt-out unset and request an upload against a fake Overleaf client. | The server asks an elicitation-capable client before writing. Declining or lacking elicitation support performs no write. Codex does not supply the user's response or evade the approval through another tool. |
| Confirmation opted out | Explicitly configure `OLCLI_MCP_UNCONFIRMED_WRITES=1`, establish a fresh MCP connection, and upload to a fake Overleaf client. | The server reports the opted-out policy and performs the simulated upload without elicitation. The skill adds no separate question for the authorized upload or compile. |
| Codex permissions | Run a task under Codex settings that require approval or deny the relevant operation. | The skill respects that effective policy even when olcli confirmation is disabled. It does not change global settings, treat implicit invocation as permission, or promise that all prompts disappear. |

## Cleanup

Move only the recorded disposable project ID to Overleaf trash; do not empty trash. Remove test sources, baselines, logs, downloaded PDFs, temporary credentials, and test associations. Verify the original project's hashes and settings are unchanged. Retain the normal tool installation and login.

Record skipped or blocked scenarios explicitly. Do not replace missing cloud evidence with a green repository check.
