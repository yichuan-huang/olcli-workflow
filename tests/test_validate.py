"""Exercise validator outcomes with isolated, synthetic repositories."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate.py"
SPEC = importlib.util.spec_from_file_location("repository_validator", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SKILL = """---
name: olcli-workflow
description: Edit associated LaTeX projects through olcli.
---

# Workflow

Preserve local work and verify cloud builds.
"""
INTERFACE = """interface:
  display_name: "olcli Workflow"
  short_description: "Sync LaTeX edits and verify Overleaf cloud builds"
policy:
  allow_implicit_invocation: true
"""


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("skills/olcli-workflow/SKILL.md", SKILL)
        self.write("skills/olcli-workflow/agents/openai.yaml", INTERFACE)
        self.write("README.md", "# Example\n\n[Skill](skills/olcli-workflow/SKILL.md)\n")

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def errors(self):
        return VALIDATOR.validate_repository(self.root)

    def assert_error(self, diagnostic):
        errors = self.errors()
        self.assertTrue(any(diagnostic in error for error in errors), errors)

    def test_valid_repository_is_unchanged(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual([], self.errors())
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_required_file_is_missing(self):
        (self.root / "skills/olcli-workflow/agents/openai.yaml").unlink()
        self.assert_error("required skill file is missing")

    def test_frontmatter_is_missing(self):
        self.write("skills/olcli-workflow/SKILL.md", "# Workflow\n")
        self.assert_error("missing or unclosed YAML frontmatter")

    def test_frontmatter_yaml_is_malformed(self):
        self.write("skills/olcli-workflow/SKILL.md", SKILL.replace("name: olcli-workflow", "name: [unfinished"))
        self.assert_error("invalid YAML")

    def test_description_is_missing(self):
        self.write("skills/olcli-workflow/SKILL.md", SKILL.replace("description: Edit associated LaTeX projects through olcli.\n", ""))
        self.assert_error("description must contain")

    def test_description_has_wrong_type(self):
        self.write("skills/olcli-workflow/SKILL.md", SKILL.replace("description: Edit associated LaTeX projects through olcli.", "description: false"))
        self.assert_error("description must contain")

    def test_skill_name_does_not_match_directory(self):
        self.write("skills/olcli-workflow/SKILL.md", SKILL.replace("name: olcli-workflow", "name: another-skill"))
        self.assert_error("name must match")

    def test_interface_yaml_is_malformed(self):
        self.write("skills/olcli-workflow/agents/openai.yaml", "interface: [unfinished\n")
        self.assert_error("invalid YAML")

    def test_ui_fields_have_invalid_values(self):
        self.write("skills/olcli-workflow/agents/openai.yaml", INTERFACE.replace('"olcli Workflow"', '""').replace('"Sync LaTeX edits and verify Overleaf cloud builds"', '"Too short"'))
        self.assert_error("display_name must be")
        self.assert_error("short_description must contain")

    def test_implicit_invocation_requires_boolean_true(self):
        for value in ("false", '"true"', "null"):
            with self.subTest(value=value):
                self.write("skills/olcli-workflow/agents/openai.yaml", INTERFACE.replace("invocation: true", f"invocation: {value}"))
                self.assert_error("must remain boolean true")

    def test_language_remnant_outside_skill_is_rejected(self):
        self.write("tests/example.py", "# " + chr(0x4E2D) + "\n")
        self.assert_error("tests/example.py:1: contains a Han character")

    def test_broken_inline_link_is_rejected(self):
        self.write("README.md", "[Missing](docs/missing.md)\n")
        self.assert_error("broken file link: docs/missing.md")

    def test_broken_reference_link_is_rejected(self):
        self.write("README.md", "[Read][guide]\n\n[guide]: missing.md\n")
        self.assert_error("broken file link: missing.md")

    def test_external_urls_and_fragments_are_not_fetched(self):
        self.write("README.md", "[External](https://example.invalid/a) [Section](#section)\n")
        self.assertEqual([], self.errors())

    def test_fenced_and_inline_examples_are_ignored(self):
        self.write("README.md", "```md\n[Example](missing.md)\n```\n`[Example](missing.md)`\n")
        self.assertEqual([], self.errors())

    def test_encoded_spaces_and_root_relative_links(self):
        self.write("docs/my guide.md", "# Guide\n")
        self.write("README.md", "[Guide](docs/my%20guide.md#guide) [Root](/README.md)\n")
        self.assertEqual([], self.errors())

    def test_file_link_outside_repository_is_rejected(self):
        self.write("README.md", "[Outside](../outside.md)\n")
        self.assert_error("file link escapes the repository")

    def test_local_environment_and_git_data_are_ignored(self):
        for directory in (".venv", ".git", "__pycache__"):
            self.write(f"{directory}/ignored.md", chr(0x4E2D))
        self.assertEqual([], self.errors())

    def test_invalid_utf8_is_reported(self):
        (self.root / "bad.md").write_bytes(b"\xff")
        self.assert_error("cannot read UTF-8 text")

    def test_cli_exit_status_and_diagnostics(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.write("README.md", "[Missing](missing.md)\n")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn("README.md:1: broken file link", result.stderr)


if __name__ == "__main__":
    unittest.main()
