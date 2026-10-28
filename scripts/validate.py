#!/usr/bin/env python3
"""Validate this skill repository without network access or file mutations."""

import argparse
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml


SKILL_PATH = Path("skills/olcli-workflow")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".txt"}
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]")
INLINE_LINK = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:[ \t]+[\"'][^\n]*?[\"'])?\s*\)"
)
REFERENCE_LINK = re.compile(r"(?m)^ {0,3}\[[^\]\n]+\]:[ \t]*(<[^>\n]+>|\S+)")


def load_mapping(text, label, errors):
    """Return a YAML mapping or append a diagnostic."""
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{label}: invalid YAML: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: expected a YAML mapping")
        return None
    return value


def check_skill(text, label, errors):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        errors.append(f"{label}: missing or unclosed YAML frontmatter")
        return
    metadata = load_mapping(match.group(1), label, errors)
    if metadata is None:
        return
    allowed = {"name", "description", "license", "allowed-tools", "metadata"}
    if set(metadata) - allowed:
        errors.append(f"{label}: unsupported frontmatter keys; review the skill schema")
    name = metadata.get("name")
    if not isinstance(name, str) or name != SKILL_PATH.name:
        errors.append(f"{label}: name must match the skill directory '{SKILL_PATH.name}'")
    description = metadata.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        errors.append(f"{label}: description must contain 1-1024 characters")
    elif "<" in description or ">" in description:
        errors.append(f"{label}: description must not contain angle brackets")
    if not text[match.end():].strip():
        errors.append(f"{label}: skill instructions must not be empty")


def check_interface(text, label, errors):
    metadata = load_mapping(text, label, errors)
    if metadata is None:
        return
    interface = metadata.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{label}: interface must be a mapping")
    else:
        display_name = interface.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            errors.append(f"{label}: display_name must be a nonempty string")
        short = interface.get("short_description")
        if not isinstance(short, str) or not 25 <= len(short.strip()) <= 64:
            errors.append(f"{label}: short_description must contain 25-64 characters")
    policy = metadata.get("policy")
    if not isinstance(policy, dict) or policy.get("allow_implicit_invocation") is not True:
        errors.append(f"{label}: policy.allow_implicit_invocation must remain boolean true")


def markdown_prose(text):
    """Mask fenced examples and inline code before checking file links."""
    output = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence is None and marker:
            fence = marker.group(1)
            output.append("\n")
        elif fence is not None:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence) and not marker.group(2).strip():
                fence = None
            output.append("\n")
        else:
            output.append(re.sub(r"(`+).*?\1", "", line))
    return "".join(output)


def check_links(text, path, root, errors):
    prose = markdown_prose(text)
    for pattern in (INLINE_LINK, REFERENCE_LINK):
        for match in pattern.finditer(prose):
            target = match.group(1).strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            relative_path = unquote(url.path)
            base = root if relative_path.startswith("/") else path.parent
            destination = (base / relative_path.lstrip("/")).resolve()
            line = prose.count("\n", 0, match.start()) + 1
            label = f"{path.relative_to(root)}:{line}"
            if not destination.is_relative_to(root):
                errors.append(f"{label}: file link escapes the repository: {target}")
            elif not destination.exists():
                errors.append(f"{label}: broken file link: {target}")


def validate_repository(root):
    """Return actionable errors; leave the repository and credentials untouched."""
    root = Path(root).resolve()
    if not root.is_dir():
        return [f"{root}: repository directory does not exist"]
    errors = []
    texts = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix not in TEXT_SUFFIXES and name != ".gitignore":
                continue
            label = str(path.relative_to(root))
            if path.is_symlink():
                errors.append(f"{label}: use a regular text file rather than a symlink")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errors.append(f"{label}: cannot read UTF-8 text: {exc}")
                continue
            texts[path.relative_to(root)] = text
            match = HAN.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{label}:{line}: contains a Han character; use English text")
            if path.suffix == ".md":
                check_links(text, path, root, errors)
    for relative, checker in (
        (SKILL_PATH / "SKILL.md", check_skill),
        (SKILL_PATH / "agents/openai.yaml", check_interface),
    ):
        if relative in texts:
            checker(texts[relative], str(relative), errors)
        elif not (root / relative).exists():
            errors.append(f"{relative}: required skill file is missing")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Repository validation passed (offline checks only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
