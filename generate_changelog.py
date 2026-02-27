#!/usr/bin/env python3
"""
generate_changelog.py

Generates CHANGELOG.md from git history, grouped by version tags.

Commit messages are categorised by conventional-commit prefixes:
  feat:     -> Added
  fix:      -> Fixed
  perf:     -> Fixed  (performance improvements)
  refactor: -> Changed
  chore:    -> Changed
  docs:     -> Changed
  style:    -> Changed
  test:     -> Changed
  build:    -> Changed
  ci:       -> Changed
  revert:   -> Fixed
  break/BREAKING CHANGE -> Breaking Changes

Any commit that doesn't match a prefix lands in "Changed".

Usage:
  python generate_changelog.py                   # writes CHANGELOG.md
  python generate_changelog.py --output OUT.md   # custom output path
  python generate_changelog.py --stdout          # print to stdout only
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ── Conventional-commit prefix → section mapping ────────────────────────────

SECTION_ORDER = ["Breaking Changes", "Added", "Fixed", "Changed"]

PREFIX_TO_SECTION = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Fixed",
    "revert": "Fixed",
    "refactor": "Changed",
    "chore": "Changed",
    "docs": "Changed",
    "doc": "Changed",
    "style": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "infra": "Changed",
}

# Commits matching these patterns anywhere in the subject go to Breaking Changes
BREAKING_PATTERNS = [
    re.compile(r"\bBREAKING[\s_-]CHANGE\b", re.IGNORECASE),
    re.compile(r"^break[:\s]", re.IGNORECASE),
]

# Commits to skip entirely (merge commits, version bumps, etc.)
SKIP_PATTERNS = [
    re.compile(r"^Merge (branch|pull request|remote)", re.IGNORECASE),
    re.compile(r"^Merge [0-9a-f]{7,}", re.IGNORECASE),
    re.compile(r"^bump version", re.IGNORECASE),
    re.compile(r"^release v?\d+\.\d+", re.IGNORECASE),
    re.compile(r"^Initial commit$", re.IGNORECASE),
]


# ── Git helpers ──────────────────────────────────────────────────────────────


def check_git_available() -> None:
    """Exit with a helpful message if git is not on PATH."""
    import shutil

    if shutil.which("git") is None:
        print(
            "Error: git is not installed or not on PATH.\n"
            "\n"
            "Install it with one of:\n"
            "  Docker / Debian / Ubuntu:  apt-get install -y git\n"
            "  Alpine:                    apk add git\n"
            "  macOS (Homebrew):          brew install git\n"
            "  Windows:                   https://git-scm.com/download/win\n",
            file=sys.stderr,
        )
        sys.exit(1)


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Error: could not run {cmd[0]!r} — is git installed?", file=sys.stderr)
        sys.exit(1)


def get_tags() -> list[tuple[str, str]]:
    """
    Return list of (tag_name, iso_date) sorted newest-first.
    Only includes tags that look like version tags (v1.2.3 or 1.2.3).
    """
    raw = run(["git", "tag", "--sort=-version:refname"])
    if not raw:
        return []

    tags = []
    for tag in raw.splitlines():
        tag = tag.strip()
        if not re.match(r"^v?\d+\.\d+", tag):
            continue
        date_str = run(["git", "log", "-1", "--format=%ai", tag])
        try:
            dt = datetime.fromisoformat(date_str)
            tags.append((tag, dt.strftime("%Y-%m-%d")))
        except ValueError:
            tags.append((tag, "unknown"))
    return tags


def get_commits_between(ref_from: str | None, ref_to: str) -> list[dict]:
    """
    Return commit dicts between two refs (exclusive ref_from, inclusive ref_to).
    Format: hash|subject
    """
    if ref_from:
        rev_range = f"{ref_from}..{ref_to}"
    else:
        rev_range = ref_to

    raw = run(["git", "log", rev_range, "--format=%H|%s"])
    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        sha, subject = line.split("|", 1)
        commits.append({"sha": sha[:7], "subject": subject.strip()})
    return commits


def get_unreleased_commits(latest_tag: str | None) -> list[dict]:
    if latest_tag:
        return get_commits_between(latest_tag, "HEAD")
    else:
        raw = run(["git", "log", "--format=%H|%s"])
        commits = []
        for line in raw.splitlines():
            if "|" not in line:
                continue
            sha, subject = line.split("|", 1)
            commits.append({"sha": sha[:7], "subject": subject.strip()})
        return commits


# ── Commit classification ────────────────────────────────────────────────────


def classify(subject: str) -> tuple[str | None, str]:
    """
    Returns (section, cleaned_subject).
    section is None if the commit should be skipped.
    """
    for skip in SKIP_PATTERNS:
        if skip.search(subject):
            return None, subject

    for pattern in BREAKING_PATTERNS:
        if pattern.search(subject):
            cleaned = re.sub(r"^break[:\s]+", "", subject, flags=re.IGNORECASE).strip()
            cleaned = re.sub(
                r"\s*BREAKING[\s_-]CHANGE\b", "", cleaned, flags=re.IGNORECASE
            ).strip()
            return "Breaking Changes", cleaned or subject

    # Match "prefix: message" or "prefix(scope): message"
    m = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?[!]?\s*:\s*(.+)$", subject)
    if m:
        prefix = m.group(1).lower()
        message = m.group(2).strip()
        # Trailing ! means breaking change
        if "!" in subject.split(":")[0]:
            return "Breaking Changes", message
        section = PREFIX_TO_SECTION.get(prefix, "Changed")
        return section, message

    # No prefix — default to Changed
    return "Changed", subject


def categorise_commits(commits: list[dict]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    for c in commits:
        section, message = classify(c["subject"])
        if section is None:
            continue
        # Capitalise first letter
        message = message[0].upper() + message[1:] if message else message
        sections[section].append(message)
    return sections


# ── Markdown rendering ───────────────────────────────────────────────────────


def render_version_block(
    version: str, date: str, sections: dict[str, list[str]]
) -> str:
    lines = [f"## [{version}] — {date}", ""]

    if not any(sections.values()):
        lines.append("_No significant changes._")
        lines.append("")
        return "\n".join(lines)

    for section in SECTION_ORDER:
        items = sections.get(section, [])
        if not items:
            continue
        lines.append(f"### {section}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def generate(repo_path: Path) -> str:
    """Generate full CHANGELOG.md content as a string."""
    import os

    orig_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        tags = get_tags()

        blocks: list[str] = []
        blocks.append("# Changelog\n")
        blocks.append(
            "All notable changes to this project will be documented in this file.\n"
        )
        blocks.append(
            "Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n"
        )

        # Unreleased section
        latest_tag = tags[0][0] if tags else None
        unreleased = get_unreleased_commits(latest_tag)
        unreleased_sections = categorise_commits(unreleased)

        if any(unreleased_sections.values()):
            today = datetime.now().strftime("%Y-%m-%d")
            blocks.append(f"## [Unreleased] — {today}\n")
            for section in SECTION_ORDER:
                items = unreleased_sections.get(section, [])
                if not items:
                    continue
                blocks.append(f"### {section}\n")
                for item in items:
                    blocks.append(f"- {item}")
                blocks.append("")

        # One block per version tag
        for i, (tag, date) in enumerate(tags):
            prev_tag = tags[i + 1][0] if i + 1 < len(tags) else None
            commits = get_commits_between(prev_tag, tag)
            sections = categorise_commits(commits)
            blocks.append(render_version_block(tag, date, sections))

        return "\n".join(blocks).rstrip() + "\n"

    finally:
        os.chdir(orig_dir)


# ── CLI entry point ──────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--repo",
        "-r",
        default=".",
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of writing a file.",
    )
    args = parser.parse_args()

    check_git_available()

    repo_path = Path(args.repo).resolve()
    if not (repo_path / ".git").exists():
        print(
            f"Error: {repo_path} does not appear to be a git repository.",
            file=sys.stderr,
        )
        sys.exit(1)

    content = generate(repo_path)

    if args.stdout:
        print(content)
    else:
        out = Path(args.output)
        out.write_text(content, encoding="utf-8")
        print(f"Written to {out}")


if __name__ == "__main__":
    main()
